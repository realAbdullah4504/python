"""
Factory for creating details extraction strategies.
"""

from typing import Dict, Type, Optional, List
from crawlers.interfaces import IDetailsStrategy
from crawlers.strategies import PdfDetailsStrategy, PostbackDetailsStrategy


class DetailsFactory:
    """Factory for creating details extraction strategies based on configuration."""
    
    def __init__(self):
        """Initialize details factory with available strategies."""
        self._strategies: Dict[str, Type[IDetailsStrategy]] = {}
        self._register_default_strategies()
        print(f"Initialized DetailsFactory with {len(self._strategies)} strategies")
    
    def _register_default_strategies(self):
        """Register default details extraction strategies."""
        self.register_strategy("pdf", PdfDetailsStrategy)
        self.register_strategy("postback", PostbackDetailsStrategy)
    
    def register_strategy(self, strategy_type: str, strategy_class: Type[IDetailsStrategy]):
        """
        Register a details extraction strategy class.
        
        Args:
            strategy_type: Type identifier for the strategy
            strategy_class: Strategy class implementing IDetailsStrategy
        """
        self._strategies[strategy_type] = strategy_class
        print(f"Registered strategy class: {strategy_type}")
    
    def create_strategy(self, strategy_type: str) -> Optional[IDetailsStrategy]:
        """
        Create an instance of the specified strategy.
        
        Args:
            strategy_type: Type identifier for the strategy
            
        Returns:
            Strategy instance or None if type not found
        """
        if strategy_type not in self._strategies:
            print(f"Unknown strategy type: {strategy_type}")
            return None
        
        try:
            strategy_class = self._strategies[strategy_type]
            strategy_instance = strategy_class()
            print(f"Created strategy instance: {strategy_type}")
            return strategy_instance
        except Exception as e:
            print(f"Error creating strategy {strategy_type}: {e}")
            return None
    
    def create_strategy_for_portal(self, portal_config: Dict) -> Optional[IDetailsStrategy]:
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
        
        return self.create_strategy(details_type)
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy types.
        
        Returns:
            List of strategy type identifiers
        """
        return list(self._strategies.keys())
    
    def can_handle_portal(self, portal_config: Dict) -> bool:
        """
        Check if factory can handle the given portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            True if a suitable strategy exists, False otherwise
        """
        details_config = portal_config.get("config", {}).get("details", {})
        details_type = details_config.get("type")
        
        return details_type in self._strategies


# Global factory instance
_details_factory = DetailsFactory()


def get_details_factory() -> DetailsFactory:
    """
    Get the global details factory instance.
    
    Returns:
        DetailsFactory instance
    """
    return _details_factory


def create_details_strategy(strategy_type: str) -> Optional[IDetailsStrategy]:
    """
    Convenience function to create a details strategy.
    
    Args:
        strategy_type: Type identifier for the strategy
        
    Returns:
        Strategy instance or None if type not found
    """
    return _details_factory.create_strategy(strategy_type)


def create_details_strategy_for_portal(portal_config: Dict) -> Optional[IDetailsStrategy]:
    """
    Convenience function to create a details strategy for a portal.
    
    Args:
        portal_config: Portal configuration dictionary
        
    Returns:
        Strategy instance or None if no suitable strategy found
    """
    return _details_factory.create_strategy_for_portal(portal_config)
