import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import re

class WW2DataCollector:
    def __init__(self, db_path="ww2_timeline.db"):
        self.db_path = db_path
        self.setup_database()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
    
    def setup_database(self):
        """Initialize SQLite database with events table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date DATE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                source TEXT NOT NULL,
                source_url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_date, title, source)
            )
        """)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    
    def parse_date(self, date_str, year=None):
        """Parse various date formats and return date object"""
        date_str = date_str.strip()
        
        # Add year if not present
        if year and not re.search(r'\b(19[3-4]\d|195[0-5])\b', date_str):
            date_str += f", {year}"
        
        # Try different date formats
        formats = [
            "%B %d, %Y",    # January 1, 1941
            "%B %d %Y",     # January 1 1941  
            "%d %B %Y",     # 1 January 1941
            "%B %Y",        # January 1941 (will default to 1st)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Extract year and use January 1st as fallback
        year_match = re.search(r'\b(19[3-4]\d|195[0-5])\b', date_str)
        if year_match:
            year_num = int(year_match.group(1))
            return datetime(year_num, 1, 1).date()
        
        return None
    
    def save_event(self, event_date, title, description, source, source_url=""):
        """Save event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO events 
                (event_date, title, description, source, source_url) 
                VALUES (?, ?, ?, ?, ?)
            """, (event_date, title, description, source, source_url))
            
            rowcount = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rowcount > 0
        
        except Exception as e:
            print(f"Error saving event: {e}")
            return False
    
    def scrape_worldwar2facts(self):
        """Scrape worldwar2facts.org timeline"""
        url = "https://www.worldwar2facts.org/timeline"
        source = "worldwar2facts.org"
        
        print(f"Scraping {source}...")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            entry_div = soup.find("div", class_="entry")
            
            if not entry_div:
                print("Could not find timeline content")
                return 0
            
            # Extract all elements
            title_dates = entry_div.find_all("span", class_="timeline_title_date")
            title_labels = entry_div.find_all("span", class_="timeline_title_label")
            descriptions = entry_div.find_all("div", class_="content")
            
            print(f"Found {len(title_dates)} events to process")
            
            saved_count = 0
            for i, (date_span, title_span, desc_div) in enumerate(zip(title_dates, title_labels, descriptions)):
                
                date_str = date_span.get_text(strip=True)
                title = title_span.get_text(strip=True)
                description = desc_div.get_text(strip=True)
                
                # Parse the date
                event_date = self.parse_date(date_str)
                
                if event_date:
                    if self.save_event(event_date, title, description, source, url):
                        saved_count += 1
                        print(f"Saved: {event_date} - {title[:50]}...")
                    else:
                        print(f"Duplicate skipped: {event_date} - {title[:30]}...")
                else:
                    print(f"✗ Could not parse date: {date_str}")
            
            print(f"Successfully saved {saved_count} events from {source}")
            return saved_count
            
        except Exception as e:
            print(f"Error scraping {source}: {e}")
            return 0
    
    # def scrape_historyplace(self):
    #     """Scrape The History Place WW2 timeline"""
    #     url = "http://www.historyplace.com/worldwar2/timeline/ww2time.htm"
    #     source = "historyplace.com"
        
    #     print(f"Scraping {source}...")
        
    #     try:
    #         response = requests.get(url, headers=self.headers)
    #         response.raise_for_status()
            
    #         soup = BeautifulSoup(response.content, "html.parser")
            
    #         # Find main content
    #         content = soup.find("table") or soup.find("div", {"align": "left"}) or soup.body
            
    #         saved_count = 0
    #         current_year = None
            
    #         # Process all text elements
    #         for element in content.find_all(['p', 'td', 'tr', 'b', 'strong']):
    #             text = element.get_text(strip=True)

    #             if not text:
    #                 continue
                
    #             # Check if this is a year header
    #             year_match = re.search(r'\b(19[3-4]\d|195[0-5])\b', text)
    #             if year_match and len(text) < 30:
    #                 current_year = int(year_match.group(1))
    #                 print(f"Processing year: {current_year}")
    #                 continue
                
    #             # Look for date patterns
    #             date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}'
    #             if re.search(date_pattern, text, re.IGNORECASE):
                    
    #                 # Split on common separators to find date and description
    #                 for separator in [' - ', ' – ', ': ', ' — ']:
    #                     if separator in text:
    #                         parts = text.split(separator, 1)
    #                         date_part = parts[0].strip()
    #                         desc_part = parts[1].strip() if len(parts) > 1 else text
    #                         break
    #                 else:
    #                     # No separator found, use first 25 chars as potential date
    #                     date_part = text[:25]
    #                     desc_part = text
                    
    #                 # Parse the date
    #                 event_date = self.parse_date(date_part, current_year)
                    
    #                 if event_date:
    #                     # Create title from first part of description
    #                     title = desc_part.split('.')[0][:100] if desc_part else "WW2 Event"
                        
    #                     if self.save_event(event_date, title, desc_part, source, url):
    #                         saved_count += 1
    #                         print(f"✓ Saved: {event_date} - {title[:50]}...")
            
    #         print(f"Successfully saved {saved_count} events from {source}")
    #         return saved_count
            
    #     except Exception as e:
    #         print(f"Error scraping {source}: {e}")
    #         return 0
    
    def get_database_stats(self):
        """Print database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        
        # Events by source
        cursor.execute("SELECT source, COUNT(*) FROM events GROUP BY source")
        by_source = cursor.fetchall()
        
        # Date range
        cursor.execute("SELECT MIN(event_date), MAX(event_date) FROM events")
        date_range = cursor.fetchone()
        
        # Events by year
        cursor.execute("""
            SELECT strftime('%Y', event_date) as year, COUNT(*) 
            FROM events 
            GROUP BY year 
            ORDER BY year
        """)
        by_year = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        print(f"Total events: {total}")
        print(f"Date range: {date_range[0]} to {date_range[1]}")
        print("\nEvents by source:")
        for source, count in by_source:
            print(f"  {source}: {count}")
        print("\nEvents by year:")
        for year, count in by_year:
            print(f"  {year}: {count}")
        print("="*50)

def main():
    # Initialize data collector
    collector = WW2DataCollector()
    
    print("Starting WW2 timeline data collection...")
    print("-" * 50)
    
    # Scrape all sources
    total_saved = 0
    
    # Site 1: worldwar2facts.org
    total_saved += collector.scrape_worldwar2facts()
    time.sleep(2)  # Be polite to servers
    
    # Site 2: historyplace.com
    # total_saved += collector.scrape_historyplace()
    
    print(f"\n🎉 SCRAPING COMPLETE!")
    print(f"Total new events saved: {total_saved}")
    
    # Show database statistics
    # collector.get_database_stats()
    
    print("\n✅ Your WW2 timeline database is ready!")
    print("📁 Database file: ww2_timeline.db")
    print("🤖 Next step: Create your Twitter bot to use this data")

if __name__ == "__main__":
    main()