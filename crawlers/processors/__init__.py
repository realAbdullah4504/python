"""
Data processing components for tender crawling.
"""

from .tender_processor import TenderProcessor
from .deduplication_service import DeduplicationService

__all__ = ['TenderProcessor', 'DeduplicationService']
