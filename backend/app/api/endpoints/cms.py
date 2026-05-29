from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.bus import Notice, NoticeRead
from app.models.user import User
from app.api.deps import get_current_user, check_role
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class NoticeCreate(BaseModel):
    title: str
    content: str
    audience: str = "all"            # all | role:<role> | depot:<depot_id>
    publish_at: Optional[datetime] = None


def _matches_audience(notice: Notice, user: User) -> bool:
    aud = notice.audience or "all"
    if aud == "all":
        return True
    if aud.startswith("role:"):
        return user.role.name == aud.split(":", 1)[1]
    if aud.startswith("depot:"):
        return str(user.depot_id) == aud.split(":", 1)[1]
    return False


def _target_users(db: Session, notice: Notice) -> List[User]:
    aud = notice.audience or "all"
    q = db.query(User)
    if aud.startswith("role:"):
        role = aud.split(":", 1)[1]
        q = q.join(User.role).filter(User.role.has(name=role))
    elif aud.startswith("depot:"):
        q = q.filter(User.depot_id == int(aud.split(":", 1)[1]))
    return q.all()


@router.get("/", response_model=List[dict])
def get_notices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    is_admin = current_user.role.name == "admin"
    read_ids = {r.notice_id for r in db.query(NoticeRead).filter(NoticeRead.user_id == current_user.id).all()}
    out = []
    for n in db.query(Notice).order_by(Notice.publish_at.desc()).all():
        published = (n.publish_at or n.created_at) <= now
        # admins see everything (for management); others see published notices aimed at them
        if not is_admin and (not published or not _matches_audience(n, current_user)):
            continue
        out.append({
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "audience": n.audience,
            "publish_at": n.publish_at,
            "created_at": n.created_at,
            "read": n.id in read_ids,
        })
    return out


@router.post("/", dependencies=[Depends(check_role(["admin", "control_operator", "depot_manager"]))])
def create_notice(payload: NoticeCreate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    notice = Notice(
        title=payload.title, content=payload.content, audience=payload.audience,
        publish_at=payload.publish_at or datetime.utcnow(), created_by=current_user.id,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return {"id": notice.id, "title": notice.title, "audience": notice.audience}


@router.post("/{notice_id}/read")
def mark_read(notice_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    existing = (
        db.query(NoticeRead)
        .filter(NoticeRead.notice_id == notice_id, NoticeRead.user_id == current_user.id)
        .first()
    )
    if not existing:
        db.add(NoticeRead(notice_id=notice_id, user_id=current_user.id))
        db.commit()
    return {"notice_id": notice_id, "read": True}


@router.get("/{notice_id}/receipts", dependencies=[Depends(check_role(["admin", "depot_manager", "control_operator"]))])
def read_receipts(notice_id: int, db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    read_at = {r.user_id: r.read_at for r in notice.reads}
    targets = _target_users(db, notice)
    rows = [{
        "user_id": u.id,
        "full_name": u.full_name or u.username,
        "read": u.id in read_at,
        "read_at": read_at.get(u.id),
    } for u in targets]
    read_count = sum(1 for r in rows if r["read"])
    return {
        "notice_id": notice_id,
        "title": notice.title,
        "audience": notice.audience,
        "total": len(rows),
        "read_count": read_count,
        "receipts": rows,
    }
