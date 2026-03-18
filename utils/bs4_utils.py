from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional, Tuple


def extract_postback_target(link) -> Tuple[Optional[str], Optional[str]]:
    """Extract postback target and argument from a link element"""
    href = link.get("href", "")
    match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", href)

    if match:
        return match.group(1), match.group(2)

    return None, None

def extract_pagination_links(soup: BeautifulSoup, selectors: Dict, return_target: bool = False) -> List[Dict] | Tuple[List[Dict], Optional[str]]:
    """Extract pagination links from the page"""
    table = soup.find(selectors["main_table"])
    if not table:
        return [] if not return_target else ([], None)

    pagination_links = []

    for row in table.find_all(selectors["table_row"], class_=selectors["pagination_row_class"]):
        for link in row.find_all(selectors["link"]):

            target, argument = extract_postback_target(link)

            if target:
                pagination_links.append({
                    "page_no": link.get_text(strip=True),
                    "target": target,
                    "argument": argument
                })

    if return_target:
        pagination_target = None
        if pagination_links:
            pagination_target = pagination_links[0].get("target")
        return pagination_links, pagination_target
    
    return pagination_links

def extract_listing_rows(soup: BeautifulSoup, url: str, selectors: Dict, column_mapping: Dict, page_no: int = 1) -> List[Dict]:
    """Extract tender listing rows from the page"""
    tenders = []

    table = soup.find(selectors["main_table"])
    if not table:
        return tenders

    tbody = soup.find(selectors["table_body"])
    if not tbody:
        return tenders

    rows = tbody.find_all(selectors["table_row"], recursive=False)

    for row in rows:

        if selectors["header_row_class"] in (row.get("class") or []):
            continue

        if selectors["pagination_row_class"] in (row.get("class") or []):
            continue

        cells = row.find_all(selectors["table_cell"])

        if len(cells) < 5:
            continue

        link = cells[column_mapping["number"]].find(selectors["link"])
        target, _ = extract_postback_target(link) if link else (None, None)
        
        tender = {
            "number": cells[column_mapping["number"]].get_text(strip=True),
            "description": cells[column_mapping["description"]].get_text(strip=True),
            "type": cells[column_mapping["type"]].get_text(strip=True),
            "date": cells[column_mapping["date"]].get_text(strip=True),
            "status": cells[column_mapping["status"]].get_text(strip=True),
            "url": url,
            "details_url": target,
            "page_no": page_no
        }
        tenders.append(tender)

    return tenders


def extract_full_text_from_page(html: str) -> str:
    """Extract and clean full text from a page"""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


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


def find_next_pagination_link(pagination_links: List[Dict], current_page: int) -> Optional[Dict]:
    """Find the next pagination link to navigate to"""
    next_page_str = str(current_page + 1)
    
    # First try to find exact next page
    for link in pagination_links:
        if link["page_no"] == next_page_str:
            return link
    
    # Then try to find ellipsis with higher page number
    for link in pagination_links:
        if link["page_no"] == "...":
            match = re.search(r'Page\$(\d+)', link["argument"], re.IGNORECASE)
            if match:
                arg_page = int(match.group(1))
                if arg_page > current_page:
                    return link
    
    return None
