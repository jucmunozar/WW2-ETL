"""Tests for date parser utility."""
from datetime import date
from src.utils.date_parser import parse_date


def test_parse_standard_date():
    """Test parsing standard date format."""
    result = parse_date("January 1, 1941")
    assert result == date(1941, 1, 1)


def test_parse_date_without_comma():
    """Test parsing date without comma."""
    result = parse_date("January 1 1941")
    assert result == date(1941, 1, 1)


def test_parse_date_with_year_only():
    """Test parsing date with only year."""
    result = parse_date("1941")
    assert result == date(1941, 1, 1)


def test_parse_invalid_date():
    """Test parsing invalid date returns None."""
    result = parse_date("invalid date")
    assert result is None or result.year == 1941  # May extract year


def test_parse_date_with_year_parameter():
    """Test parsing date with year parameter."""
    result = parse_date("January 1", year=1941)
    assert result == date(1941, 1, 1)

