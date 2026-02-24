"""Date parsing utilities for WW2 timeline events."""
import re
from datetime import datetime
from typing import Optional


def parse_date(date_str: str, year: Optional[int] = None) -> Optional[datetime.date]:
    """
    Parse various date formats and return date object.
    
    Args:
        date_str: String containing date information
        year: Optional year to use if not present in date_str
        
    Returns:
        Parsed date object or None if parsing fails
    """
    if not date_str:
        return None
        
    date_str = date_str.strip()
    
    # Add year if not present
    if year and not re.search(r'\b(19[3-4]\d|195[0-5])\b', date_str):
        date_str = f"{date_str} {year}"
    
    # Try different date formats with and without commas
    formats = [
        "%B %d %Y",     # January 1 1941 (no comma, with year)
        "%B %d, %Y",    # January 1, 1941 (with comma)
        "%d %B %Y",     # 1 January 1941
        "%B %Y",        # January 1941 (will default to 1st)
        "%Y-%m-%d",     # 1941-01-01
        "%d/%m/%Y",     # 01/01/1941
        "%m/%d/%Y",     # 01/01/1941
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # Try to extract just month and day, and combine with provided year
    if year:
        # Pattern: "Month Day" or "Month Day-" (with trailing dash)
        month_day_match = re.match(r'^\s*(\w+)\s+(\d{1,2})', date_str)
        if month_day_match:
            month_name = month_day_match.group(1)
            day = month_day_match.group(2)
            try:
                return datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y").date()
            except ValueError:
                pass
    
    # Extract year and use January 1st as fallback
    year_match = re.search(r'\b(19[3-4]\d|195[0-5])\b', date_str)
    if year_match:
        year_num = int(year_match.group(1))
        return datetime(year_num, 1, 1).date()
    
    return None

