# WW2 ETL Project Architecture

## Overview

Data engineering project with a modular, layered architecture. ETL pipeline that extracts WW2 historical events from 4 web sources, normalizes them, and stores them in PostgreSQL with a 6-table schema.

## Architecture Layers

### 1. Configuration (`config/`)

- Environment variable loading via `python-dotenv`
- `DATABASE_URL` for PostgreSQL connection
- Scraping parameters
- Centralized source URLs

### 2. Models (`src/models/`)

**ORM (SQLAlchemy 2.0)**:
- `base.py`: Engine, `Base`, `SessionLocal`, `get_session()`
- `event.py`: 6 ORM models — `Event`, `Source`, `EventSource`, `ScrapeRun`, `Tag`, `EventTag`

**DTO**:
- `raw_event.py`: `RawEventData` dataclass — output produced by scrapers

### 3. Utilities (`src/utils/`)

- `database.py`: `DatabaseManager` — SQLAlchemy sessions, dedup, scrape run tracking, statistics
- `date_parser.py`: Multi-format date parser (no DB dependency)

### 4. ETL (`src/etl/`)

- `scrapers.py`: `BaseScraper` + 3 implementations (WorldWar2Facts, HistoryCooperative, HistoryPlace)
- `collector.py`: Orchestrator — runs scrapers sequentially, records `scrape_runs`
- `scrape_result.py`: DTO with result counts

### 5. API (`src/api/`)

- `main.py`: FastAPI app with CORS and routers
- `deps.py`: Dependency injection (DB session via `get_db()`)
- `schemas.py`: Pydantic response models
- `routes/events.py`: Event endpoints (list, filter, random)
- `routes/stats.py`: Statistics endpoint

### 6. Infrastructure

- `docker-compose.yml`: PostgreSQL 16 + pgAdmin
- `alembic/`: Schema migrations
- `tests/conftest.py`: SQLite in-memory for testing (monkeypatch of SessionLocal)

## Data Flow

```
Web Sources (4)
     |
     v
Scrapers (BeautifulSoup)
     |
     v
RawEventData (dataclass DTO)
     |
     v
DatabaseManager (SQLAlchemy sessions)
     |
     +---> events (dedup by date + title)
     +---> sources (get or create)
     +---> event_sources (event <-> source link)
     +---> scrape_runs (execution record)
     |
     v
PostgreSQL (Docker)
     |
     v
REST API / pgAdmin
```

## Database Schema

```
events ──────────< event_sources >────────── sources
  |                                             |
  +──────────< event_tags >──── tags     scrape_runs
```

- `events`: UNIQUE(event_date, title) — each event exists only once
- `event_sources`: UNIQUE(event_id, source_id) — links event to each source that reported it
- `scrape_runs`: Execution history per source (status, counts, errors)

## Design Principles

1. **Separation of concerns**: Each module has a single responsibility
2. **Cross-source dedup**: Same event from N sources = 1 row in events + N rows in event_sources
3. **Observability**: scrape_runs records each pipeline execution
4. **Testability**: SQLite in-memory for tests, PostgreSQL in production
5. **Extensibility**: Adding a scraper = create a class + register in collector
