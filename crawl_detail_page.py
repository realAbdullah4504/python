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
    
    html = page.content()
    print(f"Got HTML content, length: {len(html)}")
    return html

def crawl_details(page, listing_tenders):

    results = []

    for tender in listing_tenders:

        target = tender["details_url"]

        try:

            html = simulate_postback(page, target)

            soup = BeautifulSoup(html, "html.parser")

            text = soup.get_text(" ", strip=True).lower()

            print("Text:", text)

            enriched = {
                **tender,
                "full_text": text
            }

            results.append(enriched)

            print("Processed:", tender["number"])

            # Go back to listing page with better error handling
            try:
                page.go_back()
                page.wait_for_load_state("networkidle")
                # Additional wait to ensure page is fully loaded
                import time
                time.sleep(1)
            except Exception as nav_error:
                print(f"Navigation back failed for {tender['number']}: {nav_error}")
                # Try to navigate to the original URL if go_back fails
                page.goto(source_url)
                page.wait_for_load_state("networkidle")

        except Exception as e:
            print("Failed:", tender["number"], e)

    return results


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


def save_enriched_tenders(tenders, source_url, filename="outputs/enriched_tenders.ndjson"):
    """Save enriched tenders to NDJSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        # Write metadata
        metadata = {"source_url": source_url}
        json.dump(metadata, f, ensure_ascii=False)
        f.write('\n')
        
        for tender in tenders:
            json.dump(tender, f, ensure_ascii=False)
            f.write('\n')
    print(f"Saved {len(tenders)} enriched tenders to {filename}")


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
            
            enriched_tenders = []
            
            for tender in tenders:
                target = tender["details_url"]
                
                # Open new page for each detail
                detail_page = context.new_page()
                detail_page.goto(source_url)
                detail_page.wait_for_load_state("networkidle")
                
                # Execute postback in this tab
                detail_page.evaluate(f"__doPostBack('{target}', '')")
                detail_page.wait_for_load_state("networkidle")
                
                # Extract full text
                html = detail_page.content()
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(" ", strip=True)
                
                tender["full_text"] = text
                enriched_tenders.append(tender)
                
                print(f"Processed: {tender['number']}")
                
                # Close the tab to prevent state issues
                detail_page.close()
            
            # Save results
            save_enriched_tenders(enriched_tenders, source_url)
            
            browser.close()
    else:
        print("No tenders or source URL found in NDJSON file")