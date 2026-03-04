import requests
from bs4 import BeautifulSoup
import re
import urllib3

def extract_text(url):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def score_text(text):
    procurement_score = 0
    pci_score = 0

    procurement_keywords = ["licitación", "tender", "RFP"]
    pci_keywords = ["PCI DSS", "4.0", "payment card"]

    for word in procurement_keywords:
        if word.lower() in text.lower():
            procurement_score += 2

    for word in pci_keywords:
        if word.lower() in text.lower():
            pci_score += 1

    return procurement_score, pci_score


url = "https://comprar.gob.ar/"

text = extract_text(url)
# print(text)
proc_score, pci_score = score_text(text)

print("Procurement Score:", proc_score)
print("PCI Score:", pci_score)

if proc_score >= 4 and pci_score >= 1:
    print("🚨 ALERT")
else:
    print("❌ REJECT")