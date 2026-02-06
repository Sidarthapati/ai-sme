"""
Production script to scrape Apache Kafka Confluence documentation.
Run this to collect the full dataset for the POC.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.confluence_scraper import scrape_kafka_confluence
from src.utils import log


def main():
    """Scrape Apache Kafka Confluence documentation."""
    
    max_pages = 110
    output_dir = "/Users/sidarthapati/Desktop/Projects/AI SME/data/raw/confluence"
    
    print(f"\n📚 Scraping {max_pages} Confluence pages...")
    
    try:
        documents = scrape_kafka_confluence(
            max_pages=max_pages,
            output_dir=output_dir
        )
        
        total_chars = sum(len(doc.content) for doc in documents)
        
        print(f"✅ Scraped {len(documents)} pages ({total_chars:,} characters)")
        print(f"   Saved to: {Path(output_dir).absolute()}\n")
        
        return 0
        
    except Exception as e:
        log.error(f"Scraping failed: {e}")
        print(f"❌ Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
