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

# Constants
STOP_MESSAGE = "Stopping crawl due to existing tender found"


def get_portal_by_url(portals: List[Dict], url: str) -> Optional[Dict]:
    """Find portal configuration by URL."""
    for portal in portals:
        if url in portal.get('listing_urls', []):
            return portal
    return None


def _crawl_pattern_based_portal(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
    """Crawl pattern-based portals (CSJN style)"""
    patterns = portal_config.get('patterns', {})
    portal_name = portal_config.get('name', 'Unknown')
    all_tenders = []
    
    # Initialize processor
    deduplication_service = DeduplicationService(seen_tender_numbers)
    tender_processor = TenderProcessor(deduplication_service)
    
    if not patterns:
        raise ValueError("No patterns found in configuration for URL: {}".format(url))
    
    # Check if portal has pagination configuration
    if portal_config.get('pagination', {}).get('type') == 'datatables':
        print("Using DataTables pagination...")
        parsed_tenders = []
        pagination_config = portal_config.get('pagination', {})
        
        # Initialize DataTables pagination handler
        pagination_handler = DataTablesPaginationHandler(url)
        max_pages = pagination_handler.get_max_pages(pagination_config)
        
        for page in range(1, max_pages + 1):
            print("Fetching page {}...".format(page))
            
            response_data = pagination_handler.fetch_page_data(page, pagination_config)
            if not response_data:
                break
            
            # Check if we have data
            if not response_data.get('data') or len(response_data['data']) == 0:
                print("No more data found, stopping pagination.")
                break
            
            # Check if this is the last page
            if pagination_handler.is_last_page(response_data, pagination_config):
                print("Reached last page.")
                break
            
            # Parse each tender from response
            page_tenders = []
            for item in response_data['data']:
                # Convert DataTables item to text format for parsing
                tender_text = format_tender_item(item)
                tender = parse_tender_block(tender_text, patterns)
                
                if tender:
                    page_tenders.append(tender)
            
            # Process page tenders with deduplication
            new_count, new_generic_tenders, existing_found = tender_processor.process_raw_tenders(page_tenders, portal_name, url)
            all_tenders.extend(new_generic_tenders)
            
            print("Added {} new tenders from page {}".format(new_count, page))
            
            # Stop crawling if existing tender found
            if existing_found:
                print(STOP_MESSAGE)
                break
    else:
        print("Using static page parsing...")
        # Fallback to original method
        page = open_page(url)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract all text content
        excluded_tags = portal_config.get('selectors', {}).get('excluded_tags', ['script', 'style'])
        for tag in soup(excluded_tags):
            tag.decompose()
        
        main_text = soup.get_text(separator='\n', strip=True)
        
        # Split into tender blocks
        tender_blocks = extract_tender_blocks(main_text, patterns)
        
        # Parse each block
        parsed_tenders = []
        for block in tender_blocks:
            tender = parse_tender_block(block, patterns)
            if tender:
                parsed_tenders.append(tender)
        
        # Process tenders with deduplication
        new_count, new_generic_tenders, existing_found = tender_processor.process_raw_tenders(parsed_tenders, portal_name, url)
        all_tenders.extend(new_generic_tenders)
        
        print("Added {} new tenders from static page".format(new_count))
        
        # Stop crawling if existing tender found
        if existing_found:
            print(STOP_MESSAGE)
    
    return all_tenders


def _crawl_table_based_portal(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
    """Crawl table-based portals (Comprar Gob AR style)"""
    portal_name = portal_config.get('name', 'Unknown')
    selectors = portal_config["selectors"]
    column_mapping = portal_config.get("column_mapping", {})
    pagination = portal_config.get("pagination", {})
    all_tenders = []

    # Initialize processor
    deduplication_service = DeduplicationService(seen_tender_numbers)
    tender_processor = TenderProcessor(deduplication_service)
    
    # Initialize postback pagination handler
    pagination_handler = PostbackPaginationHandler()

    playwright, browser, context = setup_browser_context()
    
    try:
        page = navigate_to_main_page(context, url)
        current_page = 1
        
        # Extract pagination info from the page
        html = page.content()
        pagination_handler.extract_pagination_info(html, pagination)
        max_pages = pagination_handler.get_max_pages(pagination)

        while current_page <= max_pages:
            print(f"Crawling page: {current_page}")

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # 🔹 SAME logic for every page (including page 1)
            tenders = extract_listing_rows(
                soup,
                url,
                selectors,
                column_mapping,
                page_no=current_page
            )

            if not tenders:
                print("No tenders found, stopping crawl")
                break

            new_count, new_tenders, existing_found = tender_processor.process_raw_tenders(tenders, portal_name)
            all_tenders.extend(new_tenders)

            print(f"Added {new_count} new tenders from page {current_page}")

            # Stop crawling if existing tender found
            if existing_found:
                print(STOP_MESSAGE)
                break

            if new_count == 0:
                print("No new tenders found, stopping crawl")
                break

            current_page += 1

            # Handle pagination using the pagination handler
            if pagination_handler.should_continue_pagination(current_page, pagination):
                pagination_success = pagination_handler.handle_pagination(page, current_page, pagination)
                if not pagination_success:
                    print("Pagination failed or no more pages available")
                    break
            else:
                print(f"Reached maximum pages limit ({max_pages}), stopping crawl")
                break

    finally:
        cleanup_browser_resources(playwright, browser)

    return all_tenders


def crawl_all_tenders(url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
    """
    Main function to crawl and parse all tenders from portal.
    Automatically detects portal type and routes to appropriate handler.
    """
    # Determine portal type
    if portal_config.get('patterns'):
        print("Detected pattern-based portal")
        return _crawl_pattern_based_portal(url, portal_config, seen_tender_numbers)
    elif portal_config.get('selectors'):
        print("Detected table-based portal")
        return _crawl_table_based_portal(url, portal_config, seen_tender_numbers)
    else:
        raise ValueError("Unable to determine portal type from configuration for URL: {}".format(url))


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
