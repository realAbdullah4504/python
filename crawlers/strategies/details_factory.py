"""
Factory for creating details extraction strategies.
"""

from typing import Dict, Optional, List
from crawlers.interfaces import IDetailsStrategy
from crawlers.strategies import PdfDetailsStrategy, PostbackDetailsStrategy


class DetailsFactory:
    """Factory for creating details extraction strategies based on configuration."""
    
    _strategies = {
        'postback': PostbackDetailsStrategy,
        'pdf': PdfDetailsStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str) -> Optional[IDetailsStrategy]:
        """
        Create an instance of the specified strategy.
        
        Args:
            strategy_type: Type identifier for the strategy
            
        Returns:
            Strategy instance or None if type not found
        """
        if strategy_type not in cls._strategies:
            print(f"Unknown strategy type: {strategy_type}")
            return None
        
        try:
            strategy_class = cls._strategies[strategy_type]
            strategy_instance = strategy_class()
            print(f"Created strategy instance: {strategy_type}")
            return strategy_instance
        except Exception as e:
            print(f"Error creating strategy {strategy_type}: {e}")
            return None
    
    @classmethod
    def create_strategy_for_portal(cls, portal_config: Dict) -> Optional[IDetailsStrategy]:
        """
        Create strategy based on portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            Strategy instance or None if no suitable strategy found
        """
        details_config = portal_config.get("config", {}).get("details", {})
        details_type = details_config.get("type")
        
        if not details_type:
            print("No details type specified in portal configuration")
            return None
        
        return cls.create_strategy(details_type)
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type) -> None:
        """
        Register a new details strategy.
        
        Args:
            strategy_type: String identifier for the strategy
            strategy_class: Class implementing IDetailsStrategy
        """
        if not issubclass(strategy_class, IDetailsStrategy):
            raise ValueError("Strategy class must implement IDetailsStrategy interface")
        
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """
        Get list of available strategy types.
        
        Returns:
            List of available strategy type strings
        """
        return list(cls._strategies.keys())
    
    @classmethod
    def can_handle_portal(cls, portal_config: Dict) -> bool:
        """
        Check if factory can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            True if a suitable strategy exists, False otherwise
        """
        details_config = portal_config.get("config", {}).get("details", {})
        details_type = details_config.get("type")
        
        return details_type in cls._strategies
