#!/usr/bin/env python3
"""
Backward-compatible wrapper for postback details extraction using the new modular system.
Preserves the original interface while using the new modular architecture.
"""

import sys
from crawlers.core.details_engine import DetailsEngine


class PostbackDetailsCrawler:
    """Backward-compatible wrapper for postback details extraction."""
    
    def __init__(self):
        """Initialize postback details crawler with modular backend."""
        self.engine = DetailsEngine()
        self.postback_strategy = self.engine.strategies.get("postback")
        if not self.postback_strategy:
            print("Error: Postback strategy not available")
            sys.exit(1)
        
        # Map original attributes for compatibility
        self.config = self.postback_strategy.config
        self.postback_portals = self.postback_strategy.postback_portals
        self.pagination_target = None
        self.argument = None
        
        print(f"Initialized PostbackDetailsCrawler with {len(self.postback_portals)} postback portals")
    
    def _filter_postback_tenders(self, tenders):
        """Filter tenders for postback processing (backward compatibility)."""
        return self.postback_strategy.filter_tenders(tenders)
    
    def process_tenders_for_url(self, tenders, source_url):
        """Process tenders for a specific URL (backward compatibility)."""
        return self.postback_strategy.process_tenders_for_url(tenders, source_url)
    
    def run(self):
        """Run postback details extraction (backward compatibility)."""
        print("Starting postback details crawler workflow")
        
        # Load tenders needing details
        from utils.file_utils import load_tenders_needing_details
        tenders = load_tenders_needing_details()
        if not tenders:
            print("No tenders found needing details")
            return
        
        print(f"Found {len(tenders)} tenders needing details")
        
        if not self.postback_portals:
            print("No active portals configured for postback processing")
            return
        
        postback_tenders = self._filter_postback_tenders(tenders)
        if not postback_tenders:
            print("No tenders found from portals configured for postback processing")
            return
        
        total_processed = 0
        for portal in self.postback_portals:
            portal_name = portal.get("name", "unknown")
            print(f"Processing portal: {portal_name}")
            for source_url in portal.get("listing_urls", []):
                processed_count = self.process_tenders_for_url(postback_tenders, source_url)
                
                # Process individual tenders for this URL
                url_tenders = [t for t in postback_tenders if t.get("url") == source_url]
                for tender in url_tenders:
                    try:
                        enriched_tender = self.postback_strategy.process_tender(tender)
                        from utils.file_utils import update_tender_with_details
                        update_tender_with_details(enriched_tender)
                        total_processed += 1
                    except Exception as e:
                        print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                        continue
                
                print(f"Portal {portal_name} - URL {source_url}: {processed_count} tenders processed")
        
        print(f"Postback processing workflow completed: {total_processed} tenders processed")
        print(f"Completed processing {total_processed} tenders")


def main():
    """Main function maintaining backward compatibility."""
    crawler = PostbackDetailsCrawler()
    crawler.run()


if __name__ == "__main__":
    main()
