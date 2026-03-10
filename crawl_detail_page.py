from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json


def simulate_postback(page, target, argument=""):
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


def load_tenders_from_ndjson(filename="outputs/tenders.ndjson"):
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


def save_enriched_tender(tender, source_url, filename="outputs/enriched_tenders.ndjson"):
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


if __name__ == "__main__":
    # Load tenders and URL from NDJSON
    tenders, source_url = load_tenders_from_ndjson()
    
    if tenders and source_url:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            # Open main listing page
            main_page = context.new_page()
            main_page.goto(source_url)
            main_page.wait_for_load_state("networkidle")
            
            for tender in tenders[:10]:
                target = tender["details_url"]
                
                # Open new page for each detail
                detail_page = context.new_page()
                detail_page.goto(source_url)
                detail_page.wait_for_load_state("networkidle")
                
                # Convert target to element ID and click directly
                elem_id = target.replace('$', '_')
                print(f"Looking for element ID: {elem_id}")
                
                link = detail_page.locator(f"#{elem_id}")
                
                if link.count() > 0:
                    with detail_page.expect_navigation():
                        link.click()
                    print(f"Direct click successful, new URL: {detail_page.url}")
                else:
                    print("Element not found, falling back to postback")
                    detail_page.evaluate(f"__doPostBack('{target}', '')")
                    detail_page.wait_for_load_state("networkidle")
                
                detail_page.wait_for_load_state("networkidle")

                print("Detail page loaded",detail_page.url)
                
                # Extract full text
                html = detail_page.content()
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(" ", strip=True)
                
                tender["full_text"] = text
                tender["details_url"] = detail_page.url # Get real URL instead of postback function string
                
                # Save this tender immediately
                save_enriched_tender(tender, source_url)
                
                print(f"Processed: {tender['number']}")
                
                # Close tab to prevent state issues
                detail_page.close()
            
            browser.close()
    else:
        print("No tenders or source URL found in NDJSON file")