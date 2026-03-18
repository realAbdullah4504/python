"""
Service for processing tender data and creating TenderModel instances.
"""

from typing import List, Dict, Tuple
from models.tender import TenderModel
from utils.file_utils import save_tender_to_ndjson
from .deduplication_service import DeduplicationService


class TenderProcessor:
    """Handles processing of raw tender data into TenderModel instances."""
    
    def __init__(self, deduplication_service: DeduplicationService):
        """
        Initialize the tender processor.
        
        Args:
            deduplication_service: Service for handling deduplication
        """
        self.dedlication_service = deduplication_service
    
    def create_tender_from_dict(
        self, 
        tender_dict: Dict, 
        portal_name: str, 
        source_url: str = None
    ) -> TenderModel:
        """
        Create a TenderModel from a dictionary.
        
        Args:
            tender_dict: Raw tender data dictionary
            portal_name: Name of the portal
            source_url: Source URL where tender was found
            
        Returns:
            TenderModel instance
        """
        if 'expediente' in tender_dict or 'docId' in tender_dict:
            # Pattern-based tender
            return TenderModel.from_pattern_tender(tender_dict, portal_name, source_url)
        else:
            # Table-based tender
            return TenderModel.from_table_tender(tender_dict, portal_name)
    
    def process_raw_tenders(
        self, 
        raw_tenders: List[Dict], 
        portal_name: str, 
        source_url: str = None
    ) -> Tuple[int, List[TenderModel], bool]:
        """
        Process raw tender dictionaries into TenderModel instances.
        
        Args:
            raw_tenders: List of raw tender dictionaries
            portal_name: Name of the portal
            source_url: Source URL where tenders were found
            
        Returns:
            Tuple of (new_count, new_tenders, existing_found)
            - new_count: Number of new tenders processed
            - new_tenders: List of new TenderModel instances
            - existing_found: True if an existing tender was encountered
        """
        # Convert raw dictionaries to TenderModel instances
        tender_models = []
        for tender_dict in raw_tenders:
            tender = self.create_tender_from_dict(tender_dict, portal_name, source_url)
            tender_models.append(tender)
        
        # Process with deduplication
        new_tenders, existing_found = self.dedlication_service.process_tenders_with_deduplication(
            tender_models
        )
        
        # Save new tenders to file
        for tender in new_tenders:
            save_tender_to_ndjson(tender.to_dict())
        
        new_count = len(new_tenders)
        return new_count, new_tenders, existing_found
