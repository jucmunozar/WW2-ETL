"""Stats endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, extract
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas import StatsResponse
from src.models.event import Event, Source, EventSource

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.execute(select(func.count(Event.id))).scalar() or 0

    date_range = db.execute(
        select(func.min(Event.event_date), func.max(Event.event_date))
    ).one()

    by_source_rows = db.execute(
        select(Source.name, func.count(EventSource.id))
        .join(EventSource, Source.id == EventSource.source_id)
        .group_by(Source.name)
    ).all()

    by_year_rows = db.execute(
        select(
            extract("year", Event.event_date).label("year"),
            func.count(Event.id),
        )
        .group_by("year")
        .order_by("year")
    ).all()

    return StatsResponse(
        total=total,
        date_range=(
            str(date_range[0]) if date_range[0] else None,
            str(date_range[1]) if date_range[1] else None,
        ),
        by_source=dict(by_source_rows),
        by_year={str(int(row[0])): row[1] for row in by_year_rows},
    )
