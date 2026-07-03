"""
Super admin access — completely separate from the normal per-school login
system. There's no "super admin user account" in the database; access is
just a secret key (set via the SUPER_ADMIN_SECRET env var) passed in a
request header. This is intentionally simple: it's meant for the platform
owner only, not something schools ever see or use.
"""
from fastapi import Header, HTTPException, status

from backend.config import settings


def verify_super_admin(x_super_admin_key: str = Header(default="")) -> None:
    if not settings.SUPER_ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Super admin access is not configured on this server (SUPER_ADMIN_SECRET not set).",
        )

    if not x_super_admin_key or x_super_admin_key != settings.SUPER_ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing super admin key.",
        )
