# Playwright Scraper

A minimal Playwright web scraper for extracting text content from web pages.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Single URL
```bash
python playwright_scraper.py https://example.com
```

### Multiple URLs (modify the script)
```python
import asyncio
from playwright_scraper import scrape_multiple_pages

urls = [
    "https://example.com",
    "https://httpbin.org/html"
]

asyncio.run(scrape_multiple_pages(urls))
```

## Features

- Extracts page title and main text content
- Removes scripts and styles for cleaner output
- Saves content to text files
- Handles multiple URLs
- Error handling and logging
- Headless browser mode

## Output

The scraper creates text files with:
- Original URL
- Page title
- Cleaned text content

Files are named `scraped_content.txt` (single URL) or `scraped_page_N.txt` (multiple URLs).
