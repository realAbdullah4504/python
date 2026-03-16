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
from crawlers.crawl_details import load_tenders_from_ndjson, process_tenders, load_processed_tenders_from_ndjson
from analysis.analyze_pci import main as analyze_main

# Load configuration
with open("config/portals.json") as f:
    config = json.load(f)

url = config["portals"][0]["listing_urls"][0]


def main():
    """Run the complete pipeline"""
    print("Starting tender analysis pipeline...")
    
    # Step 1: Crawl listings
    print("\n=== Step 1: Crawling tender listings ===")
    tenders = crawl_all_tenders(url)
    print(f"Crawled {len(tenders)} tenders from listings")
    
    # Step 2: Crawl details
    print("\n=== Step 2: Crawling tender details ===")
    loaded_tenders = load_tenders_from_ndjson()
    if loaded_tenders:
        # Load already processed tenders to avoid reprocessing
        processed_tenders_numbers = load_processed_tenders_from_ndjson()
        
        # Process all tenders (or limit to specific number if needed)
        max_tenders = len(loaded_tenders)
        process_tenders(loaded_tenders, url, max_tenders, list(processed_tenders_numbers))
        print(f"Processed details for {len(loaded_tenders)} tenders")
    else:
        print("No tenders found to process details")
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