import time
from typing import Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from app.config import settings
from app.utils.logger import logger
import logging


class RetryHandler:
    """
    Handles retry logic with exponential backoff for failed push notifications
    """
    
    def __init__(self):
        self.max_attempts = settings.max_retry_attempts
        self.initial_delay = settings.retry_initial_delay
        self.max_delay = settings.retry_max_delay
        self.exponential_base = settings.retry_exponential_base
    
    def with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic
        """
        
        @retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(
                multiplier=self.initial_delay,
                max=self.max_delay,
                exp_base=self.exponential_base
            ),
            retry=retry_if_exception_type(RetryableError),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def _execute():
            return func(*args, **kwargs)
        
        try:
            return _execute()
        except Exception as e:
            logger.error(f"All retry attempts exhausted: {str(e)}")
            raise
    
    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff time for a given attempt
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class RetryableError(Exception):
    """
    Exception type that should trigger retries
    """
    pass


class NonRetryableError(Exception):
    """
    Exception type that should NOT trigger retries (permanent failure)
    """
    pass


retry_handler = RetryHandler()