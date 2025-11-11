import time
from enum import Enum
from typing import Callable, Any
from app.config import settings
from app.utils.logger import logger


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures exceeded, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pattern to prevent cascading failures
    Protects against Firebase FCM service failures
    """
    
    def __init__(
        self,
        failure_threshold: int = settings.circuit_breaker_failure_threshold,
        timeout: int = settings.circuit_breaker_timeout,
        recovery_timeout: int = settings.circuit_breaker_recovery_timeout,
        name: str = "FCM"
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """
        Reset failure count on successful call
        """
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker {self.name} recovered, moving to CLOSED")
        
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """
        Increment failure count and open circuit if threshold exceeded
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            f"Circuit breaker {self.name} failure {self.failure_count}/{self.failure_threshold}"
        )
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker {self.name} OPENED due to repeated failures")
    
    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt recovery
        """
        if self.last_failure_time is None:
            return False
        
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def get_state(self) -> dict:
        """
        Get current circuit breaker state
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold
        }


class CircuitBreakerOpenError(Exception):
    """
    Raised when circuit breaker is open and rejecting requests
    """
    pass


# Global circuit breaker instance for FCM
fcm_circuit_breaker = CircuitBreaker(name="FCM")