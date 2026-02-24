"""Raw event data transfer object produced by scrapers."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RawEventData:
    """DTO that scrapers produce. Replaces the old Event dataclass."""
    event_date: date
    title: str
    description: Optional[str] = None
    source: str = ""
    source_url: Optional[str] = None
