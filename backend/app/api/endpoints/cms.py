from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Notice
from app.api.deps import get_current_user, check_role
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter()

class NoticeCreate(BaseModel):
    title: str
    content: str

@router.get("/", response_model=List[dict])
def get_notices(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    notices = db.query(Notice).order_by(Notice.created_at.desc()).all()
    return [{
        "id": n.id,
        "title": n.title,
        "content": n.content,
        "created_at": n.created_at
    } for n in notices]

@router.post("/", dependencies=[Depends(check_role(["admin", "control_operator", "depot_manager"]))])
def create_notice(notice: NoticeCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    db_notice = Notice(**notice.dict(), created_by=current_user.id)
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return db_notice
