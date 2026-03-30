"""
Crawler engine orchestrator.
"""

from typing import Dict, List, Set, Optional

from models.tender import TenderModel
from utils.config_resolver import load_config_with_refs, get_portal_config
from utils.file_utils import load_seen_tender_numbers, save_tenders_to_ndjson, save_seen_tender_numbers
from utils.logger import get_logger, log_phase_start, log_phase_end, log_portal_processing, log_tender_extraction, log_error_with_context, log_skip_with_reason

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
        self.logger = get_logger(__name__, "listing")

    def run(self) -> Dict[str, int]:
        """Run crawling for all active portals and return summary metadata."""
        log_phase_start(self.logger, "listing")
        
        try:
            config = load_config_with_refs(self.config_path)
            seen_tender_numbers = load_seen_tender_numbers()

            summary = {"total_tenders": 0, "portals_processed": 0}

            for portal in config.get("portals", []):
                if not portal.get("active", True):
                    log_skip_with_reason(self.logger, f"portal {portal['name']}", "inactive")
                    continue

                log_portal_processing(self.logger, portal['name'], portal['country'], len(portal.get("listing_urls", [])))
                portal_config = get_portal_config(portal)
                portal_tenders: List[TenderModel] = []

                for url in portal.get("listing_urls", []):
                    self.logger.info(f"Crawling URL: {url}")

                    tenders = self._crawl_single_url(url, portal_config, seen_tender_numbers)
                    portal_tenders.extend(tenders)

                    log_tender_extraction(self.logger, url, len(tenders))

                # Save portal tenders immediately
                self._save_portal_tenders(portal_tenders, portal['name'])
                
                # Update summary
                summary["total_tenders"] += len(portal_tenders)
                summary["portals_processed"] += 1

            self.logger.info(f"Total tenders found across all portals: {summary['total_tenders']}")
            log_phase_end(self.logger, "listing", summary)
            return summary
            
        except Exception as e:
            log_error_with_context(self.logger, e, "listing engine run")
            raise

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
            log_error_with_context(self.logger, e, f"creating crawler for {url}")
            return []
        except Exception as e:
            log_error_with_context(self.logger, e, f"crawling {url}")
            return []

    def _save_portal_tenders(self, tenders: List[TenderModel], portal_name: str) -> None:
        """Save tenders from a single portal to storage."""
        if not tenders:
            log_skip_with_reason(self.logger, f"portal {portal_name}", "no tenders to save")
            return
        
        # Save tenders to NDJSON file
        save_tenders_to_ndjson(tenders)
        
        # Save seen tender numbers for deduplication
        tender_numbers = [tender.docId or tender.number for tender in tenders if tender.docId or tender.number]
        if tender_numbers:
            save_seen_tender_numbers(tender_numbers)
        
        self.logger.info(f"Saved {len(tenders)} tenders from {portal_name}")
