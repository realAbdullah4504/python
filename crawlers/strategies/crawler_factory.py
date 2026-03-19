"""
Factory for creating appropriate crawler strategies.
"""

from typing import Dict, Optional
from ..interfaces.crawler_strategy import ICrawlerStrategy
from .pattern_based_crawler import PatternBasedCrawler
from .table_based_crawler import TableBasedCrawler


class CrawlerFactory:
    """Factory for creating crawler strategies based on portal configuration."""
    
    _strategies = {
        'pattern_based': PatternBasedCrawler,
        'table_based': TableBasedCrawler
    }
    
    @classmethod
    def create_crawler(cls, portal_config: Dict) -> ICrawlerStrategy:
        """
        Create appropriate crawler strategy based on portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            ICrawlerStrategy instance appropriate for the portal
            
        Raises:
            ValueError: If no suitable strategy is found
        """
        # Try each strategy to see if it can handle the portal
        for strategy_type, strategy_class in cls._strategies.items():
            strategy = strategy_class()
            if strategy.can_handle(portal_config):
                print(f"Selected {strategy_type} crawler strategy")
                return strategy
        
        # If no strategy can handle, raise error
        raise ValueError(f"No suitable crawler strategy found for portal configuration: {portal_config}")
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type) -> None:
        """
        Register a new crawler strategy.
        
        Args:
            strategy_type: String identifier for the strategy
            strategy_class: Class implementing ICrawlerStrategy
        """
        if not issubclass(strategy_class, ICrawlerStrategy):
            raise ValueError(f"Strategy class must implement ICrawlerStrategy interface")
        
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """
        Get list of available strategy types.
        
        Returns:
            List of available strategy type strings
        """
        return list(cls._strategies.keys())
