import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from typing import Tuple, List, Dict, Optional
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timezone
import os
import requests
from utils.playwright_utils import setup_browser_context, open_page
from utils.file_utils import load_portal_config, save_tenders_to_json, ensure_output_directory


def get_portal_by_url(portals: List[Dict], url: str) -> Optional[Dict]:
    """Find portal configuration by URL."""
    for portal in portals:
        if url in portal.get('listing_urls', []):
            return portal
    return None


def extract_tender_blocks(text: str, patterns: Dict) -> List[str]:
    """
    Split text into individual tender blocks based on date patterns.
    Each tender block starts with a date.
    """
    date_pattern = patterns['date']
    blocks = []
    
    # Find all date positions
    dates = list(re.finditer(date_pattern, text, re.IGNORECASE | re.MULTILINE))
    
    if not dates:
        return [text]  # Return whole text if no dates found
    
    for i in range(len(dates)):
        start_pos = dates[i].start()
        end_pos = dates[i + 1].start() if i + 1 < len(dates) else len(text)
        block = text[start_pos:end_pos].strip()
        if block:
            blocks.append(block)
    
    return blocks


def _extract_expediente(lines: List[str], patterns: Dict) -> tuple[Optional[str], Optional[int]]:
    """Extract expediente from lines."""
    for i, line in enumerate(lines):
        match = re.search(patterns['expediente'], line, re.IGNORECASE)
        if match:
            return match.group(1), i
    return None, None


def _extract_document_info(lines: List[str], patterns: Dict) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Extract document type and number from lines."""
    for i, line in enumerate(lines):
        match = re.search(patterns['document_type_number'], line, re.IGNORECASE)
        if match:
            doc_type = line.split()[0]  # First word is document type
            doc_number = match.group(1)
            return doc_type, doc_number, i
    return None, None, None


def _extract_category_and_description(lines: List[str], start_idx: int) -> tuple[Optional[str], Optional[str]]:
    """Extract category and description from lines."""
    if len(lines) <= 1:
        return None, None
    
    last_line = lines[-1]
    if '-' in last_line and len(last_line.split('-')) >= 3:
        category = last_line
        description_lines = lines[start_idx:-1]
    else:
        description_lines = lines[start_idx:]
        category = None
    
    description = ' '.join(description_lines).strip() if description_lines else None
    return category, description


def parse_tender_block(block: str, patterns: Dict) -> Optional[Dict[str, str]]:
    """
    Parse a single tender block and extract structured information.
    """
    lines = [line.strip() for line in block.split('\n') if line.strip()]
    if not lines:
        return None
    
    tender_data = {}
    
    # Extract date (first line should be date)
    date_match = re.match(patterns['date'], lines[0], re.IGNORECASE)
    if date_match:
        tender_data['date'] = date_match.group(1)
        remaining_lines = lines[1:]
    else:
        remaining_lines = lines
    
    # Extract expediente
    expediente, expediente_idx = _extract_expediente(remaining_lines, patterns)
    if expediente:
        tender_data['expediente'] = expediente
    
    # Extract document type and number
    doc_type, doc_number, doc_idx = _extract_document_info(remaining_lines, patterns)
    if doc_type:
        tender_data['document_type'] = doc_type
    if doc_number:
        tender_data['document_number'] = doc_number
    
    # Extract description and category
    description_start = max(
        expediente_idx if expediente_idx is not None else -1,
        doc_idx if doc_idx is not None else -1
    ) + 1
    
    category, description = _extract_category_and_description(remaining_lines, description_start)
    if category:
        tender_data['category'] = category
    if description:
        tender_data['description'] = description
    
    return tender_data if tender_data else None


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


def format_tender_item(item: Dict) -> str:
    """
    Format DataTables item into text that matches our parsing patterns.
    """
    lines = []
    
    if item.get('fechaCompleta'):
        lines.append(item['fechaCompleta'])
    
    if item.get('nroExpe'):
        lines.append("Expediente: {}".format(item['nroExpe']))
    
    if item.get('descripcionTipo') and item.get('nroDoc'):
        lines.append("{} {}".format(item['descripcionTipo'], item['nroDoc']))
    elif item.get('descripcionTipo'):
        lines.append(item['descripcionTipo'])
    
    if item.get('detalle'):
        lines.append(item['detalle'])
    
    if item.get('pathTemas'):
        lines.append(item['pathTemas'])
    
    return '\n'.join(lines)


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