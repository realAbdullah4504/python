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
    def create_crawler(cls, portal_config: Dict) -> Optional[IDetailsStrategy]:
        """
        Create appropriate details strategy based on portal configuration.
        
        Args:
            portal_config: Portal configuration dictionary
            
        Returns:
            IDetailsStrategy instance appropriate for the portal or None
        """
        # First try configuration-driven selection
        details_config = portal_config.get("details", {})
        details_type = details_config.get("type")
        
        if details_type and details_type in cls._strategies:
            try:
                strategy_class = cls._strategies[details_type]
                strategy_instance = strategy_class()
                print(f"Selected {details_type} details strategy from configuration")
                return strategy_instance
            except Exception as e:
                print(f"Error creating configured strategy {details_type}: {e}")
        
        # Fallback to can_handle method
        portal_name = portal_config.get('name')
        mock_tender = {'portal_name': portal_name}
        
        for strategy_type, strategy_class in cls._strategies.items():
            try:
                strategy = strategy_class()
                if strategy.can_handle(mock_tender):
                    print(f"Selected {strategy_type} details strategy via can_handle check")
                    return strategy
            except Exception as e:
                print(f"Error testing strategy {strategy_type}: {e}")
                continue
        
        # If no strategy can handle, return None (details are optional)
        print(f"No suitable details strategy found for portal: {portal_name}")
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
        return cls.create_crawler(portal_config)
    
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
        # Check configuration-driven selection first
        details_config = portal_config.get("details", {})
        details_type = details_config.get("type")
        
        if details_type and details_type in cls._strategies:
            return True
        
        # Fallback to can_handle check
        portal_name = portal_config.get('name')
        if not portal_name:
            return False
            
        mock_tender = {'portal_name': portal_name}
        for strategy_class in cls._strategies.values():
            try:
                strategy = strategy_class()
                if strategy.can_handle(mock_tender):
                    return True
            except Exception:
                continue
        
        return False
