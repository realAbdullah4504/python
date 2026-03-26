#!/usr/bin/env python3
"""
Backward-compatible wrapper for PDF details extraction using the new modular system.
Preserves the original interface while using the new modular architecture.
"""

import sys
from crawlers.core.details_engine import DetailsEngine


class PdfDetailsCrawler:
    """Backward-compatible wrapper for PDF details extraction."""
    
    def __init__(self):
        """Initialize PDF details crawler with modular backend."""
        self.engine = DetailsEngine()
        self.pdf_strategy = self.engine.strategies.get("pdf")
        if not self.pdf_strategy:
            print("Error: PDF strategy not available")
            sys.exit(1)
        
        # Map original attributes for compatibility
        self.config = self.pdf_strategy.config
        self.pdf_portals = self.pdf_strategy.pdf_portals
        self.pdf_timeout = self.pdf_strategy.pdf_timeout
        
        print(f"Initialized PdfDetailsCrawler with {len(self.pdf_portals)} PDF portals, timeout: {self.pdf_timeout}s")
    
    def _filter_pdf_tenders(self, tenders):
        """Filter tenders for PDF processing (backward compatibility)."""
        return self.pdf_strategy.filter_tenders(tenders)
    
    def process_tenders(self, tenders, max_tenders=10):
        """Process tenders using PDF strategy (backward compatibility)."""
        filtered_tenders = self._filter_pdf_tenders(tenders)
        if max_tenders:
            filtered_tenders = filtered_tenders[:max_tenders]
        
        processed_count = 0
        for tender in filtered_tenders:
            try:
                enriched_tender = self.pdf_strategy.process_tender(tender)
                from utils.file_utils import update_tender_with_details
                update_tender_with_details(enriched_tender)
                processed_count += 1
            except Exception as e:
                print(f"Error processing tender: {e}")
                continue
        
        return processed_count
    
    def run(self):
        """Run PDF details extraction (backward compatibility)."""
        print("Starting PDF details crawler workflow")
        
        # Load tenders needing details
        from utils.file_utils import load_tenders_needing_details
        tenders = load_tenders_needing_details()
        if not tenders:
            print("No tenders found needing details")
            return
        
        print(f"Found {len(tenders)} tenders needing details")
        
        if not self.pdf_portals:
            print("No active portals configured for PDF processing")
            return
        
        pdf_tenders = self._filter_pdf_tenders(tenders)
        if not pdf_tenders:
            print("No tenders found from portals configured for PDF processing")
            return
        
        processed_count = self.process_tenders(pdf_tenders, len(pdf_tenders))
        print(f"PDF processing workflow completed: {processed_count} tenders processed")
        print(f"Completed processing {processed_count} tenders with PDFs")


def main():
    """Main function maintaining backward compatibility."""
    crawler = PdfDetailsCrawler()
    crawler.run()


if __name__ == "__main__":
    main()
