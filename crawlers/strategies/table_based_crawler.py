"""
Table-based crawler strategy for Comprar Gob AR-style portals.
"""

from typing import List, Dict, Set
from bs4 import BeautifulSoup
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, cleanup_browser_resources
from utils.bs4_utils import extract_listing_rows
from crawlers.processors import TenderProcessor, DeduplicationService
from crawlers.pagination import PostbackPaginationHandler
from models.tender import TenderModel
from ..interfaces.crawler_strategy import ICrawlerStrategy


class TableBasedCrawler(ICrawlerStrategy):
    """Crawler strategy for table-based portals (Comprar Gob AR style)."""
    
    def crawl(self, url: str, portal_config: Dict, seen_tender_numbers: Set[str]) -> List[TenderModel]:
        """
        Crawl tenders from a table-based portal.
        
        Args:
            url: The URL to crawl
            portal_config: Configuration for portal
            seen_tender_numbers: Set of already processed tender identifiers
            
        Returns:
            List of TenderModel instances
        """
        portal_name = portal_config.get('name', 'Unknown')
        selectors = portal_config["selectors"]
        column_mapping = portal_config.get("column_mapping", {})
        pagination = portal_config.get("pagination", {})
        all_tenders = []

        # Initialize processor
        deduplication_service = DeduplicationService(seen_tender_numbers)
        tender_processor = TenderProcessor(deduplication_service)

        playwright, browser, context = setup_browser_context()
        
        try:
            page = navigate_to_main_page(context, url)
            current_page = 1
            max_pages = pagination.get("max_pages", 10)  # Get max_pages from config
            
            # Initialize PostbackPaginationHandler
            pagination_handler = PostbackPaginationHandler(page, selectors)
            
            if pagination.get("type") == "postback":
                print(f"Extracted pagination target: {pagination_handler.pagination_target or 'fallback'}")

            while current_page <= max_pages:
                print(f"Crawling page: {current_page}")

                # Handle pagination based on portal config
                if pagination.get("type") == "postback":
                    if current_page > 1:
                        # Navigate to next page using postback handler
                        pagination_response = pagination_handler.fetch_page(url, pagination, current_page)
                        if not pagination_response:
                            break
                    
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")
                else:
                    # For other pagination types, break for now
                    print("Pagination handling not implemented for this type")
                    break

                # Extract tenders from table
                tenders = extract_listing_rows(
                    soup,
                    url,
                    selectors,
                    column_mapping,
                    page_no=current_page
                )

                if not tenders:
                    print("No tenders found, stopping crawl")
                    break

                new_count, new_tenders, existing_found = tender_processor.process_raw_tenders(tenders, portal_name)
                all_tenders.extend(new_tenders)

                print(f"Added {new_count} new tenders from page {current_page}")

                # Stop crawling if existing tender found
                if existing_found:
                    print("Stopping crawl due to existing tender found")
                    break

                if new_count == 0:
                    print("No new tenders found, stopping crawl")
                    break

                current_page += 1

                # Check if we've reached the maximum pages limit
                if current_page > max_pages:
                    print(f"Reached maximum pages limit ({max_pages}), stopping crawl")
                    break

        finally:
            cleanup_browser_resources(playwright, browser)

        return all_tenders
    
    def get_crawler_type(self) -> str:
        """Return the crawler type identifier."""
        return "table_based"
    
    def can_handle(self, portal_config: Dict) -> bool:
        """
        Check if this strategy can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration to check
            
        Returns:
            True if this strategy can handle portal, False otherwise
        """
        return 'selectors' in portal_config and portal_config.get('selectors')
