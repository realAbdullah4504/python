from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

URL = "https://comprar.gob.ar/Compras.aspx?qs=W1HXHGHtH10="


TABLE_ID = "ctl00_CPH1_GridListaPliegosAperturaProxima"


def simulate_postback(page, target, argument):
    print(f"Executing postback: target={target}, argument={argument}")
    
    # Execute the postback
    page.evaluate(f"__doPostBack('{target}','{argument}')")
    
    # Wait for navigation to complete
    page.wait_for_load_state("load")
    
    # Additional wait for dynamic content
    page.wait_for_selector(f"#{TABLE_ID}", timeout=10000)
    
    import time
    time.sleep(1)
    
    html = page.content()
    print(f"Got HTML content, length: {len(html)}")
    return html


def extract_postback_target(link):
    href = link.get("href", "")
    match = re.search(r"__doPostBack\('([^']+)','([^']+)'\)", href)

    if match:
        return match.group(1), match.group(2)

    return None, None


def extract_pagination_links(soup):

    table = soup.find("table", {"id": TABLE_ID})
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


def extract_listing_rows(soup):

    tenders = []

    table = soup.find("table", {"id": TABLE_ID})
    if not table:
        return tenders

    rows = table.find_all("tr")

    for row in rows:

        if "tr-header" in (row.get("class") or []):
            continue

        if "pagination-gv" in (row.get("class") or []):
            continue

        cells = row.find_all("td")

        if len(cells) < 5:
            continue

        tender = {
            "number": cells[0].get_text(strip=True),
            "description": cells[1].get_text(strip=True),
            "type": cells[2].get_text(strip=True),
            "date": cells[3].get_text(strip=True),
            "status": cells[4].get_text(strip=True)
        }

        tenders.append(tender)

    return tenders


def crawl_all_tenders(url):

    all_tenders = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_load_state("networkidle")

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # page 1 tenders
        tenders = extract_listing_rows(soup)
        all_tenders.extend(tenders)

        pagination_links = extract_pagination_links(soup)

        visited_pages = set()

        for p_link in pagination_links:

            page_no = p_link["page_no"]

            if page_no in visited_pages:
                continue

            visited_pages.add(page_no)

            print("Crawling page:", page_no)

            html = simulate_postback(
                page,
                p_link["target"],
                p_link["argument"]
            )

            soup = BeautifulSoup(html, "html.parser")

            tenders = extract_listing_rows(soup)
            all_tenders.extend(tenders)

        browser.close()

    return all_tenders


if __name__ == "__main__":

    tenders = crawl_all_tenders(URL)

    print("Total tenders:", len(tenders))

    for t in tenders:
        print(t)