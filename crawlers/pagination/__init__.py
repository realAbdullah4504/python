"""
Pagination handling components for different pagination mechanisms.
"""

from ..interfaces.pagination_handler import IPaginationHandler
from .datatables_handler import DataTablesPaginationHandler
from .postback_handler import PostbackPaginationHandler

__all__ = ['IPaginationHandler', 'DataTablesPaginationHandler', 'PostbackPaginationHandler']
