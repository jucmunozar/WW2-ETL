import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime

# Connect or create the SQLite DB
conn = sqlite3.connect("timeline.db")
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        title TEXT,
        description TEXT
    )
""")

def scrape_site_one():
    # Target URL
    url = "https://www.worldwar2facts.org/timeline"

    # Set headers to mimic a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        # Find the main content area that holds the timeline
        entry_div = soup.find("div", class_="entry")

        """
        While reviewing the HTML, I found that the timeline is structured in a specific way;    
        where the year for each group of events is marked with "date_separator animated" class,
        each title is marked with "timeline_title_label" class, 
        the date is marked with "timeline_title_date" class, 
        and the description is marked with "content" class.
        So I neeed to extract each element separately.
        """

        events_year = entry_div.find_all("div", class_="date_separator animated")

        events_title_label = entry_div.find_all("span", class_="timeline_title_label")

        events_title_date = entry_div.find_all("span", class_="timeline_title_date")

        events_description = entry_div.find_all("div", class_="content")

        # DEBUG: check how many elements were found
        print(f"Found {len(events_year)} years, {len(events_title_label)} titles, {len(events_title_date)} dates, {len(events_description)} descriptions from site one.")

        # Print and store the timeline events
        for idx, (date, title, desc) in enumerate(zip(events_title_date, events_title_label, events_description), start=1):
            date = date.get_text(strip=True)
            title = title.get_text(strip=True)
            desc = desc.get_text(strip=True)

            try:
                date_obj = datetime.strptime(date, "%B %d %Y").date()
            except ValueError:
                print(f"Skipping invalid date: {date}")
                continue  # skip this entry if the date is malformed

            print(f"{idx}. {date}. {title}. {desc}")
            cursor.execute("INSERT INTO timeline (date, title, description) VALUES (?, ?, ?)", (date_obj, title, desc))

        # Save changes and close
        conn.commit()
        conn.close()

    except requests.exceptions.RequestException as e:
        print("Error fetching the webpage:", e)


def main():
    site_one_data = scrape_site_one()
    # site_two_data = scrape_site_two()  
    all_data = site_one_data  # + site_two_data

