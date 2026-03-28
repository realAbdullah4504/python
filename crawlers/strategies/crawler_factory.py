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
        portal_name = portal_config.get('name', 'Unknown')
        errors = []
        
        # Try each strategy to see if it can handle the portal
        for strategy_type, strategy_class in cls._strategies.items():
            try:
                strategy = strategy_class()
                if strategy.can_handle(portal_config):
                    print(f"Selected {strategy_type} crawler strategy for {portal_name}")
                    return strategy
            except Exception as e:
                errors.append(f"{strategy_type}: {e}")
                continue
        
        # If no strategy can handle, raise error with details
        error_msg = f"No suitable crawler strategy found for portal '{portal_name}'"
        if errors:
            error_msg += f". Errors encountered: {'; '.join(errors)}"
        
        raise ValueError(error_msg)
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type) -> None:
        """
        Register a new crawler strategy.
        
        Args:
            strategy_type: String identifier for the strategy
            strategy_class: Class implementing ICrawlerStrategy
        """
        if not issubclass(strategy_class, ICrawlerStrategy):
            raise ValueError("Strategy class must implement ICrawlerStrategy interface")
        
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def can_handle_portal(cls, portal_config: Dict) -> bool:
        """
        Check if factory can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            True if a suitable strategy exists, False otherwise
        """
        for strategy_class in cls._strategies.values():
            try:
                strategy = strategy_class()
                if strategy.can_handle(portal_config):
                    return True
            except Exception:
                continue
        
        return False
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """
        Get list of available strategy types.
        
        Returns:
            List of available strategy type strings
        """
        return list(cls._strategies.keys())
