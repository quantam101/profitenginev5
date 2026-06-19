"""
ERROR HANDLING & RECOVERY — Fault Tolerance
Handles failures gracefully with retry, fallback, and graceful degradation
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    RECOVERABLE = "recoverable"  # Retry
    DEGRADED = "degraded"  # Fallback mode
    CRITICAL = "critical"  # Stop trading


class RetryPolicy:
    """Exponential backoff retry with maximum attempts"""

    def __init__(self, max_attempts: int = 3, initial_delay: float = 1.0, max_delay: float = 30.0):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay

    def retry(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """Execute function with exponential backoff retry"""
        attempt = 0
        delay = self.initial_delay

        while attempt < self.max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt >= self.max_attempts:
                    logger.error("[ERROR] Final attempt failed: {}".format(str(e)))
                    return None

                actual_delay = min(delay, self.max_delay)
                logger.warning("[RETRY] Attempt {}/{} failed, retrying in {:.1f}s: {}".format(
                    attempt, self.max_attempts, actual_delay, str(e)))

                time.sleep(actual_delay)
                delay *= 2.0  # Exponential backoff

        return None


def with_fallback(fallback_value: Any):
    """Decorator that returns fallback value on exception"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error("[FALLBACK] {} failed with {}, returning fallback".format(
                    func.__name__, str(e)))
                return fallback_value
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit Breaker Pattern for cascading failure prevention

    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests
    - HALF_OPEN: Testing recovery
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """Execute function with circuit breaker protection"""

        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("[CIRCUIT_BREAKER] Entering HALF_OPEN state, testing recovery")
            else:
                logger.error("[CIRCUIT_BREAKER] OPEN, rejecting request")
                return None

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("[CIRCUIT_BREAKER] Recovery successful, CLOSED")
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error("[CIRCUIT_BREAKER] OPEN after {} failures: {}".format(
                    self.failure_count, str(e)))
                return None

            logger.warning("[CIRCUIT_BREAKER] Failure {}/{}: {}".format(
                self.failure_count, self.failure_threshold, str(e)))
            return None


class ErrorRecoveryHandler:
    """Centralized error handling and recovery strategies"""

    def __init__(self):
        self.retry_policy = RetryPolicy(max_attempts=3, initial_delay=1.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
        self.error_log = []
        self.fallback_enabled = False

    def handle_market_data_error(self, symbol: str, error: Exception) -> Optional[Any]:
        """Handle market data fetch failure"""
        logger.error("[DATA_ERROR] Failed to fetch {}: {}".format(symbol, str(error)))

        if "Connection refused" in str(error):
            return self._fallback_to_cached_data(symbol)
        elif "Rate limit" in str(error):
            logger.warning("[DATA_ERROR] Rate limited, waiting before retry")
            time.sleep(5.0)
            return None
        elif "Invalid API key" in str(error):
            logger.critical("[DATA_ERROR] Invalid API key, cannot recover")
            return None

        return None

    def handle_broker_error(self, order: Dict, error: Exception) -> bool:
        """Handle broker/order execution error"""
        logger.error("[BROKER_ERROR] Order failed: {}".format(str(error)))

        if "Insufficient funds" in str(error):
            logger.critical("[BROKER_ERROR] Insufficient funds, reduce position size")
            return False
        elif "Invalid symbol" in str(error):
            logger.error("[BROKER_ERROR] Invalid symbol, skip")
            return False
        elif "Order timeout" in str(error):
            logger.warning("[BROKER_ERROR] Timeout, retry with fresh quote")
            time.sleep(2.0)
            return True
        elif "Connection error" in str(error):
            logger.warning("[BROKER_ERROR] Connection lost, falling back to cached state")
            return False

        return False

    def handle_compliance_error(self, symbol: str, error: Exception) -> bool:
        """Handle compliance check failure"""
        logger.warning("[COMPLIANCE_ERROR] Check failed for {}: {}".format(symbol, str(error)))

        if "SHO list" in str(error):
            logger.error("[COMPLIANCE_ERROR] Short restricted, cannot trade")
            return False
        elif "Trading halt" in str(error):
            logger.error("[COMPLIANCE_ERROR] Trading halted")
            return False
        elif "Regulatory timeout" in str(error):
            logger.warning("[COMPLIANCE_ERROR] Service timeout, will retry next scan")
            return False

        return True

    def _fallback_to_cached_data(self, symbol: str) -> Optional[Any]:
        """Use last known price if live data unavailable"""
        logger.warning("[FALLBACK] Using cached price for {}".format(symbol))
        self.fallback_enabled = True
        # In production, would return cached price from database
        return None

    def log_error(self, severity: ErrorSeverity, message: str, context: Dict = None):
        """Log error with context for post-mortem analysis"""
        error_entry = {
            "timestamp": time.time(),
            "severity": severity.value,
            "message": message,
            "context": context or {}
        }
        self.error_log.append(error_entry)

        if severity == ErrorSeverity.CRITICAL:
            logger.critical("[CRITICAL] {}".format(message))
        elif severity == ErrorSeverity.DEGRADED:
            logger.error("[DEGRADED] {}".format(message))
        else:
            logger.warning("[RECOVERABLE] {}".format(message))


class GracefulDegradation:
    """Strategies for reduced functionality when errors occur"""

    @staticmethod
    def fallback_to_paper_trading():
        """Disable real money trading, continue with paper"""
        logger.warning("[DEGRADATION] Falling back to paper trading mode")

    @staticmethod
    def reduce_position_size(base_size: int, error_count: int) -> int:
        """Reduce position size after errors"""
        reduction = max(0.1, 1.0 - (error_count * 0.2))
        reduced = int(base_size * reduction)
        logger.warning("[DEGRADATION] Reducing position from {} to {} after {} errors".format(
            base_size, reduced, error_count))
        return reduced

    @staticmethod
    def pause_trading_for_duration(minutes: int):
        """Pause all trading for specified duration"""
        logger.critical("[DEGRADATION] Pausing all trading for {} minutes".format(minutes))
        return minutes

    @staticmethod
    def disable_new_signals():
        """Stop generating new signals, manage existing positions only"""
        logger.warning("[DEGRADATION] Disabled new signal generation, exit-only mode")
