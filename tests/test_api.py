"""Tests for the REST API endpoints."""
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.base import Base
import src.models.event as models  # noqa: F401
from src.api.main import app
from src.api.deps import get_db

# ---------- Test DB setup ----------

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ---------- Helpers ----------


def _seed_db():
    """Insert sample events for testing."""
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    with TestSession() as session:
        source = models.Source(name="test_source", url="http://test.com")
        session.add(source)
        session.flush()

        events_data = [
            ("1941-12-07", "Attack on Pearl Harbor", "Japan attacks the US naval base"),
            ("1944-06-06", "D-Day", "Allied invasion of Normandy"),
            ("1944-06-06", "Airborne landings", "Paratroopers land behind enemy lines"),
            ("1945-05-08", "V-E Day", "Victory in Europe"),
        ]
        for date_str, title, desc in events_data:
            evt = models.Event(
                event_date=date.fromisoformat(date_str),
                title=title,
                description=desc,
            )
            session.add(evt)
            session.flush()
            session.add(models.EventSource(
                event_id=evt.id, source_id=source.id
            ))

        session.commit()


# ---------- Tests ----------


class TestRoot:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "WW2 Timeline API"


class TestStats:
    def setup_method(self):
        _seed_db()

    def test_stats_returns_totals(self):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert data["by_source"]["test_source"] == 4
        assert "1944" in data["by_year"]

    def test_stats_empty_db(self):
        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestListEvents:
    def setup_method(self):
        _seed_db()

    def test_list_all(self):
        resp = client.get("/api/v1/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    def test_filter_by_date(self):
        resp = client.get("/api/v1/events?date=1944-06-06")
        data = resp.json()
        assert data["total"] == 2
        assert all(e["event_date"] == "1944-06-06" for e in data["items"])

    def test_filter_by_year(self):
        resp = client.get("/api/v1/events?year=1944")
        assert resp.json()["total"] == 2

    def test_filter_by_month_day(self):
        resp = client.get("/api/v1/events?month=12&day=7")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Attack on Pearl Harbor"

    def test_pagination(self):
        resp = client.get("/api/v1/events?limit=2&offset=0")
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_pagination_offset(self):
        resp = client.get("/api/v1/events?limit=2&offset=2")
        data = resp.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2

    def test_empty_result(self):
        resp = client.get("/api/v1/events?year=1939")
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_event_has_sources(self):
        resp = client.get("/api/v1/events?limit=1")
        event = resp.json()["items"][0]
        assert "sources" in event
        assert "test_source" in event["sources"]


class TestRandomEvent:
    def setup_method(self):
        _seed_db()

    def test_random_returns_event(self):
        resp = client.get("/api/v1/events/random")
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data
        assert "event_date" in data
        assert "sources" in data

    def test_random_empty_db(self):
        Base.metadata.drop_all(test_engine)
        Base.metadata.create_all(test_engine)
        resp = client.get("/api/v1/events/random")
        assert resp.status_code == 404
