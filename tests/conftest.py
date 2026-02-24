"""Pytest fixtures: SQLite in-memory engine for testing."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
import src.models.event  # noqa: F401  — ensure models are registered on Base
import src.utils.database as db_mod


@pytest.fixture(autouse=True)
def _use_sqlite_in_memory(monkeypatch):
    """Replace SessionLocal with an in-memory SQLite session for every test."""
    test_engine = create_engine("sqlite:///:memory:")

    # Enable foreign-key enforcement in SQLite
    @event.listens_for(test_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine)

    monkeypatch.setattr(db_mod, "SessionLocal", TestSession)
    yield
