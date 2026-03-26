"""
Postback details extraction strategy implementation.
"""

from typing import List, Dict
from crawlers.interfaces import IDetailsStrategy
from crawlers.processors.postback_navigator import PostbackNavigator
from utils.config_resolver import load_config_with_refs
from models.tender import TenderModel


class PostbackDetailsStrategy(IDetailsStrategy):
    """Strategy for extracting details from postback-based web pages."""
    
    def __init__(self):
        """Initialize postback details strategy."""
        self.config = load_config_with_refs("config/portals.json")
        self.postback_portals = self._get_postback_portals()
        self.navigator = PostbackNavigator()
        print(f"Initialized PostbackDetailsStrategy with {len(self.postback_portals)} postback portals")
    
    def _get_postback_portals(self) -> List[Dict]:
        """Get active portals that use postback detail processing."""
        postback_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                print(f"Skipping inactive portal: {portal.get('name', 'unknown')}")
                continue
                
            portal_config = portal.get("config", {})
            details_config = portal_config.get("details", {})
            
            if details_config.get("type") == "postback":
                postback_portals.append(portal)
                print(f"Added postback portal: {portal.get('name', 'unknown')}")
        
        print(f"Found {len(postback_portals)} active postback portals")
        return postback_portals
    
    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "postback"
    
    def can_handle(self, tender: Dict) -> bool:
        """Check if this strategy can handle the given tender."""
        portal_name = tender.get("portal_name")
        
        if not portal_name:
            return False
        
        # Check if portal is configured for postback processing
        portal_names = {portal.get("name") for portal in self.postback_portals}
        return portal_name in portal_names
    
    def filter_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders that this strategy can process."""
        postback_tenders = []
        portal_names = {portal.get("name") for portal in self.postback_portals}
        print(f"Filtering tenders for postback portals: {portal_names}")
        
        for tender in tenders:
            if tender.get("portal_name") in portal_names:
                postback_tenders.append(tender)
                print(f"Added postback tender: {tender.get('number', 'unknown')} from {tender.get('portal_name', 'unknown')}")
        
        print(f"Filtered {len(postback_tenders)} tenders from {len(tenders)} total for postback processing")
        return postback_tenders
    
    def extract_details(self, tender: Dict) -> Dict:
        """Extract details for a single tender from postback web page."""
        tender_number = tender.get('number', 'unknown')
        source_url = tender.get('url')
        
        print(f"Processing tender {tender_number} from {source_url}")
        
        if not source_url:
            print(f"Tender {tender_number} has no source URL")
            return tender
        
        if not self.navigator.validate_tender_navigation(tender):
            print(f"Tender {tender_number} missing required navigation fields")
            return tender
        
        # Get portal configuration for this URL
        portal_config = next((p for p in self.postback_portals if source_url in p.get("listing_urls", [])), None)
        if not portal_config:
            print(f"No portal configuration found for URL: {source_url}")
            return tender
        
        # Setup browser and extract details
        playwright, browser, context = self.navigator.setup_browser()
        try:
            # Extract pagination target if not already set
            if not tender.get("pagination_target"):
                self.navigator.pagination_target = self.navigator.extract_pagination_target(
                    context, source_url, portal_config
                )
                if self.navigator.pagination_target:
                    tender["pagination_target"] = self.navigator.pagination_target
            
            # Navigate to tender details
            full_text, real_url = self.navigator.navigate_to_tender_details(context, source_url, tender)
            
            # Update tender dict with extracted details
            tender["full_text"] = full_text
            tender["details_url"] = real_url
            
            # Convert to TenderModel for validation
            try:
                tender_model = TenderModel(**tender)
                print(f"Validated tender model for {tender_number}")
                # Convert back to dict for file operations
                enriched_tender = tender_model.to_dict()
            except Exception as e:
                print(f"TenderModel validation failed for {tender_number}, using dict: {e}")
                enriched_tender = tender
            
            return enriched_tender
            
        except Exception as e:
            print(f"Failed to process tender {tender_number}: {e}")
            return tender
        finally:
            from utils.playwright_utils import cleanup_browser_resources
            cleanup_browser_resources(playwright, browser)
    
    def process_tenders_for_url(self, tenders: List[Dict], source_url: str) -> int:
        """
        Process tenders for a specific listing URL.
        
        Args:
            tenders: List of tender dictionaries
            source_url: Source listing URL
            
        Returns:
            Number of tenders processed
        """
        # Get portal configuration for this URL
        portal_config = next((p for p in self.postback_portals if source_url in p.get("listing_urls", [])), None)
        if not portal_config:
            print(f"No portal configuration found for URL: {source_url}")
            return 0
        
        # Setup browser context for URL processing
        return self.navigator.process_tenders_for_url(tenders, source_url, portal_config)
