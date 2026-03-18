from utils.config_resolver import load_config_with_refs, get_portal_config
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, simulate_postback, cleanup_browser_resources
from utils.file_utils import load_existing_tender_numbers, save_tender_to_ndjson
from utils.bs4_utils import extract_listing_rows

def process_page_tenders(tenders: List[Dict], seen_tender_numbers: Set[str]) -> int:
    """Process tenders from a page and return count of new tenders"""
    new_count = 0
    for tender in tenders:
        if tender["number"] not in seen_tender_numbers:
            seen_tender_numbers.add(tender["number"])
            save_tender_to_ndjson(tender)
            new_count += 1
    return new_count


def crawl_all_tenders(url: str, portal_config: Dict) -> List[Dict]:
    selectors = portal_config["selectors"]
    column_mapping = portal_config.get("column_mapping", {})
    pagination = portal_config.get("pagination", {})
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

            current_page += 1

            # Handle pagination based on portal config
            if pagination.get("type") == "postback":
                target = pagination.get("target", "ctl00$CPH1$GridListaPliegos")
                argument = f"Page${current_page}"
                simulate_postback(page, target, argument)
            else:
                # For other pagination types, break for now
                print("Pagination handling not implemented for this type")
                break

    finally:
        cleanup_browser_resources(playwright, browser)

    return all_tenders
    
def main() -> None:
    """Main function to orchestrate the tender crawling workflow"""
    config = load_config_with_refs("config/portals.json")
    
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
            
            portal_config = get_portal_config(portal)
            tenders = crawl_all_tenders(url, portal_config)
            all_tenders.extend(tenders)
            print(f"Found {len(tenders)} tenders from {url}")
    
    print(f"Total tenders found across all portals: {len(all_tenders)}")
    
    # Display first 5 tenders
    for t in all_tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()