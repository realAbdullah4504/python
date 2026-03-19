"""
Postback pagination handler for ASP.NET WebForms postback mechanisms.
"""

from typing import Dict, Any, Optional
from requests import Session
from bs4 import BeautifulSoup
from utils.playwright_utils import simulate_postback
from utils.bs4_utils import extract_pagination_links
from .base_handler import IPaginationHandler


class PostbackPaginationHandler(IPaginationHandler):
    """Handles ASP.NET postback pagination."""
    
    def __init__(self, page, selectors: Dict):
        """
        Initialize the postback handler.
        
        Args:
            page: Playwright page object
            selectors: CSS selectors for pagination elements
        """
        self.page = page
        self.selectors = selectors
        self.pagination_target = None
        self._extract_pagination_target()
    
    def _extract_pagination_target(self) -> None:
        """Extract the pagination target from the page."""
        html = self.page.content()
        soup = BeautifulSoup(html, "html.parser")
        _, self.pagination_target = extract_pagination_links(soup, self.selectors, return_target=True)
        
        if not self.pagination_target:
            print("Warning: Could not extract pagination target, will use fallback")
    
    def fetch_page(self, base_url: str, pagination_config: Dict, page: int = 1, 
                   session: Optional[Session] = None, 
                   csrf_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Navigate to a specific page using postback.
        
        For postback pagination, this method handles the navigation
        and returns the current page content as HTML.
        """
        if page == 1:
            # First page is already loaded, return current content
            html = self.page.content()
            return {"html": html, "page": page}
        
        # Navigate to subsequent pages using postback
        target = self._get_pagination_target(pagination_config)
        argument = f"Page${page}"
        
        print(f"Executing postback: target={target}, argument={argument}")
        simulate_postback(self.page, target, argument)
        
        # Return updated page content
        html = self.page.content()
        return {"html": html, "page": page}
    
    def get_pagination_type(self) -> str:
        """Return the pagination type identifier."""
        return "postback"
    
    def has_more_data(self, response_data: Dict[str, Any], page_size: int) -> bool:
        """
        For postback pagination, we can't easily determine if there's more data
        from the response alone. This should be handled by the calling code
        based on whether tenders were found on the current page.
        """
        return True  # Assume there might be more data
    
    def extract_data_from_response(self, response_data: Dict[str, Any]) -> list:
        """
        For postback pagination, the data extraction is handled by the
        calling code using BeautifulSoup. This method returns the HTML.
        """
        return [response_data.get("html", "")]
    
    def _get_pagination_target(self, pagination_config: Dict) -> str:
        """Get the pagination target, using fallback if needed."""
        if self.pagination_target:
            return self.pagination_target
        
        # Use fallback target from config
        fallback_target = pagination_config.get("target", "ctl00$CPH1$GridListaPliegos")
        print(f"Using fallback pagination target: {fallback_target}")
        return fallback_target
    
    def update_page_reference(self, page) -> None:
        """
        Update the page reference when a new page object is available.
        
        Args:
            page: New Playwright page object
        """
        self.page = page
        self.pagination_target = None
        self._extract_pagination_target()
