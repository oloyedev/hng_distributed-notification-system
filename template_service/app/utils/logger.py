

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


def create_request_logger(request_id: str) -> logging.LoggerAdapter:
    """
    Create logger with request ID context
    Pure function - creates logger adapter with context
    
    Args:
        request_id: Request ID for tracking
    
    Returns:
        Logger adapter with request context
    """
    logger = logging.getLogger(__name__)
    return logging.LoggerAdapter(
        logger,
        {'request_id': request_id}
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
    context: Optional[dict] = None
) -> str:
    """
    Format log message with context
    Pure function
    """
    parts = [f"[{level}]", message]
    
    if context:
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        parts.append(f"- {context_str}")
    
    return " ".join(parts)


def log_template_operation(
    operation: str,
    template_code: str,
    language: str,
    version: Optional[int] = None
) -> str:
    """
    Format template operation log message
    Pure function
    """
    parts = [
        f"Template {operation}:",
        f"code={template_code}",
        f"language={language}"
    ]
    
    if version:
        parts.append(f"version={version}")
    
    return " ".join(parts)