from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.school import School
from backend.models.student import Student
from backend.models.user import User
from backend.utils.super_admin import verify_super_admin

router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/schools", dependencies=[Depends(verify_super_admin)])
def list_all_schools(db: Session = Depends(get_db)):
    schools = db.query(School).order_by(School.created_at.desc()).all()

    result = []
    for school in schools:
        student_count = db.query(Student).filter(Student.school_id == school.id).count()
        admin_user = db.query(User).filter(User.school_id == school.id, User.role == "admin").first()
        result.append({
            "id": school.id,
            "name": school.name,
            "email": school.email,
            "phone": school.phone,
            "city": school.city,
            "is_active": school.is_active,
            "student_count": student_count,
            "admin_email": admin_user.email if admin_user else None,
            "created_at": school.created_at.isoformat() if school.created_at else None,
        })

    return {
        "total_schools": len(result),
        "active_schools": sum(1 for s in result if s["is_active"]),
        "schools": result,
    }


@router.post("/schools/{school_id}/deactivate", dependencies=[Depends(verify_super_admin)])
def deactivate_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    school.is_active = False
    db.commit()
    return {"message": f"'{school.name}' has been deactivated. All logins for this school are now blocked."}


@router.post("/schools/{school_id}/reactivate", dependencies=[Depends(verify_super_admin)])
def reactivate_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    school.is_active = True
    db.commit()
    return {"message": f"'{school.name}' has been reactivated."}


@router.delete("/schools/{school_id}", dependencies=[Depends(verify_super_admin)])
def delete_school(school_id: int, db: Session = Depends(get_db)):
    """
    PERMANENT. Deletes the school and everything under it (students, fees,
    staff, users, attendance, grades, announcements — all of it), relying
    on the ON DELETE CASCADE foreign keys already set up on every table.
    There's no undo — this is meant for genuine cleanup (spam/test/demo
    signups you don't want kept around), not routine account management.
    Use /deactivate instead if you just want to block access but keep data.
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    school_name = school.name
    db.delete(school)
    db.commit()
    return {"message": f"'{school_name}' and all its data have been permanently deleted."}
