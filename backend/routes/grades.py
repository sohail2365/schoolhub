from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.grade import Grade
from backend.models.student import Student
from backend.schemas.grade import GradeCreate, GradeOut, GradeUpdate
from backend.utils.jwt_handler import verify_token
from backend.utils.rbac import require_roles

router = APIRouter(prefix="/grades", tags=["grades"])


def _grade_letter(percentage: float) -> str:
    if percentage >= 80:
        return "A"
    if percentage >= 60:
        return "B"
    if percentage >= 40:
        return "C"
    if percentage >= 25:
        return "D"
    return "F"


# ✅ NEW: List all grades for the school (optional student_id / subject filters).
# Purely additive — does not change any existing endpoint.
@router.get("", response_model=list[GradeOut])
def list_grades(
    student_id: int | None = None,
    subject: str | None = None,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    query = db.query(Grade).filter(Grade.school_id == token["school_id"])
    if student_id:
        query = query.filter(Grade.student_id == student_id)
    if subject:
        query = query.filter(Grade.subject == subject)
    return query.order_by(Grade.id.desc()).all()


@router.get("/student/{student_id}", response_model=list[GradeOut])
def get_student_grades(
    student_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    return (
        db.query(Grade)
        .filter(Grade.school_id == token["school_id"], Grade.student_id == student_id)
        .order_by(Grade.id.desc())
        .all()
    )


@router.get("/class/{class_name}")
def get_class_grades(
    class_name: str,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    return (
        db.query(Grade)
        .join(Student, Student.id == Grade.student_id)
        .filter(
            Grade.school_id == token["school_id"],
            Student.class_name == class_name,
        )
        .all()
    )


@router.post("", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
def create_grade(
    payload: GradeCreate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
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

    if payload.exam_date and payload.exam_date > date.today():
        raise HTTPException(status_code=422, detail="Grades cannot be entered for future dates")

    if payload.marks_obtained > payload.total_marks:
        raise HTTPException(status_code=422, detail="Marks cannot exceed total marks")

    percentage = round((payload.marks_obtained / payload.total_marks) * 100, 2)
    letter = _grade_letter(percentage)

    grade = Grade(
        school_id=token["school_id"],
        student_id=payload.student_id,
        subject=payload.subject,
        marks_obtained=payload.marks_obtained,
        total_marks=payload.total_marks,
        percentage=percentage,
        grade=letter,
        teacher_id=payload.teacher_id or token["user_id"],
        exam_date=payload.exam_date,
    )
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade


@router.put("/{grade_id}", response_model=GradeOut)
def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    grade = (
        db.query(Grade)
        .filter(Grade.id == grade_id, Grade.school_id == token["school_id"])
        .first()
    )
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    data = payload.model_dump(exclude_unset=True)
    marks = data.get("marks_obtained", grade.marks_obtained)
    total = data.get("total_marks", grade.total_marks)
    exam_date = data.get("exam_date", grade.exam_date)

    if exam_date and exam_date > date.today():
        raise HTTPException(status_code=422, detail="Grades cannot be entered for future dates")
    if marks > total:
        raise HTTPException(status_code=422, detail="Marks cannot exceed total marks")

    for key, value in data.items():
        setattr(grade, key, value)

    grade.percentage = round((marks / total) * 100, 2)
    grade.grade = _grade_letter(grade.percentage)

    db.commit()
    db.refresh(grade)
    return grade


@router.delete("/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade(
    grade_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    grade = (
        db.query(Grade)
        .filter(Grade.id == grade_id, Grade.school_id == token["school_id"])
        .first()
    )
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    db.delete(grade)
    db.commit()
    return None


@router.get("/subject/{subject}/stats")
def subject_stats(
    subject: str,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    grades = (
        db.query(Grade)
        .filter(Grade.school_id == token["school_id"], Grade.subject == subject)
        .all()
    )
    if not grades:
        return {"subject": subject, "count": 0, "avg_percentage": 0.0}

    avg = round(sum(g.percentage for g in grades) / len(grades), 2)
    return {"subject": subject, "count": len(grades), "avg_percentage": avg}