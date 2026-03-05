import requests
import os
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Bs4TenderCrawler:
    def __init__(self, base_url: str, output_dir: str = "outputs"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.portal_name = urlparse(base_url).netloc
        self.output_path = os.path.join(output_dir, "tenders_raw.ndjson")

    # -----------------------
    # ASP.NET Helpers
    # -----------------------

    def extract_hidden_fields(self, soup):
        fields = {}
        for field in ["__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
            tag = soup.find("input", {"name": field})
            if tag:
                fields[field] = tag.get("value", "")
        return fields

    def extract_listing_rows(self, soup):
        tenders = []
        rows = soup.find_all("tr")

        for row in rows:
            link = row.find("a", id=re.compile(r'lnkNumeroProceso'))
            if not link:
                continue

            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            tender = {
                "number": link.get_text(strip=True),
                "description": cells[1].get_text(strip=True),
                "type": cells[2].get_text(strip=True),
                "date": cells[3].get_text(strip=True),
                "status": cells[4].get_text(strip=True),
                "postback_target": self.extract_postback_target(link)
            }

            tenders.append(tender)

        return tenders

    def extract_postback_target(self, link):
        href = link.get("href", "")
        match = re.search(r"__doPostBack\('([^']+)'", href)
        return match.group(1) if match else None

    def simulate_postback(self, hidden_fields, event_target):
        payload = hidden_fields.copy()
        payload["__EVENTTARGET"] = event_target
        payload["__EVENTARGUMENT"] = ""

        response = self.session.post(self.base_url, data=payload)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def extract_detail_text(self, soup):
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    # -----------------------
    # Pipeline
    # -----------------------

    def crawl(self):
        print(f"Opening: {self.base_url}")

        response = self.session.get(self.base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        hidden_fields = self.extract_hidden_fields(soup)
        tenders = self.extract_listing_rows(soup)

        print(f"Found {len(tenders)} tenders")

        with open(self.output_path, "w", encoding="utf-8") as f:

            for tender in tenders:
                try:
                    if not tender["postback_target"]:
                        continue

                    print(f"Processing tender: {tender['number']}")

                    detail_soup = self.simulate_postback(
                        hidden_fields,
                        tender["postback_target"]
                    )

                    detail_text = self.extract_detail_text(detail_soup)

                    record = {
                        "portal": self.portal_name,
                        "number": tender["number"],
                        "description": tender["description"],
                        "type": tender["type"],
                        "date": tender["date"],
                        "status": tender["status"],
                        "detail_text": detail_text,
                        "scraped_at": datetime.utcnow().isoformat()
                    }

                    # Write as NDJSON
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                except Exception as e:
                    print(f"Error processing {tender.get('number')}: {e}")
                    continue

        print(f"\nScraping complete. Data saved to {self.output_path}")


# -----------------------
# Entry Point
# -----------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Usage: python bs4_tender_crawler.py <URL>")
        sys.exit(1)

    crawler = Bs4TenderCrawler(url)
    crawler.crawl()