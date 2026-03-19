"""
Detail Crawler Strategy Interface.

Defines the contract for all tender detail extraction implementations.
Each portal type will have its own detail crawler implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.tender import TenderModel


class IDetailCrawlerStrategy(ABC):
    """Interface for tender detail extraction strategies."""
    
    @abstractmethod
    def fetch_details(self, tender_summary: Dict[str, Any], portal_config: Dict[str, Any]) -> Optional[TenderModel]:
        """
        Fetch full tender details from the details page.
        
        Args:
            tender_summary: Basic tender information with details_url
            portal_config: Portal configuration for detail extraction
            
        Returns:
            Complete TenderModel with full details, or None if extraction fails
        """
        pass
    
    @abstractmethod
    def can_handle(self, portal_config: Dict[str, Any]) -> bool:
        """
        Check if this detail crawler can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration to check
            
        Returns:
            True if this crawler can handle the portal, False otherwise
        """
        pass
    
    @abstractmethod
    def get_crawler_type(self) -> str:
        """
        Return the detail crawler type identifier.
        
        Returns:
            String identifier for this crawler type
        """
        pass
