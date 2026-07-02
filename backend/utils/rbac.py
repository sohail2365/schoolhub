from typing import Iterable

from fastapi import Depends, HTTPException, status

from backend.utils.jwt_handler import verify_token


def require_roles(allowed_roles: Iterable[str]):
    allowed = set(allowed_roles)

    def checker(token: dict = Depends(verify_token)) -> dict:
        role = token.get("role")
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return token

    return checker
