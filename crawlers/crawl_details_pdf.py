#!/usr/bin/env python3
"""
PDF Details Crawler
Downloads and extracts text from PDF URLs for tenders that have PDF documents
"""

import json
from typing import List, Dict, Optional
import requests
import PyPDF2
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import logging

from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.config_resolver import load_config_with_refs
from models.tender import TenderModel

class PdfDetailsCrawler:
    """Handles PDF-based tender detail extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = load_config_with_refs("config/portals.json")
        self.pdf_portals = self._get_pdf_portals()
        self.pdf_timeout = self._get_pdf_timeout()
        self.logger.info(f"Initialized PdfDetailsCrawler with {len(self.pdf_portals)} PDF portals, timeout: {self.pdf_timeout}s")
    
    def _get_pdf_timeout(self) -> int:
        """Get PDF timeout from configuration"""
        timeout = self.config["templates"]["detail_types"]["pdf"].get("timeout", 60)
        self.logger.debug(f"PDF timeout set to {timeout}s")
        return timeout
    
    def _get_pdf_portals(self) -> List[Dict]:
        """Get active portals that use PDF detail processing"""
        pdf_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                self.logger.debug(f"Skipping inactive portal: {portal.get('name', 'unknown')}")
                continue
                
            portal_config = portal.get("config", {})
            if portal_config.get("details", {}).get("type") == "pdf":
                pdf_portals.append(portal)
                self.logger.debug(f"Added PDF portal: {portal.get('name', 'unknown')}")
        
        self.logger.info(f"Found {len(pdf_portals)} active PDF portals")
        return pdf_portals
    
    def _filter_pdf_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders from portals that use PDF processing"""
        pdf_tenders = []
        portal_names = {portal.get("name") for portal in self.pdf_portals}
        self.logger.debug(f"Filtering tenders for PDF portals: {portal_names}")
        
        for tender in tenders:
            if tender.get("portal_name") in portal_names and tender.get("details_url"):
                pdf_tenders.append(tender)
                self.logger.debug(f"Added PDF tender: {tender.get('number', 'unknown')} from {tender.get('portal_name', 'unknown')}")
        
        self.logger.info(f"Filtered {len(pdf_tenders)} tenders from {len(tenders)} total for PDF processing")
        return pdf_tenders
    
    def _extract_text_direct(self, pdf_bytes: bytes) -> str:
        """Extract text directly from PDF bytes using PyPDF2"""
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            self.logger.debug(f"PDF has {len(pdf_reader.pages)} pages")
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text + "\n"
                        self.logger.debug(f"Extracted {len(page_text)} characters from page {page_num}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    continue
                    
            self.logger.info(f"Direct extraction completed: {len(text)} characters extracted")
            return text
        except Exception as e:
            self.logger.error(f"Direct PDF extraction failed: {e}")
            return ""
    
    def _extract_text_ocr(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using OCR (for scanned PDFs)"""
        try:
            self.logger.info("Starting OCR extraction for PDF")
            images = convert_from_bytes(pdf_bytes, dpi=200, fmt='jpeg')
            self.logger.debug(f"Converted PDF to {len(images)} images for OCR")
            
            text = ""
            for page_num, image in enumerate(images, 1):
                try:
                    page_text = pytesseract.image_to_string(image, lang='spa+eng')
                    if page_text.strip():
                        text += f"\n--- Page {page_num} (OCR) ---\n"
                        text += page_text + "\n"
                        self.logger.debug(f"OCR extracted {len(page_text)} characters from page {page_num}")
                except Exception as e:
                    self.logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue
                    
            self.logger.info(f"OCR extraction completed: {len(text)} characters extracted")
            return text
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def _extract_text_from_pdf_url(self, pdf_url: str) -> str:
        """Download PDF from URL and extract text"""
        self.logger.info(f"Processing PDF URL: {pdf_url}")
        try:
            response = requests.get(pdf_url, timeout=self.pdf_timeout)
            response.raise_for_status()
            self.logger.debug(f"Downloaded PDF: {len(response.content)} bytes")
            
            pdf_bytes = response.content
            
            # Try direct text extraction first
            text = self._extract_text_direct(pdf_bytes)
            if text.strip():
                self.logger.info("Direct text extraction succeeded")
                return text
            
            # Fall back to OCR
            self.logger.info("Direct extraction failed, trying OCR")
            return self._extract_text_ocr(pdf_bytes)
                
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_url}: {e}")
            return ""
    
    def _process_single_tender(self, tender: Dict) -> Dict:
        """Process a single tender and extract PDF text"""
        tender_number = tender.get('number', 'unknown')
        portal_name = tender.get('portal_name', 'unknown')
        pdf_url = tender.get("details_url")
        
        self.logger.info(f"Processing tender {tender_number} from {portal_name}")
        
        if not pdf_url:
            self.logger.warning(f"Tender {tender_number} has no PDF URL")
            return tender
        
        # Check if URL points to a PDF
        if not (pdf_url.lower().endswith('.pdf') or 'descargar' in pdf_url.lower()):
            self.logger.debug(f"Skipping tender {tender_number}: URL does not appear to be PDF")
            return tender
        
        pdf_text = self._extract_text_from_pdf_url(pdf_url)
        
        # Update tender dict with extracted details
        if pdf_text:
            tender["full_text"] = pdf_text
            tender["text_source"] = "pdf_extraction"
            self.logger.info(f"Successfully extracted {len(pdf_text)} characters for tender {tender_number}")
        else:
            tender["full_text"] = ""
            tender["text_source"] = "pdf_extraction_failed"
            self.logger.warning(f"Failed to extract text for tender {tender_number}")
        
        # Convert to TenderModel for validation
        try:
            tender_model = TenderModel(**tender)
            self.logger.debug(f"Validated tender model for {tender_number}")
            # Convert back to dict for file operations
            enriched_tender = tender_model.to_dict()
        except Exception as e:
            self.logger.warning(f"TenderModel validation failed for {tender_number}, using dict: {e}")
            enriched_tender = tender
        
        return enriched_tender
    
    def process_tenders(self, tenders: List[Dict], max_tenders: int = 10) -> int:
        """Process multiple tenders and save PDF extracted text data"""
        processed_count = 0
        total_tenders = min(len(tenders), max_tenders)
        self.logger.info(f"Starting to process {total_tenders} tenders (max: {max_tenders})")
        
        for i, tender in enumerate(tenders[:max_tenders], 1):
            tender_number = tender.get('number', 'unknown')
            self.logger.info(f"Processing tender {i}/{total_tenders}: {tender_number}")
            try:
                enriched_tender = self._process_single_tender(tender)
                update_tender_with_details(enriched_tender)
                processed_count += 1
                self.logger.debug(f"Successfully processed and saved tender {tender_number}")
            except Exception as e:
                self.logger.error(f"Error processing tender {tender_number}: {e}")
                continue
        
        self.logger.info(f"Completed processing {processed_count}/{total_tenders} tenders successfully")
        return processed_count
    
    def run(self) -> None:
        """Main method to orchestrate the PDF processing workflow"""
        self.logger.info("Starting PDF details crawler workflow")
        tenders = load_tenders_needing_details()
        if not tenders:
            self.logger.info("No tenders found needing details")
            return
        
        self.logger.info(f"Found {len(tenders)} tenders needing details")
        
        if not self.pdf_portals:
            self.logger.warning("No active portals configured for PDF processing")
            print("No active portals configured for PDF processing")
            return
        
        pdf_tenders = self._filter_pdf_tenders(tenders)
        if not pdf_tenders:
            self.logger.warning("No tenders found from portals configured for PDF processing")
            print("No tenders found from portals configured for PDF processing")
            return
        
        processed_count = self.process_tenders(pdf_tenders, len(pdf_tenders))
        self.logger.info(f"PDF processing workflow completed: {processed_count} tenders processed")
        print(f"Completed processing {processed_count} tenders with PDFs")

def main():
    """Main function to orchestrate the PDF processing workflow"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pdf_details_crawler.log'),
            logging.StreamHandler()
        ]
    )
    
    crawler = PdfDetailsCrawler()
    crawler.run()


if __name__ == "__main__":
    main()
