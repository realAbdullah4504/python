"""
Details engine orchestrator for processing tender details.
"""

from typing import Dict, List, Optional, Set
from crawlers.interfaces import IDetailsStrategy
from crawlers.strategies import DetailsFactory
from utils.file_utils import load_tenders_needing_details, update_tender_with_details
from utils.config_resolver import load_config_with_refs, get_portal_config
from collections import defaultdict


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

    def _group_tenders_by_portal(self, tenders: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group tenders by their portal name.
        
        Args:
            tenders: List of tender dictionaries
            
        Returns:
            Dictionary mapping portal names to their tenders
        """
        portal_tenders = defaultdict(list)
        for tender in tenders:
            portal_name = tender.get('portal_name', 'Unknown')
            portal_tenders[portal_name].append(tender)
        return dict(portal_tenders)

    def _process_portal_details(self, portal_name: str, tenders: List[Dict], config: Dict) -> int:
        """
        Process details for tenders from a specific portal using appropriate strategy.
        
        Args:
            portal_name: Name of the portal
            tenders: List of tender dictionaries from this portal
            config: Global configuration containing portal definitions
            
        Returns:
            Number of successfully processed tenders
        """
        try:
            # Find the portal configuration
            portal_config = None
            for portal in config.get("portals", []):
                if portal.get("name") == portal_name:
                    portal_config = get_portal_config(portal)
                    break
            
            if not portal_config:
                print(f"No configuration found for portal: {portal_name}")
                return 0
            
            # Use factory to select appropriate strategy for this portal
            try:
                strategy = self.details_factory.create_crawler(portal_config)
                if not strategy:
                    print(f"No suitable details strategy found for portal: {portal_name}")
                    return 0
                
                print(f"Processing {len(tenders)} tenders from {portal_name} with {strategy.get_strategy_type()} strategy")
                
            except ValueError as e:
                print(f"Error creating details strategy for {portal_name}: {e}")
                return 0
            
            # Process tenders with the selected strategy
            processed_count = 0
            for tender in tenders:
                try:
                    enriched_tender = strategy.process_tender(tender)
                    update_tender_with_details(enriched_tender)
                    processed_count += 1
                    print(f"Successfully processed tender {tender.get('number', 'unknown')} from {portal_name}")
                except Exception as e:
                    print(f"Error processing tender {tender.get('number', 'unknown')} from {portal_name}: {e}")
                    continue
            
            return processed_count
            
        except Exception as e:
            print(f"Error processing details for portal {portal_name}: {e}")
            return 0

    def run(self, max_tenders: int = None) -> Dict[str, int]:
        """
        Run details extraction for all tenders using appropriate strategies.
        
        Args:
            max_tenders: Maximum number of tenders to process (None for all)
            
        Returns:
            Summary statistics of processing results
        """
        tenders = load_tenders_needing_details()
        
        if not tenders:
            print("No tenders found needing details")
            return {"total_tenders": 0, "portals_processed": 0, "processed": 0}
        
        if max_tenders:
            tenders = tenders[:max_tenders]
        
        # Load configuration for strategy selection
        config = load_config_with_refs(self.config_path)
        
        # Group tenders by portal
        portal_tenders = self._group_tenders_by_portal(tenders)
        
        summary = {
            "total_tenders": len(tenders), 
            "portals_processed": 0, 
            "processed": 0
        }

        print(f"Processing {len(tenders)} tenders from {len(portal_tenders)} portals")
        
        # Process each portal with its appropriate strategy
        for portal_name, portal_tender_list in portal_tenders.items():
            print(f"\nProcessing portal: {portal_name} ({len(portal_tender_list)} tenders)")
            
            processed_count = self._process_portal_details(
                portal_name, portal_tender_list, config
            )
            
            # Update summary
            summary["processed"] += processed_count
            summary["portals_processed"] += 1
            
            print(f"Completed {portal_name}: {processed_count}/{len(portal_tender_list)} tenders processed")

        print(f"\nTotal tenders processed across all portals: {summary['processed']}")
        return summary
