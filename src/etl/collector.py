"""Main data collector for WW2 timeline events."""
import logging

from src.utils.database import DatabaseManager
from src.etl.scrapers import WorldWar2FactsScraper, HistoryCooperativeScraper, HistoryPlaceScraper, WikipediaScraper

logger = logging.getLogger(__name__)


class WW2DataCollector:
    """Main class for collecting WW2 timeline data from multiple sources."""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.scrapers = [
            WorldWar2FactsScraper(self.db_manager),
            HistoryCooperativeScraper(self.db_manager),
            HistoryPlaceScraper(self.db_manager),
            WikipediaScraper(self.db_manager),
        ]

    def collect_all(self) -> int:
        """
        Collect data from all sources.

        Returns:
            Total number of new events saved
        """
        logger.info("Starting WW2 timeline data collection...")

        total_saved = 0
        for scraper in self.scrapers:
            source_name = scraper.SOURCE_NAME
            run_id = self.db_manager.start_scrape_run(source_name)
            try:
                saved = scraper.scrape()
                total_saved += saved
                self.db_manager.complete_scrape_run(
                    run_id,
                    status="success",
                    events_new=saved,
                )
            except Exception as e:
                logger.error("Error in scraper %s: %s", source_name, e)
                self.db_manager.complete_scrape_run(
                    run_id,
                    status="failed",
                    error_message=str(e),
                )
                continue

        logger.info("Scraping complete! Total new events saved: %d", total_saved)
        return total_saved

    def get_stats(self):
        """Print database statistics."""
        self.db_manager.print_stats()
