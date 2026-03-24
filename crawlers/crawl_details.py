#!/usr/bin/env python3
"""
Postback Details Crawler
Extracts details from web pages using postback navigation for tenders that have web-based detail pages
"""

import json
from typing import List, Dict, Optional

from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.bs4_utils import extract_full_text_from_page, extract_pagination_links
from utils.playwright_utils import setup_browser_context, simulate_postback_with_retry, cleanup_browser_resources
from utils.config_resolver import load_config_with_refs
from bs4 import BeautifulSoup

class PostbackDetailsCrawler:
    """Handles postback-based tender detail extraction"""
    
    def __init__(self):
        self.config = load_config_with_refs("config/portals.json")
        self.postback_portals = self._get_postback_portals()
        self.pagination_target = None
    
    def _get_postback_portals(self) -> List[Dict]:
        """Get active portals that use postback detail processing"""
        postback_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                continue
                
            portal_config = portal.get("config", {})
            details_config = portal_config.get("details", {})
            
            if details_config.get("type") == "postback":
                postback_portals.append(portal)
                print(f"Portal '{portal['name']}' uses postback processing")
        
        return postback_portals
    
    def _filter_postback_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders from portals that use postback processing"""
        postback_tenders = []
        portal_names = {portal.get("name") for portal in self.postback_portals}
        
        for tender in tenders:
            tender_portal = tender.get("portal_name", "Unknown")
            if tender_portal in portal_names:
                print(f"Tender portal: {tender_portal}")
                postback_tenders.append(tender)
        
        return postback_tenders
    
    def _extract_pagination_target(self, context, source_url: str, portal_config: Dict) -> Optional[str]:
        """Extract pagination target from the page content"""
        page = context.new_page()
        try:
            page.goto(source_url)
            page.wait_for_load_state("networkidle")
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            selectors = portal_config.get("config", {}).get("selectors", {})
            if not selectors:
                print("No selectors found in portal config, using fallback")
                return None
            
            _, pagination_target = extract_pagination_links(soup, selectors, return_target=True)
            
            if pagination_target:
                print(f"Extracted pagination target: {pagination_target}")
            else:
                print("Warning: Could not extract pagination target, will use fallback")
            
            return pagination_target
            
        finally:
            page.close()
    
    def _process_single_tender(self, context, source_url: str, tender: Dict) -> Dict:
        """Process a single tender and return the enriched tender data"""
        # Check if tender has required fields
        if not tender.get("pagination_argument"):
            raise KeyError("pagination_argument")
        if not tender.get("pagination_target") and not self.pagination_target:
            raise KeyError("pagination_target")
        
        target = tender["details_url"]
        argument = tender["pagination_argument"]
        pagination_target = tender.get("pagination_target") or self.pagination_target
        
        # Open new page for each detail
        detail_page = context.new_page()
        detail_page.goto(source_url)
        detail_page.wait_for_load_state("networkidle")
        
        # First navigate to the correct page
        simulate_postback_with_retry(detail_page, pagination_target, argument)
        # Then fetch the tender detail
        html, real_url = simulate_postback_with_retry(detail_page, target)
        print(real_url)
        
        # Extract full text and update tender
        full_text = extract_full_text_from_page(html)
        tender["full_text"] = full_text
        tender["details_url"] = real_url
        
        # Close tab to prevent state issues
        detail_page.close()
        
        return tender
    
    def process_tenders_for_url(self, tenders: List[Dict], source_url: str) -> int:
        """Process tenders for a specific listing URL and return count of processed tenders"""
        playwright, browser, context = setup_browser_context()
        processed_count = 0
        
        try:
            # Find the portal config for this source URL
            portal_config = None
            for portal in self.postback_portals:
                if source_url in portal.get("listing_urls", []):
                    portal_config = portal
                    break
            
            if not portal_config:
                print(f"Warning: No portal config found for URL {source_url}")
                return 0
            
            # Extract pagination target for this specific URL
            pagination_target = self._extract_pagination_target(context, source_url, portal_config)
            
            # Filter tenders that match this source URL
            url_tenders = [t for t in tenders if t.get("source_url") == source_url]
            
            if not url_tenders:
                print(f"No tenders found for URL {source_url}")
                return 0
            
            print(f"Processing {len(url_tenders)} tenders for URL {source_url}")
            
            for tender in url_tenders:
                try:
                    # Use extracted pagination target if tender doesn't have one
                    if not tender.get("pagination_target") and pagination_target:
                        tender["pagination_target"] = pagination_target
                    
                    enriched_tender = self._process_single_tender(context, source_url, tender)
                    update_tender_with_details(enriched_tender)
                    print(f"Processed: {enriched_tender['number']}")
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                    continue
        finally:
            cleanup_browser_resources(playwright, browser)
        
        return processed_count
    
    def process_tenders(self, tenders: List[Dict], source_url: str, max_tenders: int = 10) -> None:
        """Process multiple tenders and save enriched data (legacy method for compatibility)"""
        self.process_tenders_for_url(tenders[:max_tenders], source_url)
    
    def run(self) -> None:
        """Main method to orchestrate the postback processing workflow"""
        # Load tenders that need details from NDJSON
        tenders = load_tenders_needing_details()
        
        if not tenders:
            print("No tenders found that need details")
            return
        
        if not self.postback_portals:
            print("No active portals configured for postback processing")
            return
        
        # Filter tenders from portals that use postback processing
        postback_tenders = self._filter_postback_tenders(tenders)
        
        if not postback_tenders:
            print("No tenders found from portals configured for postback processing")
            return
        
        print(f"Found {len(postback_tenders)} tenders from portals using postback processing")
        
        # Process all listing URLs for each portal
        total_processed = 0
        for portal in self.postback_portals:
            portal_name = portal.get("name", "Unknown")
            listing_urls = portal.get("listing_urls", [])
            
            print(f"Processing {len(listing_urls)} listing URLs for portal '{portal_name}'")
            
            for source_url in listing_urls:
                print(f"Processing listing URL: {source_url}")
                
                # Process tenders for this specific listing URL
                processed_count = self.process_tenders_for_url(postback_tenders, source_url)
                total_processed += processed_count
                
                if processed_count > 0:
                    print(f"Processed {processed_count} tenders for {source_url}")
        
        print(f"Completed processing {total_processed} tenders across all listing URLs")

def main() -> None:
    """Main function to orchestrate the postback processing workflow"""
    crawler = PostbackDetailsCrawler()
    crawler.run()

if __name__ == "__main__":
    main()