# backend/routes/filters.py

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.attendance import Attendance
from backend.models.fee import Fee, FeeStatus
from backend.models.grade import Grade
from backend.models.school import School
from backend.models.student import Student
from backend.schemas.student import StudentOut
from backend.utils.rbac import require_roles
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/filters", tags=["filters"])


# =============== SCHEMAS ===============

class FilterSchema(BaseModel):
    search: Optional[str] = None
    class_name: Optional[str] = None
    attendance_status: Optional[str] = None  # present, absent
    fee_status: Optional[str] = None  # pending, partial, paid
    date: Optional[str] = None  # for attendance filter


# =============== FILTER ENDPOINTS ===============

@router.post("/students", response_model=list[StudentOut])
def filter_students(
    filters: FilterSchema,
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    """
    Advanced student filtering with multiple criteria.

    Supports:
    - Search by name or roll number
    - Filter by class
    - Filter by today's attendance
    - Filter by fee status
    """
    school_id = token["school_id"]
    query = db.query(Student).filter(Student.school_id == school_id)

    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                Student.name.ilike(search_term),
                Student.roll_number.ilike(search_term),
                Student.father_name.ilike(search_term),
            )
        )

    if filters.class_name:
        query = query.filter(Student.class_name == filters.class_name)

    if filters.attendance_status:
        today = datetime.now().date()

        if filters.attendance_status == "present":
            attendance_ids = (
                db.query(Attendance.student_id)
                .filter(
                    Attendance.school_id == school_id,
                    Attendance.date == today,
                    Attendance.is_present == True,
                )
                .all()
            )
        elif filters.attendance_status == "absent":
            attendance_ids = (
                db.query(Attendance.student_id)
                .filter(
                    Attendance.school_id == school_id,
                    Attendance.date == today,
                    Attendance.is_present == False,
                )
                .all()
            )
        else:
            attendance_ids = []

        student_ids = [a[0] for a in attendance_ids]
        query = query.filter(Student.id.in_(student_ids))

    if filters.fee_status:
        try:
            status_value = FeeStatus(filters.fee_status)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid fee_status value")

        fee_ids = (
            db.query(Fee.student_id)
            .filter(Fee.school_id == school_id, Fee.status == status_value)
            .all()
        )
        student_ids = [f[0] for f in fee_ids]
        query = query.filter(Student.id.in_(student_ids))

    return query.all()


@router.get("/classes")
def get_available_classes(
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    """Get list of available classes from school settings."""
    school = db.query(School).filter(School.id == token["school_id"]).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    classes = school.active_classes.split(",") if school.active_classes else []
    classes = [c.strip() for c in classes if c.strip()]

    return {"classes": classes, "total": len(classes)}


@router.get("/attendance-status/{student_id}")
def get_today_attendance(
    student_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    """Check today's attendance for a student."""
    today = datetime.now().date()

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.school_id == token["school_id"],
            Attendance.student_id == student_id,
            Attendance.date == today,
        )
        .first()
    )

    if not attendance:
        return {"status": "not_marked", "message": "Attendance not marked yet"}

    return {
        "status": "present" if attendance.is_present else "absent",
        "is_present": attendance.is_present,
        "date": attendance.date.isoformat(),
    }


@router.get("/analytics")
def get_analytics(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    """
    Get all analytics data for dashboard cards.

    Returns:
    - Total students
    - Average attendance
    - Fee collection
    - Class performance
    - Pending fees
    - Top performers
    - Low attendance count
    - Overdue fees
    """
    school_id = token["school_id"]
    today = datetime.now().date()

    # Total Students
    total_students = db.query(Student).filter(Student.school_id == school_id).count()

    # Average Attendance Today
    total_marked = (
        db.query(Attendance)
        .filter(Attendance.school_id == school_id, Attendance.date == today)
        .count()
    )
    present_today = (
        db.query(Attendance)
        .filter(
            Attendance.school_id == school_id,
            Attendance.date == today,
            Attendance.is_present == True,
        )
        .count()
    )
    avg_attendance = round((present_today / total_marked * 100)) if total_marked > 0 else 0

    # Fee Collection
    paid_fees = (
        db.query(Fee)
        .filter(Fee.school_id == school_id, Fee.status == FeeStatus.paid)
        .all()
    )
    total_collected = sum(f.amount for f in paid_fees)

    # Class Performance (Average Grade)
    grades = db.query(Grade).filter(Grade.school_id == school_id).all()
    if grades:
        percentages = [g.percentage for g in grades]
        avg_grade = round(sum(percentages) / len(percentages))
    else:
        avg_grade = 0

    # Pending Fees Amount
    pending_fees = (
        db.query(Fee)
        .filter(Fee.school_id == school_id, Fee.status == FeeStatus.pending)
        .all()
    )
    total_pending = sum(f.amount for f in pending_fees)

    # Top Performers (Grade > 85%)
    top_performers_count = len([g for g in grades if g.percentage > 85]) if grades else 0

    # Low Attendance (< 75%)
    all_students = db.query(Student).filter(Student.school_id == school_id).all()
    low_attendance_count = 0

    for student in all_students:
        total_days = (
            db.query(Attendance)
            .filter(Attendance.school_id == school_id, Attendance.student_id == student.id)
            .count()
        )
        present_days = (
            db.query(Attendance)
            .filter(
                Attendance.school_id == school_id,
                Attendance.student_id == student.id,
                Attendance.is_present == True,
            )
            .count()
        )

        if total_days > 0:
            attendance_percent = (present_days / total_days) * 100
            if attendance_percent < 75:
                low_attendance_count += 1

    # Overdue Fees (due_date < today, still pending)
    overdue_fees_count = (
        db.query(Fee)
        .filter(
            Fee.school_id == school_id,
            Fee.status == FeeStatus.pending,
            Fee.due_date < today,
        )
        .count()
    )

    return {
        "total_students": total_students,
        "avg_attendance": f"{avg_attendance}%",
        "fee_collection": f"PKR {total_collected:,.0f}",
        "class_performance": f"{avg_grade}%",
        "pending_fees": f"PKR {total_pending:,.0f}",
        "top_performers": top_performers_count,
        "low_attendance": low_attendance_count,
        "overdue_fees": overdue_fees_count,
    }