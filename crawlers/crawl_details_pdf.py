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

from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.config_resolver import load_config_with_refs

class PdfDetailsCrawler:
    """Handles PDF-based tender detail extraction"""
    
    def __init__(self):
        self.config = load_config_with_refs("config/portals.json")
        self.pdf_portals = self._get_pdf_portals()
        self.pdf_timeout = self._get_pdf_timeout()
    
    def _get_pdf_timeout(self) -> int:
        """Get PDF timeout from configuration"""
        detail_config = self.config["templates"]["detail_types"]["pdf"]
        return detail_config.get("timeout", 60)
    
    def _get_pdf_portals(self) -> List[Dict]:
        """Get active portals that use PDF detail processing"""
        pdf_portals = []
        for portal in self.config["portals"]:
            if not portal.get("active", True):
                continue
                
            portal_config = portal.get("config", {})
            details_config = portal_config.get("details", {})
            
            if details_config.get("type") == "pdf":
                pdf_portals.append(portal)
                print(f"Portal '{portal['name']}' uses PDF processing")
        
        return pdf_portals
    
    def _filter_pdf_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders from portals that use PDF processing"""
        pdf_tenders = []
        portal_names = {portal.get("name") for portal in self.pdf_portals}
        
        for tender in tenders:
            tender_portal = tender.get("portal_name", "Unknown")
            
            # Check if this tender's portal uses PDF processing
            if tender_portal in portal_names:
                print(f"Portal name: {tender_portal} | Tender portal: {tender_portal}")
                details_url = tender.get("details_url")
                print(f"Details URL: {details_url}")
                if details_url:
                    pdf_tenders.append(tender)
        
        return pdf_tenders
    
    def _extract_text_direct(self, pdf_bytes: bytes) -> str:
        """Extract text directly from PDF bytes using PyPDF2"""
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text + "\n"
                except Exception as e:
                    print(f"Warning: Could not extract text from page {page_num}: {e}")
                    continue
                    
            return text
        except Exception as e:
            print(f"Error in direct text extraction: {e}")
            return ""
    
    def _extract_text_ocr(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using OCR (for scanned PDFs)"""
        try:
            # Convert PDF to images
            print("Converting PDF to images for OCR...")
            images = convert_from_bytes(pdf_bytes, dpi=200, fmt='jpeg')
            
            text = ""
            for page_num, image in enumerate(images, 1):
                try:
                    # Extract text from image using pytesseract
                    page_text = pytesseract.image_to_string(image, lang='spa+eng')  # Spanish + English
                    if page_text.strip():
                        text += f"\n--- Page {page_num} (OCR) ---\n"
                        text += page_text + "\n"
                except Exception as e:
                    print(f"Warning: Could not OCR page {page_num}: {e}")
                    continue
                    
            return text
        except Exception as e:
            print(f"Error in OCR extraction: {e}")
            return ""
    
    def _extract_text_from_pdf_url(self, pdf_url: str, use_ocr_fallback: bool = True) -> str:
        """
        Download PDF from URL and extract text
        
        Args:
            pdf_url (str): URL of the PDF to scrape
            use_ocr_fallback (bool): Whether to use OCR if direct text extraction fails
        
        Returns:
            str: Extracted text content
        """
        try:
            # Download the PDF
            print(f"Downloading PDF from: {pdf_url}")
            response = requests.get(pdf_url, timeout=self.pdf_timeout)
            response.raise_for_status()
            
            pdf_bytes = response.content
            
            # Try direct text extraction first
            print("Attempting direct text extraction...")
            text = self._extract_text_direct(pdf_bytes)
            
            if text.strip():
                print(f"Successfully extracted {len(text)} characters via direct extraction")
                return text
            elif use_ocr_fallback:
                print("Direct extraction failed or returned empty text, trying OCR...")
                ocr_text = self._extract_text_ocr(pdf_bytes)
                if ocr_text.strip():
                    print(f"Successfully extracted {len(ocr_text)} characters via OCR")
                    return ocr_text
                else:
                    print("OCR extraction also failed or returned empty text")
                    return ""
            else:
                print("Direct extraction failed and OCR fallback is disabled")
                return ""
                
        except requests.RequestException as e:
            print(f"Error downloading PDF: {e}")
            return ""
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return ""
    
    def _process_single_tender(self, tender: Dict) -> Dict:
        """Process a single tender and extract PDF text"""
        # Use details_url field which contains the PDF URL
        pdf_url = tender.get("details_url")
        
        if not pdf_url:
            print(f"No details_url found for tender {tender.get('number', 'unknown')}")
            return tender
        
        # Check if URL points to a PDF
        if not pdf_url.lower().endswith('.pdf') and 'descargar' not in pdf_url.lower():
            print(f"details_url does not appear to be a PDF: {pdf_url}")
            return tender
        
        # Extract text from PDF
        pdf_text = self._extract_text_from_pdf_url(pdf_url)
        
        if pdf_text:
            tender["full_text"] = pdf_text
            tender["text_source"] = "pdf_extraction"
            print(f"Successfully extracted PDF text for tender {tender.get('number', 'unknown')}")
        else:
            print(f"Failed to extract PDF text for tender {tender.get('number', 'unknown')}")
            tender["full_text"] = ""
            tender["text_source"] = "pdf_extraction_failed"
        
        return tender
    
    def process_tenders(self, tenders: List[Dict], max_tenders: int = 10) -> int:
        """Process multiple tenders and save PDF extracted text data"""
        processed_count = 0
        
        for tender in tenders[:max_tenders]:
            try:
                enriched_tender = self._process_single_tender(tender)
                update_tender_with_details(enriched_tender)
                print(f"Processed PDF for: {enriched_tender.get('number', 'unknown')}")
                processed_count += 1
            except Exception as e:
                print(f"Error processing PDF for tender {tender.get('number', 'unknown')}: {e}")
                continue
        
        return processed_count
    
    def run(self) -> None:
        """Main method to orchestrate the PDF processing workflow"""
        # Load tenders that need details from NDJSON
        tenders = load_tenders_needing_details()
        
        if not tenders:
            print("No tenders found that need details")
            return
        
        if not self.pdf_portals:
            print("No active portals configured for PDF processing")
            return
        
        # Filter tenders from portals that use PDF processing
        pdf_tenders = self._filter_pdf_tenders(tenders)
        
        if not pdf_tenders:
            print("No tenders found from portals configured for PDF processing")
            return
        
        print(f"Found {len(pdf_tenders)} tenders from portals using PDF processing")
        
        # Process all tenders with PDFs
        processed_count = self.process_tenders(pdf_tenders, len(pdf_tenders))
        print(f"Completed processing {processed_count} tenders with PDFs")

def main() -> None:
    """Main function to orchestrate the PDF processing workflow"""
    crawler = PdfDetailsCrawler()
    crawler.run()

if __name__ == "__main__":
    main()
