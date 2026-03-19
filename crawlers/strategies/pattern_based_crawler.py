"""
Pattern-based crawler strategy for CSJN-style portals.
"""

from typing import List, Dict, Set
from bs4 import BeautifulSoup
from utils.playwright_utils import open_page
from utils.bs4_utils import extract_tender_blocks, parse_tender_block, format_tender_item
from crawlers.processors import TenderProcessor, DeduplicationService
from crawlers.pagination import DataTablesPaginationHandler
from models.tender import TenderModel
from ..interfaces.crawler_strategy import ICrawlerStrategy


class PatternBasedCrawler(ICrawlerStrategy):
    """Crawler strategy for pattern-based portals (CSJN style)."""
    
    def crawl(self, url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
        """
        Crawl tenders from a pattern-based portal.
        
        Args:
            url: The URL to crawl
            portal_config: Configuration for portal
            seen_tender_numbers: Set of already processed tender identifiers
            
        Returns:
            List of TenderModel instances
        """
        patterns = portal_config.get('patterns', {})
        portal_name = portal_config.get('name', 'Unknown')
        all_tenders = []
        
        # Initialize processor
        deduplication_service = DeduplicationService(seen_tender_numbers)
        tender_processor = TenderProcessor(deduplication_service)
        
        if not patterns:
            raise ValueError("No patterns found in configuration for URL: {}".format(url))
        
        # Check if portal has pagination configuration
        if portal_config.get('pagination', {}).get('type') == 'datatables':
            all_tenders.extend(self._crawl_with_datatables(
                url, portal_config, portal_name, tender_processor
            ))
        else:
            all_tenders.extend(self._crawl_static_page(
                url, portal_config, portal_name, tender_processor
            ))
        
        return all_tenders
    
    def get_crawler_type(self) -> str:
        """Return the crawler type identifier."""
        return "pattern_based"
    
    def can_handle(self, portal_config: Dict) -> bool:
        """
        Check if this strategy can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration to check
            
        Returns:
            True if this strategy can handle portal, False otherwise
        """
        return 'patterns' in portal_config and portal_config.get('patterns')
    
    def _crawl_with_datatables(self, url: str, portal_config: Dict, portal_name: str, 
                           tender_processor: TenderProcessor) -> List[TenderModel]:
        """Handle DataTables pagination for pattern-based crawler."""
        print("Using DataTables pagination...")
        parsed_tenders = []
        pagination_config = portal_config.get('pagination', {})
        max_pages = pagination_config.get('max_pages', 50)
        
        # Initialize DataTables pagination handler
        pagination_handler = DataTablesPaginationHandler()
        patterns = portal_config.get('patterns', {})
        
        for page in range(1, max_pages + 1):
            print("Fetching page {}...".format(page))
            
            response_data = pagination_handler.fetch_page(url, pagination_config, page)
            if not response_data:
                break
            
            # Check if we have data
            data_items = pagination_handler.extract_data_from_response(response_data)
            if not data_items or len(data_items) == 0:
                print("No more data found, stopping pagination.")
                break
            
            # Parse each tender from response
            page_tenders = []
            for item in data_items:
                # Convert DataTables item to text format for parsing
                tender_text = format_tender_item(item)
                tender = parse_tender_block(tender_text, patterns)
                
                if tender:
                    page_tenders.append(tender)
            
            # Process page tenders with deduplication
            new_count, new_generic_tenders, existing_found = tender_processor.process_raw_tenders(
                page_tenders, portal_name, url
            )
            parsed_tenders.extend(new_generic_tenders)
            
            print("Added {} new tenders from page {}".format(new_count, page))
            
            # Stop crawling if existing tender found
            if existing_found:
                print("Stopping crawl due to existing tender found")
                break
            
            # Check if this is the last page
            if not pagination_handler.has_more_data(response_data, pagination_config['page_size']):
                print("Reached last page.")
                break
        
        return parsed_tenders
    
    def _crawl_static_page(self, url: str, portal_config: Dict, portal_name: str,
                         tender_processor: TenderProcessor) -> List[TenderModel]:
        """Handle static page parsing for pattern-based crawler."""
        print("Using static page parsing...")
        patterns = portal_config.get('patterns', {})
        
        # Fallback to original method
        page = open_page(url)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract all text content
        text_content = soup.get_text()
        
        # Split into tender blocks using patterns
        tender_blocks = extract_tender_blocks(text_content, patterns)
        
        # Parse each tender block
        parsed_tenders = []
        for block in tender_blocks:
            tender = parse_tender_block(block, patterns)
            if tender:
                parsed_tenders.append(tender)
        
        # Process tenders with deduplication
        new_count, new_generic_tenders, existing_found = tender_processor.process_raw_tenders(
            parsed_tenders, portal_name, url
        )
        
        print("Added {} new tenders from static page".format(new_count))
        
        # Stop crawling if existing tender found
        if existing_found:
            print("Stopping crawl due to existing tender found")
        
        return new_generic_tenders
