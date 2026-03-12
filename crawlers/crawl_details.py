from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple


with open("config/portals.json") as f:
    config = json.load(f)

URL = config["portals"][0]["url"]


def simulate_postback(page, target, argument=""):
    print(f"Executing postback: target={target}, argument={argument}")

    old_url = page.url

    page.evaluate(f"__doPostBack('{target}','{argument}')")

    try:
        page.wait_for_url(lambda url: url != old_url, timeout=5000)
        print("Navigation happened")
    except Exception as e:
        print(f"No navigation, waiting for DOM update: {e}")
        page.wait_for_load_state("networkidle")

    import time
    time.sleep(1)

    html = page.content()
    real_url = page.url

    return html, real_url


def load_tenders_from_ndjson(filename: str = "outputs/tenders.ndjson") -> List[Dict]:
    """Load tenders from NDJSON file, skipping metadata line"""
    tenders = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Process tender records
        for line in lines:
            if line.strip():
                tenders.append(json.loads(line))
    
    print(f"Loaded {len(tenders)} tenders from {filename}")
    return tenders


def save_enriched_tender(tender: Dict, source_url: str, filename: str = "outputs/enriched_tenders.ndjson") -> None:
    """Save enriched tender to NDJSON file"""
    with open(filename, 'a', encoding='utf-8') as f:
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


def extract_full_text_from_page(html: str) -> str:
    """Extract and clean full text from a page"""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ", strip=True)


def process_single_tender(context, source_url: str, tender: Dict) -> Dict:
    """Process a single tender and return the enriched tender data"""
    target = tender["details_url"]
    argument = tender["pagination_argument"]
    
    # Open new page for each detail
    detail_page = context.new_page()
    detail_page.goto(source_url)
    detail_page.wait_for_load_state("networkidle")
    
    # First navigate to the correct page
    simulate_postback(detail_page, tender["pagination_target"], argument)
    # Then fetch the tender detail
    html, real_url = simulate_postback(detail_page, target)
    print(real_url)
    
    # Extract full text and update tender
    full_text = extract_full_text_from_page(html)
    tender["full_text"] = full_text
    tender["details_url"] = real_url  # Get real URL instead of postback function string
    
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
        try:
            browser.close()
            playwright.stop()
        except Exception as e:
            print(f"Warning: Error during browser cleanup: {e}")
            # Try to force cleanup if normal close fails
            try:
                if 'playwright' in locals():
                    playwright.stop()
            except:
                pass


def main() -> None:
    """Main function to orchestrate the tender processing workflow"""
    # Load tenders and URL from NDJSON
    tenders = load_tenders_from_ndjson()
    
    if not tenders:
        print("No tenders found in NDJSON file")
        return
    
    # Process all tenders, but limit to the number of tenders
    max_tenders = len(tenders)
    process_tenders(tenders, URL, max_tenders)
    print(f"Completed processing {min(len(tenders), max_tenders)} tenders")


if __name__ == "__main__":
    main()