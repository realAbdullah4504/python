from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple


def simulate_postback(page, target: str, argument: str = "") -> Tuple[str, str]:
    """Execute ASP.NET postback and return HTML content and real URL"""
    print(f"Executing postback: target={target}, argument={argument}")

    # Execute the postback
    page.evaluate(f"__doPostBack('{target}','{argument}')")
    
    # Wait for navigation to complete
    page.wait_for_load_state("networkidle")
    
    import time
    time.sleep(1)
    
    # Get current URL after navigation
    real_url = page.url
    print(f"Resolved real URL: {real_url}")
    
    html = page.content()
    return html, real_url


def load_tenders_from_ndjson(filename: str = "outputs/tenders.ndjson") -> Tuple[List[Dict], Optional[str]]:
    """Load tenders from NDJSON file, skipping metadata line"""
    tenders = []
    source_url = None
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Read metadata from first line
        if lines:
            metadata = json.loads(lines[0].strip())
            source_url = metadata.get("source_url")
            print(f"Source URL: {source_url}")
        
        # Skip first line (metadata) and process tender records
        for line in lines[1:]:
            if line.strip():
                tenders.append(json.loads(line))
    
    print(f"Loaded {len(tenders)} tenders from {filename}")
    return tenders, source_url


def save_enriched_tender(tender: Dict, source_url: str, filename: str = "outputs/enriched_tenders.ndjson") -> None:
    """Save enriched tender to NDJSON file"""
    with open(filename, 'a', encoding='utf-8') as f:
        if f.tell() == 0:
            # Write metadata if file is empty
            metadata = {"source_url": source_url}
            json.dump(metadata, f, ensure_ascii=False)
            f.write('\n')
        
        json.dump(tender, f, ensure_ascii=False)
        f.write('\n')
        f.flush()  # Ensure immediate write to disk


def setup_browser_context(headless: bool = True) -> Tuple:
    """Setup and return browser context and main page"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    return playwright, browser, context


def navigate_to_main_page(context, source_url: str):
    """Navigate to the main listing page and return the page object"""
    main_page = context.new_page()
    main_page.goto(source_url)
    main_page.wait_for_load_state("networkidle")
    return main_page


def extract_full_text_from_page(page) -> str:
    """Extract and clean full text from a page"""
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def try_direct_click(detail_page, target: str) -> bool:
    """Try to click element directly by ID, return True if successful"""
    elem_id = target.replace('$', '_')
    print(f"Looking for element ID: {elem_id}")
    
    link = detail_page.locator(f"#{elem_id}")
    
    if link.count() > 0:
        with detail_page.expect_navigation():
            link.click()
        print(f"Direct click successful, new URL: {detail_page.url}")
        return True
    return False


def fallback_to_postback(detail_page, target: str) -> None:
    """Fallback method using postback when direct click fails"""
    print("Element not found, falling back to postback")
    detail_page.evaluate(f"__doPostBack('{target}', '')")
    detail_page.wait_for_load_state("networkidle")


def process_single_tender(context, source_url: str, tender: Dict) -> Dict:
    """Process a single tender and return the enriched tender data"""
    target = tender["details_url"]
    
    # Open new page for each detail
    detail_page = context.new_page()
    detail_page.goto(source_url)
    detail_page.wait_for_load_state("networkidle")
    
    # Try direct click first, fallback to postback
    if not try_direct_click(detail_page, target):
        fallback_to_postback(detail_page, target)
    
    detail_page.wait_for_load_state("networkidle")
    print("Detail page loaded", detail_page.url)
    
    # Extract full text and update tender
    full_text = extract_full_text_from_page(detail_page)
    tender["full_text"] = full_text
    tender["details_url"] = detail_page.url  # Get real URL instead of postback function string
    
    # Close tab to prevent state issues
    detail_page.close()
    
    return tender


def process_tenders(tenders: List[Dict], source_url: str, max_tenders: int = 10) -> None:
    """Process multiple tenders and save enriched data"""
    playwright, browser, context = setup_browser_context()
    
    try:
        for tender in tenders[:max_tenders]:
            try:
                enriched_tender = process_single_tender(context, source_url, tender)
                save_enriched_tender(enriched_tender, source_url)
                print(f"Processed: {enriched_tender['number']}")
            except Exception as e:
                print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                continue
    finally:
        browser.close()
        playwright.stop()


def main() -> None:
    """Main function to orchestrate the tender processing workflow"""
    # Load tenders and URL from NDJSON
    tenders, source_url = load_tenders_from_ndjson()
    
    if not tenders or not source_url:
        print("No tenders or source URL found in NDJSON file")
        return
    
    # Process all tenders, but limit to the number of tenders
    max_tenders = len(tenders)
    process_tenders(tenders, source_url, max_tenders)
    print(f"Completed processing {min(len(tenders), max_tenders)} tenders")


if __name__ == "__main__":
    main(max_tenders=10)