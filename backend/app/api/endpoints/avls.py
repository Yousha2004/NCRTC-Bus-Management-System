from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Bus, BusLocationHistory, Depot, Duty
from app.models.user import User
from app.api.deps import get_current_user, scope_to_depot
from geoalchemy2.functions import ST_AsGeoJSON
from datetime import datetime, date, timedelta
from typing import Optional
import json

router = APIRouter()


def _point(db, geom):
    if geom is None:
        return None
    return json.loads(db.scalar(ST_AsGeoJSON(geom)))


def _today_duty(db: Session, bus_id: int):
    return (
        db.query(Duty)
        .filter(Duty.bus_id == bus_id, Duty.date == date.today())
        .order_by(Duty.start_time)
        .first()
    )


@router.get("/depots")
def list_depots(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Depot)
    if current_user.role.name not in ("admin", "control_operator"):
        q = q.filter(Depot.id == current_user.depot_id)
    return [{"id": d.id, "code": d.code, "name": d.name} for d in q.all()]


@router.get("/live")
def get_live_locations(
    depot_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = scope_to_depot(db.query(Bus), Bus, current_user)
    if depot_id is not None:
        q = q.filter(Bus.depot_id == depot_id)
    result = []
    for bus in q.all():
        duty = _today_duty(db, bus.id)
        result.append({
            "id": bus.id,
            "bus_number": bus.bus_number,
            "model": bus.model,
            "status": bus.status,
            "depot_id": bus.depot_id,
            "speed": round(bus.current_speed or 0.0, 1),
            "location": _point(db, bus.current_location),
            "last_updated": bus.last_updated,
            "driver": duty.driver.full_name if duty and duty.driver else None,
            "route": duty.route.route_name if duty and duty.route else None,
        })
    return result


@router.get("/vehicle/{bus_id}")
def vehicle_detail(bus_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    duty = _today_duty(db, bus_id)
    # last 30 minutes of pings as an ordered polyline
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    pings = (
        db.query(BusLocationHistory)
        .filter(BusLocationHistory.bus_id == bus_id, BusLocationHistory.timestamp >= cutoff)
        .order_by(BusLocationHistory.timestamp)
        .all()
    )
    trail = [_point(db, p.location)["coordinates"] for p in pings]
    return {
        "id": bus.id,
        "bus_number": bus.bus_number,
        "model": bus.model,
        "status": bus.status,
        "speed": round(bus.current_speed or 0.0, 1),
        "depot": bus.depot.name if bus.depot else None,
        "driver": duty.driver.full_name if duty and duty.driver else None,
        "route": duty.route.route_name if duty and duty.route else None,
        "location": _point(db, bus.current_location),
        "recent_trail": trail,
    }


@router.get("/history/{bus_id}")
def get_bus_history(
    bus_id: int,
    on: Optional[str] = Query(None, description="Date as YYYY-MM-DD; defaults to today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    day = datetime.strptime(on, "%Y-%m-%d").date() if on else date.today()
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    pings = (
        db.query(BusLocationHistory)
        .filter(
            BusLocationHistory.bus_id == bus_id,
            BusLocationHistory.timestamp >= start,
            BusLocationHistory.timestamp < end,
        )
        .order_by(BusLocationHistory.timestamp)
        .all()
    )
    path = []
    for p in pings:
        loc = _point(db, p.location)
        path.append({
            "coordinates": loc["coordinates"],
            "speed": round(p.speed or 0.0, 1),
            "timestamp": p.timestamp,
        })
    return {"bus_id": bus_id, "date": str(day), "count": len(path), "path": path}
