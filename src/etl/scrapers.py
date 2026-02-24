"""Web scrapers for different WW2 timeline sources."""
import logging
import time
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

from config.settings import USER_AGENT, REQUEST_DELAY, REQUEST_TIMEOUT, SOURCE_URLS, WIKIPEDIA_ARTICLES
from src.models.raw_event import RawEventData
from src.utils.date_parser import parse_date
from src.utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for web scrapers."""

    SOURCE_NAME: str = ""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize scraper.

        Args:
            db_manager: DatabaseManager instance for saving events
        """
        self.db_manager = db_manager
        self.headers = {"User-Agent": USER_AGENT}

    def scrape(self) -> int:
        """
        Scrape events from source.

        Returns:
            Number of events saved
        """
        raise NotImplementedError

    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make HTTP request and return BeautifulSoup object."""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            logger.error("Error fetching %s: %s", url, e)
            return None


class WorldWar2FactsScraper(BaseScraper):
    """Scraper for worldwar2facts.org timeline."""

    SOURCE_NAME = "worldwar2facts.org"

    def scrape(self) -> int:
        """Scrape worldwar2facts.org timeline."""
        url = SOURCE_URLS["worldwar2facts"]
        source = "worldwar2facts.org"

        logger.info("Scraping %s...", source)

        soup = self._make_request(url)
        if not soup:
            return 0

        entry_div = soup.find("div", class_="entry")

        if not entry_div:
            logger.warning("Could not find timeline content on %s", source)
            return 0

        # Extract all elements
        title_dates = entry_div.find_all("span", class_="timeline_title_date")
        title_labels = entry_div.find_all("span", class_="timeline_title_label")
        descriptions = entry_div.find_all("div", class_="content")

        logger.info("Found %d events to process", len(title_dates))

        saved_count = 0
        for date_span, title_span, desc_div in zip(title_dates, title_labels, descriptions):
            date_str = date_span.get_text(strip=True)
            title = title_span.get_text(strip=True)
            description = desc_div.get_text(strip=True)

            # If description is empty, use title as description
            if not description:
                description = title

            # Parse the date
            event_date = parse_date(date_str)

            if event_date:
                event = RawEventData(
                    event_date=event_date,
                    title=title,
                    description=description,
                    source=source,
                    source_url=url
                )

                if self.db_manager.save_event(event):
                    saved_count += 1
                    logger.info("Saved: %s - %s", event_date, title[:50])
                else:
                    logger.debug("Duplicate skipped: %s - %s", event_date, title[:30])
            else:
                logger.warning("Could not parse date: %s", date_str)

        logger.info("Successfully saved %d events from %s", saved_count, source)
        time.sleep(REQUEST_DELAY)
        return saved_count



class HistoryPlaceScraper(BaseScraper):
    """Scraper for The History Place WW2 timeline (historyplace.com)."""

    SOURCE_NAME = "historyplace.com"

    def scrape(self) -> int:
        """Scrape historyplace.com timeline."""
        url = SOURCE_URLS.get("historyplace")
        source = "historyplace.com"

        logger.info("Scraping %s...", source)

        soup = self._make_request(url)
        if not soup:
            return 0

        # The timeline content is inside the first blockquote element
        block = soup.find("blockquote")
        if not block:
            logger.warning("Could not find timeline blockquote content on %s", source)
            return 0

        saved_count = 0
        current_year = None

        # iterate through top-level h3 and p elements in the blockquote
        for elem in block.find_all(['h3', 'p'], recursive=False):
            if elem.name == 'h3':
                # example: <h3><strong><a name="1918" id="1918"></a><font color="#0000A0">1918</font> </strong></h3>
                year_text = elem.get_text(strip=True)
                year_match = re.search(r"\b(19\d{2}|20\d{2})\b", year_text)
                if year_match:
                    try:
                        current_year = int(year_match.group(1))
                    except Exception:
                        current_year = None
                continue

            # process paragraph entries
            if elem.name == 'p':
                # Skip "See also:" entries
                if "See also" in elem.get_text():
                    continue

                strong = elem.find('strong')
                if not strong:
                    continue

                # date part is inside the strong/font, e.g. "November 11"
                date_text = strong.get_text(strip=True)

                # remove the strong tag to get the rest of the content (title/description)
                strong.decompose()

                # prefer anchor text as title if present
                a = elem.find('a')
                if a and a.get_text(strip=True):
                    title = a.get_text(strip=True)
                else:
                    # fallback: take text after the dash or the whole paragraph
                    full_text = elem.get_text(" ", strip=True)
                    # remove leading dash if present
                    title = re.split(r"[-–—]\\s*", full_text, maxsplit=1)[-1].strip() if '-' in full_text or '–' in full_text or '—' in full_text else full_text[:200]

                description = elem.get_text(" ", strip=True)

                # parse date using helper, provide current_year when available
                event_date = parse_date(date_text, current_year)
                if not event_date:
                    logger.warning("Could not parse date: %s (year=%s)", date_text, current_year)
                    continue

                event = RawEventData(
                    event_date=event_date,
                    title=title,
                    description=description,
                    source=source,
                    source_url=url
                )

                if self.db_manager.save_event(event):
                    saved_count += 1
                    logger.info("Saved: %s - %s", event_date, title[:50])
                else:
                    logger.debug("Duplicate skipped: %s - %s", event_date, title[:30])

        logger.info("Successfully saved %d events from %s", saved_count, source)
        time.sleep(REQUEST_DELAY)
        return saved_count

class HistoryCooperativeScraper(BaseScraper):
    """Scraper for historycooperative.org WW2 timeline."""

    SOURCE_NAME = "historycooperative.org"

    def scrape(self) -> int:
        """Scrape historycooperative.org timeline."""
        url = SOURCE_URLS["historycooperative"]
        source = "historycooperative.org"

        logger.info("Scraping %s...", source)

        soup = self._make_request(url)
        if not soup:
            return 0

        entry_div = soup.find("div", class_="entry-content")

        if not entry_div:
            logger.warning("Could not find timeline content on %s", source)
            return 0

        entries = entry_div.find_all("p")
        saved_count = 0
        current_year = None

        for p in entries:
            # Check for year headers (h2 tags)
            if p.find_previous_sibling("h2"):
                year_tag = p.find_previous_sibling("h2")
                year_text = year_tag.get_text(strip=True)
                year_match = year_text.split()[0] if year_text else None
                if year_match and year_match.isdigit() and 1930 <= int(year_match) <= 1950:
                    current_year = int(year_match)

            strong_tag = p.find("strong")
            if strong_tag:
                date_text = strong_tag.get_text(strip=True)

                try:
                    # Clean and parse the date (format: "date – title")
                    clean_date = date_text.split('–')[0].strip()
                    event_date = parse_date(clean_date, current_year)

                    if not event_date:
                        continue

                    # Extract the full paragraph text to get complete title
                    full_text = p.get_text(" ", strip=True)

                    # Split on the date separator (–) to separate date from content
                    if '–' in full_text:
                        parts = full_text.split('–', 1)
                        content = parts[1].strip() if len(parts) > 1 else full_text
                    else:
                        content = full_text

                    # Extract title as first sentence (up to period, exclamation, or question mark)
                    # This prevents long descriptions from being included in the title
                    sentence_match = re.match(r'^([^.!?]*[.!?])', content)
                    if sentence_match:
                        title = sentence_match.group(1).strip()
                    else:
                        # If no sentence ending found, take first 100 chars
                        title = content[:100] + ('...' if len(content) > 100 else '')

                    # Clean up: remove multiple spaces, replace multiple spaces with single space
                    title = re.sub(r'\s+', ' ', title)

                    # Use full paragraph text as description
                    description = full_text

                    event = RawEventData(
                        event_date=event_date,
                        title=title,
                        description=description,
                        source=source,
                        source_url=url
                    )

                    if self.db_manager.save_event(event):
                        saved_count += 1
                        logger.info("Saved: %s - %s", event_date, title[:50])
                    else:
                        logger.debug("Duplicate skipped: %s - %s", event_date, title[:30])

                except Exception as e:
                    logger.error("Error processing date: %s - %s", date_text, e)
                    continue

        logger.info("Successfully saved %d events from %s", saved_count, source)
        time.sleep(REQUEST_DELAY)
        return saved_count


class WikipediaScraper(BaseScraper):
    """
    Scraper for Wikipedia WW2 timeline articles via the REST API.

    Uses the Wikimedia REST API (rest_v1) to fetch article HTML,
    then parses timeline sections to extract events.

    Each article (one per year, 1939-1945) has sections by month.
    Within each month, top-level <li> items represent days, and
    nested <li> items within those are the individual events.

    API endpoint: GET /api/rest_v1/page/html/{title}
    """

    BASE_URL = SOURCE_URLS["wikipedia"]
    SOURCE_NAME = "wikipedia.org"
    SKIP_SECTIONS = {"See also", "Footnotes", "References", "Notes", "External links"}
    MONTHS = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    }

    def scrape(self) -> int:
        """Scrape WW2 events from all Wikipedia timeline articles."""
        logger.info("Scraping %s...", self.SOURCE_NAME)
        saved_count = 0

        for article in WIKIPEDIA_ARTICLES:
            saved_count += self._scrape_article(article)
            time.sleep(REQUEST_DELAY)

        logger.info("Successfully saved %d events from %s", saved_count, self.SOURCE_NAME)
        return saved_count

    def _fetch_article_html(self, article_title: str) -> Optional[BeautifulSoup]:
        """
        Fetch article HTML from the Wikipedia REST API.

        Endpoint: GET /page/html/{title}
        """
        url = f"{self.BASE_URL}/page/html/{article_title}"
        headers = {
            **self.headers,
            "Accept": "text/html; charset=utf-8",
        }
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            logger.error("Error fetching Wikipedia article %s: %s", article_title, e)
            return None

    def _extract_month(self, header_text: str) -> Optional[str]:
        """
        Extract month name from header text.

        Handles both "January" (1939-1941) and "January 1945" (1945) formats.
        Returns None if the header is not a month section.
        """
        if header_text in self.SKIP_SECTIONS:
            return None
        for month in self.MONTHS:
            if header_text.startswith(month):
                return month
        return None

    def _extract_year(self, article_title: str) -> Optional[int]:
        """Extract year from article title like 'Timeline_of_World_War_II_(1939)'."""
        match = re.search(r"\((\d{4})\)", article_title)
        if match:
            return int(match.group(1))
        return None

    def _scrape_article(self, article_title: str) -> int:
        """Scrape events from a single Wikipedia timeline article."""
        year = self._extract_year(article_title)
        if not year:
            logger.warning("Could not extract year from article title: %s", article_title)
            return 0

        soup = self._fetch_article_html(article_title)
        if not soup:
            return 0

        article_url = f"https://en.wikipedia.org/wiki/{article_title}"
        saved_count = 0

        for section in soup.find_all("section"):
            header = section.find("h2")
            if not header:
                continue

            month_name = self._extract_month(header.get_text(strip=True))
            if not month_name:
                continue

            # 1939-1941: events in <ul><li> (one <ul> per day)
            for ul in section.find_all("ul", recursive=False):
                for day_li in ul.find_all("li", recursive=False):
                    saved_count += self._process_day_entry(
                        day_li, month_name, year, article_url
                    )

            # 1942-1945: events in <dl><dd> (format: "DAY: event text")
            for dl in section.find_all("dl", recursive=False):
                for dd in dl.find_all("dd", recursive=False):
                    saved_count += self._process_dd_entry(
                        dd, month_name, year, article_url
                    )

        logger.info("Saved %d events from %s (%d)", saved_count, self.SOURCE_NAME, year)
        return saved_count

    def _process_day_entry(self, day_li, month_name: str, year: int, article_url: str) -> int:
        """Process a single day <li> which may contain nested event <li> items."""
        # Extract the day text (direct text before the nested <ul>)
        # Format is typically "1 September" (day + month already included)
        day_text = ""
        for child in day_li.children:
            if hasattr(child, "name") and child.name == "ul":
                break
            if isinstance(child, str):
                day_text += child.strip()

        # day_text already contains month (e.g. "1 September"), extract just the day number
        day_match = re.match(r"^(\d{1,2})", day_text)
        if day_match:
            date_str = f"{month_name} {day_match.group(1)}"
        else:
            date_str = month_name
        event_date = parse_date(date_str, year)

        if not event_date:
            logger.debug("Could not parse date: %s %d", date_str, year)
            return 0

        saved_count = 0
        nested_ul = day_li.find("ul")

        if nested_ul:
            # Day has nested events
            for event_li in nested_ul.find_all("li", recursive=False):
                event_text = event_li.get_text(" ", strip=True)
                if not event_text:
                    continue

                # Remove leading colon (some entries start with ": event text")
                event_text = re.sub(r"^:\s*", "", event_text).strip()
                if not event_text:
                    continue

                title = self._extract_title(event_text)
                saved_count += self._save_event(
                    event_date, title, event_text, article_url
                )
        else:
            # Day entry is the event itself (no nested list)
            event_text = day_li.get_text(" ", strip=True)
            # Remove the leading date portion (e.g. "1 September")
            event_text = re.sub(r"^\d{1,2}\s+\w+\s*:?\s*", "", event_text).strip()
            if event_text:
                title = self._extract_title(event_text)
                saved_count += self._save_event(
                    event_date, title, event_text, article_url
                )

        return saved_count

    def _process_dd_entry(self, dd, month_name: str, year: int, article_url: str) -> int:
        """
        Process a <dd> entry from 1942-1945 articles.

        Format: "DAY: event text" or just "event text" (continuation of previous day).
        """
        text = dd.get_text(" ", strip=True)
        if not text:
            return 0

        # Try to extract day number from "DAY: ..." pattern
        day_match = re.match(r"^(\d{1,2})\s*:\s*(.+)", text)
        if day_match:
            day = day_match.group(1)
            event_text = day_match.group(2).strip()
            date_str = f"{month_name} {day}"
        else:
            # No day prefix — treat as event without specific date
            event_text = text
            date_str = month_name

        event_date = parse_date(date_str, year)
        if not event_date:
            logger.debug("Could not parse date from dd: %s %d", date_str, year)
            return 0

        title = self._extract_title(event_text)
        return self._save_event(event_date, title, event_text, article_url)

    def _extract_title(self, text: str) -> str:
        """Extract the first sentence as title, capped at 200 chars."""
        sentence_match = re.match(r"^([^.!?]*[.!?])", text)
        if sentence_match:
            title = sentence_match.group(1).strip()
        else:
            title = text[:200] + ("..." if len(text) > 200 else "")
        return re.sub(r"\s+", " ", title)

    def _save_event(self, event_date, title: str, description: str, article_url: str) -> int:
        """Create a RawEventData and save it. Returns 1 if new, 0 if duplicate."""
        event = RawEventData(
            event_date=event_date,
            title=title,
            description=description,
            source=self.SOURCE_NAME,
            source_url=article_url,
        )
        if self.db_manager.save_event(event):
            logger.info("Saved: %s - %s", event_date, title[:50])
            return 1
        logger.debug("Duplicate skipped: %s - %s", event_date, title[:30])
        return 0
