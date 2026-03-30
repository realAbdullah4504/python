"""
Centralized logging utility for the tender crawling pipeline.
Provides consistent logging configuration and helper functions.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        log_file: Optional log file path
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Fix Unicode encoding for Windows console
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str, phase: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with phase-specific configuration.
    
    Args:
        name: Logger name (usually __name__)
        phase: Phase name for context (listing, details, pci_analysis)
    
    Returns:
        Configured logger instance
    """
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{phase or 'pipeline'}_{timestamp}.log" if phase else None
    
    return setup_logger(
        name=name,
        level=logging.INFO,
        log_file=log_file
    )


def log_phase_start(logger: logging.Logger, phase_name: str, context: Optional[dict] = None):
    """Log the start of a phase with context."""
    logger.info(f"Starting {phase_name} phase")
    if context:
        for key, value in context.items():
            logger.info(f"  Context - {key}: {value}")


def log_phase_end(logger: logging.Logger, phase_name: str, summary: Optional[dict] = None):
    """Log the end of a phase with summary."""
    logger.info(f"Completed {phase_name} phase")
    if summary:
        for key, value in summary.items():
            logger.info(f"  Summary - {key}: {value}")


def log_portal_processing(logger: logging.Logger, portal_name: str, country: str, url_count: int):
    """Log portal processing start."""
    logger.info(f"Processing portal: {portal_name} ({country}) - {url_count} URLs")


def log_tender_extraction(logger: logging.Logger, url: str, tender_count: int):
    """Log tender extraction results."""
    logger.info(f"Extracted {tender_count} tenders from {url}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str):
    """Log error with context information."""
    logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}")


def log_skip_with_reason(logger: logging.Logger, item: str, reason: str):
    """Log skipped items with reasons."""
    logger.warning(f"Skipped {item}: {reason}")
