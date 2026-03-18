"""
Service for handling tender deduplication logic.
"""

from typing import Set, Tuple, List
from models.tender import TenderModel


class DeduplicationService:
    """Handles duplicate detection and tracking of processed tenders."""
    
    def __init__(self, seen_tender_numbers: Set[str]):
        """
        Initialize the deduplication service.
        
        Args:
            seen_tender_numbers: Set of already processed tender identifiers
        """
        self.seen_tender_numbers = seen_tender_numbers
    
    def is_duplicate(self, tender: TenderModel) -> bool:
        """
        Check if a tender is a duplicate.
        
        Args:
            tender: The tender to check
            
        Returns:
            True if the tender is a duplicate, False otherwise
        """
        tender_id = tender.docId if tender.docId else tender.number
        return tender_id in self.seen_tender_numbers
    
    def add_tender(self, tender: TenderModel) -> None:
        """
        Add a tender to the seen set.
        
        Args:
            tender: The tender to add to the seen set
        """
        tender_id = tender.docId if tender.docId else tender.number
        self.seen_tender_numbers.add(tender_id)
    
    def process_tenders_with_deduplication(
        self, 
        tenders: List[TenderModel]
    ) -> Tuple[List[TenderModel], bool]:
        """
        Process a list of tenders, filtering out duplicates.
        
        Args:
            tenders: List of tenders to process
            
        Returns:
            Tuple of (new_tenders, existing_found)
            - new_tenders: List of tenders that are not duplicates
            - existing_found: True if an existing tender was encountered
        """
        new_tenders = []
        existing_found = False
        
        for tender in tenders:
            if self.is_duplicate(tender):
                existing_found = True
                print(f"Found existing tender: {tender.docId or tender.number}, stopping crawl")
                break
            
            self.add_tender(tender)
            new_tenders.append(tender)
        
        return new_tenders, existing_found
    
    def get_seen_count(self) -> int:
        """
        Get the count of seen tenders.
        
        Returns:
            Number of tenders in the seen set
        """
        return len(self.seen_tender_numbers)
