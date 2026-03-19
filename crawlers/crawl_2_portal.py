from typing import Tuple, List, Dict, Optional
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
import os
import requests
from utils.playwright_utils import setup_browser_context, open_page
from utils.config_resolver import load_config_with_refs, get_portal_config
from utils.web_utils import save_tender_to_ndjson, ensure_output_directory, extract_csrf_token_and_session
from utils.file_utils import load_seen_tender_numbers
from utils.bs4_utils import extract_tender_blocks, parse_tender_block, format_tender_item
from models.tender import TenderModel

def map_pattern_to_generic_tender(pattern_tender: Dict, portal_name: str, source_url: str) -> TenderModel:
    """Map pattern-based tender structure to generic tender structure"""
    return TenderModel.from_pattern_tender(pattern_tender, portal_name, source_url)


def process_page_tenders(tenders: List[Dict], seen_tender_numbers: set, portal_name: str, source_url: str) -> Tuple[int, List[TenderModel]]:
    """Process tenders from a page and return count of new tenders and new tenders list"""
    new_count = 0
    new_tenders = []
    for tender in tenders:
        # Map to generic structure
        generic_tender = map_pattern_to_generic_tender(tender, portal_name, source_url)
        
        # Use docId for deduplication, fallback to number for backward compatibility
        tender_id = generic_tender.docId if generic_tender.docId else generic_tender.number
        
        if tender_id not in seen_tender_numbers:
            seen_tender_numbers.add(tender_id)
            save_tender_to_ndjson(generic_tender.to_dict())
            new_count += 1
            new_tenders.append(generic_tender)
    return new_count, new_tenders


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


def crawl_all_tenders(url: str, portal_config: Dict, seen_tender_numbers: set) -> List[TenderModel]:
    """
    Main function to crawl and parse all tenders from portal.
    """
    patterns = portal_config.get('patterns', {})
    
    if not patterns:
        raise ValueError("No patterns found in configuration for URL: {}".format(url))
    
    all_tenders = []
    
    # Check if portal has pagination configuration
    if portal_config.get('pagination', {}).get('type') == 'datatables':
        print("Using DataTables pagination...")
        # For DataTables, we need to process differently
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
            new_count, new_generic_tenders = process_page_tenders(page_tenders, seen_tender_numbers, portal_config.get('name', 'Unknown'), url)
            all_tenders.extend(new_generic_tenders)
            
            print("Added {} new tenders from page {}".format(new_count, page))
            
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
        new_count, new_generic_tenders = process_page_tenders(parsed_tenders, seen_tender_numbers, portal_config.get('name', 'Unknown'), url)
        all_tenders.extend(new_generic_tenders)
        
        print("Added {} new tenders from static page".format(new_count))
    
    return all_tenders


def main() -> None:
    """Main function to orchestrate the pattern-based tender crawling workflow"""
    config = load_config_with_refs("config/portals.json")
    
    all_tenders = []
    seen_tender_numbers = load_seen_tender_numbers()
    
    # Loop over all portals
    for portal in config["portals"]:
        if not portal.get("active", True):
            print(f"Skipping inactive portal: {portal['name']}")
            continue
            
        # Only process pattern-based portals (those with schema "pattern_based" or no schema but with patterns)
        portal_config = get_portal_config(portal)
        if not portal_config.get("patterns"):
            print(f"Skipping non-pattern-based portal: {portal['name']}")
            continue
            
        print(f"Processing portal: {portal['name']} ({portal['country']})")
        
        # Loop over all listing URLs for this portal
        for url in portal["listing_urls"]:
            print(f"Crawling URL: {url}")
            
            tenders = crawl_all_tenders(url, portal_config, seen_tender_numbers)
            all_tenders.extend(tenders)
            print(f"Found {len(tenders)} tenders from {url}")
    
    print(f"Total tenders found across all pattern-based portals: {len(all_tenders)}")
    
    # Display first 5 tenders in generic format
    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()