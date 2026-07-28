from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.student import Student
from backend.models.test_record import TestRecord, TestTermType
from backend.schemas.test_record import TestRecordOut, TestRecordUpdate
from backend.utils.rbac import require_roles
from backend.utils.storage import delete_file, get_signed_url, upload_student_file

router = APIRouter(prefix="/test-records", tags=["test-records"])


def _parse_term_type(value: str) -> TestTermType:
    try:
        return TestTermType(value.strip().lower())
    except ValueError:
        raise HTTPException(status_code=422, detail="term_type must be 'monthly' or 'annual'")


def _compute_percentage(marks_obtained: float, total_marks: float) -> float:
    if total_marks <= 0:
        return 0.0
    return round((marks_obtained / total_marks) * 100, 2)


@router.post("", response_model=TestRecordOut, status_code=status.HTTP_201_CREATED)
def create_test_record(
    student_id: int = Form(...),
    term_type: str = Form(...),
    period: str = Form(..., description="YYYY-MM for monthly, YYYY for annual"),
    subject: str = Form(...),
    marks_obtained: float = Form(...),
    total_marks: float = Form(default=100),
    remarks: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
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

    parsed_term = _parse_term_type(term_type)
    image_path = None
    if image is not None:
        image_path = upload_student_file(
            image, token["school_id"], student_id, subfolder=f"test_records/{parsed_term.value}"
        )

    record = TestRecord(
        school_id=token["school_id"],
        student_id=student_id,
        term_type=parsed_term,
        period=period.strip(),
        subject=subject.strip(),
        marks_obtained=marks_obtained,
        total_marks=total_marks,
        percentage=_compute_percentage(marks_obtained, total_marks),
        remarks=remarks,
        image_url=image_path,
        recorded_by_user_id=token.get("user_id"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[TestRecordOut])
def list_test_records(
    student_id: int | None = Query(default=None),
    class_name: str | None = Query(default=None, alias="class"),
    term_type: str | None = Query(default=None),
    period: str | None = Query(default=None),
    token: dict = Depends(require_roles(["admin", "teacher", "parent", "student"])),
    db: Session = Depends(get_db),
):
    query = db.query(TestRecord).filter(TestRecord.school_id == token["school_id"])

    if student_id:
        query = query.filter(TestRecord.student_id == student_id)
    elif class_name:
        student_ids = [
            s.id
            for s in db.query(Student.id).filter(
                Student.school_id == token["school_id"], Student.class_name == class_name
            )
        ]
        query = query.filter(TestRecord.student_id.in_(student_ids))

    if term_type:
        query = query.filter(TestRecord.term_type == _parse_term_type(term_type))
    if period:
        query = query.filter(TestRecord.period == period.strip())

    return query.order_by(TestRecord.created_at.desc()).all()


@router.get("/{record_id}/image-url")
def get_test_record_image_url(
    record_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    record = (
        db.query(TestRecord)
        .filter(TestRecord.id == record_id, TestRecord.school_id == token["school_id"])
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found")
    if not record.image_url:
        raise HTTPException(status_code=404, detail="This record has no attached photo")

    return {"url": get_signed_url(record.image_url), "expires_in_seconds": 3600}


@router.put("/{record_id}", response_model=TestRecordOut)
def update_test_record(
    record_id: int,
    payload: TestRecordUpdate,
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    record = (
        db.query(TestRecord)
        .filter(TestRecord.id == record_id, TestRecord.school_id == token["school_id"])
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(record, key, value)

    record.percentage = _compute_percentage(record.marks_obtained, record.total_marks)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_record(
    record_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    record = (
        db.query(TestRecord)
        .filter(TestRecord.id == record_id, TestRecord.school_id == token["school_id"])
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found")

    if record.image_url:
        delete_file(record.image_url)

    db.delete(record)
    db.commit()
    return None
