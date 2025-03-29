import requests
import urllib.parse
from bs4 import BeautifulSoup

def get_domain_historical_ip_address(domain):
    # url = f"https://viewdns.info/iphistory/?domain={domain}"
    token = "380548677f9845739b3776d526c3885cb9002e91f8c"
    targetUrl = urllib.parse.quote(f"https://viewdns.info/iphistory/?domain={domain}")
    url = "http://api.scrape.do/?token={}&url={}".format(token, targetUrl)
    response = requests.request("GET", url)

    soup = BeautifulSoup(response.text, 'html.parser')

    # print(f'This is soup {response.text}')

    table = soup.find("table", {"class": "min-w-full bg-white dark:bg-gray-800"})
    print(f'This is table {table}')
    if not table:
        print("No data found.")
        return []

    rows = table.find_all("tr")[1:]
    ips = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 4:
            ips.append({
                'ip': cols[0].text.strip(),
                'location': cols[1].text.strip(),
                'owner': cols[2].text.strip(),
                'last_seen': cols[3].text.strip(),
            })

    return ips

print(get_domain_historical_ip_address("netsoltech.com"))
