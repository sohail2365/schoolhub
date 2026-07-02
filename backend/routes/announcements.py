from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.announcement import Announcement
from backend.schemas.announcement import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementOut])
def list_announcements(
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (
        db.query(Announcement)
        .filter(
            Announcement.school_id == token["school_id"],
            (Announcement.expires_at.is_(None)) | (Announcement.expires_at >= now),
        )
        .order_by(Announcement.created_at.desc())
        .all()
    )


@router.post("", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    item = Announcement(
        school_id=token["school_id"],
        title=payload.title,
        content=payload.content,
        created_by=token["user_id"],
        expires_at=payload.expires_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    item = (
        db.query(Announcement)
        .filter(
            Announcement.id == announcement_id,
            Announcement.school_id == token["school_id"],
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    item = (
        db.query(Announcement)
        .filter(
            Announcement.id == announcement_id,
            Announcement.school_id == token["school_id"],
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")

    db.delete(item)
    db.commit()
    return None
