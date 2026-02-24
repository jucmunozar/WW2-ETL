# Roadmap: WW2-ETL Portfolio Ready

Improvements organized by priority and complexity to make the project portfolio-ready.

---

## Phase 1: Data Quality (high priority)

### 1.1 Semantic Deduplication with AI
**Status**: Pending
**Complexity**: Medium

Currently dedup is by exact title (`UNIQUE(event_date, title)`). But sources describe the same event with different words:
- "D-Day, Allied invasion of Normandy"
- "D-Day: invasion of Europe begins with Allied landings..."

**Implementation**:
- AI agent that compares events on the same date by semantic similarity
- Uses an LLM (Claude Haiku) to decide if two events are the same
- Smart merge: picks the best title/description
- Optional human-in-the-loop for ambiguous cases
- Estimated cost: pennies per run (~3-5 comparisons per event)

### 1.2 Existing Data Cleanup
**Status**: Partially done (15 duplicates merged via pg_trgm)
**Complexity**: Low

- Clean `\r\n` characters in titles
- Normalize punctuation and whitespace
- Validate all dates are within WW2 range (1918-1945)

---

## Phase 2: Orchestration (high priority)

### 2.1 Apache Airflow
**Complexity**: Medium-High

Replace `scripts/run_etl.py` with an Airflow DAG:
- Task 1: Scrape WorldWar2Facts
- Task 2: Scrape HistoryCooperative
- Task 3: Scrape HistoryPlace
- Task 4: AI Dedup (depends on 1-3)
- Task 5: Generate statistics

**Benefits**: Scheduling, retry logic, monitoring UI, failure alerts.

### 2.2 Add Airflow to Docker Compose
- Airflow webserver + scheduler + worker
- Use the same PostgreSQL as Airflow backend

---

## Phase 3: API + Frontend (medium priority)

### 3.1 REST API with FastAPI
**Status**: Done
**Complexity**: Medium

Endpoints:
- `GET /events` — list events (paginated, filters by date/source/year)
- `GET /events/random` — random event
- `GET /stats` — database statistics

Stack: FastAPI + Pydantic + SQLAlchemy (reuses existing models)

### 3.2 Simple Frontend
**Complexity**: Medium

- Interactive WW2 event timeline
- Filters by year, source, tags
- Stack: React or plain HTML with HTMX

---

## Phase 4: Data Enrichment (medium priority)

### 4.1 Auto-tagging with AI
**Complexity**: Medium

Use an LLM to automatically categorize events:
- Categories: battle, politics, diplomacy, holocaust, pacific_front, european_front, etc.
- Populate the existing `tags` and `event_tags` tables

### 4.2 Add More Sources
**Complexity**: Low (per source)

- National WW2 Museum
- Imperial War Museum

Each new source = 1 class inheriting from `BaseScraper`.

### 4.3 Geolocation
**Complexity**: Medium

- Add `location` column to events (via Alembic migration)
- Extract locations from text with NER (Named Entity Recognition)
- Visualize on a map

---

## Phase 5: Infrastructure (low priority)

### 5.1 CI/CD with GitHub Actions
**Complexity**: Low

- Run tests on each push
- Lint with ruff/flake8
- Type checking with mypy

### 5.2 Structured Logging
**Complexity**: Low

- Replace `print()` with `logging` module
- JSON log format
- Levels: INFO for saves, WARNING for duplicates, ERROR for failures

### 5.3 Monitoring
**Complexity**: Medium

- Dashboard for scrape_runs (successes, failures, trends)
- Alerts when a scraper fails N consecutive times
- Data quality metrics (% duplicates, events per source)

---

## Suggested Implementation Order

| # | Feature | Portfolio Impact | Effort |
|---|---------|-----------------|--------|
| 1 | CI/CD (GitHub Actions) | High | Low |
| 2 | REST API (FastAPI) | Very high | Medium |
| 3 | Auto-tagging with AI | Very high | Medium |
| 4 | Semantic dedup with AI | High | Medium |
| 5 | Structured logging | Medium | Low |
| 6 | Airflow orchestration | Very high | High |
| 7 | More data sources | Medium | Low |
| 8 | Frontend / timeline | High | Medium |
| 9 | Geolocation + map | High | High |
