"""
PDF text extraction utility for processing tender documents.
"""

import requests
import PyPDF2
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from typing import Optional


class PdfTextExtractor:
    """Utility class for extracting text from PDF documents."""
    
    def __init__(self, timeout: int = 60):
        """
        Initialize PDF text extractor.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def extract_text_direct(self, pdf_bytes: bytes) -> str:
        """
        Extract text directly from PDF bytes using PyPDF2.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
        """
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text + "\n"
                        print(f"Extracted {len(page_text)} characters from page {page_num}")
                except Exception as e:
                    print(f"Failed to extract text from page {page_num}: {e}")
                    continue
                    
            print(f"Direct extraction completed: {len(text)} characters extracted")
            return text
        except Exception as e:
            print(f"Direct PDF extraction failed: {e}")
            return ""
    
    def extract_text_ocr(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using OCR (for scanned PDFs).
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            OCR extracted text content
        """
        try:
            print("Starting OCR extraction for PDF")
            images = convert_from_bytes(pdf_bytes, dpi=200, fmt='jpeg')
            print(f"Converted PDF to {len(images)} images for OCR")
            
            text = ""
            for page_num, image in enumerate(images, 1):
                try:
                    page_text = pytesseract.image_to_string(image, lang='spa+eng')
                    if page_text.strip():
                        text += f"\n--- Page {page_num} (OCR) ---\n"
                        text += page_text + "\n"
                        print(f"OCR extracted {len(page_text)} characters from page {page_num}")
                except Exception as e:
                    print(f"OCR failed for page {page_num}: {e}")
                    continue
                    
            print(f"OCR extraction completed: {len(text)} characters extracted")
            return text
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
    
    def download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """
        Download PDF from URL.
        
        Args:
            pdf_url: URL to PDF file
            
        Returns:
            PDF content as bytes or None if download fails
        """
        try:
            response = requests.get(pdf_url, timeout=self.timeout)
            response.raise_for_status()
            print(f"Downloaded PDF: {len(response.content)} bytes")
            return response.content
        except Exception as e:
            print(f"Error downloading PDF {pdf_url}: {e}")
            return None
    
    def extract_text_from_pdf_url(self, pdf_url: str) -> str:
        """
        Download PDF from URL and extract text.
        
        Args:
            pdf_url: URL to PDF file
            
        Returns:
            Extracted text content
        """
        print(f"Processing PDF URL: {pdf_url}")
        
        pdf_bytes = self.download_pdf(pdf_url)
        if not pdf_bytes:
            return ""
        
        # Try direct text extraction first
        text = self.extract_text_direct(pdf_bytes)
        if text.strip():
            print("Direct text extraction succeeded")
            return text
        
        # Fall back to OCR
        print("Direct extraction failed, trying OCR")
        return self.extract_text_ocr(pdf_bytes)
    
    def is_pdf_url(self, url: str) -> bool:
        """
        Check if URL appears to point to a PDF file.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be PDF, False otherwise
        """
        return url.lower().endswith('.pdf') or 'descargar' in url.lower()
