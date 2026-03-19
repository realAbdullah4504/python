from typing import Tuple, List, Dict, Optional, Set
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
import os
import requests
from utils.playwright_utils import setup_browser_context, open_page, navigate_to_main_page, simulate_postback, cleanup_browser_resources
from utils.config_resolver import load_config_with_refs, get_portal_config
from utils.file_utils import load_existing_tender_numbers, save_tender_to_ndjson, ensure_output_directory
from utils.web_utils import extract_csrf_token_and_session
from utils.bs4_utils import (
    extract_tender_blocks, parse_tender_block, format_tender_item,
    extract_pagination_links, extract_listing_rows, find_next_pagination_link
)
from models.tender import TenderModel
from crawlers.processors import TenderProcessor, DeduplicationService
from crawlers.pagination import DataTablesPaginationHandler, PostbackPaginationHandler
from crawlers.strategies import CrawlerFactory

# Constants
STOP_MESSAGE = "Stopping crawl due to existing tender found"


def get_portal_by_url(portals: List[Dict], url: str) -> Optional[Dict]:
    """Find portal configuration by URL."""
    for portal in portals:
        if url in portal.get('listing_urls', []):
            return portal
    return None


def crawl_all_tenders(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
    """
    Main function to crawl and parse all tenders from portal.
    Uses strategy pattern to select appropriate crawler.
    """
    try:
        # Create appropriate crawler strategy using factory
        crawler = CrawlerFactory.create_crawler(portal_config)
        
        # Execute crawling using the selected strategy
        tenders = crawler.crawl(url, portal_config, seen_tender_numbers)
        
        return tenders
        
    except ValueError as e:
        print(f"Error creating crawler: {e}")
        return []


def main() -> None:
    """Main function to orchestrate the unified tender crawling workflow"""
    config = load_config_with_refs("config/portals.json")
    
    all_tenders = []
    seen_tender_numbers = load_existing_tender_numbers("outputs/tenders.ndjson")
    
    # Loop over all portals
    for portal in config["portals"]:
        if not portal.get("active", True):
            print(f"Skipping inactive portal: {portal['name']}")
            continue
            
        print(f"Processing portal: {portal['name']} ({portal['country']})")
        
        # Get portal configuration
        portal_config = get_portal_config(portal)
        
        # Loop over all listing URLs for this portal
        for url in portal["listing_urls"]:
            print(f"Crawling URL: {url}")
            
            tenders = crawl_all_tenders(url, portal_config, seen_tender_numbers)
            all_tenders.extend(tenders)
            print(f"Found {len(tenders)} tenders from {url}")
    
    print(f"Total tenders found across all portals: {len(all_tenders)}")
    
    # Display first 5 tenders in generic format
    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()
