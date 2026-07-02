from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


class GradeCreate(BaseModel):
    student_id: int = Field(gt=0)
    subject: str = Field(min_length=1, max_length=100)
    marks_obtained: float = Field(ge=0)
    total_marks: float = Field(gt=0, default=100)
    teacher_id: int | None = None
    exam_date: date | None = None

    @field_validator("exam_date")
    @classmethod
    def validate_exam_date(cls, v: date | None):
        if v and v > date.today():
            raise ValueError("Grades cannot be entered for future dates")
        return v


class GradeUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=100)
    marks_obtained: float | None = Field(default=None, ge=0)
    total_marks: float | None = Field(default=None, gt=0)
    teacher_id: int | None = None
    exam_date: date | None = None


class GradeOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    subject: str
    marks_obtained: float
    total_marks: float
    percentage: float
    grade: str | None = None
    teacher_id: int | None = None
    exam_date: date | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
