from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.attendance import Attendance
from backend.models.fee import Fee, FeeStatus
from backend.models.grade import Grade
from backend.models.payment import Payment
from backend.models.student import Student
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard_summary(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    school_id = token["school_id"]

    students = db.query(Student).filter(Student.school_id == school_id).count()
    fees = db.query(Fee).filter(Fee.school_id == school_id).all()
    grades = db.query(Grade).filter(Grade.school_id == school_id).all()

    total_fee = round(sum(f.amount for f in fees), 2)
    total_paid = round(sum(f.paid_amount for f in fees), 2)
    avg_grade = round(sum(g.percentage for g in grades) / len(grades), 2) if grades else 0.0

    return {
        "school_id": school_id,
        "total_students": students,
        "fees_total": total_fee,
        "fees_collected": total_paid,
        "fees_due": round(total_fee - total_paid, 2),
        "average_percentage": avg_grade,
    }


@router.get("/attendance-today")
def attendance_today(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    today = date.today()
    records = (
        db.query(Attendance)
        .filter(Attendance.school_id == token["school_id"], Attendance.date == today)
        .all()
    )
    total = len(records)
    present = sum(1 for r in records if r.is_present)

    return {
        "date": today.isoformat(),
        "total_marked": total,
        "present": present,
        "absent": total - present,
    }


@router.get("/metrics")
def dashboard_metrics(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    """Get dashboard metrics for professional dashboard"""
    school_id = token["school_id"]

    # Total students
    total_students = db.query(Student).filter(Student.school_id == school_id).count()
    
    # Fees data
    fees = db.query(Fee).filter(Fee.school_id == school_id).all()
    total_fees_amount = round(sum(f.amount for f in fees), 2)
    total_fees_paid = round(sum(f.paid_amount for f in fees), 2)
    total_fees_due = round(total_fees_amount - total_fees_paid, 2)
    pending_fees_count = sum(1 for f in fees if f.paid_amount < f.amount)
    
    # Attendance data
    attendance_records = db.query(Attendance).filter(Attendance.school_id == school_id).all()
    attendance_rate = 0.0
    if attendance_records:
        present_count = sum(1 for a in attendance_records if a.is_present)
        attendance_rate = round((present_count / len(attendance_records)) * 100, 2)
    
    return {
        "total_students": total_students,
        "total_fees_amount": total_fees_amount,
        "total_fees_due": total_fees_due,
        "total_fees_paid": total_fees_paid,
        "pending_fees_count": pending_fees_count,
        "attendance_rate": attendance_rate,
    }


@router.get("/daily-digest")
def daily_digest(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    school_id = token["school_id"]
    today = date.today()

    total_students = db.query(Student).filter(Student.school_id == school_id).count()

    today_attendance = (
        db.query(Attendance)
        .filter(Attendance.school_id == school_id, Attendance.date == today)
        .all()
    )
    marked = len(today_attendance)
    present = sum(1 for a in today_attendance if a.is_present)
    absent = marked - present
    attendance_rate_today = round((present / marked) * 100, 2) if marked else None

    fees = db.query(Fee).filter(Fee.school_id == school_id).all()
    total_due = round(sum(f.due_amount for f in fees), 2)
    overdue_count = sum(1 for f in fees if f.status != FeeStatus.paid and f.due_amount > 0)

    payments_today = (
        db.query(Payment)
        .filter(Payment.school_id == school_id, Payment.payment_date == today)
        .all()
    )
    collected_today = round(sum(p.amount_paid for p in payments_today), 2)

    return {
        "date": today.isoformat(),
        "total_students": total_students,
        "attendance": {
            "marked": marked,
            "present": present,
            "absent": absent,
            "not_marked": total_students - marked if total_students >= marked else 0,
            "attendance_rate_today": attendance_rate_today,
        },
        "fees": {
            "collected_today": collected_today,
            "total_outstanding": total_due,
            "overdue_count": overdue_count,
        },
    }


@router.get("/recent-activities")
def recent_activities(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    school_id = token["school_id"]

    latest_students = (
        db.query(Student)
        .filter(Student.school_id == school_id)
        .order_by(Student.created_at.desc())
        .limit(5)
        .all()
    )
    latest_fees = (
        db.query(Fee)
        .filter(Fee.school_id == school_id)
        .order_by(Fee.updated_at.desc())
        .limit(5)
        .all()
    )

    return {
        "students": [
            {"id": s.id, "name": s.name, "created_at": s.created_at.isoformat()}
            for s in latest_students
        ],
        "fees": [
            {"id": f.id, "fee_name": f.fee_name, "updated_at": f.updated_at.isoformat()}
            for f in latest_fees
        ],
    }