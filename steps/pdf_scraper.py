#!/usr/bin/env python3
"""
PDF Text Scraper
Downloads and extracts text from PDF URLs with OCR fallback for scanned PDFs
"""

import requests
import PyPDF2
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import sys

def extract_text_from_pdf_url(pdf_url, use_ocr_fallback=True):
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
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        pdf_bytes = response.content
        
        # Try direct text extraction first
        print("Attempting direct text extraction...")
        text = extract_text_direct(pdf_bytes)
        
        if text.strip():
            print(f"Successfully extracted {len(text)} characters via direct extraction")
            return text
        elif use_ocr_fallback:
            print("Direct extraction failed or returned empty text, trying OCR...")
            ocr_text = extract_text_ocr(pdf_bytes)
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

def extract_text_direct(pdf_bytes):
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

def extract_text_ocr(pdf_bytes):
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

def save_text_to_file(text, filename):
    """Save extracted text to a file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Text saved to: {filename}")
    except Exception as e:
        print(f"Error saving text to file: {e}")

def main():
    # PDF URL to scrape
    pdf_url = "https://www.csjn.gov.ar/documentos/descargar?ID=157655"
    
    # Extract text
    extracted_text = extract_text_from_pdf_url(pdf_url)
    
    if extracted_text:
        print(f"\n{'='*50}")
        print("EXTRACTED TEXT PREVIEW:")
        print(f"{'='*50}")
        print(extracted_text[:1000])  # Show first 1000 characters
        if len(extracted_text) > 1000:
            print(f"... (and {len(extracted_text) - 1000} more characters)")
        
        # Save to file
        output_filename = "extracted_text.txt"
        save_text_to_file(extracted_text, output_filename)
        
        print(f"\nTotal characters extracted: {len(extracted_text)}")
    else:
        print("No text could be extracted from the PDF")
        sys.exit(1)

if __name__ == "__main__":
    main()
