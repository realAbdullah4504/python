from typing import List, Dict, Set
from crawlers.core import CrawlerEngine
from crawlers.core.details_engine import DetailsEngine
from crawlers.core.pci_analysis_engine import PCIAnalysisEngine

def main() -> None:
    """Main entry point (delegates orchestration to CrawlerEngine, DetailsEngine, and PCIAnalysisEngine)."""
    # Step 1: Run the crawler to collect tender data
    print("Starting crawling phase...")
    crawler_engine = CrawlerEngine()
    crawler_summary = crawler_engine.run()
    print(f"Crawling completed. Summary: {crawler_summary}")
    
    # Step 2: Run the details engine to enrich tender data
    print("\nStarting details extraction phase...")
    details_engine = DetailsEngine()
    details_summary = details_engine.run()
    print(f"Details extraction completed. Summary: {details_summary}")
    
    # Step 3: Run the PCI analysis engine to score tenders
    print("\nStarting PCI analysis phase...")
    pci_engine = PCIAnalysisEngine()
    pci_summary = pci_engine.run()
    print(f"PCI analysis completed. Summary: {pci_summary}")
    
    # Overall summary
    print("\nPipeline completed successfully!")
    # print("Crawler: {}".format(crawler_summary))
    print("Details: {}".format(details_summary))
    print("PCI Analysis: {}".format(pci_summary))


if __name__ == "__main__":
    main()
