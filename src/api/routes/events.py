"""Event endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session, selectinload

from src.api.deps import get_db
from src.api.schemas import EventResponse, EventListResponse
from src.models.event import Event, EventSource

router = APIRouter(prefix="/api/v1/events", tags=["events"])


def _event_to_response(event: Event) -> EventResponse:
    sources = [es.source.name for es in event.event_sources]
    return EventResponse(
        event_date=event.event_date,
        title=event.title,
        description=event.description,
        sources=sources,
    )


def _base_query():
    return select(Event).options(
        selectinload(Event.event_sources).selectinload(EventSource.source)
    )


@router.get("/random", response_model=EventResponse)
def get_random_event(db: Session = Depends(get_db)):
    event = db.execute(
        _base_query().order_by(func.random()).limit(1)
    ).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="No events found")
    return _event_to_response(event)


@router.get("", response_model=EventListResponse)
def list_events(
    date: Optional[date] = Query(None, description="Exact date (YYYY-MM-DD)"),
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month"),
    day: Optional[int] = Query(None, ge=1, le=31, description="Filter by day"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = _base_query()
    count_query = select(func.count(Event.id))

    if date:
        query = query.where(Event.event_date == date)
        count_query = count_query.where(Event.event_date == date)
    else:
        if year:
            query = query.where(extract("year", Event.event_date) == year)
            count_query = count_query.where(extract("year", Event.event_date) == year)
        if month:
            query = query.where(extract("month", Event.event_date) == month)
            count_query = count_query.where(extract("month", Event.event_date) == month)
        if day:
            query = query.where(extract("day", Event.event_date) == day)
            count_query = count_query.where(extract("day", Event.event_date) == day)

    total = db.execute(count_query).scalar() or 0

    events = db.execute(
        query.order_by(Event.event_date).limit(limit).offset(offset)
    ).scalars().all()

    return EventListResponse(
        items=[_event_to_response(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )
