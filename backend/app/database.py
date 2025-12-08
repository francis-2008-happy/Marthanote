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
    Base.metadata.create_all(bind=engine)
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
