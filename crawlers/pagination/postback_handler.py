"""
Postback pagination handler for ASP.NET WebForms postback pagination.
"""

from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_handler import IPaginationHandler
from utils.playwright_utils import simulate_postback
from utils.bs4_utils import extract_pagination_links


class PostbackPaginationHandler(IPaginationHandler):
    """
    Handles ASP.NET WebForms postback pagination.
    
    This handler manages pagination through JavaScript __doPostBack calls,
    commonly used in ASP.NET WebForms applications like Comprar Gob AR.
    """
    
    def handle_pagination(
        self, 
        page, 
        current_page: int, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Handle ASP.NET postback pagination.
        
        Args:
            page: Playwright page object
            current_page: Current page number
            pagination_config: Pagination configuration
            
        Returns:
            True if pagination was successful, False if no more pages
        """
        try:
            # Get pagination target from config or extract from page
            pagination_target = pagination_config.get('target')
            
            if not pagination_target:
                # Extract pagination target from current page
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                selectors = pagination_config.get('selectors', {})
                _, extracted_target = extract_pagination_links(soup, selectors, return_target=True)
                
                if extracted_target:
                    pagination_target = extracted_target
                    print(f"Extracted pagination target: {pagination_target}")
                else:
                    # Use fallback target
                    pagination_target = pagination_config.get('fallback_target', "ctl00$CPH1$GridListaPliegos")
                    print(f"Using fallback pagination target: {pagination_target}")
            
            # Simulate postback to next page
            argument = f"Page${current_page + 1}"
            simulate_postback(page, pagination_target, argument)
            
            return True
            
        except Exception as e:
            print(f"Error handling postback pagination: {e}")
            return False
    
    def extract_pagination_info(
        self, 
        html_content: str, 
        pagination_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract pagination information from the page content.
        
        Args:
            html_content: HTML content of the current page
            pagination_config: Pagination configuration
            
        Returns:
            Dictionary containing pagination information
        """
        soup = BeautifulSoup(html_content, "html.parser")
        selectors = pagination_config.get('selectors', {})
        
        # Extract pagination links and target
        pagination_links, pagination_target = extract_pagination_links(
            soup, selectors, return_target=True
        )
        
        return {
            'type': 'postback',
            'target': pagination_target,
            'pagination_links': pagination_links,
            'max_pages': pagination_config.get('max_pages', 10)
        }
    
    def is_last_page(
        self, 
        page_data: Any, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if the current page is the last page for postback pagination.
        
        For postback pagination, we typically check if we've reached max_pages
        or if no new data is found.
        
        Args:
            page_data: Data extracted from the current page (list of tenders)
            pagination_config: Pagination configuration
            
        Returns:
            True if this is the last page, False otherwise
        """
        # If no data found, we're likely on the last page
        if not page_data or len(page_data) == 0:
            return True
        
        # For postback pagination, we rely on max_pages limit
        # The actual last page detection happens during crawling
        return False
    
    def has_pagination_controls(
        self, 
        html_content: str, 
        selectors: Dict[str, Any]
    ) -> bool:
        """
        Check if the page has pagination controls.
        
        Args:
            html_content: HTML content of the page
            selectors: CSS selectors for pagination elements
            
        Returns:
            True if pagination controls are found, False otherwise
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Look for pagination row
        table = soup.find(selectors.get("main_table", "table"))
        if not table:
            return False
        
        pagination_rows = table.find_all(
            selectors.get("table_row", "tr"), 
            class_=selectors.get("pagination_row_class", "pagination-gv")
        )
        
        return len(pagination_rows) > 0
