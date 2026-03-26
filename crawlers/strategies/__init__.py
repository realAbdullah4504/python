"""
Crawler strategy implementations for different portal types.
"""

from ..interfaces.crawler_strategy import ICrawlerStrategy
from .pattern_based_crawler import PatternBasedCrawler
from .table_based_crawler import TableBasedCrawler
from .crawler_factory import CrawlerFactory
from ..interfaces.details_strategy import IDetailsStrategy
from .pdf_details_strategy import PdfDetailsStrategy
from .postback_details_strategy import PostbackDetailsStrategy
from .details_factory import DetailsFactory

__all__ = [
    'ICrawlerStrategy', 
    'PatternBasedCrawler', 
    'TableBasedCrawler', 
    'CrawlerFactory',
    'IDetailsStrategy',
    'PdfDetailsStrategy',
    'PostbackDetailsStrategy',
    'DetailsFactory'
]
