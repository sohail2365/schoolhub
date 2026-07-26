from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class DocumentType(str, enum.Enum):
    id_card = "id_card"          # scanned/photographed existing ID card
    b_form = "b_form"            # NADRA B-form / CNIC of child
    test_paper = "test_paper"    # photo of a physical test/exam paper
    profile_photo = "profile_photo"  # passport-size photo used on printed student card
    other = "other"


class StudentDocument(Base):
    """
    Stores a reference (URL) to a file kept in Supabase Storage — NOT the
    file bytes themselves. A student can have multiple documents of the
    same type over time (e.g. a B-form re-upload), so this is a one-to-many
    table rather than columns on Student.
    """

    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, validate_strings=True),
        nullable=False,
        index=True,
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    label: Mapped[str | None] = mapped_column(String(150), nullable=True)  # e.g. "Monthly test - Math - July"

    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
