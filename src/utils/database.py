"""Database management utilities for WW2 ETL project (SQLAlchemy)."""
import logging
import re
from datetime import datetime, date
from typing import Optional, List, Dict

from sqlalchemy import select, func, extract

from src.models.base import SessionLocal
from src.models.event import Event, Source, EventSource, ScrapeRun
from src.models.raw_event import RawEventData

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for WW2 events via SQLAlchemy."""

    def __init__(self):
        self._source_cache: Dict[str, int] = {}

    def _get_or_create_source(self, session, source_name: str, source_url: Optional[str] = None) -> int:
        """Get source ID from cache or DB, creating if needed."""
        if source_name in self._source_cache and not source_url:
            return self._source_cache[source_name]

        source = session.execute(
            select(Source).where(Source.name == source_name)
        ).scalar_one_or_none()

        if not source:
            source = Source(name=source_name, url=source_url)
            session.add(source)
            session.flush()
        elif source_url and not source.url:
            source.url = source_url
            session.flush()

        self._source_cache[source_name] = source.id
        return source.id

    def save_event(self, raw: RawEventData) -> bool:
        """
        Save a raw event into the normalized schema.

        Returns True if a new event row was created, False if duplicate.
        """
        # Normalize whitespace in title and description
        raw.title = re.sub(r"\s+", " ", raw.title).strip()
        if raw.description:
            raw.description = re.sub(r"\s+", " ", raw.description).strip()

        with SessionLocal() as session:
            try:
                source_id = self._get_or_create_source(
                    session, raw.source, raw.source_url
                )

                # Try to find existing event (dedup by date + title)
                event = session.execute(
                    select(Event).where(
                        Event.event_date == raw.event_date,
                        Event.title == raw.title,
                    )
                ).scalar_one_or_none()

                is_new = event is None
                if is_new:
                    event = Event(
                        event_date=raw.event_date,
                        title=raw.title,
                        description=raw.description,
                    )
                    session.add(event)
                    session.flush()

                # Link event <-> source (ignore if already linked)
                existing_link = session.execute(
                    select(EventSource).where(
                        EventSource.event_id == event.id,
                        EventSource.source_id == source_id,
                    )
                ).scalar_one_or_none()

                if not existing_link:
                    session.add(EventSource(
                        event_id=event.id,
                        source_id=source_id,
                        source_url=raw.source_url,
                    ))

                session.commit()
                return is_new

            except Exception as e:
                session.rollback()
                logger.error("Error saving event: %s", e)
                return False

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        with SessionLocal() as session:
            return session.get(Event, event_id)

    def get_events_by_date(self, target_date: date) -> List[Event]:
        """Get all events for a specific date."""
        with SessionLocal() as session:
            result = session.execute(
                select(Event).where(Event.event_date == target_date)
            )
            return list(result.scalars().all())

    def get_today_events(self, limit: int = 10) -> List[Event]:
        """Get events that occurred on today's month/day (any year)."""
        today = date.today()
        with SessionLocal() as session:
            result = session.execute(
                select(Event)
                .where(
                    extract("month", Event.event_date) == today.month,
                    extract("day", Event.event_date) == today.day,
                )
                .order_by(func.random())
                .limit(limit)
            )
            return list(result.scalars().all())

    def get_random_event(self) -> Optional[Event]:
        """Get a single random event from the database."""
        with SessionLocal() as session:
            result = session.execute(
                select(Event).order_by(func.random()).limit(1)
            )
            return result.scalar_one_or_none()

    # ------ Scrape-run tracking ------

    def start_scrape_run(self, source_name: str) -> int:
        """Start a new scrape run, return its ID."""
        with SessionLocal() as session:
            source_id = self._get_or_create_source(session, source_name)
            run = ScrapeRun(source_id=source_id, status="running")
            session.add(run)
            session.commit()
            return run.id

    def complete_scrape_run(
        self,
        run_id: int,
        status: str,
        events_found: int = 0,
        events_new: int = 0,
        events_duplicate: int = 0,
        error_message: Optional[str] = None,
    ):
        """Mark a scrape run as completed."""
        with SessionLocal() as session:
            run = session.get(ScrapeRun, run_id)
            if run:
                run.status = status
                run.completed_at = datetime.utcnow()
                run.events_found = events_found
                run.events_new = events_new
                run.events_duplicate = events_duplicate
                run.error_message = error_message
                session.commit()

    # ------ Statistics ------

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with SessionLocal() as session:
            total = session.execute(
                select(func.count(Event.id))
            ).scalar() or 0

            date_range = session.execute(
                select(
                    func.min(Event.event_date),
                    func.max(Event.event_date),
                )
            ).one()

            by_source_rows = session.execute(
                select(Source.name, func.count(EventSource.id))
                .join(EventSource, Source.id == EventSource.source_id)
                .group_by(Source.name)
            ).all()
            by_source = dict(by_source_rows)

            by_year_rows = session.execute(
                select(
                    extract("year", Event.event_date).label("year"),
                    func.count(Event.id),
                )
                .group_by("year")
                .order_by("year")
            ).all()
            by_year = {str(int(row[0])): row[1] for row in by_year_rows}

            return {
                "total": total,
                "date_range": (
                    str(date_range[0]) if date_range[0] else None,
                    str(date_range[1]) if date_range[1] else None,
                ),
                "by_source": by_source,
                "by_year": by_year,
            }

    def print_stats(self):
        """Log database statistics."""
        stats = self.get_database_stats()

        logger.info("=" * 50)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 50)
        logger.info("Total events: %d", stats["total"])
        if stats["date_range"][0] and stats["date_range"][1]:
            logger.info("Date range: %s to %s", stats["date_range"][0], stats["date_range"][1])
        logger.info("Events by source:")
        for source, count in stats["by_source"].items():
            logger.info("  %s: %d", source, count)
        logger.info("Events by year:")
        for year, count in sorted(stats["by_year"].items()):
            logger.info("  %s: %d", year, count)
        logger.info("=" * 50)
