from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class RateLimitHit(Base):
    """
    Tracks request counts per (client IP + action) inside a time window.
    DB-backed on purpose: Vercel's serverless functions are stateless and
    cold-start frequently, so an in-memory counter would reset constantly and
    protect nothing. One row per IP+action; count resets when the window
    rolls over.
    """

    __tablename__ = "rate_limit_hits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # IP + action together identify a bucket, e.g. "1.2.3.4|login".
    bucket_key: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # When the current counting window started; once it's older than the
    # window length, the count resets to 1 on the next request.
    window_start: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
