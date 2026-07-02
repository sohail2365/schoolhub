from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class SchoolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=50)
    address: str | None = None

class SchoolRegisterRequest(BaseModel):
    school_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    admin_name: str = Field(min_length=2, max_length=150)

class SchoolProfileOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    city: str | None = None
    address: str | None = None
    principal_name: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SchoolProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    city: str | None = Field(default=None, max_length=50)
    address: str | None = None
    principal_name: str | None = Field(default=None, max_length=100)