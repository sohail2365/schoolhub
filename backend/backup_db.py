"""
Automated backup script for school.db.

Uses SQLite's built-in online backup API (via the `.backup` command), which
is SAFE to run while the app is live and serving requests — it doesn't lock
or corrupt the database, unlike a plain file copy.

Usage:
    python backend/backup_db.py

Set up as a daily cron job on your VPS (see deployment guide) so backups
run automatically without you having to remember.

Keeps the last KEEP_DAYS backups and deletes older ones automatically, so
disk space doesn't grow forever.
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(PROJECT_ROOT, "school.db")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
KEEP_DAYS = 14


def backup_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(BACKUP_DIR, f"school_{timestamp}.db")

    # Use SQLite's online backup API — safe to run while the app is live.
    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(backup_path)
    with dest:
        source.backup(dest)
    source.close()
    dest.close()

    size_kb = os.path.getsize(backup_path) / 1024
    print(f"✅ Backup created: {backup_path} ({size_kb:.1f} KB)")

    _cleanup_old_backups()


def _cleanup_old_backups():
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    removed = 0

    for filename in os.listdir(BACKUP_DIR):
        if not (filename.startswith("school_") and filename.endswith(".db")):
            continue
        filepath = os.path.join(BACKUP_DIR, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if file_time < cutoff:
            os.remove(filepath)
            removed += 1

    if removed:
        print(f"🗑️  Removed {removed} backup(s) older than {KEEP_DAYS} days")


if __name__ == "__main__":
    backup_database()
