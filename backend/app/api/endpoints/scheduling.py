from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Schedule, Route, Bus
from app.api.deps import get_current_user, check_role
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter()

class ScheduleCreate(BaseModel):
    bus_id: int
    route_id: int
    driver_id: int
    conductor_id: int
    departure_time: datetime
    arrival_time: datetime

@router.get("/", response_model=List[dict])
def get_schedules(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    schedules = db.query(Schedule).all()
    result = []
    for s in schedules:
        result.append({
            "id": s.id,
            "bus_number": s.bus.bus_number,
            "route_name": s.route.route_name,
            "departure_time": s.departure_time,
            "arrival_time": s.arrival_time
        })
    return result

@router.post("/", dependencies=[Depends(check_role(["admin", "control_operator"]))])
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/routes")
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).all()
