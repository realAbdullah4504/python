import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, simulate_postback, cleanup_browser_resources
from utils.file_utils import load_existing_tender_numbers, save_tender_to_ndjson

def extract_postback_target(link) -> Tuple[Optional[str], Optional[str]]:
    """Extract postback target and argument from a link element"""
    href = link.get("href", "")
    match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", href)

    if match:
        return match.group(1), match.group(2)

    return None, None


def extract_pagination_links(soup: BeautifulSoup, selectors: Dict) -> List[Dict]:
    """Extract pagination links from the page"""
    table = soup.find(selectors["main_table"])
    if not table:
        return []

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

    return pagination_links


def extract_listing_rows(soup: BeautifulSoup, url: str, selectors: Dict, column_mapping: Dict, page_no: int = 1, pagination_target: str = "", pagination_argument: str = "") -> List[Dict]:
    """Extract tender listing rows from the page"""
    tenders = []

    table = soup.find(selectors["main_table"])
    if not table:
        return tenders

    tbody = table.find(selectors["table_body"])
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
        # print(link, target)
        tender = {
            "number": cells[column_mapping["number"]].get_text(strip=True),
            "description": cells[column_mapping["description"]].get_text(strip=True),
            "type": cells[column_mapping["type"]].get_text(strip=True),
            "date": cells[column_mapping["date"]].get_text(strip=True),
            "status": cells[column_mapping["status"]].get_text(strip=True),
            "url":url,
            "details_url": target,
            "page_no": page_no,
            "pagination_target": pagination_target,
            "pagination_argument": pagination_argument
        }
        tenders.append(tender)

    return tenders


def process_page_tenders(tenders: List[Dict], seen_tender_numbers: Set[str]) -> int:
    """Process tenders from a page and return count of new tenders"""
    new_count = 0
    for tender in tenders:
        if tender["number"] not in seen_tender_numbers:
            seen_tender_numbers.add(tender["number"])
            save_tender_to_ndjson(tender)
            new_count += 1
    return new_count


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


def crawl_all_tenders(url: str, selectors: Dict, column_mapping: Dict) -> List[Dict]:
    all_tenders = []
    seen_tender_numbers = load_existing_tender_numbers()

    playwright, browser, context = setup_browser_context()
    
    try:
        page = navigate_to_main_page(context, url)
        current_page = 1

        while True:
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

            new_count = process_page_tenders(tenders, seen_tender_numbers)
            all_tenders.extend([t for t in tenders if t["number"] in seen_tender_numbers])

            print(f"Added {new_count} new tenders from page {current_page}")

            if new_count == 0:
                print("No new tenders found, stopping crawl")
                break

            # 🔹 Pagination logic
            pagination_links = extract_pagination_links(soup, selectors)
            next_link = find_next_pagination_link(pagination_links, current_page)

            if not next_link:
                print(f"No more pages found after page {current_page}")
                break

            # 🔹 Update page number
            if next_link["page_no"] == "...":
                match = re.search(r'Page\$(\d+)', next_link["argument"], re.IGNORECASE)
                if match:
                    current_page = int(match.group(1))
            else:
                current_page += 1

            # 🔹 Navigate to next page
            simulate_postback(page, next_link["target"], next_link["argument"])

    finally:
        cleanup_browser_resources(playwright, browser)

    return all_tenders
    
def main() -> None:
    """Main function to orchestrate the tender crawling workflow"""
    with open("config/portals.json") as f:
        config = json.load(f)
    
    all_tenders = []
    
    # Loop over all portals
    for portal in config["portals"]:
        if not portal.get("active", True):
            print(f"Skipping inactive portal: {portal['name']}")
            continue
            
        print(f"Processing portal: {portal['name']} ({portal['country']})")
        
        # Loop over all listing URLs for this portal
        for url in portal["listing_urls"]:
            print(f"Crawling URL: {url}")
            
            tenders = crawl_all_tenders(url, portal["selectors"], portal["column_mapping"])
            all_tenders.extend(tenders)
            print(f"Found {len(tenders)} tenders from {url}")
    
    print(f"Total tenders found across all portals: {len(all_tenders)}")
    
    # Display first 5 tenders
    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()