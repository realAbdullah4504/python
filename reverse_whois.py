import requests
import urllib.parse
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def reverse_whois(lookup_keyword):
    domains = []
    """
    This function will use ViewDNS to fetch reverse WHOIS info.
    Input: Lookup keyword like email or registrar name.
    Returns a list of domains as strings.
    """
    logger.info(f'Querying reverse whois for {lookup_keyword}')

    token = "380548677f9845739b3776d526c3885cb9002e91f8c"
    target_url = urllib.parse.quote(f"https://viewdns.info/reversewhois/?q={lookup_keyword}")  # Fixed the correct ViewDNS URL
    url = f"http://api.scrape.do/?token={token}&url={target_url}"
    
    response = requests.get(url)  # Simplified request
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", {"class": "min-w-full bg-white dark:bg-gray-800"}) # ViewDNS uses border="1" tables
    if not table:
        logger.warning("No data found.")
        return []

    try:
        for row in table.find_all("tr")[1:]:  # Skip the header row
            columns = row.find_all("td")
            if not columns:
                continue
            dom = columns[0].get_text(strip=True)
            if dom.lower() == "domain name":
                continue
            domains.append(dom)
    except Exception as e:
        logger.error(f'Error while fetching reverse WHOIS info: {e}')

    return domains

print(reverse_whois("netsoltech.com"))