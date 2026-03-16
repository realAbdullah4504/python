#!/usr/bin/env python3
"""
Main pipeline script to run the complete tender analysis workflow.
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawlers.crawl_listings import crawl_all_tenders
from crawlers.crawl_details import (
    load_tenders_from_ndjson,
    process_tenders,
    load_processed_tenders_from_ndjson,
)
from analysis.analyze_pci import main as analyze_main


def load_config():
    with open("config/portals.json") as f:
        return json.load(f)


def main():
    """Run the complete pipeline"""
    print("Starting tender analysis pipeline...")

    config = load_config()

    # STEP 1: Crawl Listings
    print("\n=== Step 1: Crawling tender listings ===")

    
    for portal in config["portals"]:
        if not portal.get("active", False):
            continue

        portal_name = portal["name"]
        urls = portal.get("listing_urls", [])

        print(f"\nPortal: {portal_name}")

        for url in urls:
            print(f"Crawling listing: {url}")
            tenders = crawl_all_tenders(url)
            total_crawled += len(tenders)

    print(f"\nTotal tenders crawled: {total_crawled}")

    # STEP 2: Crawl Details
    print("\n=== Step 2: Crawling tender details ===")

    loaded_tenders = load_tenders_from_ndjson()

    if not loaded_tenders:
        print("No tenders found to process details")
        return

    processed_tenders_numbers = load_processed_tenders_from_ndjson()

    max_tenders = len(loaded_tenders)

    process_tenders(
        loaded_tenders,
        max_tenders=max_tenders,
        processed_tenders=list(processed_tenders_numbers),
    )

    print(f"Processed details for {max_tenders} tenders")

    # STEP 3: PCI Analysis
    print("\n=== Step 3: Analyzing PCI compliance ===")

    analyze_main()

    print("PCI analysis completed")

    print("\n=== Pipeline completed successfully ===")
    print("Files generated:")
    print("- outputs/tenders.ndjson")
    print("- outputs/enriched_tenders.ndjson")
    print("- outputs/scored_tenders.ndjson")


if __name__ == "__main__":
    main()