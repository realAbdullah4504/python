"""
Crawler engine orchestrator.
"""

from typing import Dict, List, Set, Optional

from models.tender import TenderModel
from utils.config_resolver import load_config_with_refs, get_portal_config
from utils.file_utils import load_seen_tender_numbers, save_tenders_to_ndjson, save_seen_tender_numbers

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

    def run(self) -> Dict[str, int]:
        """Run crawling for all active portals and return summary metadata."""
        config = load_config_with_refs(self.config_path)
        seen_tender_numbers = load_seen_tender_numbers()

        summary = {"total_tenders": 0, "portals_processed": 0}

        for portal in config.get("portals", []):
            if not portal.get("active", True):
                print(f"Skipping inactive portal: {portal['name']}")
                continue

            print(f"Processing portal: {portal['name']} ({portal['country']})")
            portal_config = get_portal_config(portal)
            portal_tenders: List[TenderModel] = []

            for url in portal.get("listing_urls", []):
                print(f"Crawling URL: {url}")

                tenders = self._crawl_single_url(url, portal_config, seen_tender_numbers)
                portal_tenders.extend(tenders)

                print(f"Found {len(tenders)} tenders from {url}")

            # Save portal tenders immediately
            self._save_portal_tenders(portal_tenders, portal['name'])
            
            # Update summary
            summary["total_tenders"] += len(portal_tenders)
            summary["portals_processed"] += 1

        print(f"Total tenders found across all portals: {summary['total_tenders']}")
        return summary

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

    def _save_portal_tenders(self, tenders: List[TenderModel], portal_name: str) -> None:
        """Save tenders from a single portal to storage."""
        if not tenders:
            print(f"No tenders to save for portal: {portal_name}")
            return
        
        # Save tenders to NDJSON file
        save_tenders_to_ndjson(tenders)
        
        # Save seen tender numbers for deduplication
        tender_numbers = [tender.docId or tender.number for tender in tenders if tender.docId or tender.number]
        if tender_numbers:
            save_seen_tender_numbers(tender_numbers)
        
        print(f"Saved {len(tenders)} tenders from {portal_name}")
