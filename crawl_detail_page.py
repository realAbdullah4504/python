from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json

KEYWORDS = [
    "licitación",
    "licitacion",
    "concurso",
    "convocatoria",
    "adquisición",
]

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

def score_keywords(text):

    score = 0

    for word in KEYWORDS:
        if word in text:
            score += 1

    return score

def crawl_details(page, listing_tenders):

    results = []

    for tender in listing_tenders:

        target = tender["details_url"]

        try:

            html = simulate_postback(page, target)

            soup = BeautifulSoup(html, "html.parser")

            text = soup.get_text(" ", strip=True).lower()

            print("Text:", text)

            score = score_keywords(text)

            enriched = {
                **tender,
                "keyword_score": score
            }

            results.append(enriched)

            print("Processed:", tender["number"])

            # Go back to listing page
            page.go_back()
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


def save_enriched_tenders(tenders, source_url, filename="enriched_tenders.ndjson"):
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
            page = browser.new_page()
            
            # Go to the main page first using URL from metadata
            page.goto(source_url)
            page.wait_for_load_state("networkidle")
            
            # Crawl details for each tender
            enriched_tenders = crawl_details(page, tenders)
            
            # Save enriched tenders with source URL
            save_enriched_tenders(enriched_tenders, source_url)
            
            print(f"Processed {len(enriched_tenders)} tenders with keyword scores")
            
            browser.close()
    else:
        print("No tenders or source URL found in NDJSON file")