"""
PDF details extraction strategy implementation.
"""

from typing import List, Dict, Set
from crawlers.interfaces import IDetailsStrategy
from crawlers.processors.pdf_text_extractor import PdfTextExtractor
from utils.config_resolver import load_config_with_refs
from models.tender import TenderModel


class PdfDetailsStrategy(IDetailsStrategy):
    """Strategy for extracting details from PDF documents."""
    
    def __init__(self):
        """Initialize PDF details strategy."""
        self.config = load_config_with_refs("config/portals.json")
        self.pdf_portals = self._get_pdf_portals()
        self.pdf_timeout = self._get_pdf_timeout()
        self.text_extractor = PdfTextExtractor(self.pdf_timeout)
        print(f"Initialized PdfDetailsStrategy with {len(self.pdf_portals)} PDF portals")
    
    def _get_pdf_timeout(self) -> int:
        """Get PDF timeout from configuration."""
        timeout = self.config["templates"]["detail_types"]["pdf"].get("timeout", 60)
        print(f"PDF timeout set to {timeout}s")
        return timeout
    
    def _get_pdf_portals(self) -> List[Dict]:
        """Get active portals that use PDF detail processing."""
        pdf_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                print(f"Skipping inactive portal: {portal.get('name', 'unknown')}")
                continue
                
            portal_config = portal.get("config", {})
            if portal_config.get("details", {}).get("type") == "pdf":
                pdf_portals.append(portal)
                print(f"Added PDF portal: {portal.get('name', 'unknown')}")
        
        print(f"Found {len(pdf_portals)} active PDF portals")
        return pdf_portals
    
    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "pdf"
    
    def can_handle(self, tender: Dict) -> bool:
        """Check if this strategy can handle the given tender."""
        portal_name = tender.get("portal_name")
        details_url = tender.get("details_url")
        
        if not portal_name or not details_url:
            return False
        
        # Check if portal is configured for PDF processing
        portal_names = {portal.get("name") for portal in self.pdf_portals}
        if portal_name not in portal_names:
            return False
        
        # Check if URL appears to be PDF
        return self.text_extractor.is_pdf_url(details_url)
    
    def filter_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders that this strategy can process."""
        pdf_tenders = []
        portal_names = {portal.get("name") for portal in self.pdf_portals}
        print(f"Filtering tenders for PDF portals: {portal_names}")
        
        for tender in tenders:
            if tender.get("portal_name") in portal_names and tender.get("details_url"):
                if self.text_extractor.is_pdf_url(tender.get("details_url", "")):
                    pdf_tenders.append(tender)
                    print(f"Added PDF tender: {tender.get('number', 'unknown')} from {tender.get('portal_name', 'unknown')}")
        
        print(f"Filtered {len(pdf_tenders)} tenders from {len(tenders)} total for PDF processing")
        return pdf_tenders
    
    def extract_details(self, tender: Dict) -> Dict:
        """Extract details for a single tender from PDF."""
        tender_number = tender.get('number', 'unknown')
        portal_name = tender.get('portal_name', 'unknown')
        pdf_url = tender.get("details_url")
        
        print(f"Processing tender {tender_number} from {portal_name}")
        
        if not pdf_url:
            print(f"Tender {tender_number} has no PDF URL")
            return tender
        
        if not self.text_extractor.is_pdf_url(pdf_url):
            print(f"Skipping tender {tender_number}: URL does not appear to be PDF")
            return tender
        
        pdf_text = self.text_extractor.extract_text_from_pdf_url(pdf_url)
        
        # Update tender dict with extracted details
        if pdf_text:
            tender["full_text"] = pdf_text
            tender["text_source"] = "pdf_extraction"
            print(f"Successfully extracted {len(pdf_text)} characters for tender {tender_number}")
        else:
            tender["full_text"] = ""
            tender["text_source"] = "pdf_extraction_failed"
            print(f"Failed to extract text for tender {tender_number}")
        
        # Convert to TenderModel for validation
        try:
            tender_model = TenderModel(**tender)
            print(f"Validated tender model for {tender_number}")
            # Convert back to dict for file operations
            enriched_tender = tender_model.to_dict()
        except Exception as e:
            print(f"TenderModel validation failed for {tender_number}, using dict: {e}")
            enriched_tender = tender
        
        return enriched_tender
