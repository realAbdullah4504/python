"""
Crawler interfaces package.

Contains all interface definitions for the crawler system.
"""

from .crawler_strategy import ICrawlerStrategy
from .pagination_handler import IPaginationHandler
from .details_strategy import IDetailsStrategy

__all__ = [
    'ICrawlerStrategy',
    'IPaginationHandler',
    'IDetailsStrategy',
]
