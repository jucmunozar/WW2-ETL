# WW2-ETL Project Structure

## Directory Tree

```
WW2-ETL/
│
├── config/                         # Project configuration
│   ├── __init__.py
│   └── settings.py                 # DATABASE_URL, scraping params
│
├── src/                            # Main source code
│   ├── models/                     # Data models
│   │   ├── base.py                 # SQLAlchemy engine, Base, SessionLocal
│   │   ├── event.py                # 6 ORM models (Event, Source, EventSource, ScrapeRun, Tag, EventTag)
│   │   └── raw_event.py            # RawEventData dataclass (scraper DTO)
│   │
│   ├── etl/                        # ETL modules
│   │   ├── collector.py            # Pipeline orchestrator + scrape_run tracking
│   │   ├── scrapers.py             # BaseScraper + 3 implementations
│   │   └── scrape_result.py        # ScrapeResult dataclass
│   │
│   ├── utils/                      # Utilities
│   │   ├── database.py             # DatabaseManager (SQLAlchemy sessions, dedup, stats)
│   │   └── date_parser.py          # Multi-format date parser
│   │
│   ├── api/                        # REST API
│   │   ├── main.py                 # FastAPI app, CORS, routers
│   │   ├── deps.py                 # Dependency injection (DB session)
│   │   ├── schemas.py              # Pydantic response models
│   │   └── routes/                 # Endpoints
│   │       ├── events.py           # /api/v1/events, /api/v1/events/random
│   │       └── stats.py            # /api/v1/stats
│   │
├── alembic/                        # Database migrations
│   ├── env.py                      # Config: imports Base, reads DATABASE_URL
│   └── versions/                   # Auto-generated migration scripts
│
├── scripts/                        # Entry points
│   ├── run_etl.py                  # Run ETL pipeline
│   └── run_api.py                  # Run REST API
│
├── tests/                          # Tests
│   ├── conftest.py                 # Fixtures: SQLite in-memory (monkeypatch SessionLocal)
│   ├── test_database.py            # DatabaseManager tests (12 tests)
│   └── test_date_parser.py         # Date parser tests (5 tests)
│
├── docs/                           # Documentation
│   ├── ARCHITECTURE.md             # Architecture and data flow
│   ├── STRUCTURE.md                # This file
│   └── ROADMAP.md                  # Future improvements
│
├── docker-compose.yml              # PostgreSQL 16 + pgAdmin
├── pgadmin-servers.json            # pgAdmin server auto-config
├── alembic.ini                     # Alembic config
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignored files
├── requirements.txt                # Python dependencies
├── setup.py                        # Python package config
└── README.md                       # Main documentation
```

## Module Descriptions

### `config/`
Centralized configuration. Reads environment variables via `python-dotenv`. `DATABASE_URL` points to PostgreSQL by default.

### `src/models/`
- **`base.py`**: Creates the SQLAlchemy engine, declarative `Base` class, and `SessionLocal` (session factory)
- **`event.py`**: 6 ORM models with relationships:
  - `Event` — historical event (UNIQUE date+title)
  - `Source` — data source (UNIQUE name)
  - `EventSource` — N:M event-source link
  - `ScrapeRun` — scraper execution record
  - `Tag` / `EventTag` — tagging system (prepared for future use)
- **`raw_event.py`**: `RawEventData` — simple dataclass produced by scrapers before normalization

### `src/etl/`
- **`scrapers.py`**: Base class + 3 scrapers that produce `RawEventData` and save via `DatabaseManager`
- **`collector.py`**: Orchestrates execution: iterates scrapers, creates `scrape_runs`, handles errors
- **`scrape_result.py`**: Dataclass with counts (found, new, duplicate)

### `src/utils/`
- **`database.py`**: `DatabaseManager` — main DB interface. Methods: `save_event`, `get_event`, `get_events_by_date`, `get_today_events`, `get_random_event`, `start_scrape_run`, `complete_scrape_run`, `get_database_stats`
- **`date_parser.py`**: `parse_date()` — converts multi-format strings to `date` objects

### `src/api/`
- **`main.py`**: FastAPI application with CORS middleware and router registration
- **`deps.py`**: `get_db()` dependency that yields SQLAlchemy sessions
- **`schemas.py`**: Pydantic models for API responses
- **`routes/events.py`**: Event listing, filtering by date/year/month/day, random event
- **`routes/stats.py`**: Database statistics (total, by source, by year)

### `alembic/`
Schema migrations. Alembic compares ORM models against the DB and generates ALTER TABLE scripts automatically.

### `tests/`
- **`conftest.py`**: Monkeypatches `SessionLocal` with SQLite in-memory for each test
- Tests require no Docker or PostgreSQL

## Conventions

- **Directories/files**: `snake_case`
- **Classes**: `PascalCase` (`WW2DataCollector`, `DatabaseManager`)
- **Functions/variables**: `snake_case` (`get_events_by_date`)
- **Constants**: `UPPER_CASE` (`DATABASE_URL`)
