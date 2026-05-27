from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Incident
from app.api.deps import get_current_user, check_role
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class IncidentCreate(BaseModel):
    bus_id: int
    description: str
    severity: str
    status: Optional[str] = "open"

@router.get("/", response_model=List[dict])
def get_incidents(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    incidents = db.query(Incident).all()
    return [{
        "id": i.id,
        "bus_id": i.bus_id,
        "description": i.description,
        "severity": i.severity,
        "status": i.status,
        "reported_at": i.reported_at
    } for i in incidents]

@router.post("/")
def report_incident(incident: IncidentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_incident = Incident(**incident.dict())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

@router.patch("/{incident_id}")
def update_incident(incident_id: int, status: str, db: Session = Depends(get_db), current_user=Depends(check_role(["admin", "control_operator"]))):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if db_incident:
        db_incident.status = status
        db.commit()
        db.refresh(db_incident)
    return db_incident
