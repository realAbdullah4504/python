from ast import arguments
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json

URL = "https://comprar.gob.ar/Compras.aspx?qs=W1HXHGHtH10="



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


def extract_postback_target(link):
    href = link.get("href", "")
    match = re.search(r"__doPostBack\('([^']+)','([^']*)'\)", href)

    if match:
        return match.group(1), match.group(2)

    return None, None


def extract_pagination_links(soup):

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


def extract_listing_rows(soup, page_no=1,pagination_target="",pagination_argument=""):

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
            # "description": cells[1].get_text(strip=True),
            # "type": cells[2].get_text(strip=True),
            # "date": cells[3].get_text(strip=True),
            # "status": cells[4].get_text(strip=True),
            "details_url": target,
            "page_no": page_no,
            "pagination_target":pagination_target,
            "pagination_argument":pagination_argument
        }
        tenders.append(tender)

    return tenders

def existing_tender_numbers():
    """Load existing tender numbers from NDJSON file"""
    existing_numbers = set()
    try:
        with open("outputs/tenders.ndjson", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if "number" in data:
                        existing_numbers.add(data["number"])
    except FileNotFoundError:
        pass
    return existing_numbers

def crawl_all_tenders(url):

    all_tenders = []
    
    seen_tender_numbers = set()
    seen_tender_numbers.update(existing_tender_numbers())

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_load_state("networkidle")

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # page 1 tenders
        tenders = extract_listing_rows(soup, page_no=1)
        for tender in tenders:
            if tender["number"] not in seen_tender_numbers:
                seen_tender_numbers.add(tender["number"])
                all_tenders.append(tender)
                save_tender_to_ndjson(tender)

        current_page = 1

        while True:
            pagination_links = extract_pagination_links(soup)

            next_page_str = str(current_page + 1)
            next_link = None

            for link in pagination_links:
                if link["page_no"] == next_page_str:
                    next_link = link
                    break

            if not next_link:
                for link in pagination_links:
                    if link["page_no"] == "...":
                        match = re.search(r'Page\$(\d+)', link["argument"], re.IGNORECASE)
                        if match:
                            arg_page = int(match.group(1))
                            if arg_page > current_page: # Ensure we are moving forward
                                next_link = link
                                break

            if not next_link:
                print("No more pages found after page", current_page)
                break

            if next_link["page_no"] == "...":
                match = re.search(r'Page\$(\d+)', next_link["argument"], re.IGNORECASE)
                if match:
                    current_page = int(match.group(1))
            else:
                current_page += 1

            print("Crawling page:", current_page)

            html = simulate_postback(
                page,
                next_link["target"],
                next_link["argument"]
            )
            print(next_link["argument"])
            soup = BeautifulSoup(html, "html.parser")

            tenders = extract_listing_rows(soup, page_no=current_page,pagination_target=next_link["target"],pagination_argument=next_link["argument"])
            
            if not tenders:
                break
                
            # Add only new tenders (deduplication)
            new_tenders_count = 0
            for tender in tenders:
                if tender["number"] not in seen_tender_numbers:
                    seen_tender_numbers.add(tender["number"])
                    all_tenders.append(tender)
                    save_tender_to_ndjson(tender)
                    new_tenders_count += 1
            
            print(f"Added {new_tenders_count} new tenders from page {current_page}")
            
            # If no new tenders found, we might be at the end
            if new_tenders_count == 0:
                print("No new tenders found, stopping crawl")
                break

        browser.close()

    return all_tenders


def save_tender_to_ndjson(tender, filename="outputs/tenders.ndjson"):
    """Save a single tender to NDJSON file (append mode)"""
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            json.dump(tender, f, ensure_ascii=False)
            f.write('\n')
                
    except Exception as e:
        print(f"Error saving tender {tender.get('number', 'unknown')}: {e}")
        return False
    
    return True


if __name__ == "__main__":

    tenders = crawl_all_tenders(URL)

    print("Total tenders found:", len(tenders))

    for t in tenders[:5]:
        print(t)