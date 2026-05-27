from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Bus
from app.api.deps import get_current_user
from geoalchemy2.functions import ST_AsGeoJSON
import json

router = APIRouter()

@router.get("/live")
def get_live_locations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    buses = db.query(Bus).all()
    result = []
    for bus in buses:
        location = None
        if bus.current_location is not None:
            loc_json = db.scalar(ST_AsGeoJSON(bus.current_location))
            location = json.loads(loc_json)

        result.append({
            "id": bus.id,
            "bus_number": bus.bus_number,
            "model": bus.model,
            "status": bus.status,
            "location": location,
            "last_updated": bus.last_updated
        })
    return result

@router.get("/history/{bus_id}")
def get_bus_history(bus_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    return {"bus_id": bus_id, "history": []}
