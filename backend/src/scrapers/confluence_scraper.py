"""
Confluence scraper for extracting documentation from public Confluence wikis.
Designed to work with Apache Kafka's public Confluence space for POC.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import time
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path
from dataclasses import dataclass, asdict

from ..utils import log


@dataclass
class ConfluenceDocument:
    """Data class for a scraped Confluence document."""
    id: str
    title: str
    content: str
    url: str
    space: str
    labels: List[str]
    last_modified: Optional[str]
    source_type: str = "confluence"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PublicConfluenceScraper:
    """
    Scraper for public Confluence wikis (no authentication required).
    Optimized for Apache Kafka's Confluence space.
    """
    
    def __init__(self, base_url: str, max_retries: int = 3, delay: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            base_url: Base Confluence URL (e.g., https://cwiki.apache.org/confluence)
            max_retries: Maximum retry attempts for failed requests
            delay: Delay between requests in seconds (be respectful to servers)
        """
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-SME-Scraper/1.0 (Educational Purpose)'
        })
        self.visited_urls: Set[str] = set()
        
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """
        Make HTTP request with retries and error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response object or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                log.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    log.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
    
    def _clean_html(self, html: str) -> str:
        """
        Convert Confluence HTML to clean text.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script, style, and navigation elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Remove Confluence-specific UI elements
        for class_name in ['plugin', 'pageSection', 'navmenu', 'labels-section']:
            for element in soup.find_all(class_=class_name):
                element.decompose()
        
        # Get text with proper spacing
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def _extract_page_id(self, url: str) -> str:
        """
        Extract page ID from Confluence URL.
        
        Args:
            url: Confluence page URL
            
        Returns:
            Page identifier
        """
        # Try to extract from URL patterns
        if 'pageId=' in url:
            return url.split('pageId=')[1].split('&')[0]
        elif '/pages/' in url:
            return url.split('/pages/')[1].split('/')[0]
        else:
            # Use URL path as ID
            parsed = urlparse(url)
            return parsed.path.replace('/', '_').strip('_')
    
    def _extract_space_key(self, url: str) -> str:
        """
        Extract space key from Confluence URL.
        
        Args:
            url: Confluence page URL
            
        Returns:
            Space key (e.g., 'KAFKA')
        """
        if '/display/' in url:
            parts = url.split('/display/')[1].split('/')
            return parts[0] if parts else 'unknown'
        return 'unknown'
    
    def scrape_page(self, page_url: str) -> Optional[ConfluenceDocument]:
        """
        Scrape a single Confluence page.
        
        Args:
            page_url: URL of the page to scrape
            
        Returns:
            ConfluenceDocument or None if scraping failed
        """
        if page_url in self.visited_urls:
            log.debug(f"Already visited: {page_url}")
            return None
        
        log.info(f"Scraping page: {page_url}")
        self.visited_urls.add(page_url)
        
        response = self._make_request(page_url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.text.strip() if title_elem else 'Untitled'
            
            # Extract main content
            main_content = soup.find('div', {'id': 'main-content'})
            if not main_content:
                main_content = soup.find('div', {'class': 'wiki-content'})
            
            if main_content:
                content = self._clean_html(str(main_content))
            else:
                log.warning(f"Could not find main content for: {page_url}")
                content = self._clean_html(response.text)
            
            # Extract labels/tags
            labels = []
            label_elements = soup.find_all('a', {'class': 'label'})
            for label_elem in label_elements:
                label_text = label_elem.text.strip()
                if label_text:
                    labels.append(label_text)
            
            # Extract last modified date
            last_modified = None
            modified_elem = soup.find('span', {'class': 'last-modified'})
            if modified_elem:
                last_modified = modified_elem.text.strip()
            
            # Create document
            page_id = self._extract_page_id(page_url)
            space_key = self._extract_space_key(page_url)
            
            doc = ConfluenceDocument(
                id=page_id,
                title=title,
                content=content,
                url=page_url,
                space=space_key,
                labels=labels,
                last_modified=last_modified,
                source_type="confluence"
            )
            
            log.info(f"Successfully scraped: {title}")
            return doc
            
        except Exception as e:
            log.error(f"Error parsing page {page_url}: {e}")
            return None
        
        finally:
            # Be respectful to the server
            time.sleep(self.delay)
    
    def find_page_links(self, space_url: str, max_links: int = 100) -> List[str]:
        """
        Find all page links within a Confluence space.
        
        Args:
            space_url: URL of the Confluence space (e.g., /display/KAFKA)
            max_links: Maximum number of links to collect
            
        Returns:
            List of page URLs
        """
        log.info(f"Finding page links in: {space_url}")
        
        response = self._make_request(space_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_links = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's a wiki page link
            if '/display/' in href or '/pages/' in href:
                # Convert relative URLs to absolute
                full_url = urljoin(self.base_url, href)
                
                # Remove query parameters and anchors for deduplication
                parsed = urlparse(full_url)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                
                # Add to set (automatically deduplicates)
                page_links.add(clean_url)
                
                if len(page_links) >= max_links:
                    break
        
        page_list = list(page_links)
        log.info(f"Found {len(page_list)} unique page links")
        return page_list
    
    def scrape_space(
        self, 
        space_url: str, 
        max_pages: int = 50,
        output_dir: Optional[Path] = None
    ) -> List[ConfluenceDocument]:
        """
        Scrape multiple pages from a Confluence space.
        
        Args:
            space_url: URL of the space (e.g., https://cwiki.apache.org/confluence/display/KAFKA)
            max_pages: Maximum number of pages to scrape
            output_dir: Optional directory to save raw JSON files
            
        Returns:
            List of ConfluenceDocument objects
        """
        log.info(f"Starting to scrape space: {space_url}")
        log.info(f"Max pages to scrape: {max_pages}")
        
        # First, find all page links
        page_urls = self.find_page_links(space_url, max_links=max_pages * 2)
        
        # Limit to max_pages
        page_urls = page_urls[:max_pages]
        
        # Scrape each page
        documents = []
        for i, page_url in enumerate(page_urls, 1):
            log.info(f"Progress: {i}/{len(page_urls)}")
            
            doc = self.scrape_page(page_url)
            if doc:
                documents.append(doc)
                
                # Save to file if output directory specified
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"confluence_{doc.id}.json"
                    filepath = output_dir / filename
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
                    
                    log.debug(f"Saved to: {filepath}")
        
        log.info(f"Scraping complete! Successfully scraped {len(documents)} pages")
        return documents
    
    def scrape_single_page_and_save(
        self, 
        page_url: str, 
        output_dir: Path
    ) -> Optional[ConfluenceDocument]:
        """
        Scrape a single page and save to JSON.
        
        Args:
            page_url: URL of the page to scrape
            output_dir: Directory to save the JSON file
            
        Returns:
            ConfluenceDocument or None if failed
        """
        doc = self.scrape_page(page_url)
        
        if doc and output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"confluence_{doc.id}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
            
            log.info(f"Saved to: {filepath}")
        
        return doc


# Convenience function for quick scraping
def scrape_kafka_confluence(
    max_pages: int = 30,
    output_dir: Optional[str] = None
) -> List[ConfluenceDocument]:
    """
    Quick function to scrape Apache Kafka Confluence documentation.
    
    Args:
        max_pages: Maximum number of pages to scrape
        output_dir: Optional directory to save JSON files
        
    Returns:
        List of scraped documents
    """
    base_url = "https://cwiki.apache.org/confluence"
    space_url = "https://cwiki.apache.org/confluence/display/KAFKA"
    
    scraper = PublicConfluenceScraper(base_url)
    
    output_path = Path(output_dir) if output_dir else None
    
    return scraper.scrape_space(space_url, max_pages=max_pages, output_dir=output_path)
