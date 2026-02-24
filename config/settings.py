"""
Configuration settings for WW2 ETL project.
Loads from environment variables with sensible defaults.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ww2_user:ww2_secret@localhost:5432/ww2_db"
)

# Scraping configuration
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "2"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(PROJECT_ROOT / "logs" / "ww2_etl.log"))

# Source URLs
SOURCE_URLS = {
    "worldwar2facts": "https://www.worldwar2facts.org/timeline",
    "historycooperative": "https://historycooperative.org/ww2-dates/",
    "historyplace": "http://www.historyplace.com/worldwar2/timeline/ww2time.htm",
    "wikipedia": "https://en.wikipedia.org/api/rest_v1",
}

# Wikipedia API configuration
WIKIPEDIA_ARTICLES = [
    "Timeline_of_World_War_II_(1939)",
    "Timeline_of_World_War_II_(1940)",
    "Timeline_of_World_War_II_(1941)",
    "Timeline_of_World_War_II_(1942)",
    "Timeline_of_World_War_II_(1943)",
    "Timeline_of_World_War_II_(1944)",
    "Timeline_of_World_War_II_(1945)",
]
