from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Incident, IncidentEvent, Bus, Duty
from app.models.user import User
from app.api.deps import get_current_user, check_role, scope_to_depot
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

router = APIRouter()

VALID_STATUSES = ["open", "acknowledged", "in_progress", "resolved", "closed"]


class IncidentCreate(BaseModel):
    type: str = "other"          # breakdown | accident | complaint | other
    severity: str = "P3"         # P1 | P2 | P3
    description: str
    bus_id: Optional[int] = None


class StatusChange(BaseModel):
    status: str
    note: str


class AssignIn(BaseModel):
    assigned_to: int


def _incident_summary(i: Incident):
    return {
        "id": i.id,
        "type": i.type,
        "severity": i.severity,
        "status": i.status,
        "description": i.description,
        "bus_id": i.bus_id,
        "bus_number": i.bus.bus_number if i.bus else None,
        "depot_id": i.depot_id,
        "raised_by": i.raiser.full_name if i.raiser else None,
        "assigned_to": i.assignee.full_name if i.assignee else None,
        "assigned_to_id": i.assigned_to,
        "reported_at": i.reported_at,
        "resolved_at": i.resolved_at,
    }


@router.get("/", response_model=List[dict])
def get_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    depot_id: Optional[int] = Query(None),
    mine: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = scope_to_depot(db.query(Incident), Incident, current_user)
    if status:
        q = q.filter(Incident.status == status)
    if severity:
        q = q.filter(Incident.severity == severity)
    if depot_id is not None:
        q = q.filter(Incident.depot_id == depot_id)
    if mine:
        q = q.filter((Incident.raised_by == current_user.id) | (Incident.assigned_to == current_user.id))
    q = q.order_by(Incident.reported_at.desc())
    return [_incident_summary(i) for i in q.all()]


def _create(db, *, type, severity, description, bus_id, user, location=None):
    depot_id = user.depot_id
    if bus_id:
        bus = db.query(Bus).filter(Bus.id == bus_id).first()
        if bus:
            depot_id = bus.depot_id
    inc = Incident(
        type=type, severity=severity, status="open", description=description,
        bus_id=bus_id, depot_id=depot_id, raised_by=user.id, location=location,
    )
    db.add(inc)
    db.flush()
    db.add(IncidentEvent(incident_id=inc.id, actor_id=user.id,
                         from_status=None, to_status="open", note="Incident raised"))
    db.commit()
    db.refresh(inc)
    return inc


@router.post("/")
def report_incident(payload: IncidentCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    inc = _create(db, type=payload.type, severity=payload.severity,
                  description=payload.description, bus_id=payload.bus_id, user=current_user)
    return _incident_summary(inc)


@router.post("/panic")
def panic(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Driver panic button: auto-create a P1 breakdown for the driver's vehicle today."""
    duty = (
        db.query(Duty)
        .filter(Duty.driver_id == current_user.id, Duty.date == date.today())
        .first()
    )
    bus_id = duty.bus_id if duty else None
    location = duty.bus.current_location if duty and duty.bus else None
    inc = _create(
        db, type="breakdown", severity="P1",
        description=f"PANIC raised by {current_user.full_name or current_user.username}",
        bus_id=bus_id, user=current_user, location=location,
    )
    return _incident_summary(inc)


@router.get("/{incident_id}")
def incident_detail(incident_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = _incident_summary(inc)
    data["events"] = [{
        "ts": e.ts,
        "actor": e.actor.full_name if e.actor else None,
        "from_status": e.from_status,
        "to_status": e.to_status,
        "note": e.note,
    } for e in inc.events]
    return data


@router.post("/{incident_id}/status")
def change_status(incident_id: int, payload: StatusChange, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use one of {VALID_STATUSES}")
    if not payload.note.strip():
        raise HTTPException(status_code=400, detail="A note is required for every status change")
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    old = inc.status
    inc.status = payload.status
    if payload.status == "resolved" and inc.resolved_at is None:
        inc.resolved_at = datetime.utcnow()
    db.add(IncidentEvent(incident_id=inc.id, actor_id=current_user.id,
                         from_status=old, to_status=payload.status, note=payload.note))
    db.commit()
    db.refresh(inc)
    return _incident_summary(inc)


@router.post("/{incident_id}/assign",
             dependencies=[Depends(check_role(["admin", "control_operator", "depot_manager"]))])
def assign_incident(incident_id: int, payload: AssignIn, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    assignee = db.query(User).filter(User.id == payload.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=400, detail="Assignee not found")
    inc.assigned_to = payload.assigned_to
    db.add(IncidentEvent(incident_id=inc.id, actor_id=current_user.id,
                         from_status=inc.status, to_status=inc.status,
                         note=f"Assigned to {assignee.full_name or assignee.username}"))
    db.commit()
    db.refresh(inc)
    return _incident_summary(inc)
