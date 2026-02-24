"""SQLAlchemy engine, Base, and session configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from config.settings import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    """Create and return a new database session."""
    return SessionLocal()
