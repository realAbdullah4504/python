import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

base_url = "https://comprar.gob.ar/"
response = requests.get(base_url, verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
soup = BeautifulSoup(response.text, "html.parser")

links = []
all_links = []

for a in soup.find_all("a", href=True):
    href = a["href"]
    all_links.append(href)
    
    if "detalle" in href.lower() or "tender" in href.lower() or "compra" in href.lower() or "proceso" in href.lower() or "licitacion" in href.lower():
        full_url = urljoin(base_url, href)
        links.append(full_url)

print(f"Total links found: {len(all_links)}")
print(f"Matching links: {len(links)}")
print("Found links:")
for link in links:
    print(link)