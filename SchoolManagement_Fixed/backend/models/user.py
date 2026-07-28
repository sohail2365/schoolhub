from datetime import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    parent = "parent"
    staff = "staff"
    student = "student"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, validate_strings=True),
        nullable=False,
        default=UserRole.staff,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Brute-force login protection. DB-backed (not in-memory) so it actually
    # works across Vercel's stateless serverless invocations — an in-memory
    # counter would reset on every cold start and protect nothing.
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )