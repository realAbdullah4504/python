#!/usr/bin/env python3
"""
Postback Details Crawler
Extracts details from web pages using postback navigation for tenders that have web-based detail pages
"""

import json
from typing import List, Dict, Optional
import logging

from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.bs4_utils import extract_full_text_from_page, extract_pagination_links
from utils.playwright_utils import setup_browser_context, simulate_postback_with_retry, cleanup_browser_resources
from utils.config_resolver import load_config_with_refs
from bs4 import BeautifulSoup
from models.tender import TenderModel

class PostbackDetailsCrawler:
    """Handles postback-based tender detail extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = load_config_with_refs("config/portals.json")
        self.postback_portals = self._get_postback_portals()
        self.pagination_target = None
        self.logger.info(f"Initialized PostbackDetailsCrawler with {len(self.postback_portals)} postback portals")
    
    def _get_postback_portals(self) -> List[Dict]:
        """Get active portals that use postback detail processing"""
        postback_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                self.logger.debug(f"Skipping inactive portal: {portal.get('name', 'unknown')}")
                continue
                
            portal_config = portal.get("config", {})
            details_config = portal_config.get("details", {})
            
            if details_config.get("type") == "postback":
                postback_portals.append(portal)
                self.logger.debug(f"Added postback portal: {portal.get('name', 'unknown')}")
        
        self.logger.info(f"Found {len(postback_portals)} active postback portals")
        return postback_portals
    
    def _filter_postback_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders from portals that use postback processing"""
        postback_tenders = []
        portal_names = {portal.get("name") for portal in self.postback_portals}
        self.logger.debug(f"Filtering tenders for postback portals: {portal_names}")
        
        for tender in tenders:
            if tender.get("portal_name") in portal_names:
                postback_tenders.append(tender)
                self.logger.debug(f"Added postback tender: {tender.get('number', 'unknown')} from {tender.get('portal_name', 'unknown')}")
        
        self.logger.info(f"Filtered {len(postback_tenders)} tenders from {len(tenders)} total for postback processing")
        return postback_tenders
    
    def _extract_pagination_target(self, context, source_url: str, portal_config: Dict) -> Optional[str]:
        """Extract pagination target from the page content"""
        self.logger.info(f"Extracting pagination target from: {source_url}")
        page = context.new_page()
        try:
            page.goto(source_url)
            page.wait_for_load_state("networkidle")
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            selectors = portal_config.get("config", {}).get("selectors", {})
            if not selectors:
                self.logger.warning("No selectors found in portal config")
                return None
            
            _, pagination_target = extract_pagination_links(soup, selectors, return_target=True)
            self.logger.info(f"Extracted pagination target: {pagination_target}")
            return pagination_target
            
        except Exception as e:
            self.logger.error(f"Failed to extract pagination target from {source_url}: {e}")
            return None
        finally:
            page.close()
    
    def _process_single_tender(self, context, source_url: str, tender: Dict) -> Dict:
        """Process a single tender and return the enriched tender data"""
        tender_number = tender.get('number', 'unknown')
        self.logger.info(f"Processing tender {tender_number} from {source_url}")
        
        if not tender.get("pagination_argument"):
            self.logger.error(f"Tender {tender_number} missing pagination_argument")
            raise KeyError("pagination_argument")
        
        target = tender["details_url"]
        argument = tender["pagination_argument"]
        pagination_target = tender.get("pagination_target") or self.pagination_target
        
        if not pagination_target:
            self.logger.error(f"Tender {tender_number} missing pagination_target")
            raise KeyError("pagination_target")
        
        self.logger.debug(f"Tender {tender_number} - Target: {target}, Argument: {argument}, Pagination Target: {pagination_target}")
        
        detail_page = context.new_page()
        try:
            detail_page.goto(source_url)
            detail_page.wait_for_load_state("networkidle")
            
            simulate_postback_with_retry(detail_page, pagination_target, argument)
            html, real_url = simulate_postback_with_retry(detail_page, target)
            
            full_text = extract_full_text_from_page(html)
            
            # Update tender dict with extracted details
            tender["full_text"] = full_text
            tender["details_url"] = real_url
            
            # Convert to TenderModel for validation
            try:
                tender_model = TenderModel(**tender)
                self.logger.debug(f"Validated tender model for {tender_number}")
                # Convert back to dict for file operations
                enriched_tender = tender_model.to_dict()
            except Exception as e:
                self.logger.warning(f"TenderModel validation failed for {tender_number}, using dict: {e}")
                enriched_tender = tender
            
            self.logger.info(f"Successfully extracted {len(full_text)} characters for tender {tender_number}")
            self.logger.debug(f"Real URL for tender {tender_number}: {real_url}")
            return enriched_tender
        except Exception as e:
            self.logger.error(f"Failed to process tender {tender_number}: {e}")
            raise
        finally:
            detail_page.close()
    
    def process_tenders_for_url(self, tenders: List[Dict], source_url: str) -> int:
        """Process tenders for a specific listing URL"""
        self.logger.info(f"Processing tenders for URL: {source_url}")
        playwright, browser, context = setup_browser_context()
        processed_count = 0
        
        try:
            portal_config = next((p for p in self.postback_portals if source_url in p.get("listing_urls", [])), None)
            if not portal_config:
                self.logger.warning(f"No portal configuration found for URL: {source_url}")
                return 0
            
            portal_name = portal_config.get("name", "unknown")
            self.logger.debug(f"Using portal configuration for: {portal_name}")
            
            self.pagination_target = self._extract_pagination_target(context, source_url, portal_config)
            
            url_tenders = [t for t in tenders if t.get("source_url") == source_url]
            if not url_tenders:
                self.logger.warning(f"No tenders found for source URL: {source_url}")
                return 0
            
            self.logger.info(f"Found {len(url_tenders)} tenders to process for {source_url}")
            
            for i, tender in enumerate(url_tenders, 1):
                tender_number = tender.get('number', 'unknown')
                self.logger.info(f"Processing tender {i}/{len(url_tenders)}: {tender_number}")
                try:
                    if not tender.get("pagination_target") and self.pagination_target:
                        tender["pagination_target"] = self.pagination_target
                        self.logger.debug(f"Set pagination target for tender {tender_number}")
                    
                    enriched_tender = self._process_single_tender(context, source_url, tender)
                    update_tender_with_details(enriched_tender)
                    processed_count += 1
                    self.logger.debug(f"Successfully processed and saved tender {tender_number}")
                except Exception as e:
                    self.logger.error(f"Error processing tender {tender_number}: {e}")
                    continue
        finally:
            cleanup_browser_resources(playwright, browser)
        
        self.logger.info(f"Completed processing {processed_count}/{len(url_tenders)} tenders for {source_url}")
        return processed_count
    
    def run(self) -> None:
        """Main method to orchestrate the postback processing workflow"""
        self.logger.info("Starting postback details crawler workflow")
        tenders = load_tenders_needing_details()
        if not tenders:
            self.logger.info("No tenders found needing details")
            return
        
        self.logger.info(f"Found {len(tenders)} tenders needing details")
        
        if not self.postback_portals:
            self.logger.warning("No active portals configured for postback processing")
            print("No active portals configured for postback processing")
            return
        
        postback_tenders = self._filter_postback_tenders(tenders)
        if not postback_tenders:
            self.logger.warning("No tenders found from portals configured for postback processing")
            print("No tenders found from portals configured for postback processing")
            return
        
        total_processed = 0
        for portal in self.postback_portals:
            portal_name = portal.get("name", "unknown")
            self.logger.info(f"Processing portal: {portal_name}")
            for source_url in portal.get("listing_urls", []):
                processed_count = self.process_tenders_for_url(postback_tenders, source_url)
                total_processed += processed_count
                self.logger.info(f"Portal {portal_name} - URL {source_url}: {processed_count} tenders processed")
        
        self.logger.info(f"Postback processing workflow completed: {total_processed} tenders processed")
        print(f"Completed processing {total_processed} tenders")

def main():
    """Main function to orchestrate the postback processing workflow"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/postback_details_crawler.log'),
            logging.StreamHandler()
        ]
    )
    
    crawler = PostbackDetailsCrawler()
    crawler.run()

if __name__ == "__main__":
    main()