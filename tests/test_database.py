"""Tests for the DatabaseManager with SQLite in-memory backend."""
from datetime import date

from src.models.raw_event import RawEventData
from src.utils.database import DatabaseManager


def _make_raw(
    event_date=None, title="Test event", description="desc",
    source="test_source", source_url="http://example.com",
):
    return RawEventData(
        event_date=event_date or date(1941, 12, 7),
        title=title,
        description=description,
        source=source,
        source_url=source_url,
    )


class TestSaveEvent:
    def test_save_new_event_returns_true(self):
        dm = DatabaseManager()
        assert dm.save_event(_make_raw()) is True

    def test_save_duplicate_returns_false(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw())
        assert dm.save_event(_make_raw()) is False

    def test_same_event_different_source_deduplicates(self):
        dm = DatabaseManager()
        raw_a = _make_raw(source="source_a")
        raw_b = _make_raw(source="source_b")

        assert dm.save_event(raw_a) is True
        assert dm.save_event(raw_b) is False  # event already exists

        stats = dm.get_database_stats()
        assert stats["total"] == 1  # only 1 event
        assert len(stats["by_source"]) == 2  # linked to 2 sources


class TestGetEvent:
    def test_get_event_by_id(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw(title="Pearl Harbor"))

        event = dm.get_event(1)
        assert event is not None
        assert event.title == "Pearl Harbor"

    def test_get_missing_event_returns_none(self):
        dm = DatabaseManager()
        assert dm.get_event(999) is None


class TestGetEventsByDate:
    def test_returns_events_for_date(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw(event_date=date(1944, 6, 6), title="D-Day"))
        dm.save_event(_make_raw(event_date=date(1944, 6, 6), title="Normandy"))
        dm.save_event(_make_raw(event_date=date(1945, 5, 8), title="VE Day"))

        events = dm.get_events_by_date(date(1944, 6, 6))
        assert len(events) == 2


class TestGetTodayEvents:
    def test_returns_empty_when_no_match(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw(event_date=date(1941, 1, 1), title="New Year"))
        # Unless today is Jan 1 this will be empty
        events = dm.get_today_events()
        # Just verify no crash; actual result depends on today's date
        assert isinstance(events, list)


class TestGetRandomEvent:
    def test_returns_none_on_empty_db(self):
        dm = DatabaseManager()
        assert dm.get_random_event() is None

    def test_returns_event_when_data_exists(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw())
        event = dm.get_random_event()
        assert event is not None
        assert event.title == "Test event"


class TestScrapeRuns:
    def test_start_and_complete_scrape_run(self):
        dm = DatabaseManager()
        run_id = dm.start_scrape_run("test_scraper")
        assert isinstance(run_id, int)

        dm.complete_scrape_run(
            run_id,
            status="success",
            events_found=10,
            events_new=5,
            events_duplicate=5,
        )
        # No assertion on the values — just ensure no errors


class TestDatabaseStats:
    def test_stats_on_empty_db(self):
        dm = DatabaseManager()
        stats = dm.get_database_stats()
        assert stats["total"] == 0
        assert stats["by_source"] == {}
        assert stats["by_year"] == {}

    def test_stats_with_data(self):
        dm = DatabaseManager()
        dm.save_event(_make_raw(event_date=date(1941, 12, 7), title="Pearl Harbor"))
        dm.save_event(_make_raw(event_date=date(1944, 6, 6), title="D-Day"))

        stats = dm.get_database_stats()
        assert stats["total"] == 2
        assert "1941" in stats["by_year"]
        assert "1944" in stats["by_year"]
