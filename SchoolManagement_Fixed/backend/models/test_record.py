from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class TestTermType(str, enum.Enum):
    monthly = "monthly"
    annual = "annual"


class TestRecord(Base):
    """
    A single test/exam result entry, separate from the existing Grade model.
    Grade is a lightweight per-subject mark; TestRecord additionally tracks
    which term (monthly/annual), which month/year, and an optional photo of
    the actual physical answer sheet/report — used for the paper-record
    archive schools want alongside digital marks.
    """

    __tablename__ = "test_records"

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

    term_type: Mapped[TestTermType] = mapped_column(
        Enum(TestTermType, validate_strings=True),
        nullable=False,
        index=True,
    )
    # For monthly records: "2026-07" style (YYYY-MM). For annual: just the year, e.g. "2026".
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=100)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Photo of the physical answer sheet / report card, if uploaded.
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    recorded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
