"""
Crawler strategy implementations for different portal types.
"""

from .base_crawler import ICrawlerStrategy
from .pattern_based_crawler import PatternBasedCrawler
from .table_based_crawler import TableBasedCrawler
from .crawler_factory import CrawlerFactory

__all__ = ['ICrawlerStrategy', 'PatternBasedCrawler', 'TableBasedCrawler', 'CrawlerFactory']
