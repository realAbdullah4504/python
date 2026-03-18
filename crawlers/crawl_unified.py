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

# Constants
STOP_MESSAGE = "Stopping crawl due to existing tender found"


def get_portal_by_url(portals: List[Dict], url: str) -> Optional[Dict]:
    """Find portal configuration by URL."""
    for portal in portals:
        if url in portal.get('listing_urls', []):
            return portal
    return None


def fetch_datatables_page(base_url: str, pagination_config: Dict, page: int = 1, session: requests.Session = None, csrf_token: str = None) -> Optional[Dict]:
    """
    Fetch a single page of data from DataTables API.
    """
    from urllib.parse import urljoin
    
    if not session or not csrf_token:
        csrf_token, session = extract_csrf_token_and_session(base_url)
    
    endpoint = pagination_config['endpoint']
    # Ensure proper URL construction
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    url = urljoin(base_url, endpoint)
    
    print("Fetching from URL: {}".format(url))
    
    # DataTables request payload
    payload = {
        "draw": page,
        "start": (page - 1) * pagination_config['page_size'],
        "length": pagination_config['page_size'],
        "search": {"value": "", "regex": False},
        "order": [{"column": 0, "dir": "desc"}],
        "columns": [{"data": "0", "name": "", "searchable": True, "orderable": False, "search": {"value": "", "regex": False}}],
        "formBusqueda": {
            "qa": "",
            "nroDoca": "",
            "anioDoca": "",
            "temaBase": "K76",
            "temaPrincipal_a": "K76",
            "subTema_a": "",
            "fechaDesde_a": "",
            "fechaHasta_a": ""
        }
    }
    
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-CSRF-TOKEN': csrf_token,
        'Referer': base_url,
        'Origin': 'https://www.csjn.gov.ar'
    }
    
    try:
        response = session.post(url, json=payload, headers=headers, timeout=60)
        print("Response status: {}".format(response.status_code))
        if response.status_code != 200:
            print("Response content: {}".format(response.text[:500]))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Timeout error fetching page {}: Request took too long".format(page))
        return None
    except requests.exceptions.SSLError as e:
        print("SSL error fetching page {}: {}".format(page, e))
        return None
    except requests.exceptions.ConnectionError as e:
        print("Connection error fetching page {}: {}".format(page, e))
        return None
    except requests.RequestException as e:
        print("Error fetching page {}: {}".format(page, e))
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
        max_pages = pagination_config.get('max_pages', 50)
        
        for page in range(1, max_pages + 1):
            print("Fetching page {}...".format(page))
            
            response_data = fetch_datatables_page(url, pagination_config, page)
            if not response_data:
                break
            
            # Check if we have data
            if not response_data.get('data') or len(response_data['data']) == 0:
                print("No more data found, stopping pagination.")
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
            
            # Check if this is the last page
            if len(response_data['data']) < pagination_config['page_size']:
                print("Reached last page.")
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

    playwright, browser, context = setup_browser_context()
    
    try:
        page = navigate_to_main_page(context, url)
        current_page = 1
        max_pages = pagination.get("max_pages", 10)  # Get max_pages from config
        
        # Extract pagination links and target
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        _, pagination_target = extract_pagination_links(soup, selectors, return_target=True)
        
        # Use fallback target if none found
        if not pagination_target:
            pagination_target = pagination.get("target", "ctl00$CPH1$GridListaPliegos")
            print(f"Using fallback pagination target: {pagination_target}")
        else:
            print(f"Extracted pagination target: {pagination_target}")

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

            # Handle pagination based on portal config
            if pagination.get("type") == "postback":
                if current_page > max_pages:
                    print(f"Reached maximum pages limit ({max_pages}), stopping crawl")
                    break
                target = pagination_target  # Use extracted target
                argument = f"Page${current_page}"
                simulate_postback(page, target, argument)
            else:
                # For other pagination types, break for now
                print("Pagination handling not implemented for this type")
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
