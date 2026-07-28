from typing import Iterable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.utils.jwt_handler import verify_token


def require_roles(allowed_roles: Iterable[str]):
    allowed = set(allowed_roles)

    def checker(
        token: dict = Depends(verify_token),
        db: Session = Depends(get_db),
    ) -> dict:
        role = token.get("role")
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Re-check against the live database on every request — not just at
        # login — so deactivating a school/user takes effect immediately,
        # even for someone who already has a valid (up to 7-day) token.
        # Imported here (not at module level) to avoid a circular import
        # between rbac.py and the model modules.
        from backend.models.school import School
        from backend.models.user import User

        school = db.query(School).filter(School.id == token.get("school_id")).first()
        if not school or not school.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This school's account has been deactivated. Please contact support.",
            )

        user = db.query(User).filter(User.id == token.get("user_id")).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user account is inactive.",
            )

        return token

    return checker
