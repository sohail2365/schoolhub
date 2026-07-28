from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TestRecordCreate(BaseModel):
    student_id: int = Field(gt=0)
    term_type: str  # "monthly" or "annual"
    period: str = Field(min_length=4, max_length=20)  # "2026-07" or "2026"
    subject: str = Field(min_length=1, max_length=100)
    marks_obtained: float = Field(ge=0)
    total_marks: float = Field(gt=0, default=100)
    remarks: str | None = Field(default=None, max_length=255)

    @field_validator("term_type")
    @classmethod
    def validate_term_type(cls, v):
        v = str(v).strip().lower()
        if v not in ("monthly", "annual"):
            raise ValueError("term_type must be 'monthly' or 'annual'")
        return v


class TestRecordUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=100)
    marks_obtained: float | None = Field(default=None, ge=0)
    total_marks: float | None = Field(default=None, gt=0)
    remarks: str | None = Field(default=None, max_length=255)


class TestRecordOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    term_type: str
    period: str
    subject: str
    marks_obtained: float
    total_marks: float
    percentage: float
    remarks: str | None = None
    image_url: str | None = None
    recorded_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
