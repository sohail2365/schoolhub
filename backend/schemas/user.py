from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    token: str
    access_token: str
    user_id: int
    role: str
    school_id: int


class RefreshResponse(BaseModel):
    new_access_token: str