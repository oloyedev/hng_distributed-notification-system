import logging
import sys
import json
from datetime import datetime
from app.config import settings


class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
        }
        
        # Add correlation_id if present
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logger(name: str) -> logging.Logger:
    """
    Setup structured JSON logger with correlation IDs
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    logger.addHandler(handler)
    
    return logger


# Create logger instance
logger = setup_logger(settings.service_name)