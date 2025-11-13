
"""
Logging utility - Functional approach
"""
import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with consistent formatting
    Pure function - same input produces same configured logger
    
    Args:
        name: Logger name
        level: Logging level
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '[%(filename)s:%(lineno)d] - %(message)s'
        )
    
    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


def create_correlation_logger(correlation_id: str) -> logging.LoggerAdapter:
    """
    Create logger with correlation ID
    Pure function - creates logger adapter with context
    
    Args:
        correlation_id: Correlation ID for request tracking
    
    Returns:
        Logger adapter with correlation context
    """
    logger = logging.getLogger(__name__)
    return logging.LoggerAdapter(
        logger,
        {'correlation_id': correlation_id}
    )


# Logging level mapping - Pure data
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def get_log_level(level_name: str) -> int:
    """
    Get logging level from string
    Pure function
    """
    return LOG_LEVELS.get(level_name.upper(), logging.INFO)


def format_log_message(
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    **context
) -> str:
    """
    Format log message with context
    Pure function
    """
    parts = [f"[{level}]", message]
    
    if correlation_id:
        parts.insert(1, f"[correlation_id={correlation_id}]")
    
    if context:
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        parts.append(f"- {context_str}")
    
    return " ".join(parts)