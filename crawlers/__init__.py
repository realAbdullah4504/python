"""
Crawlers package for tender data extraction.

This package provides comprehensive crawling capabilities for tender listings and details extraction.
It includes strategies for different portal types and data extraction methods.
"""

# Core components
from .core import CrawlerEngine, DetailsEngine

# Interfaces
from .interfaces import ICrawlerStrategy, IPaginationHandler, IDetailsStrategy

# Strategy implementations
from .strategies import (
    PatternBasedCrawler,
    TableBasedCrawler,
    CrawlerFactory,
    PdfDetailsStrategy,
    PostbackDetailsStrategy,
    DetailsFactory,
    get_details_factory,
    create_details_strategy,
    create_details_strategy_for_portal
)

# Models
from .models import TenderModel, TenderList

# Processors
from .processors import TenderProcessor, DeduplicationService

__all__ = [
    # Core engines
    'CrawlerEngine',
    'DetailsEngine',
    
    # Interfaces
    'ICrawlerStrategy',
    'IPaginationHandler', 
    'IDetailsStrategy',
    
    # Listing strategies
    'PatternBasedCrawler',
    'TableBasedCrawler',
    'CrawlerFactory',
    
    # Details strategies
    'PdfDetailsStrategy',
    'PostbackDetailsStrategy',
    'DetailsFactory',
    'get_details_factory',
    'create_details_strategy',
    'create_details_strategy_for_portal',
    
    # Models
    'TenderModel',
    'TenderList',
    
    # Processors
    'TenderProcessor',
    'DeduplicationService',
]
