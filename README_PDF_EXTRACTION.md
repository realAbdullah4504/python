# PDF Text Extraction for CSJN Tenders

This script extracts text from PDF documents linked in the CSJN tenders data and adds it as a `fulltext` field to enrich the tender records.

## Features

- **Dual Extraction Method**: First tries native PDF text extraction with PyPDF2, falls back to OCR for scanned PDFs
- **OCR Support**: Uses Tesseract OCR with Spanish and English language support
- **Smart Processing**: Automatically detects when OCR is needed (scanned/image-based PDFs)
- **Backup Creation**: Automatically creates backup of original JSON file before processing
- **Resume Capability**: Can skip already processed tenders
- **Error Handling**: Robust error handling with detailed logging

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

#### Windows
Run the setup script:
```bash
setup_ocr.bat
```

Or install manually:
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and check "Add Tesseract to your PATH"
3. Restart your terminal

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

## Usage

### Basic Usage
```bash
python crawlers/crawl_pdf_details.py
```

### What the script does:
1. Loads tenders from `outputs/tenders_crawled.json`
2. Checks if Tesseract OCR is available
3. For each tender without `fulltext`:
   - Builds PDF URL using the document ID: `https://www.csjn.gov.ar/documentos/descargar?ID=<docId>`
   - Downloads the PDF
   - First tries native text extraction
   - If that fails or produces poor results, uses OCR
   - Adds extracted text as `fulltext` field
   - Adds `pdf_enriched_at` timestamp
4. Saves enriched data back to the same JSON file
5. Creates backup of original file

### Processing Options
- **First run**: Processes all tenders without `fulltext`
- **Reprocessing**: If you run again, it will ask if you want to re-process already enriched tenders
- **Selective processing**: Only processes tenders missing the `fulltext` field

## Output

The script enrichs each tender record with:
```json
{
  "date": "8 de abril de 2026",
  "expediente": "2339/2025",
  "document_type": "Informe",
  "document_number": "2339/2025",
  "category": "Asuntos Administrativos - Adq. y contrataciones de bienes y servicios - Invitaciones en curso - Pliegos y condiciones técnicas",
  "description": "CONTRATACION DEL SERVICIO DE LIMPIEZA INTEGRAL...",
  "portal_name": "CSJN Adquisiciones",
  "source_url": "https://www.csjn.gov.ar/transparencia/adquisiciones-y-contrataciones",
  "created_at": "2026-03-17T10:47:19.884542+00:00",
  "raw_data": {
    "docId": 153536,
    // ... other fields
  },
  "fulltext": "Extracted PDF text content here...",
  "pdf_enriched_at": "2026-03-17T11:30:00.000000+00:00"
}
```

## Configuration

### OCR Settings
- **DPI**: 300 (default, good balance of quality and speed)
- **Languages**: Spanish + English (`spa+eng`)
- **Page Mode**: 6 (Assume uniform block of text)
- **Engine Mode**: 3 (Default OCR engine mode)

### Rate Limiting
- **Delay**: 1 second between requests to be respectful to the server
- **Timeout**: 30 seconds per PDF download

## Troubleshooting

### Tesseract Not Found
```
Warning: Tesseract OCR not found or not properly configured
```
**Solution**: Run the setup script or install Tesseract OCR manually

### PDF Download Fails
```
Error downloading PDF: HTTP Error 404: Not Found
```
**Solution**: The document ID might be invalid or the PDF might not be available

### OCR Produces Poor Results
- Try increasing the DPI in the `extract_text_with_ocr` function
- Check if the PDF quality is very low
- Some scanned documents may have poor OCR accuracy

### Memory Issues
Large PDFs with many pages can consume significant memory during OCR. The script processes pages one at a time to minimize memory usage.

## Dependencies

- `PyPDF2`: Native PDF text extraction
- `pytesseract`: Python wrapper for Tesseract OCR
- `pdf2image`: Convert PDF to images for OCR
- `Pillow`: Image processing
- `requests`: HTTP requests for PDF download

## Notes

- The script automatically detects when OCR is needed
- Spanish language support is configured for better accuracy with Argentine documents
- A backup is created before any modifications
- Processing is rate-limited to avoid overwhelming the server
