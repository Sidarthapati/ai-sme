"""
Scrapers module for fetching data from various sources.

This module contains:
- confluence_scraper.py: Scrape Confluence documentation ✅
- github_indexer.py: Index GitHub repositories ✅
"""

from .confluence_scraper import (
    PublicConfluenceScraper,
    ConfluenceDocument,
    scrape_kafka_confluence
)

from .github_indexer import (
    LocalGitHubIndexer,
    CodeDocument,
    index_kafka_repository
)

__all__ = [
    "PublicConfluenceScraper",
    "ConfluenceDocument",
    "scrape_kafka_confluence",
    "LocalGitHubIndexer",
    "CodeDocument",
    "index_kafka_repository",
]
