"""
Base interface for crawler strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set
from models.tender import TenderModel


class ICrawlerStrategy(ABC):
    """Abstract base class for crawler strategies."""
    
    @abstractmethod
    def crawl(self, url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
        """
        Crawl tenders from a portal using the specific strategy.
        
        Args:
            url: The URL to crawl
            portal_config: Configuration for the portal
            seen_tender_numbers: Set of already processed tender identifiers
            
        Returns:
            List of TenderModel instances
        """
        pass
    
    @abstractmethod
    def get_crawler_type(self) -> str:
        """
        Get the crawler type identifier.
        
        Returns:
            String identifier for crawler type
        """
        pass
    
    @abstractmethod
    def can_handle(self, portal_config: Dict) -> bool:
        """
        Check if this strategy can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration to check
            
        Returns:
            True if this strategy can handle the portal, False otherwise
        """
        pass
