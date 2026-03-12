#!/usr/bin/env python3
"""
Main pipeline script to run the complete tender analysis workflow.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawlers.crawl_listings import crawl_all_tenders
from crawlers.crawl_details import process_tenders, load_tenders_from_ndjson
from analysis.analyze_pci import main as analyze_main


def main():
    """Run the complete pipeline"""
    print("Starting tender analysis pipeline...")
    
    # Step 1: Crawl listings
    print("\n=== Step 1: Crawling tender listings ===")
    tenders = crawl_all_tenders(url)
    print(f"Crawled {len(tenders)} tenders")
    
    # Step 2: Crawl details
    print("\n=== Step 2: Crawling tender details ===")
    loaded_tenders = load_tenders_from_ndjson()
    if loaded_tenders:
        process_tenders(loaded_tenders, url, len(loaded_tenders))
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
    print("- outputs/tenders.ndjson")
    print("- outputs/enriched_tenders.ndjson") 
    print("- outputs/scored_tenders.ndjson")


if __name__ == "__main__":
    main()