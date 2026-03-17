from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, simulate_postback, cleanup_browser_resources
from utils.file_utils import load_existing_tender_numbers, save_tender_to_ndjson
from utils.bs4_utils import extract_pagination_links, extract_listing_rows, find_next_pagination_link, extract_postback_target

def process_page_tenders(tenders: List[Dict], seen_tender_numbers: Set[str]) -> int:
    """Process tenders from a page and return count of new tenders"""
    new_count = 0
    for tender in tenders:
        if tender["number"] not in seen_tender_numbers:
            seen_tender_numbers.add(tender["number"])
            save_tender_to_ndjson(tender)
            new_count += 1
    return new_count


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