"""
Data backup export.

On Vercel + Supabase Postgres there's no local .db file to copy and no easy
cron, so backup works as a protected HTTP endpoint that returns the whole
database as JSON. You (or a free scheduler like cron-job.org / GitHub Actions)
call it periodically and save the file somewhere safe.

Protected by BACKUP_SECRET (set in env). Without that secret set, the
endpoint is disabled (returns 503) — it never exposes data by accident.
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, engine

router = APIRouter(prefix="/backup", tags=["backup"])


def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


@router.get("/export")
def export_backup(
    x_backup_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """
    Returns every table's rows as JSON. Guarded by the X-Backup-Secret header,
    which must match BACKUP_SECRET. Read-only — never modifies data.
    """
    if not settings.BACKUP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup is not configured. Set BACKUP_SECRET to enable it.",
        )
    # Constant-ish comparison; secrets are short so this is fine.
    if x_backup_secret != settings.BACKUP_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid backup secret")

    inspector = sa_inspect(engine)
    dump = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "tables": {},
    }

    # Skip the rate-limit bookkeeping table — it's transient, not real data.
    skip_tables = {"rate_limit_hits"}

    for table_name in inspector.get_table_names():
        if table_name in skip_tables:
            continue
        try:
            rows = db.execute(
                # Read every row from the table. Table name comes from the DB's
                # own schema inspection (not user input), so this is safe.
                __import__("sqlalchemy").text(f'SELECT * FROM "{table_name}"')
            )
            cols = rows.keys()
            dump["tables"][table_name] = [
                {c: _serialize(v) for c, v in zip(cols, row)} for row in rows.fetchall()
            ]
        except Exception as e:
            dump["tables"][table_name] = {"error": str(e)}

    return dump
