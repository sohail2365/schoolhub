from datetime import datetime
from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=2)
    expires_at: datetime | None = None


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    content: str | None = Field(default=None, min_length=2)
    expires_at: datetime | None = None


class AnnouncementOut(BaseModel):
    id: int
    school_id: int
    title: str
    content: str
    created_by: int | None = None
    created_at: datetime
    expires_at: datetime | None = None

    class Config:
        from_attributes = True

