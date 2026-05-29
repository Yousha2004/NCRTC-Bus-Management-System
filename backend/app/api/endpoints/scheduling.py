from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Duty, Route, RouteStop, Stop, Bus
from app.models.user import User
from app.api.deps import get_current_user, check_role, scope_to_depot, sees_all_depots
from geoalchemy2.functions import ST_AsGeoJSON
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import List, Optional
import json

router = APIRouter()


# ---------- Routes ----------
class RouteStopIn(BaseModel):
    stop_id: int
    sequence: int
    planned_offset_min: int = 0


class RouteCreate(BaseModel):
    code: str
    route_name: str
    depot_id: int
    stops: List[RouteStopIn] = []


@router.get("/routes")
def get_routes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = scope_to_depot(db.query(Route), Route, current_user)
    out = []
    for r in q.all():
        stops = [
            {"stop_id": rs.stop_id, "name": rs.stop.name if rs.stop else None,
             "sequence": rs.sequence, "planned_offset_min": rs.planned_offset_min}
            for rs in r.stops
        ]
        out.append({"id": r.id, "code": r.code, "route_name": r.route_name,
                    "depot_id": r.depot_id, "stops": stops})
    return out


@router.post("/routes", dependencies=[Depends(check_role(["admin"]))])
def create_route(payload: RouteCreate, db: Session = Depends(get_db)):
    if db.query(Route).filter(Route.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Route code already exists")
    route = Route(code=payload.code, route_name=payload.route_name, depot_id=payload.depot_id)
    db.add(route)
    db.flush()
    # build ordered stops + derive the path geometry from their locations
    coords = []
    for s in sorted(payload.stops, key=lambda x: x.sequence):
        stop = db.query(Stop).filter(Stop.id == s.stop_id).first()
        if not stop:
            raise HTTPException(status_code=400, detail=f"Stop {s.stop_id} not found")
        db.add(RouteStop(route_id=route.id, stop_id=s.stop_id,
                         sequence=s.sequence, planned_offset_min=s.planned_offset_min))
        pt = json.loads(db.scalar(ST_AsGeoJSON(stop.location)))
        coords.append(tuple(pt["coordinates"]))
    if len(coords) >= 2:
        route.path = from_shape(LineString(coords), srid=4326)
    db.commit()
    db.refresh(route)
    return {"id": route.id, "code": route.code, "route_name": route.route_name}


@router.get("/stops")
def get_stops(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [{"id": s.id, "name": s.name} for s in db.query(Stop).order_by(Stop.name).all()]


# ---------- Assignment dropdown helpers ----------
@router.get("/vehicles")
def get_vehicles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = scope_to_depot(db.query(Bus), Bus, current_user)
    return [{"id": b.id, "bus_number": b.bus_number, "depot_id": b.depot_id} for b in q.all()]


@router.get("/drivers")
def get_drivers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(User).join(User.role).filter(User.role.has(name="driver"))
    if not sees_all_depots(current_user):
        q = q.filter(User.depot_id == current_user.depot_id)
    return [{"id": u.id, "full_name": u.full_name, "username": u.username,
             "depot_id": u.depot_id} for u in q.all()]


# ---------- Duties / roster ----------
class DutyCreate(BaseModel):
    date: date
    bus_id: int
    route_id: int
    driver_id: int
    conductor_id: Optional[int] = None
    start_time: datetime
    end_time: datetime


def _duty_dict(d: Duty):
    return {
        "id": d.id,
        "date": str(d.date),
        "bus_id": d.bus_id,
        "bus_number": d.bus.bus_number if d.bus else None,
        "route_id": d.route_id,
        "route_name": d.route.route_name if d.route else None,
        "driver_id": d.driver_id,
        "driver_name": d.driver.full_name if d.driver else None,
        "conductor_id": d.conductor_id,
        "depot_id": d.depot_id,
        "start_time": d.start_time,
        "end_time": d.end_time,
        "status": d.status,
        "ack_at": d.ack_at,
    }


@router.get("/duties")
def get_duties(
    week_start: Optional[str] = Query(None, description="Monday of the week, YYYY-MM-DD"),
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = scope_to_depot(db.query(Duty), Duty, current_user)
    if depot_id is not None:
        q = q.filter(Duty.depot_id == depot_id)
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
        q = q.filter(Duty.date >= start, Duty.date < start + timedelta(days=7))
    return [_duty_dict(d) for d in q.order_by(Duty.date, Duty.start_time).all()]


@router.post("/duties", dependencies=[Depends(check_role(["admin", "depot_manager", "control_operator"]))])
def assign_duty(payload: DutyCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    bus = db.query(Bus).filter(Bus.id == payload.bus_id).first()
    if not bus:
        raise HTTPException(status_code=400, detail="Vehicle not found")
    # prevent double-booking a driver on the same day
    clash = db.query(Duty).filter(Duty.date == payload.date, Duty.driver_id == payload.driver_id).first()
    if clash:
        raise HTTPException(status_code=400, detail="Driver already has a duty that day")
    duty = Duty(
        date=payload.date, bus_id=payload.bus_id, route_id=payload.route_id,
        driver_id=payload.driver_id, conductor_id=payload.conductor_id,
        depot_id=bus.depot_id, start_time=payload.start_time, end_time=payload.end_time,
        status="draft",
    )
    db.add(duty)
    db.commit()
    db.refresh(duty)
    return _duty_dict(duty)


class PublishIn(BaseModel):
    date: date
    depot_id: Optional[int] = None


@router.post("/duties/publish", dependencies=[Depends(check_role(["admin", "depot_manager", "control_operator"]))])
def publish_duties(payload: PublishIn, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    q = db.query(Duty).filter(Duty.date == payload.date, Duty.status == "draft")
    if not sees_all_depots(current_user):
        q = q.filter(Duty.depot_id == current_user.depot_id)
    elif payload.depot_id is not None:
        q = q.filter(Duty.depot_id == payload.depot_id)
    count = 0
    for d in q.all():
        d.status = "published"
        count += 1
    db.commit()
    return {"published": count, "date": str(payload.date)}


@router.get("/duties/today")
def my_duty_today(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    duty = (
        db.query(Duty)
        .filter(Duty.driver_id == current_user.id, Duty.date == date.today())
        .order_by(Duty.start_time)
        .first()
    )
    if not duty:
        return None
    return _duty_dict(duty)


@router.post("/duties/{duty_id}/acknowledge")
def acknowledge_duty(duty_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    duty = db.query(Duty).filter(Duty.id == duty_id).first()
    if not duty:
        raise HTTPException(status_code=404, detail="Duty not found")
    if duty.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your duty")
    duty.status = "acknowledged"
    duty.ack_at = datetime.utcnow()
    db.commit()
    db.refresh(duty)
    return _duty_dict(duty)
