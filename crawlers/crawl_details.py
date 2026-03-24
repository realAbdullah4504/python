#!/usr/bin/env python3
"""
Postback Details Crawler
Extracts details from web pages using postback navigation for tenders that have web-based detail pages
"""

import re
import json
from typing import List, Dict, Optional, Tuple
import time
from datetime import datetime

from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.bs4_utils import extract_full_text_from_page
from utils.playwright_utils import setup_browser_context, simulate_postback_with_retry, cleanup_browser_resources
from utils.config_resolver import load_config_with_refs

# Load and resolve configuration
config = load_config_with_refs("config/portals.json")

# Get detail configuration from resolved config
DETAIL_CONFIG = config["templates"]["detail_types"]["postback"]
WAIT_STRATEGY = DETAIL_CONFIG.get("wait_strategy", "networkidle")

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


def process_tenders(tenders: List[Dict], source_url: str, max_tenders: int = 10) -> None:
    """Process multiple tenders and save enriched data"""
    playwright, browser, context = setup_browser_context()
    
    try:
        for tender in tenders[:max_tenders]:
            try:
                enriched_tender = process_single_tender(context, source_url, tender)
                update_tender_with_details(enriched_tender)
                print(f"Processed: {enriched_tender['number']}")
            except Exception as e:
                print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                continue
    finally:
        cleanup_browser_resources(playwright, browser)


def get_postback_portals() -> List[Dict]:
    """Get active portals that use postback detail processing"""
    postback_portals = []
    for portal in config["portals"]:
        if not portal.get("active", True):
            continue
            
        portal_config = portal.get("config", {})
        details_config = portal_config.get("details", {})
        
        # Check if this portal uses postback processing
        if details_config.get("type") == "postback":
            postback_portals.append(portal)
            print(f"Portal '{portal['name']}' uses postback processing")
    
    return postback_portals

def filter_postback_tenders(tenders: List[Dict], postback_portals: List[Dict]) -> List[Dict]:
    """Filter tenders from portals that use postback processing"""
    postback_tenders = []
    for tender in tenders:
        tender_portal = tender.get("portal_name", "Unknown")
        
        # Check if this tender's portal uses postback processing
        for portal in postback_portals:
            if tender_portal == portal.get("name"):
                # Check if tender has postback fields
                if tender.get("pagination_argument") and tender.get("pagination_target"):
                    postback_tenders.append(tender)
                    break
    
    return postback_tenders

def main() -> None:
    """Main function to orchestrate the postback processing workflow"""
    # Load tenders that need details from NDJSON
    tenders = load_tenders_needing_details()
    
    if not tenders:
        print("No tenders found that need details")
        return
    
    # Get portals that use postback detail processing
    postback_portals = get_postback_portals()
    
    if not postback_portals:
        print("No active portals configured for postback processing")
        return
    
    # Filter tenders from portals that use postback processing
    postback_tenders = filter_postback_tenders(tenders, postback_portals)
    
    if not postback_tenders:
        print("No tenders found from portals configured for postback processing")
        return
    
    print(f"Found {len(postback_tenders)} tenders from portals using postback processing")
    
    # Get the first active portal URL for processing
    source_url = postback_portals[0]["listing_urls"][0]
    
    # Process all tenders with postback, but limit to the number of tenders
    max_tenders = len(postback_tenders)
    process_tenders(postback_tenders, source_url, max_tenders)
    print(f"Completed processing {min(len(postback_tenders), max_tenders)} tenders")


if __name__ == "__main__":
    main()