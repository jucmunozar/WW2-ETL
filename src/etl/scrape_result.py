"""Scrape result data transfer object."""
from dataclasses import dataclass


@dataclass
class ScrapeResult:
    """Result summary of a single scraper run."""
    events_found: int = 0
    events_new: int = 0
    events_duplicate: int = 0
