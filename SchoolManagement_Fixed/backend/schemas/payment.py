from datetime import date, datetime
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    fee_id: int = Field(gt=0)
    amount_paid: float = Field(gt=0)
    payment_date: date | None = None
    payment_method: str | None = None
    receipt_number: str | None = Field(default=None, max_length=100)


class PaymentOut(BaseModel):
    id: int
    school_id: int
    fee_id: int
    amount_paid: float
    payment_date: date
    payment_method: str | None = None
    receipt_number: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
