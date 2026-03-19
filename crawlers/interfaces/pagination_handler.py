"""
Base interface for pagination handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests


class IPaginationHandler(ABC):
    """Abstract base class for pagination handlers."""
    
    @abstractmethod
    def fetch_page(self, base_url: str, pagination_config: Dict, page: int = 1, 
                   session: Optional[requests.Session] = None, 
                   csrf_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single page of data.
        
        Args:
            base_url: Base URL for the portal
            pagination_config: Pagination configuration
            page: Page number to fetch
            session: HTTP session (optional)
            csrf_token: CSRF token (optional)
            
        Returns:
            Page data or None if failed
        """
        pass
    
    @abstractmethod
    def get_pagination_type(self) -> str:
        """
        Get the pagination type identifier.
        
        Returns:
            String identifier for pagination type
        """
        pass
    
    @abstractmethod
    def has_more_data(self, response_data: Dict[str, Any], page_size: int) -> bool:
        """
        Check if there's more data available.
        
        Args:
            response_data: Response data from current page
            page_size: Expected page size
            
        Returns:
            True if more data is available, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_data_from_response(self, response_data: Dict[str, Any]) -> list:
        """
        Extract the actual data items from response.
        
        Args:
            response_data: Response data from API
            
        Returns:
            List of data items
        """
        pass
