#!/bin/bash

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo.
echo "Installing Tesseract OCR and Poppler..."

# Check for different package managers
if command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu. Installing with apt..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng poppler-utils
elif command -v yum &> /dev/null; then
    echo "Detected CentOS/RHEL. Installing with yum..."
    sudo yum install -y tesseract tesseract-langpack-spa poppler-utils
elif command -v brew &> /dev/null; then
    echo "Detected macOS. Installing with brew..."
    brew install tesseract tesseract-lang poppler
elif command -v pacman &> /dev/null; then
    echo "Detected Arch Linux. Installing with pacman..."
    sudo pacman -S tesseract tesseract-data-spa poppler
else
    echo "No recognized package manager found."
    echo "Please install Tesseract OCR and Poppler manually:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-spa poppler-utils"
    echo "  CentOS/RHEL: sudo yum install tesseract tesseract-langpack-spa poppler-utils"
    echo "  macOS: brew install tesseract tesseract-lang poppler"
    echo "  Arch: sudo pacman -S tesseract tesseract-data-spa poppler"
    exit 1
fi

echo.
echo "Installation completed!"
echo "You can now run the PDF crawling script."
