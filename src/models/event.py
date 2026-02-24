"""SQLAlchemy ORM models for WW2 ETL project."""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    String, Text, Date, DateTime, Integer, Boolean,
    ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Event(Base):
    """A WW2 timeline event (deduplicated by date + title)."""
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("event_date", "title", name="uq_event_date_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    event_sources: Mapped[List["EventSource"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    event_tags: Mapped[List["EventTag"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class Source(Base):
    """A data source (e.g. worldwar2facts.org)."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    event_sources: Mapped[List["EventSource"]] = relationship(
        back_populates="source"
    )
    scrape_runs: Mapped[List["ScrapeRun"]] = relationship(
        back_populates="source"
    )


class EventSource(Base):
    """Link table: which source provided which event."""
    __tablename__ = "event_sources"
    __table_args__ = (
        UniqueConstraint("event_id", "source_id", name="uq_event_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="event_sources")
    source: Mapped["Source"] = relationship(back_populates="event_sources")


class ScrapeRun(Base):
    """Record of a single scraper execution."""
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(20), default="running"
    )  # running, success, failed
    events_found: Mapped[int] = mapped_column(Integer, default=0)
    events_new: Mapped[int] = mapped_column(Integer, default=0)
    events_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="scrape_runs")


class Tag(Base):
    """A tag/category for events."""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relationships
    event_tags: Mapped[List["EventTag"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class EventTag(Base):
    """Many-to-many link between events and tags."""
    __tablename__ = "event_tags"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id"), primary_key=True
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="event_tags")
    tag: Mapped["Tag"] = relationship(back_populates="event_tags")
