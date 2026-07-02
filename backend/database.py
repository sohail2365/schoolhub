from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

DATABASE_URL = settings.DATABASE_URL

# SQLite needs check_same_thread=False (single-file, thread-safety workaround).
# Postgres (and other real DB servers) don't understand that argument at all —
# passing it would crash the connection. So the connect_args are conditional
# on which database we're actually pointed at.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # Serverless platforms (e.g. Vercel) spin up short-lived function
    # instances — NullPool avoids leaking idle connections across
    # invocations, which matters a lot on free-tier Postgres connection
    # limits (Supabase/Neon free tiers cap concurrent connections).
    from sqlalchemy.pool import NullPool

    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)