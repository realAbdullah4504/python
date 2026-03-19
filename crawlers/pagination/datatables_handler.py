"""
DataTables pagination handler for AJAX-based pagination.
"""

from typing import Dict, Any, Optional
from urllib.parse import urljoin
import requests
from utils.web_utils import extract_csrf_token_and_session
from .base_handler import IPaginationHandler


class DataTablesPaginationHandler(IPaginationHandler):
    """Handles DataTables AJAX pagination."""
    
    def fetch_page(self, base_url: str, pagination_config: Dict, page: int = 1, 
                   session: Optional[requests.Session] = None, 
                   csrf_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a single page of data from DataTables API.
        """
        if not session or not csrf_token:
            csrf_token, session = extract_csrf_token_and_session(base_url)
        
        endpoint = pagination_config['endpoint']
        # Ensure proper URL construction
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = urljoin(base_url, endpoint)
        
        print("Fetching from URL: {}".format(url))
        
        # DataTables request payload
        payload = self._build_payload(page, pagination_config)
        
        headers = self._build_headers(csrf_token, base_url)
        
        try:
            response = session.post(url, json=payload, headers=headers, timeout=60)
            print("Response status: {}".format(response.status_code))
            if response.status_code != 200:
                print("Response content: {}".format(response.text[:500]))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Timeout error fetching page {}: Request took too long".format(page))
            return None
        except requests.exceptions.SSLError as e:
            print("SSL error fetching page {}: {}".format(page, e))
            return None
        except requests.exceptions.ConnectionError as e:
            print("Connection error fetching page {}: {}".format(page, e))
            return None
        except requests.RequestException as e:
            print("Error fetching page {}: {}".format(page, e))
            return None
    
    def get_pagination_type(self) -> str:
        """Return the pagination type identifier."""
        return "datatables"
    
    def has_more_data(self, response_data: Dict[str, Any], page_size: int) -> bool:
        """Check if there's more data available."""
        data = response_data.get('data', [])
        return len(data) > 0 and len(data) >= page_size
    
    def extract_data_from_response(self, response_data: Dict[str, Any]) -> list:
        """Extract the actual data items from DataTables response."""
        return response_data.get('data', [])
    
    def _build_payload(self, page: int, pagination_config: Dict) -> Dict[str, Any]:
        """Build the DataTables request payload."""
        return {
            "draw": page,
            "start": (page - 1) * pagination_config['page_size'],
            "length": pagination_config['page_size'],
            "search": {"value": "", "regex": False},
            "order": [{"column": 0, "dir": "desc"}],
            "columns": [{"data": "0", "name": "", "searchable": True, "orderable": False, "search": {"value": "", "regex": False}}],
            "formBusqueda": {
                "qa": "",
                "nroDoca": "",
                "anioDoca": "",
                "temaBase": "K76",
                "temaPrincipal_a": "K76",
                "subTema_a": "",
                "fechaDesde_a": "",
                "fechaHasta_a": ""
            }
        }
    
    def _build_headers(self, csrf_token: str, base_url: str) -> Dict[str, str]:
        """Build the request headers."""
        return {
            'Content-Type': 'application/json; charset=utf-8',
            'X-CSRF-TOKEN': csrf_token,
            'Referer': base_url,
            'Origin': 'https://www.csjn.gov.ar'
        }
