from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.attendance import Attendance
from backend.models.fee import Fee
from backend.models.grade import Grade
from backend.models.payment import Payment
from backend.models.student import Student
from backend.schemas.student import StudentCreate, StudentOut, StudentUpdate
from backend.utils.jwt_handler import verify_token
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(
    class_name: str | None = Query(default=None, alias="class"),
    search: str | None = None,
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    query = db.query(Student).filter(Student.school_id == token["school_id"])

    if class_name:
        query = query.filter(Student.class_name == class_name)
    if search:
        query = query.filter(Student.name.ilike(f"%{search}%"))

    return query.order_by(Student.id.desc()).all()


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
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
    return student


@router.get("/{student_id}/profile")
def get_student_profile(
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

    attendance_records = (
        db.query(Attendance)
        .filter(Attendance.school_id == token["school_id"], Attendance.student_id == student_id)
        .order_by(Attendance.date.desc())
        .all()
    )
    total_marked = len(attendance_records)
    present_count = sum(1 for a in attendance_records if a.is_present)
    attendance_rate = round((present_count / total_marked) * 100, 2) if total_marked else 0.0

    grades = (
        db.query(Grade)
        .filter(Grade.school_id == token["school_id"], Grade.student_id == student_id)
        .order_by(Grade.exam_date.desc().nullslast(), Grade.id.desc())
        .all()
    )
    avg_percentage = round(sum(g.percentage for g in grades) / len(grades), 2) if grades else 0.0

    fees = (
        db.query(Fee)
        .filter(Fee.school_id == token["school_id"], Fee.student_id == student_id)
        .order_by(Fee.id.desc())
        .all()
    )
    total_fee_amount = round(sum(f.amount for f in fees), 2)
    total_paid = round(sum(f.paid_amount for f in fees), 2)
    total_due = round(total_fee_amount - total_paid, 2)

    fee_ids = [f.id for f in fees]
    payments = (
        db.query(Payment)
        .filter(Payment.school_id == token["school_id"], Payment.fee_id.in_(fee_ids))
        .order_by(Payment.payment_date.desc())
        .all()
        if fee_ids
        else []
    )

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "father_name": student.father_name,
            "mother_name": student.mother_name,
            "class_name": student.class_name,
            "roll_number": student.roll_number,
            "email": student.email,
            "phone": student.phone,
            "gender": student.gender,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "address": student.address,
        },
        "attendance": {
            "total_marked": total_marked,
            "present": present_count,
            "absent": total_marked - present_count,
            "attendance_rate": attendance_rate,
            "recent_records": [
                {"date": a.date.isoformat(), "is_present": a.is_present, "remarks": a.remarks}
                for a in attendance_records[:15]
            ],
        },
        "grades": {
            "average_percentage": avg_percentage,
            "records": [
                {
                    "id": g.id,
                    "subject": g.subject,
                    "marks_obtained": g.marks_obtained,
                    "total_marks": g.total_marks,
                    "percentage": g.percentage,
                    "grade": g.grade,
                    "exam_date": g.exam_date.isoformat() if g.exam_date else None,
                }
                for g in grades
            ],
        },
        "fees": {
            "total_amount": total_fee_amount,
            "total_paid": total_paid,
            "total_due": total_due,
            "records": [
                {
                    "id": f.id,
                    "fee_name": f.fee_name,
                    "amount": f.amount,
                    "paid_amount": f.paid_amount,
                    "due_amount": f.due_amount,
                    "status": f.status,
                    "due_date": f.due_date.isoformat() if f.due_date else None,
                    "month": f.month,
                }
                for f in fees
            ],
            "payments": [
                {
                    "id": p.id,
                    "fee_id": p.fee_id,
                    "amount_paid": p.amount_paid,
                    "payment_date": p.payment_date.isoformat(),
                    "payment_method": p.payment_method,
                    "receipt_number": p.receipt_number,
                }
                for p in payments
            ],
        },
    }


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()

    # ✅ FIX: normalize gender safely
    if "gender" in data and data["gender"] not in ["male", "female", "other"]:
        data["gender"] = None
    if payload.date_of_birth and payload.date_of_birth > date.today():
        raise HTTPException(status_code=422, detail="DOB cannot be a future date")

    exists = (
        db.query(Student)
        .filter(
            Student.school_id == token["school_id"],
            Student.class_name == payload.class_name,
            Student.roll_number == payload.roll_number,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Roll number already exists in this class")

    student = Student(
        school_id=token["school_id"],
        **data,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == token["school_id"])
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    data = payload.model_dump(exclude_unset=True)

    if "date_of_birth" in data and data["date_of_birth"] and data["date_of_birth"] > date.today():
        raise HTTPException(status_code=422, detail="DOB cannot be a future date")

    if "roll_number" in data or "class_name" in data:
        check_class_name = data.get("class_name", student.class_name)
        check_roll_number = data.get("roll_number", student.roll_number)
        duplicate = (
            db.query(Student)
            .filter(
                Student.school_id == token["school_id"],
                Student.class_name == check_class_name,
                Student.roll_number == check_roll_number,
                Student.id != student_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Roll number already exists in this class")

    for key, value in data.items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == token["school_id"])
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return None


@router.get("/{student_id}/report")
def student_report(
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

    return {
        "student_id": student.id,
        "name": student.name,
        "class_name": student.class_name,
        "message": "Detailed report endpoint ready for grades/attendance aggregation",
    }
