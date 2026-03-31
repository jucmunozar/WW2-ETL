"""Tests for RAG module."""
from src.etl.embeddings import build_content
from src.rag.chain import format_context


class TestBuildContent:
    """Tests for build_content function."""

    def test_title_only(self):
        """When event has no description, return just the title."""

        class FakeEvent:
            title = "Germany invades Poland"
            description = None

        result = build_content(FakeEvent())
        assert result == "Germany invades Poland"

    def test_title_and_description(self):
        """When event has description, join with period."""

        class FakeEvent:
            title = "Germany invades Poland"
            description = "On September 1, 1939"

        result = build_content(FakeEvent())
        assert result == "Germany invades Poland. On September 1, 1939"

    def test_empty_description(self):
        """When description is empty string, treat as no description."""

        class FakeEvent:
            title = "Germany invades Poland"
            description = ""

        result = build_content(FakeEvent())
        assert result == "Germany invades Poland"


class TestFormatContext:
    """Tests for format_context function."""

    def test_single_event(self):
        events = [
            {
                "event_id": 1,
                "date": "1939-09-01",
                "title": "Germany invades Poland",
                "description": "Start of WW2",
                "content": "Germany invades Poland. Start of WW2",
            }
        ]
        result = format_context(events)
        assert "1939-09-01" in result
        assert "Germany invades Poland" in result
        assert "Start of WW2" in result

    def test_multiple_events(self):
        events = [
            {
                "event_id": 1,
                "date": "1939-09-01",
                "title": "Event A",
                "description": "Desc A",
                "content": "Event A. Desc A",
            },
            {
                "event_id": 2,
                "date": "1941-12-07",
                "title": "Event B",
                "description": "Desc B",
                "content": "Event B. Desc B",
            },
        ]
        result = format_context(events)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_empty_list(self):
        result = format_context([])
        assert result == ""
