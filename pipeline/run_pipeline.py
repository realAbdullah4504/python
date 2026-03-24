#!/usr/bin/env python3
"""
Main pipeline script to run the complete tender analysis workflow.
"""

import sys
import os
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawlers.crawl_listings import crawl_all_tenders
from crawlers.crawl_details import load_tenders_needing_details, process_tenders
from analysis.analyze_pci import main as analyze_main

# Load configuration
with open("config/portals.json") as f:
    config = json.load(f)


def crawl_all_portals():
    """Crawl tenders from all active portals and their listing URLs"""
    all_tenders = []
    
    for portal in config["portals"]:
        if not portal.get("active", True):
            print(f"Skipping inactive portal: {portal['name']}")
            continue
            
        print(f"\n--- Processing portal: {portal['name']} ({portal['country']}) ---")
        
        for url in portal["listing_urls"]:
            print(f"Crawling URL: {url}")
            try:
                tenders = crawl_all_tenders(url,portal["selectors"], portal["column_mapping"])
                print(f"Crawled {len(tenders)} tenders from {url}")
                all_tenders.extend(tenders)
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                continue
    
    return all_tenders


def get_first_active_portal_url():
    """Get the first listing URL from active portals"""
    for portal in config["portals"]:
        if portal.get("active", True) and portal.get("listing_urls"):
            return portal["listing_urls"][0]
    return None


def main():
    """Run the complete pipeline"""
    print("Starting tender analysis pipeline...")
    
    # Step 1: Crawl listings from all portals
    print("\n=== Step 1: Crawling tender listings ===")
    tenders = crawl_all_portals()
    print(f"Total crawled {len(tenders)} tenders from all portals")
    
    # Step 2: Crawl details
    print("\n=== Step 2: Crawling tender details ===")
    tenders_needing_details = load_tenders_needing_details()
    if tenders_needing_details:
        # Process all tenders (or limit to specific number if needed)
        # max_tenders = len(tenders_needing_details)
        max_tenders = 10
        
        # Use the first active portal URL for processing details
        process_url = get_first_active_portal_url()
        if not process_url:
            print("No active portal URLs found for processing details")
            return
            
        process_tenders(tenders_needing_details, process_url, max_tenders)
        print(f"Processed details for {len(tenders_needing_details)} tenders")
    else:
        print("No tenders found that need details")
        return
    
    # Step 3: Analyze PCI compliance
    print("\n=== Step 3: Analyzing PCI compliance ===")
    analyze_main()
    print("PCI analysis completed")
    
    print("\n=== Pipeline completed successfully ===")
    print("Files generated:")
    print("- outputs/tenders.ndjson (raw tender listings)")
    print("- outputs/enriched_tenders.ndjson (tenders with full text details)") 
    print("- outputs/scored_tenders.ndjson (tenders with PCI compliance scores)")


if __name__ == "__main__":
    main()