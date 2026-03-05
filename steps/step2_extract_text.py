import requests
from bs4 import BeautifulSoup
import urllib3

url = "https://comprar.gob.ar/"

# Disable SSL warnings (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, "html.parser")

# Remove scripts and styles
for tag in soup(["script", "style", "noscript"]):
    tag.decompose()

text = soup.get_text(separator=" ")

clean_text = " ".join(text.split())

print(clean_text[:1000])