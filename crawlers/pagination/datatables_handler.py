"""
DataTables pagination handler for AJAX-based pagination.
"""

from typing import Dict, Any, Optional
from urllib.parse import urljoin
import requests
from .base_handler import IPaginationHandler
from utils.web_utils import extract_csrf_token_and_session


class DataTablesPaginationHandler(IPaginationHandler):
    """
    Handles DataTables AJAX pagination commonly used in modern web applications.
    
    This handler manages pagination through AJAX requests to DataTables endpoints,
    typically used in CSJN-style portals.
    """
    
    def __init__(self, base_url: str):
        """
        Initialize the DataTables pagination handler.
        
        Args:
            base_url: Base URL of the portal
        """
        self.base_url = base_url
        self.session = None
        self.csrf_token = None
    
    def handle_pagination(
        self, 
        page,  # Not used for DataTables (uses AJAX instead)
        current_page: int, 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Handle DataTables pagination via AJAX request.
        
        For DataTables, pagination is handled via AJAX requests rather than
        browser navigation, so this method fetches data for the specified page.
        
        Args:
            page: Playwright page object (not used for DataTables)
            current_page: Current page number to fetch
            pagination_config: Pagination configuration
            
        Returns:
            True if pagination was successful, False if no more data
        """
        # DataTables uses AJAX, so we don't navigate the page
        # The actual pagination logic is in fetch_page_data
        return True
    
    def extract_pagination_info(
        self, 
        html_content: str, 
        pagination_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract pagination information for DataTables.
        
        DataTables pagination info is minimal since it's AJAX-based.
        
        Args:
            html_content: HTML content (not used for DataTables)
            pagination_config: Pagination configuration
            
        Returns:
            Dictionary with pagination configuration
        """
        return {
            'type': 'datatables',
            'endpoint': pagination_config.get('endpoint', ''),
            'page_size': pagination_config.get('page_size', 10),
            'max_pages': pagination_config.get('max_pages', 50)
        }
    
    def is_last_page(
        self, 
        page_data: Dict[str, Any], 
        pagination_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if the current page is the last page for DataTables.
        
        Args:
            page_data: Response data from DataTables AJAX request
            pagination_config: Pagination configuration
            
        Returns:
            True if this is the last page, False otherwise
        """
        if not page_data or not page_data.get('data'):
            return True
        
        data_length = len(page_data['data'])
        page_size = pagination_config.get('page_size', 10)
        
        # If we got fewer results than page size, we're likely on the last page
        return data_length < page_size
    
    def fetch_page_data(
        self, 
        page: int, 
        pagination_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a specific page using DataTables AJAX.
        
        Args:
            page: Page number to fetch
            pagination_config: Pagination configuration
            
        Returns:
            Response data from DataTables API or None if failed
        """
        # Initialize session and CSRF token if needed
        if not self.session or not self.csrf_token:
            self.csrf_token, self.session = extract_csrf_token_and_session(self.base_url)
        
        endpoint = pagination_config['endpoint']
        # Ensure proper URL construction
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = urljoin(self.base_url, endpoint)
        
        print(f"Fetching from URL: {url}")
        
        # DataTables request payload
        payload = {
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
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'X-CSRF-TOKEN': self.csrf_token,
            'Referer': self.base_url,
            'Origin': 'https://www.csjn.gov.ar'
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=60)
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response content: {response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"Timeout error fetching page {page}: Request took too long")
            return None
        except requests.exceptions.SSLError as e:
            print(f"SSL error fetching page {page}: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error fetching page {page}: {e}")
            return None
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return None
