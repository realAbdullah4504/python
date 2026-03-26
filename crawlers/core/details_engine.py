"""
Details engine orchestrator for processing tender details.
"""

from typing import Dict, List, Optional, Set
from crawlers.interfaces import IDetailsStrategy
from crawlers.strategies import DetailsFactory
from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.config_resolver import load_config_with_refs, get_portal_config


class DetailsEngine:
    """Main orchestrator for details extraction workflow."""

    def __init__(
        self,
        config_path: str = "config/portals.json",
        details_factory: Optional[type] = None,
    ):
        """Initialize details engine with factory and config."""
        self.config_path = config_path
        self.details_factory = details_factory or DetailsFactory

    def _process_portal_details(self, portal_config: Dict, tenders: List[Dict]) -> int:
        """
        Process details for tenders from a specific portal using strategy selected by the factory.
        
        Args:
            portal_config: Portal configuration dictionary
            tenders: List of tender dictionaries to process
            
        Returns:
            Number of successfully processed tenders
        """
        try:
            details_strategy = self.details_factory.create_crawler(portal_config)
            if not details_strategy:
                print("No details strategy available for portal")
                return 0
            
            processed_count = 0
            for tender in tenders:
                try:
                    enriched_tender = details_strategy.process_tender(tender)
                    update_tender_with_details(enriched_tender)
                    processed_count += 1
                    print(f"Successfully processed tender {tender.get('number', 'unknown')}")
                except Exception as e:
                    print(f"Error processing tender {tender.get('number', 'unknown')}: {e}")
                    continue
            
            return processed_count
        except Exception as e:
            print(f"Error creating details strategy: {e}")
            return 0

    def run(self, max_tenders: int = None) -> Dict[str, int]:
        """
        Run details extraction for all active portals and return summary metadata.
        
        Args:
            max_tenders: Maximum number of tenders to process (None for all)
            
        Returns:
            Summary statistics of processing results
        """
        config = load_config_with_refs(self.config_path)
        tenders = load_tenders_needing_details()
        
        if not tenders:
            print("No tenders found needing details")
            return {"total_tenders": 0, "portals_processed": 0, "processed": 0}
        
        if max_tenders:
            tenders = tenders[:max_tenders]
        
        summary = {"total_tenders": len(tenders), "portals_processed": 0, "processed": 0}

        for portal in config.get("portals", []):
            if not portal.get("active", True):
                print(f"Skipping inactive portal: {portal['name']}")
                continue

            print(f"Processing portal: {portal['name']} ({portal['country']})")
            portal_config = get_portal_config(portal)
            
            # Filter tenders for this portal
            portal_tenders = [t for t in tenders if t.get('portal_name') == portal.get('name')]
            
            if not portal_tenders:
                print(f"No tenders found for portal: {portal['name']}")
                continue
            
            print(f"Found {len(portal_tenders)} tenders needing details for {portal['name']}")
            
            # Process portal tenders using factory
            processed_count = self._process_portal_details(portal_config, portal_tenders)
            
            # Update summary
            summary["processed"] += processed_count
            summary["portals_processed"] += 1
            
            print(f"Processed {processed_count}/{len(portal_tenders)} tenders for {portal['name']}")

        print(f"Total tenders processed across all portals: {summary['processed']}")
        return summary
