"""
Crawler engine orchestrator.
"""

from typing import Dict, List, Set, Optional

from models.tender import TenderModel
from utils.config_resolver import load_config_with_refs, get_portal_config
from utils.file_utils import load_seen_tender_numbers

from crawlers.strategies import CrawlerFactory


class CrawlerEngine:
    """Main orchestrator for crawling workflow."""

    def __init__(
        self,
        config_path: str = "config/portals.json",
        output_path: str = "outputs/tenders.ndjson",
        crawler_factory: Optional[type] = None,
    ):
        self.config_path = config_path
        self.output_path = output_path
        self.crawler_factory = crawler_factory or CrawlerFactory

    def run(self) -> List[TenderModel]:
        """Run crawling for all active portals and return collected tenders."""
        config = load_config_with_refs(self.config_path)
        seen_tender_numbers = load_seen_tender_numbers()

        all_tenders: List[TenderModel] = []

        for portal in config.get("portals", []):
            if not portal.get("active", True):
                print(f"Skipping inactive portal: {portal['name']}")
                continue

            print(f"Processing portal: {portal['name']} ({portal['country']})")
            portal_config = get_portal_config(portal)

            for url in portal.get("listing_urls", []):
                print(f"Crawling URL: {url}")

                tenders = self._crawl_single_url(url, portal_config, seen_tender_numbers)
                all_tenders.extend(tenders)

                print(f"Found {len(tenders)} tenders from {url}")

        print(f"Total tenders found across all portals: {len(all_tenders)}")
        return all_tenders

    def _crawl_single_url(
        self,
        url: str,
        portal_config: Dict,
        seen_tender_numbers: Set[str],
    ) -> List[TenderModel]:
        """Crawl a single URL using strategy selected by the factory."""
        try:
            crawler = self.crawler_factory.create_crawler(portal_config)
            return crawler.crawl(url, portal_config, seen_tender_numbers)
        except ValueError as e:
            print(f"Error creating crawler: {e}")
            return []
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return []
