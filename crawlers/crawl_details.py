import re
import json
from typing import List, Dict, Optional, Tuple
import time
from datetime import datetime
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, simulate_postback_with_retry, cleanup_browser_resources
from utils.file_utils import load_tenders_from_ndjson, load_processed_tenders_from_ndjson, save_enriched_tender
from utils.bs4_utils import extract_full_text_from_page

with open("config/portals.json") as f:
    config = json.load(f)

URL = config["portals"][0]["listing_urls"][0]


def process_single_tender(context, source_url: str, tender: Dict) -> Dict:
    """Process a single tender and return the enriched tender data"""
    target = tender["details_url"]
    argument = tender["pagination_argument"]
    
    # Open new page for each detail
    detail_page = context.new_page()
    detail_page.goto(source_url)
    detail_page.wait_for_load_state("networkidle")
    
    # First navigate to the correct page
    simulate_postback_with_retry(detail_page, tender["pagination_target"], argument)
    # Then fetch the tender detail
    html, real_url = simulate_postback_with_retry(detail_page, target)
    print(real_url)
    
    # Extract full text and update tender
    full_text = extract_full_text_from_page(html)
    tender["full_text"] = full_text
    tender["details_url"] = real_url  # Get real URL instead of postback function string
    
    # Close tab to prevent state issues
    detail_page.close()
    
    return tender


def process_tenders(tenders: List[Dict], source_url: str, max_tenders: int = 10, processed_tenders_numbers: List[str] = []) -> None:
    """Process multiple tenders and save enriched data"""
    playwright, browser, context = setup_browser_context()
    
    try:
        for tender in tenders[:max_tenders]:
            try:
                if tender["number"] in processed_tenders_numbers:
                    print(f"Skipping already processed tender: {tender['number']}")
                    continue
                enriched_tender = process_single_tender(context, source_url, tender)
                save_enriched_tender(enriched_tender)
                print(f"Processed: {enriched_tender['number']}")
            except Exception as e:
                print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                continue
    finally:
        cleanup_browser_resources(playwright, browser)


def main() -> None:
    """Main function to orchestrate the tender processing workflow"""
    # Load tenders and URL from NDJSON
    tenders = load_tenders_from_ndjson()
    processed_tenders_numbers=load_processed_tenders_from_ndjson()
    
    if not tenders:
        print("No tenders found in NDJSON file")
        return
    
    # Process all tenders, but limit to the number of tenders
    max_tenders = len(tenders)
    process_tenders(tenders, URL, max_tenders,processed_tenders_numbers)
    print(f"Completed processing {min(len(tenders), max_tenders)} tenders")


if __name__ == "__main__":
    main()