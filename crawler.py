from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

URL = "https://comprar.gob.ar/Compras.aspx?qs=iouVZE0yWCs="


# TABLE_ID = "ctl00_CPH1_GridListaPliegosAperturaProxima"

def simulate_postback(page, target, argument):
    print(f"Executing postback: target={target}, argument={argument}")
    
    # Execute the postback
    page.evaluate(f"__doPostBack('{target}','{argument}')")
    
    # Wait for navigation to complete
    page.wait_for_load_state("load")
    
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


def extract_listing_rows(soup):

    tenders = []

    table = soup.find("table")
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

        current_page = 1

        while True:
            pagination_links = extract_pagination_links(soup)
            # print(f"Found {len(pagination_links)} pagination links on page {current_page}")
            # for link in pagination_links:
            #     print(f"  Page: '{link['page_no']}' -> {link['argument']}")

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
                print(match.group(1))
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

            soup = BeautifulSoup(html, "html.parser")

            tenders = extract_listing_rows(soup)
            
            if not tenders:
                break
                
            all_tenders.extend(tenders)

        browser.close()

    return all_tenders


if __name__ == "__main__":

    tenders = crawl_all_tenders(URL)

    print("Total tenders:", len(tenders))

    # for t in tenders:
    #     print(t)