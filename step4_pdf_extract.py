import pdfplumber

# For local files, read directly instead of using requests
pdf_path = "C:/Users/abdul/Desktop/Why Your AI Keeps Breaking Your Product — Context Engineering Guide.pdf"

with pdfplumber.open(pdf_path) as pdf:
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:  # Regular extraction worked
            full_text += text
        # else:  # Could add OCR fallback here if needed
        #     import pytesseract
        #     from PIL import Image
        #     img = page.to_image()
        #     full_text += pytesseract.image_to_string(img)

print(f"Extracted {len(full_text)} characters")
print("First 1000 characters:")
print(full_text[:1000])