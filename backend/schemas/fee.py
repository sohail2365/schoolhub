from datetime import date, datetime
from pydantic import BaseModel, Field


class FeeCreate(BaseModel):
    student_id: int = Field(gt=0)
    fee_name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    due_date: date | None = None
    month: str | None = Field(default=None, max_length=20)


class FeeUpdate(BaseModel):
    fee_name: str | None = Field(default=None, min_length=1, max_length=100)
    amount: float | None = Field(default=None, gt=0)
    due_date: date | None = None
    month: str | None = Field(default=None, max_length=20)


class FeeOut(BaseModel):
    id: int
    school_id: int
    student_id: int
    fee_name: str | None = None
    amount: float
    due_date: date | None = None
    paid_amount: float
    due_amount: float
    month: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
