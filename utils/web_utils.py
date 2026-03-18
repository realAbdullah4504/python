import requests
import re
from typing import Tuple


def extract_csrf_token_and_session(base_url: str) -> Tuple[str, requests.Session]:
    """
    Extract CSRF token and create session with proper cookies.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        # First, visit the main page to get cookies and CSRF token
        response = session.get(base_url, timeout=60)
        response.raise_for_status()
        
        # Extract CSRF token from the page content
        csrf_token = None
        if response.text:
            # Look for the token in the JavaScript
            token_match = re.search(r'token\s*=\s*"([^"]+)"', response.text)
            if token_match:
                csrf_token = token_match.group(1)
                print("Extracted CSRF token: {}".format(csrf_token[:20] + "..."))
        
        if not csrf_token:
            print("Warning: Could not extract CSRF token, using fallback")
            csrf_token = "92f60e65-2bac-42a4-bc27-199443bdedba"  # Fallback
        
        return csrf_token, session
        
    except requests.exceptions.Timeout:
        print("Timeout error extracting CSRF token, using fallback")
        return "92f60e65-2bac-42a4-bc27-199443bdedba", session
    except requests.exceptions.SSLError as e:
        print("SSL error extracting CSRF token: {}, using fallback".format(e))
        return "92f60e65-2bac-42a4-bc27-199443bdedba", session
    except requests.exceptions.ConnectionError as e:
        print("Connection error extracting CSRF token: {}, using fallback".format(e))
        return "92f60e65-2bac-42a4-bc27-199443bdedba", session
    except requests.RequestException as e:
        print("Error extracting CSRF token: {}, using fallback".format(e))
        return "92f60e65-2bac-42a4-bc27-199443bdedba", session
