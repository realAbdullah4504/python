"""
Postback navigation utility for handling web-based detail pages.
"""

from typing import Optional, Tuple
from utils.playwright_utils import setup_browser_context, simulate_postback_with_retry, cleanup_browser_resources
from utils.bs4_utils import extract_full_text_from_page, extract_pagination_links
from bs4 import BeautifulSoup


class PostbackNavigator:
    """Utility class for navigating postback-based web pages."""
    
    def __init__(self):
        """Initialize postback navigator."""
        self.pagination_target = None
    
    def setup_browser(self):
        """Setup browser context and return components."""
        return setup_browser_context()
    
    def extract_pagination_target(self, context, source_url: str, portal_config: dict) -> Optional[str]:
        """
        Extract pagination target from the page content.
        
        Args:
            context: Browser context
            source_url: URL to extract pagination target from
            portal_config: Portal configuration
            
        Returns:
            Pagination target string or None if extraction fails
        """
        print(f"Extracting pagination target from: {source_url}")
        page = context.new_page()
        try:
            page.goto(source_url)
            page.wait_for_load_state("networkidle")
            
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            selectors = portal_config.get("config", {}).get("selectors", {})
            if not selectors:
                print("No selectors found in portal config")
                return None
            
            _, pagination_target = extract_pagination_links(soup, selectors, return_target=True)
            print(f"Extracted pagination target: {pagination_target}")
            return pagination_target
            
        except Exception as e:
            print(f"Failed to extract pagination target from {source_url}: {e}")
            return None
        finally:
            page.close()
    
    def navigate_to_tender_details(self, context, source_url: str, tender: dict) -> Tuple[str, str]:
        """
        Navigate to tender details page using postback.
        
        Args:
            context: Browser context
            source_url: Source listing URL
            tender: Tender dictionary with navigation info
            
        Returns:
            Tuple of (extracted_text, real_url)
        """
        tender_number = tender.get('number', 'unknown')
        print(f"Navigating to details for tender {tender_number} from {source_url}")
        
        if not tender.get("page_no"):
            print(f"Tender {tender_number} missing page_no")
            raise KeyError("page_no")
        
        target = tender["details_url"]
        argument = f"Page${tender.get('page_no')}"
        pagination_target = tender.get("pagination_target") or self.pagination_target
        
        if not pagination_target:
            print(f"Tender {tender_number} missing pagination_target")
            raise KeyError("pagination_target")
        
        print(f"Tender {tender_number} - Target: {target}, Argument: {argument}, Pagination Target: {pagination_target}")
        
        detail_page = context.new_page()
        try:
            detail_page.goto(source_url)
            detail_page.wait_for_load_state("networkidle")
            
            simulate_postback_with_retry(detail_page, pagination_target, argument)
            html, real_url = simulate_postback_with_retry(detail_page, target)
            
            full_text = extract_full_text_from_page(html)
            
            print(f"Successfully extracted {len(full_text)} characters for tender {tender_number}")
            print(f"Real URL for tender {tender_number}: {real_url}")
            
            return full_text, real_url
        except Exception as e:
            print(f"Failed to navigate to details for tender {tender_number}: {e}")
            raise
        finally:
            detail_page.close()
    
        
    def validate_tender_navigation(self, tender: dict) -> bool:
        """
        Validate tender has required navigation fields.
        
        Args:
            tender: Tender dictionary to validate
            
        Returns:
            True if tender has required fields, False otherwise
        """
        required_fields = ['number', 'page_no', 'details_url']
        return all(field in tender for field in required_fields)
