"""
Details engine orchestrator for processing tender details.
"""

from typing import Dict, List, Type
from crawlers.interfaces import IDetailsStrategy
from crawlers.strategies import PdfDetailsStrategy, PostbackDetailsStrategy
from utils.file_utils import load_tenders_needing_details, update_tender_with_details


class DetailsEngine:
    """Main orchestrator for details extraction workflow."""
    
    def __init__(self):
        """Initialize details engine with available strategies."""
        self.strategies: Dict[str, IDetailsStrategy] = {}
        self._register_default_strategies()
        print(f"Initialized DetailsEngine with {len(self.strategies)} strategies")
    
    def _register_default_strategies(self):
        """Register default details extraction strategies."""
        self.register_strategy("pdf", PdfDetailsStrategy())
        self.register_strategy("postback", PostbackDetailsStrategy())
    
    def register_strategy(self, strategy_type: str, strategy: IDetailsStrategy):
        """
        Register a details extraction strategy.
        
        Args:
            strategy_type: Type identifier for the strategy
            strategy: Strategy instance implementing IDetailsStrategy
        """
        self.strategies[strategy_type] = strategy
        print(f"Registered strategy: {strategy_type}")
    
    def get_strategy_for_tender(self, tender: Dict) -> IDetailsStrategy:
        """
        Get the appropriate strategy for processing a tender.
        
        Args:
            tender: Tender dictionary
            
        Returns:
            Strategy instance that can handle the tender
        """
        for strategy_type, strategy in self.strategies.items():
            if strategy.can_handle(tender):
                print(f"Selected strategy '{strategy_type}' for tender {tender.get('number', 'unknown')}")
                return strategy
        
        print(f"No strategy found for tender {tender.get('number', 'unknown')}")
        return None
    
    def filter_tenders_by_strategy(self, tenders: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Filter tenders by the strategies that can handle them.
        
        Args:
            tenders: List of tender dictionaries
            
        Returns:
            Dictionary mapping strategy types to lists of tenders they can handle
        """
        strategy_tenders = {}
        
        for strategy_type, strategy in self.strategies.items():
            filtered_tenders = strategy.filter_tenders(tenders)
            if filtered_tenders:
                strategy_tenders[strategy_type] = filtered_tenders
                print(f"Strategy '{strategy_type}' can handle {len(filtered_tenders)} tenders")
        
        return strategy_tenders
    
    def process_tender(self, tender: Dict) -> Dict:
        """
        Process a single tender using the appropriate strategy.
        
        Args:
            tender: Tender dictionary to process
            
        Returns:
            Enriched tender dictionary or original if processing fails
        """
        strategy = self.get_strategy_for_tender(tender)
        if not strategy:
            print(f"No strategy available for tender {tender.get('number', 'unknown')}")
            return tender
        
        return strategy.process_tender(tender)
    
    def process_tenders(self, tenders: List[Dict], max_tenders: int = None) -> int:
        """
        Process multiple tenders and save enriched data.
        
        Args:
            tenders: List of tender dictionaries to process
            max_tenders: Maximum number of tenders to process (None for all)
            
        Returns:
            Number of successfully processed tenders
        """
        if max_tenders:
            tenders = tenders[:max_tenders]
        
        processed_count = 0
        total_tenders = len(tenders)
        print(f"Starting to process {total_tenders} tenders")
        
        for i, tender in enumerate(tenders, 1):
            tender_number = tender.get('number', 'unknown')
            print(f"Processing tender {i}/{total_tenders}: {tender_number}")
            
            try:
                enriched_tender = self.process_tender(tender)
                update_tender_with_details(enriched_tender)
                processed_count += 1
                print(f"Successfully processed and saved tender {tender_number}")
            except Exception as e:
                print(f"Error processing tender {tender_number}: {e}")
                continue
        
        print(f"Completed processing {processed_count}/{total_tenders} tenders successfully")
        return processed_count
    
    def run(self, max_tenders: int = None) -> Dict[str, int]:
        """
        Run the complete details extraction workflow.
        
        Args:
            max_tenders: Maximum number of tenders to process (None for all)
            
        Returns:
            Summary statistics of processing results
        """
        print("Starting details extraction workflow")
        
        # Load tenders needing details
        tenders = load_tenders_needing_details()
        if not tenders:
            print("No tenders found needing details")
            return {"total_tenders": 0, "processed": 0}
        
        print(f"Found {len(tenders)} tenders needing details")
        
        if max_tenders:
            tenders = tenders[:max_tenders]
            print(f"Processing limited to {len(tenders)} tenders")
        
        # Filter tenders by strategy
        strategy_tenders = self.filter_tenders_by_strategy(tenders)
        
        if not strategy_tenders:
            print("No tenders found for available strategies")
            return {"total_tenders": len(tenders), "processed": 0}
        
        # Process tenders by strategy
        total_processed = 0
        for strategy_type, strategy_tender_list in strategy_tenders.items():
            print(f"Processing {len(strategy_tender_list)} tenders with strategy '{strategy_type}'")
            
            processed = self.process_tenders(strategy_tender_list)
            total_processed += processed
        
        summary = {
            "total_tenders": len(tenders),
            "processed": total_processed,
            "strategies_used": list(strategy_tenders.keys())
        }
        
        print(f"Details extraction workflow completed: {summary}")
        return summary
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy types.
        
        Returns:
            List of strategy type identifiers
        """
        return list(self.strategies.keys())
