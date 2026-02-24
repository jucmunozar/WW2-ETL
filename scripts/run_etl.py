#!/usr/bin/env python3
"""Script to run the WW2 ETL pipeline."""
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from src.etl.collector import WW2DataCollector


def main():
    """Run the ETL pipeline."""
    collector = WW2DataCollector()
    collector.collect_all()
    collector.get_stats()


if __name__ == "__main__":
    main()
