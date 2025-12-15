"""
Database configuration and session management for SQLAlchemy.
Handles connection pooling and session lifecycle.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .models import Base
import os

# Use SQLite for simplicity (can be upgraded to PostgreSQL in production)
DATABASE_URL = "sqlite:///./data/marthanote.db"

# Create database directory if it doesn't exist
os.makedirs("./data", exist_ok=True)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=StaticPool,  # Use StaticPool for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables on startup."""
    # Create any missing tables
    Base.metadata.create_all(bind=engine)

    # Ensure the documents table has the device_id column (SQLite won't alter existing tables automatically)
    try:
        with engine.connect() as conn:
            res = conn.execute("PRAGMA table_info(documents);")
            cols = [r[1] for r in res.fetchall()]
            if "device_id" not in cols:
                print("Adding missing 'device_id' column to documents table")
                conn.execute("ALTER TABLE documents ADD COLUMN device_id TEXT;")
    except Exception as e:
        print(f"Warning: could not ensure device_id column exists: {e}")

    print("✓ Database tables initialized.")


def get_db() -> Session:
    """
    Dependency injection function for FastAPI routes.
    Usage in routes: @router.get("/path")
    async def route(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
