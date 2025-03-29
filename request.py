import requests
from bs4 import BeautifulSoup

def get_domain_historical_ip_address(domain):
    ips = []
    '''
    This function will use viewdns to fetch historical IP address
    for a domain.
    '''
    print(f'Fetching historical IP address for domain {domain}')
    url = f"https://viewdns.info/iphistory/?domain={domain}"
    headers = {
        "Sec-Ch-Ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"104\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://viewdns.info/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the correct table (ViewDNS usually uses border="1" tables)
    table = soup.find("table", {"class": "min-w-full bg-white dark:bg-gray-800"})  
    print(f'this is table {table}')
    if not table:
        print("No data found.")
        return []
    rows = table.find_all("tr")[1:]  # Skip header row
    for row in rows:
        cols = row.find_all("td")  # Extract all <td> elements
        if len(cols) >= 4:  # Ensure there are enough columns
            ip = cols[0].get_text(strip=True)
            location = cols[1].get_text(strip=True)
            owner = cols[2].get_text(strip=True)
            last_seen = cols[3].get_text(strip=True)

            ips.append({
                'ip': ip,
                'location': location,
                'owner': owner,
                'last_seen': last_seen,
            })
    
    # Print results
    for ip_data in ips:
        print(f"IP: {ip_data['ip']}, Location: {ip_data['location']}, Owner: {ip_data['owner']}, Last Seen: {ip_data['last_seen']}")
    
    return ips

# Run function
get_domain_historical_ip_address("netsoltech.com")
