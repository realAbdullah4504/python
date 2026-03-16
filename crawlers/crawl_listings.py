from ast import arguments
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime

def simulate_postback(page, target: str, argument: str = "") -> str:
    """Simulate a postback event on the page"""
    print(f"Executing postback: target={target}, argument={argument}")

    old_url = page.url

    page.evaluate(f"__doPostBack('{target}','{argument}')")

    try:
        page.wait_for_url(lambda url: url != old_url, timeout=5000)
        print("Navigation happened")
    except Exception as e:
        print(f"No navigation, waiting for DOM update: {e}")
        page.wait_for_load_state("networkidle")

    return page.content()


def extract_postback_target(link) -> Tuple[Optional[str], Optional[str]]:
    """Extract postback target and argument from a link element"""
    href = link.get("href", "")
    match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", href)

    if match:
        return match.group(1), match.group(2)

    return None, None


def extract_pagination_links(soup: BeautifulSoup) -> List[Dict]:
    """Extract pagination links from the page"""
    table = soup.find("table")
    if not table:
        return []

    pagination_links = []

    for row in table.find_all("tr", class_="pagination-gv"):
        for link in row.find_all("a"):

            target, argument = extract_postback_target(link)

            if target:
                pagination_links.append({
                    "page_no": link.get_text(strip=True),
                    "target": target,
                    "argument": argument
                })

    return pagination_links


def extract_listing_rows(soup: BeautifulSoup,url:str, page_no: int = 1, pagination_target: str = "", pagination_argument: str = "") -> List[Dict]:
    """Extract tender listing rows from the page"""
    tenders = []

    table = soup.find("table")
    if not table:
        return tenders

    tbody = table.find("tbody")
    if not tbody:
        return tenders

    rows = tbody.find_all("tr", recursive=False)

    for row in rows:

        if "tr-header" in (row.get("class") or []):
            continue

        if "pagination-gv" in (row.get("class") or []):
            continue

        cells = row.find_all("td")

        if len(cells) < 5:
            continue

        link = cells[0].find("a")
        target, _ = extract_postback_target(link) if link else (None, None)
        # print(link, target)
        tender = {
            "number": cells[0].get_text(strip=True),
            "description": cells[1].get_text(strip=True),
            "type": cells[2].get_text(strip=True),
            "date": cells[3].get_text(strip=True),
            "status": cells[4].get_text(strip=True),
            "url":url,
            "details_url": target,
            "page_no": page_no,
            "pagination_target": pagination_target,
            "pagination_argument": pagination_argument
        }
        tenders.append(tender)

    return tenders


def setup_browser_context(headless: bool = True) -> Tuple:
    """Setup and return browser context and main page"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    return playwright, browser, context


def navigate_to_main_page(context, url: str):
    """Navigate to the main listing page and return the page object"""
    page = context.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page

def load_existing_tender_numbers(filename: str = "outputs/tenders.ndjson") -> Set[str]:
    """Load existing tender numbers from NDJSON file"""
    existing_numbers = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if "number" in data:
                        existing_numbers.add(data["number"])
    except FileNotFoundError:
        pass
    return existing_numbers

def save_tender_to_ndjson(tender: Dict, filename: str = "outputs/tenders.ndjson") -> bool:
    """Save a single tender to NDJSON file (append mode)"""
    try:
        # Add creation date time to the tender
        tender["created_at"] = datetime.now().isoformat()
        with open(filename, 'a', encoding='utf-8') as f:
            json.dump(tender, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        print(f"Error saving tender {tender.get('number', 'unknown')}: {e}")
        return False
    return True


def process_page_tenders(tenders: List[Dict], seen_tender_numbers: Set[str]) -> int:
    """Process tenders from a page and return count of new tenders"""
    new_count = 0
    for tender in tenders:
        if tender["number"] not in seen_tender_numbers:
            seen_tender_numbers.add(tender["number"])
            save_tender_to_ndjson(tender)
            new_count += 1
    return new_count


def find_next_pagination_link(pagination_links: List[Dict], current_page: int) -> Optional[Dict]:
    """Find the next pagination link to navigate to"""
    next_page_str = str(current_page + 1)
    
    # First try to find exact next page
    for link in pagination_links:
        if link["page_no"] == next_page_str:
            return link
    
    # Then try to find ellipsis with higher page number
    for link in pagination_links:
        if link["page_no"] == "...":
            match = re.search(r'Page\$(\d+)', link["argument"], re.IGNORECASE)
            if match:
                arg_page = int(match.group(1))
                if arg_page > current_page:
                    return link
    
    return None


def cleanup_browser_resources(playwright, browser) -> None:
    """Clean up browser resources with proper error handling"""
    try:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
    except Exception as e:
        print(f"Warning: Error during browser cleanup: {e}")
        # Try to force cleanup if normal close fails
        try:
            if 'playwright' in locals():
                playwright.stop()
        except RuntimeError:
            pass


def crawl_all_tenders(url: str) -> List[Dict]:
    """Crawl all tenders from the given URL"""
    all_tenders = []
    seen_tender_numbers = load_existing_tender_numbers()

    playwright, browser, context = setup_browser_context()
    
    try:
        page = navigate_to_main_page(context, url)
        
        # Process first page
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        tenders = extract_listing_rows(soup,url, page_no=1)
        
        new_count = process_page_tenders(tenders, seen_tender_numbers)
        all_tenders.extend([t for t in tenders if t["number"] in seen_tender_numbers])
        print(f"Added {new_count} new tenders from page 1")
        
        current_page = 1
        
        # while True:
        #     pagination_links = extract_pagination_links(soup)
        #     next_link = find_next_pagination_link(pagination_links, current_page)
            
        #     if not next_link:
        #         print(f"No more pages found after page {current_page}")
        #         break
            
        #     # Update current page number
        #     if next_link["page_no"] == "...":
        #         match = re.search(r'Page\$(\d+)', next_link["argument"], re.IGNORECASE)
        #         if match:
        #             current_page = int(match.group(1))
        #     else:
        #         current_page += 1
            
        #     print(f"Crawling page: {current_page}")
            
        #     # Navigate to next page
        #     html = simulate_postback(page, next_link["target"], next_link["argument"])
        #     soup = BeautifulSoup(html, "html.parser")
            
        #     tenders = extract_listing_rows(
        #         soup,
        #         url,
        #         page_no=current_page,
        #         pagination_target=next_link["target"],
        #         pagination_argument=next_link["argument"]
        #     )
            
        #     if not tenders:
        #         break
            
        #     new_count = process_page_tenders(tenders, seen_tender_numbers)
        #     all_tenders.extend([t for t in tenders if t["number"] in seen_tender_numbers])
        #     print(f"Added {new_count} new tenders from page {current_page}")
            
        #     if new_count == 0:
        #         print("No new tenders found, stopping crawl")
        #         break
    
    finally:
        cleanup_browser_resources(playwright, browser)
    
    return all_tenders


def main() -> None:
    """Main function to orchestrate the tender crawling workflow"""
    tenders = crawl_all_tenders(URL)
    print(f"Total tenders found: {len(tenders)}")
    
    # Display first 5 tenders
    for t in tenders[:5]:
        print(t)


if __name__ == "__main__":
    main()