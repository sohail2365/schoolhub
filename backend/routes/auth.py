from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.school import School
from backend.models.user import User, UserRole
from backend.schemas.school import SchoolRegisterRequest
from backend.schemas.user import AuthResponse, LoginRequest, RefreshRequest, RefreshResponse
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
        token=token, access_token=token, user_id=admin.id, role=admin.role.value, school_id=school.id
    )

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token = create_access_token(
        {"school_id": user.school_id, "user_id": user.id, "role": user.role.value}
    )
    return AuthResponse(
        token=token, access_token=token, user_id=user.id, role=user.role.value, school_id=user.school_id
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

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}