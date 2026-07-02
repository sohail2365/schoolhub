from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    token: str
    access_token: str
    user_id: int
    role: str
    school_id: int
    full_name: str
    email: str
    school_name: str


class RefreshResponse(BaseModel):
    new_access_token: str