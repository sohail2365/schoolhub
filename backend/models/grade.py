from datetime import date, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Date as SqlDate
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Grade(Base):
    __tablename__ = "grades"

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

    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=100)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)

    teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    exam_date: Mapped[date | None] = mapped_column(SqlDate, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )