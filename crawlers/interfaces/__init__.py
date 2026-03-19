"""
Crawler interfaces package.

Contains all interface definitions for the crawler system.
"""

from .crawler_strategy import ICrawlerStrategy
from .pagination_handler import IPaginationHandler
from .detail_crawler_strategy import IDetailCrawlerStrategy

__all__ = [
    'ICrawlerStrategy',
    'IPaginationHandler', 
    'IDetailCrawlerStrategy'
]
