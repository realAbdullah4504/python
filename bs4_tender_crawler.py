import requests
import os
import re
from bs4 import BeautifulSoup
import warnings
from urllib.parse import urljoin
import urllib3

# Suppress BeautifulSoup warnings
try:
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except NameError:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Bs4TenderCrawler:
    def __init__(self, base_url: str, output_dir: str = "outputs"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_listing_rows(self, soup):
        """
        Extract structured data from listing table rows using BeautifulSoup
        """
        tenders = []
        rows = soup.find_all("tr")
        
        for row in rows:
            try:
                # Find the process number link
                link = row.find("a", id=re.compile(r'lnkNumeroProceso'))
                if not link:
                    continue
                
                # Get all cells in the row
                cells = row.find_all("td")
                if len(cells) < 5:
                    continue
                
                # Extract data from cells
                tender_data = {
                    "number": link.get_text(strip=True),
                    "description": cells[1].get_text(strip=True),
                    "type": cells[2].get_text(strip=True),
                    "date": cells[3].get_text(strip=True),
                    "status": cells[4].get_text(strip=True),
                }
                
                tenders.append(tender_data)
                
            except Exception:
                continue
        
        return tenders

    def extract_postback_data(self, soup):
        """
        Extract ASP.NET postback data needed for form submissions
        """
        postback_data = {}
        
        # Extract viewstate
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        if viewstate:
            postback_data["__VIEWSTATE"] = viewstate.get("value", "")
        
        # Extract viewstate generator
        viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        if viewstate_gen:
            postback_data["__VIEWSTATEGENERATOR"] = viewstate_gen.get("value", "")
        
        # Extract event validation
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})
        if event_validation:
            postback_data["__EVENTVALIDATION"] = event_validation.get("value", "")
        
        return postback_data

    def extract_detail_page(self, soup):
        """
        Extract clean text from detail page using BeautifulSoup
        """
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get clean text
        return soup.get_text(separator='\n', strip=True)

    def click_postback_link(self, link_target, postback_data):
        """
        Simulate clicking a postback link by submitting form data
        """
        # Prepare postback data
        data = postback_data.copy()
        data["__EVENTTARGET"] = link_target
        data["__EVENTARGUMENT"] = ""
        
        # Make POST request
        response = self.session.post(self.base_url, data=data)
        response.raise_for_status()
        
        return BeautifulSoup(response.text, "html.parser")

    def process_page(self, page_number):
        """
        Process a single listing page
        """
        print(f"\nProcessing listing page {page_number}")
        
        # Get the listing page
        response = self.session.get(self.base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract postback data
        postback_data = self.extract_postback_data(soup)
        
        # Extract tender information
        tenders = self.extract_listing_rows(soup)
        print(f"Found {len(tenders)} tenders on this page")
        
        # Find all postback links
        postback_links = soup.find_all("a", id=re.compile(r'lnkNumeroProceso'))
        
        for i, (tender_info, link) in enumerate(zip(tenders, postback_links)):
            try:
                # Extract the link target from onclick or href
                onclick = link.get("onclick", "")
                href = link.get("href", "")
                
                # Parse the postback target
                target_match = None
                if onclick:
                    target_match = re.search(r"__doPostBack\('([^']+)'", onclick)
                elif href and "__doPostBack" in href:
                    target_match = re.search(r"__doPostBack\('([^']+)'", href)
                
                if not target_match:
                    print(f"Could not extract target for tender {tender_info['number']}")
                    continue
                
                link_target = target_match.group(1)
                print(f"Opening tender: {tender_info['number']}")
                
                # Click the postback link
                detail_soup = self.click_postback_link(link_target, postback_data)
                
                # Extract detail content
                detail_text = self.extract_detail_page(detail_soup)
                
                # Save to file
                filename = f"{self.output_dir}/page{page_number}_tender_{i+1}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("TENDER SUMMARY\n")
                    f.write("=" * 50 + "\n")
                    for k, v in tender_info.items():
                        f.write(f"{k.upper()}: {v}\n")
                    
                    f.write("\n\nFULL DETAIL PAGE\n")
                    f.write("=" * 50 + "\n")
                    f.write(detail_text)
                
                print(f"Saved: {filename}")
                
            except Exception as e:
                print(f"Error processing tender {tender_info.get('number', 'unknown')}: {e}")
                continue

    def has_next_page(self, soup):
        """
        Check if there's a next page link
        """
        next_link = soup.find("a", string=re.compile(r'Siguiente|Next', re.IGNORECASE))
        return next_link is not None

    def go_to_next_page(self):
        """
        Navigate to next page (this would need to be implemented based on the site's pagination)
        """
        # This is a placeholder - actual implementation depends on how the site handles pagination
        # For many ASP.NET sites, pagination is also done via postback
        return False

    def run(self):
        """
        Main crawler method
        """
        page_number = 1
        
        try:
            self.process_page(page_number)
            
            # For now, just process the first page
            # Implement pagination logic if needed
                
        except Exception as e:
            print(f"Error during crawling: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Usage: python bs4_tender_crawler.py <URL>")
        print("Example: python bs4_tender_crawler.py https://comprar.gob.ar/Compras.aspx?qs=W1HXHGHtH10=")
        sys.exit(1)
    
    crawler = Bs4TenderCrawler(url)
    crawler.run()
