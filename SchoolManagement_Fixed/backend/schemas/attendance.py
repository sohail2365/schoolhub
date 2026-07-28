from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


class AttendanceCreate(BaseModel):
    student_id: int = Field(gt=0)
    date: date
    is_present: bool = True
    remarks: str | None = Field(default=None, max_length=255)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date):
        if v > date.today():
            raise ValueError("Attendance can only be marked for current or past dates")
        return v


class AttendanceOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    date: date
    is_present: bool
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendanceUpdate(BaseModel):
    is_present: bool | None = None
    remarks: str | None = Field(default=None, max_length=255)