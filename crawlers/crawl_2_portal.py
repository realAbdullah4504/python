from typing import Tuple, List, Dict, Optional
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
import os
import requests
from utils.playwright_utils import setup_browser_context, open_page
from utils.file_utils import load_portal_config, save_tenders_to_json, ensure_output_directory
from utils.bs4_utils import extract_tender_blocks, parse_tender_block, format_tender_item


def get_portal_by_url(portals: List[Dict], url: str) -> Optional[Dict]:
    """Find portal configuration by URL."""
    for portal in portals:
        if url in portal.get('listing_urls', []):
            return portal
    return None


def extract_csrf_token_and_session(base_url: str) -> tuple[str, requests.Session]:
    """
    Extract CSRF token and create session with proper cookies.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        # First, visit the main page to get cookies and CSRF token
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
        
        # Extract CSRF token from the page content
        csrf_token = None
        if response.text:
            # Look for the token in the JavaScript
            import re
            token_match = re.search(r'token\s*=\s*"([^"]+)"', response.text)
            if token_match:
                csrf_token = token_match.group(1)
                print("Extracted CSRF token: {}".format(csrf_token[:20] + "..."))
        
        if not csrf_token:
            print("Warning: Could not extract CSRF token, using fallback")
            csrf_token = "92f60e65-2bac-42a4-bc27-199443bdedba"  # Fallback
        
        return csrf_token, session
        
    except requests.RequestException as e:
        print("Error extracting CSRF token: {}".format(e))
        return "92f60e65-2bac-42a4-bc27-199443bdedba", session


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
        response = session.post(url, json=payload, headers=headers, timeout=30)
        print("Response status: {}".format(response.status_code))
        if response.status_code != 200:
            print("Response content: {}".format(response.text[:500]))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching page {}: {}".format(page, e))
        return None


def crawl_all_pages(base_url: str, portal_config: Dict, patterns: Dict, output_file: str) -> List[Dict]:
    """
    Crawl all pages using DataTables pagination with incremental saving.
    """
    pagination_config = portal_config.get('pagination', {})
    if not pagination_config or pagination_config.get('type') != 'datatables':
        return []
    
    all_tenders = []
    max_pages = pagination_config.get('max_pages', 50)
    
    # Create output directory
    ensure_output_directory(output_file)
    
    for page in range(1, max_pages + 1):
        print("Fetching page {}...".format(page))
        
        response_data = fetch_datatables_page(base_url, pagination_config, page)
        if not response_data:
            break
        
        # Check if we have data
        if not response_data.get('data') or len(response_data['data']) == 0:
            print("No more data found, stopping pagination.")
            break
        
        page_tenders = []
        # Parse each tender from response
        for item in response_data['data']:
            # Convert DataTables item to text format for parsing
            tender_text = format_tender_item(item)
            tender = parse_tender_block(tender_text, patterns)
            
            if tender:
                tender.update({
                    'portal_name': portal_config['name'],
                    'source_url': base_url,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'raw_data': item  # Keep raw data for reference
                })
                page_tenders.append(tender)
                all_tenders.append(tender)
        
        # Save after each page is processed
        print("Saving {} tenders from page {}...".format(len(page_tenders), page))
        save_tenders_to_json(all_tenders, output_file)
        
        print("Total tenders so far: {}".format(len(all_tenders)))
        
        # Check if this is the last page
        if len(response_data['data']) < pagination_config['page_size']:
            print("Reached last page.")
            break
    
    return all_tenders


def crawl_all_tenders(url: str, output_file: str = "tenders_crawled.json") -> List[Dict]:
    """
    Main function to crawl and parse all tenders from portal.
    """
    # Load configuration
    config = load_portal_config()
    portal = get_portal_by_url(config['portals'], url)
    
    if not portal:
        raise ValueError("No configuration found for URL: {}".format(url))
    
    patterns = portal['patterns']
    
    # Check if portal has pagination configuration
    if portal.get('pagination', {}).get('type') == 'datatables':
        print("Using DataTables pagination...")
        parsed_tenders = crawl_all_pages(url, portal, patterns, output_file)
    else:
        print("Using static page parsing...")
        # Fallback to original method
        page = open_page(url)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract all text content
        excluded_tags = portal.get('selectors', {}).get('excluded_tags', ['script', 'style'])
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
                tender['portal_name'] = portal['name']
                tender['source_url'] = url
                tender['created_at'] = datetime.now(timezone.utc).isoformat()
                parsed_tenders.append(tender)
    
    # Save to file
    ensure_output_directory(output_file)
    save_tenders_to_json(parsed_tenders, output_file)
    
    print("Found and parsed {} tenders".format(len(parsed_tenders)))
    return parsed_tenders


if __name__ == "__main__":
    url = "https://www.csjn.gov.ar/transparencia/adquisiciones-y-contrataciones"
    tenders = crawl_all_tenders(url, "outputs/tenders_crawled.json")
    
    print("\nSample tender data:")
    for i, tender in enumerate(tenders[:3]):  # Show first 3 tenders
        print("\nTender {}:".format(i + 1))
        for key, value in tender.items():
            print("  {}: {}".format(key, value))