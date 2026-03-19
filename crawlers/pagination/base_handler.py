"""
Base interface for pagination handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from playwright.sync_api import Page as PlaywrightPage


class IPaginationHandler(ABC):
    """
    Abstract base class for handling different types of pagination.
    
    This interface defines the contract that all pagination handlers must implement,
    ensuring consistent behavior across different pagination mechanisms.
    """
    
    @abstractmethod
    def handle_pagination(
        self, 
        page: PlaywrightPage, 
        current_page: int, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Handle pagination to navigate to the next page.
        
        Args:
            page: Playwright page object
            current_page: Current page number
            pagination_config: Pagination configuration dictionary
            
        Returns:
            True if pagination was successful, False if no more pages available
        """
        pass
    
    @abstractmethod
    def extract_pagination_info(
        self, 
        html_content: str, 
        pagination_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract pagination information from the page content.
        
        Args:
            html_content: HTML content of the current page
            pagination_config: Pagination configuration dictionary
            
        Returns:
            Dictionary containing pagination information
        """
        pass
    
    @abstractmethod
    def is_last_page(
        self, 
        page_data: Any, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if the current page is the last page.
        
        Args:
            page_data: Data from the current page (type depends on handler)
            pagination_config: Pagination configuration dictionary
            
        Returns:
            True if this is the last page, False otherwise
        """
        pass
    
    def get_max_pages(self, pagination_config: Dict[str, Any]) -> int:
        """
        Get the maximum number of pages to crawl.
        
        Args:
            pagination_config: Pagination configuration dictionary
            
        Returns:
            Maximum number of pages to crawl
        """
        return pagination_config.get('max_pages', 10)
    
    def should_continue_pagination(
        self, 
        current_page: int, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if pagination should continue.
        
        Args:
            current_page: Current page number
            pagination_config: Pagination configuration dictionary
            
        Returns:
            True if pagination should continue, False otherwise
        """
        max_pages = self.get_max_pages(pagination_config)
        return current_page <= max_pages
