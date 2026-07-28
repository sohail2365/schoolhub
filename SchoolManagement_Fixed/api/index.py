"""
Vercel entrypoint.

Vercel looks for a FastAPI instance named `app` at conventional paths like
api/index.py. This file just re-exports the real app from backend/main.py
so the actual application code stays in one place (also used for local dev
via `python -m backend.main`).
"""
from backend.main import app  # noqa: F401
