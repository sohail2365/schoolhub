from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.school import School
from backend.models.student import Student
from backend.models.user import User
from backend.schemas.school import SchoolCreate, SchoolProfileOut, SchoolProfileUpdate
from backend.utils.jwt_handler import verify_token
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/schools", tags=["schools"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db)):
    existing_name = db.query(School).filter(School.name == payload.name).first()
    if existing_name:
        raise HTTPException(status_code=409, detail="School name already exists")
    
    existing_email = db.query(School).filter(School.email == payload.email).first() if payload.email else None
    if existing_email:
        raise HTTPException(status_code=409, detail="School email already exists")
    
    school = School(
        name=payload.name,
        email=payload.email or f"admin@{payload.name.lower().replace(' ', '')}.com",
        phone=payload.phone,
        city=payload.city,
        address=payload.address,
        password_hash="temp",
    )
    
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return {
        "id": school.id,
        "name": school.name,
        "city": school.city,
        "email": school.email,
        "message": "School created successfully"
    }

@router.get("/profile", response_model=SchoolProfileOut)
def get_school_profile(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == token.get("school_id")).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.put("/profile", response_model=SchoolProfileOut)
def update_school_profile(payload: SchoolProfileUpdate, token: dict = Depends(require_roles(["admin"])), db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == token.get("school_id")).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(school, key, value)

    db.commit()
    db.refresh(school)
    return school

@router.get("/stats")
def school_stats(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    school_id = token.get("school_id")
    total_students = db.query(Student).filter(Student.school_id == school_id).count()
    total_users = db.query(User).filter(User.school_id == school_id).count()
    return {
        "school_id": school_id,
        "total_students": total_students,
        "total_users": total_users,
    }