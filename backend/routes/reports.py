from datetime import date as dt_date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.attendance import Attendance
from backend.models.fee import Fee
from backend.models.grade import Grade
from backend.models.student import Student
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


def _validate_range(start_date: dt_date, end_date: dt_date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="End date must be greater than start date")
    if end_date > dt_date.today():
        raise HTTPException(status_code=422, detail="Reports can only be generated for completed ranges")


@router.get("/attendance/{start_date}/{end_date}")
def attendance_report_range(
    start_date: dt_date,
    end_date: dt_date,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    _validate_range(start_date, end_date)

    records = (
        db.query(Attendance)
        .filter(
            Attendance.school_id == token["school_id"],
            Attendance.date >= start_date,
            Attendance.date <= end_date,
        )
        .all()
    )

    total = len(records)
    present = sum(1 for r in records if r.is_present)
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_records": total,
        "present_records": present,
        "attendance_percentage": round((present / total) * 100, 2) if total else 0.0,
    }


@router.get("/performance/{student_id}")
def performance_report_student(
    student_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == token["school_id"])
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    grades = (
        db.query(Grade)
        .filter(Grade.school_id == token["school_id"], Grade.student_id == student_id)
        .order_by(Grade.exam_date.asc(), Grade.id.asc())
        .all()
    )

    avg = round(sum(g.percentage for g in grades) / len(grades), 2) if grades else 0.0
    trend = "no_data"
    if len(grades) >= 2:
        trend = "improving" if grades[-1].percentage > grades[0].percentage else "declining"

    return {
        "student_id": student.id,
        "student_name": student.name,
        "average_percentage": avg,
        "trend": trend,
        "grades_count": len(grades),
    }


@router.get("/fees-collection")
def fees_collection_report(
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    fees = db.query(Fee).filter(Fee.school_id == token["school_id"]).all()
    total = round(sum(f.amount for f in fees), 2)
    paid = round(sum(f.paid_amount for f in fees), 2)

    return {
        "school_id": token["school_id"],
        "total_fee_amount": total,
        "collected_amount": paid,
        "due_amount": round(total - paid, 2),
        "collection_rate": round((paid / total) * 100, 2) if total else 0.0,
    }


@router.get("/class/{class_name}/performance")
def class_performance_report(
    class_name: str,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    students = (
        db.query(Student)
        .filter(Student.school_id == token["school_id"], Student.class_name == class_name)
        .all()
    )

    output = []
    for s in students:
        grades = db.query(Grade).filter(
            Grade.school_id == token["school_id"],
            Grade.student_id == s.id,
        ).all()
        avg = round(sum(g.percentage for g in grades) / len(grades), 2) if grades else 0.0
        output.append(
            {
                "student_id": s.id,
                "student_name": s.name,
                "average_percentage": avg,
            }
        )

    return {"class_name": class_name, "students": output}
