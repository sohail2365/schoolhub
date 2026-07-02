from datetime import date as dt_date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.attendance import Attendance
from backend.models.student import Student
from backend.schemas.attendance import AttendanceCreate, AttendanceOut, AttendanceUpdate
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/attendance", tags=["attendance"])


# ✅ NEW: List all attendance records for the school (optional date / student filters).
# Purely additive — does not change any existing endpoint.
@router.get("", response_model=list[AttendanceOut])
def list_attendance(
    date: dt_date | None = None,
    student_id: int | None = None,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    query = db.query(Attendance).filter(Attendance.school_id == token["school_id"])
    if date:
        query = query.filter(Attendance.date == date)
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    return query.order_by(Attendance.date.desc(), Attendance.id.desc()).all()


@router.get("/date/{date}", response_model=list[AttendanceOut])
def get_attendance_by_date(
    date: dt_date,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    return (
        db.query(Attendance)
        .filter(Attendance.school_id == token["school_id"], Attendance.date == date)
        .order_by(Attendance.id.desc())
        .all()
    )


@router.get("/student/{student_id}", response_model=list[AttendanceOut])
def get_student_attendance(
    student_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    return (
        db.query(Attendance)
        .filter(
            Attendance.school_id == token["school_id"],
            Attendance.student_id == student_id,
        )
        .order_by(Attendance.date.desc())
        .all()
    )


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    payload: AttendanceCreate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    if payload.date > dt_date.today():
        raise HTTPException(
            status_code=422,
            detail="Attendance can only be marked for current or past dates",
        )

    student = (
        db.query(Student)
        .filter(
            Student.id == payload.student_id,
            Student.school_id == token["school_id"],
        )
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.school_id == token["school_id"],
            Attendance.student_id == payload.student_id,
            Attendance.date == payload.date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked for this date")

    record = Attendance(
        school_id=token["school_id"],
        student_id=payload.student_id,
        date=payload.date,
        is_present=payload.is_present,
        remarks=payload.remarks,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ✅ NEW: Update an existing attendance record. Purely additive.
@router.put("/{attendance_id}", response_model=AttendanceOut)
def update_attendance(
    attendance_id: int,
    payload: AttendanceUpdate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id, Attendance.school_id == token["school_id"])
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


# ✅ NEW: Delete an attendance record. Purely additive.
@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    attendance_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id, Attendance.school_id == token["school_id"])
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(record)
    db.commit()
    return None


@router.get("/report/{student_id}")
def attendance_report_student(
    student_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Attendance)
        .filter(
            Attendance.school_id == token["school_id"],
            Attendance.student_id == student_id,
        )
        .all()
    )
    total = len(records)
    present = sum(1 for r in records if r.is_present)
    percentage = round((present / total) * 100, 2) if total else 0.0

    return {
        "student_id": student_id,
        "total_days": total,
        "present_days": present,
        "attendance_percentage": percentage,
        "absent_dates": [r.date.isoformat() for r in records if not r.is_present],
    }


@router.get("/class/{class_name}/report")
def attendance_report_class(
    class_name: str,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    students = (
        db.query(Student)
        .filter(
            Student.school_id == token["school_id"],
            Student.class_name == class_name,
        )
        .all()
    )

    result = []
    for s in students:
        records = (
            db.query(Attendance)
            .filter(
                Attendance.school_id == token["school_id"],
                Attendance.student_id == s.id,
            )
            .all()
        )
        total = len(records)
        present = sum(1 for r in records if r.is_present)
        pct = round((present / total) * 100, 2) if total else 0.0
        result.append(
            {
                "student_id": s.id,
                "student_name": s.name,
                "attendance_percentage": pct,
            }
        )

    return {"class_name": class_name, "students": result}