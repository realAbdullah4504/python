"""
Base interface for details extraction strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from models.tender import TenderModel


class IDetailsStrategy(ABC):
    """Abstract base class for details extraction strategies."""
    
    @abstractmethod
    def extract_details(self, tender: Dict) -> Dict:
        """
        Extract details for a single tender.
        
        Args:
            tender: Tender dictionary requiring details extraction
            
        Returns:
            Enriched tender dictionary with extracted details
        """
        pass
    
    @abstractmethod
    def can_handle(self, tender: Dict) -> bool:
        """
        Check if this strategy can handle the given tender.
        
        Args:
            tender: Tender dictionary to check
            
        Returns:
            True if this strategy can handle the tender, False otherwise
        """
        pass
    
    @abstractmethod
    def get_strategy_type(self) -> str:
        """
        Get the strategy type identifier.
        
        Returns:
            String identifier for strategy type
        """
        pass
    
    @abstractmethod
    def filter_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """
        Filter tenders that this strategy can process.
        
        Args:
            tenders: List of tender dictionaries
            
        Returns:
            Filtered list of tenders this strategy can handle
        """
        pass
    
    def validate_tender(self, tender: Dict) -> bool:
        """
        Validate tender has required fields for processing.
        
        Args:
            tender: Tender dictionary to validate
            
        Returns:
            True if tender is valid for processing, False otherwise
        """
        required_fields = ['number', 'portal_name']
        return all(field in tender for field in required_fields)
    
    def process_tender(self, tender: Dict) -> Dict:
        """
        Process a single tender with validation and error handling.
        
        Args:
            tender: Tender dictionary to process
            
        Returns:
            Enriched tender dictionary or original tender if processing fails
        """
        if not self.validate_tender(tender):
            print(f"Tender validation failed: {tender.get('number', 'unknown')}")
            return tender
        
        if not self.can_handle(tender):
            print(f"Strategy cannot handle tender: {tender.get('number', 'unknown')}")
            return tender
        
        try:
            return self.extract_details(tender)
        except Exception as e:
            print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
            return tender
