from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.student import Student
from backend.models.student_document import DocumentType, StudentDocument
from backend.schemas.student_document import StudentDocumentOut
from backend.utils.rbac import require_roles
from backend.utils.storage import delete_file, get_signed_url, upload_student_file

router = APIRouter(prefix="/students", tags=["student-documents"])


def _get_student_or_404(db: Session, student_id: int, school_id: int) -> Student:
    student = (
        db.query(Student)
        .filter(Student.id == student_id, Student.school_id == school_id)
        .first()
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _parse_doc_type(value: str) -> DocumentType:
    try:
        return DocumentType(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="doc_type must be one of: id_card, b_form, test_paper, profile_photo, other",
        )


# ==================== STUDENT DOCUMENTS (ID card, B-form, test papers, etc.) ====================

@router.post(
    "/{student_id}/documents",
    response_model=StudentDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_student_document(
    student_id: int,
    doc_type: str = Query(..., description="id_card | b_form | test_paper | profile_photo | other"),
    label: str | None = Query(default=None, max_length=150),
    file: UploadFile = File(...),
    token: dict = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db),
):
    student = _get_student_or_404(db, student_id, token["school_id"])
    parsed_type = _parse_doc_type(doc_type)

    path = upload_student_file(file, token["school_id"], student.id, subfolder=parsed_type.value)

    doc = StudentDocument(
        school_id=token["school_id"],
        student_id=student.id,
        doc_type=parsed_type,
        file_url=path,
        file_name=file.filename,
        label=label,
        uploaded_by_user_id=token.get("user_id"),
    )
    db.add(doc)

    # A profile_photo upload also updates the canonical card photo shown on
    # the printable student card, so admins don't have to set it twice.
    if parsed_type == DocumentType.profile_photo:
        student.photo_url = path

    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{student_id}/documents", response_model=list[StudentDocumentOut])
def list_student_documents(
    student_id: int,
    doc_type: str | None = Query(default=None),
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    _get_student_or_404(db, student_id, token["school_id"])

    query = db.query(StudentDocument).filter(
        StudentDocument.school_id == token["school_id"],
        StudentDocument.student_id == student_id,
    )
    if doc_type:
        query = query.filter(StudentDocument.doc_type == _parse_doc_type(doc_type))
    return query.order_by(StudentDocument.created_at.desc()).all()


@router.get("/{student_id}/documents/{document_id}/url")
def get_student_document_url(
    student_id: int,
    document_id: int,
    token: dict = Depends(require_roles(["admin", "teacher", "parent"])),
    db: Session = Depends(get_db),
):
    """Returns a fresh 1-hour signed link to view/download the file."""
    doc = (
        db.query(StudentDocument)
        .filter(
            StudentDocument.id == document_id,
            StudentDocument.student_id == student_id,
            StudentDocument.school_id == token["school_id"],
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"url": get_signed_url(doc.file_url), "expires_in_seconds": 3600}


@router.delete("/{student_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_document(
    student_id: int,
    document_id: int,
    token: dict = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(StudentDocument)
        .filter(
            StudentDocument.id == document_id,
            StudentDocument.student_id == student_id,
            StudentDocument.school_id == token["school_id"],
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_file(doc.file_url)
    db.delete(doc)
    db.commit()
    return None
