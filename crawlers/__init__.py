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
    DetailsFactory
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
    
    # Models
    'TenderModel',
    'TenderList',
    
    # Processors
    'TenderProcessor',
    'DeduplicationService',
]
