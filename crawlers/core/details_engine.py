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

    def _process_portal_details(self, tenders: List[Dict]) -> int:
        """
        Process details for tenders using appropriate strategies.
        
        Args:
            tenders: List of tender dictionaries to process
            
        Returns:
            Number of successfully processed tenders
        """
        try:
            processed_count = 0
            
            # Try each strategy to filter and process tenders
            for strategy_type, strategy_class in self.details_factory._strategies.items():
                strategy = strategy_class()
                
                # Filter tenders that this strategy can handle
                filtered_tenders = strategy.filter_tenders(tenders)
                
                if not filtered_tenders:
                    print(f"No tenders for {strategy_type} strategy")
                    continue
                
                print(f"Processing {len(filtered_tenders)} tenders with {strategy_type} strategy")
                
                # Process filtered tenders
                for tender in filtered_tenders:
                    try:
                        enriched_tender = strategy.process_tender(tender)
                        update_tender_with_details(enriched_tender)
                        processed_count += 1
                        print(f"Successfully processed tender {tender.get('number', 'unknown')} with {strategy_type}")
                    except Exception as e:
                        print(f"Error processing tender {tender.get('number', 'unknown')} with {strategy_type}: {e}")
                        continue
            
            return processed_count
        except Exception as e:
            print(f"Error in details processing: {e}")
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
        
        summary = {"total_tenders": len(tenders), "portals_processed": 0, "processed": 0}

        print(f"Processing {len(tenders)} tenders needing details")
        
        # Process all tenders with appropriate strategies
        processed_count = self._process_portal_details(tenders)
        
        # Update summary
        summary["processed"] = processed_count
        summary["portals_processed"] = 1  # We process all strategies in one go

        print(f"Total tenders processed across all strategies: {summary['processed']}")
        return summary
