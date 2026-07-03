import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.config import settings
from backend.database import get_db
from backend.models.password_reset import PasswordResetToken
from backend.models.school import School
from backend.models.user import User, UserRole
from backend.schemas.school import SchoolRegisterRequest
from backend.schemas.user import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    ResetPasswordRequest,
)
from backend.utils.email import send_password_reset_email
from backend.utils.jwt_handler import create_access_token, decode_token
from backend.utils.password import hash_password, validate_password_strength, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_school(payload: SchoolRegisterRequest, db: Session = Depends(get_db)):
    validate_password_strength(payload.password)

    if db.query(School).filter(School.email == payload.email).first():
        raise HTTPException(status_code=409, detail="School email already exists")

    school = School(
        name=payload.school_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(school)
    db.flush()

    admin = User(
        school_id=school.id,
        username=payload.email.split("@")[0],
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.admin_name,
        role=UserRole.admin,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token(
        {"school_id": school.id, "user_id": admin.id, "role": admin.role.value}
    )
    return AuthResponse(
        token=token, access_token=token, user_id=admin.id, role=admin.role.value, school_id=school.id,
        full_name=admin.full_name, email=admin.email, school_name=school.name
    )

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    school = db.query(School).filter(School.id == user.school_id).first()
    if school and not school.is_active:
        raise HTTPException(status_code=403, detail="This school's account has been deactivated. Please contact support.")

    token = create_access_token(
        {"school_id": user.school_id, "user_id": user.id, "role": user.role.value}
    )
    return AuthResponse(
        token=token, access_token=token, user_id=user.id, role=user.role.value, school_id=user.school_id,
        full_name=user.full_name, email=user.email, school_name=school.name if school else ""
    )

@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    token = create_access_token(
        {
            "school_id": data["school_id"],
            "user_id": data["user_id"],
            "role": data["role"],
        }
    )
    return RefreshResponse(new_access_token=token)

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Always return the same response whether or not the email exists —
    # otherwise this endpoint becomes a way to check which emails are
    # registered, which is a privacy/enumeration leak.
    generic_response = {"message": "If that email is registered, a reset link has been sent."}

    if not user:
        return generic_response

    # Invalidate any previous unused tokens for this user before issuing a new one.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used == False  # noqa: E712
    ).update({"used": True})

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()

    reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password.html?token={token}"
    send_password_reset_email(user.email, reset_link, user.full_name or "there")

    return generic_response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    validate_password_strength(payload.new_password)

    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token, PasswordResetToken.used == False)  # noqa: E712
        .first()
    )

    if not reset_token or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    reset_token.used = True
    db.commit()

    return {"message": "Password reset successfully. You can now log in with your new password."}


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}