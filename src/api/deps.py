"""FastAPI dependency injection."""
from collections.abc import Generator

from sqlalchemy.orm import Session

from src.models.base import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session, closing it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
