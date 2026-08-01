"""
Simple per-IP rate limiting for sensitive endpoints (login, register,
password reset). Complements the existing per-account login lockout: lockout
stops repeated guesses against ONE account, while this stops one IP from
hammering MANY accounts or spamming registrations.

DB-backed (see RateLimitHit) so it survives Vercel's stateless cold starts.
Fails OPEN: if the rate-limit check itself errors (e.g. transient DB issue),
the request is allowed through rather than locking users out — availability
over strictness for this particular guard.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.models.rate_limit import RateLimitHit


def _client_ip(request: Request) -> str:
    # Vercel/proxies put the real client IP in X-Forwarded-For (first entry).
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(
    request: Request,
    db: Session,
    action: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Raises HTTP 429 if this IP has exceeded max_requests for `action` within
    the rolling window. Call at the very start of a route handler.
    """
    try:
        ip = _client_ip(request)
        bucket = f"{ip}|{action}"
        now = datetime.utcnow()
        window = timedelta(seconds=window_seconds)

        row = db.query(RateLimitHit).filter(RateLimitHit.bucket_key == bucket).first()

        if row is None:
            db.add(RateLimitHit(bucket_key=bucket, count=1, window_start=now))
            db.commit()
            return

        if now - row.window_start > window:
            # Window expired — start a fresh one.
            row.count = 1
            row.window_start = now
            db.commit()
            return

        if row.count >= max_requests:
            retry_in = int(window_seconds - (now - row.window_start).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in about {max(retry_in, 1)} seconds.",
            )

        row.count += 1
        db.commit()
    except HTTPException:
        raise  # the 429 must propagate
    except Exception:
        # Fail open: never let the limiter's own failure block a real user.
        try:
            db.rollback()
        except Exception:
            pass
