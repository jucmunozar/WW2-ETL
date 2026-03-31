"""Pydantic response models for the WW2 API."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class EventResponse(BaseModel):
    event_date: date
    title: str
    description: Optional[str] = None
    sources: list[str]

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total: int
    date_range: tuple[Optional[str], Optional[str]]
    by_source: dict[str, int]
    by_year: dict[str, int]

class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5

class SemanticSearchResult(BaseModel):
    event_id: int
    date: str
    title: str
    description: Optional[str] = None
    content: str

class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResult]

class ChatRequest(BaseModel):
    question: str
    limit: int = 5

class ChatResponse(BaseModel):
    answer: str
    sources: list[SemanticSearchResult]   
