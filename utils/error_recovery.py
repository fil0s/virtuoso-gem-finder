#!/usr/bin/env python3
"""
Advanced error recovery and resilience patterns for the early token monitor.

This module provides structured error handling, circuit breakers, and recovery
strategies to replace catch-all exception patterns throughout the codebase.
"""

import asyncio
import logging
import time
import functools
from enum import Enum
from typing import Dict, Any, Optional, Callable, Type, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from utils.exceptions import (
    VirtuosoError, 
    APIError, 
    APIConnectionError, 
    APIDataError,
    ConfigurationError,
    DatabaseError
)

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests  
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class ErrorStats:
    """Track error statistics for circuit breaker decisions"""
    total_requests: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    failure_types: Dict[str, int] = field(default_factory=dict)

@dataclass
class RecoveryStrategy:
    """Defines how to recover from different types of errors"""
    retry_attempts: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    recoverable_exceptions: tuple = (APIConnectionError, ConnectionError, TimeoutError)
    circuit_breaker_enabled: bool = True
    
class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascade failures.
    
    Monitors error rates and temporarily blocks requests to failing services
    to allow them time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple = (APIError, ConnectionError),
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.stats = ErrorStats()
        self._state_lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized: "
                   f"threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    async def _record_success(self):
        """Record a successful operation"""
        async with self._state_lock:
            self.stats.total_requests += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker '{self.name}' closed - service recovered")
    
    async def _record_failure(self, exception: Exception):
        """Record a failed operation"""
        async with self._state_lock:
            self.stats.total_requests += 1
            self.stats.total_failures += 1
            self.stats.consecutive_failures += 1
            self.stats.last_failure_time = datetime.now()
            
            exc_type = type(exception).__name__
            self.stats.failure_types[exc_type] = self.stats.failure_types.get(exc_type, 0) + 1
            
            if (self.state == CircuitState.CLOSED and 
                self.stats.consecutive_failures >= self.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' opened - "
                             f"{self.stats.consecutive_failures} consecutive failures")
    
    async def _can_attempt(self) -> bool:
        """Check if we can attempt the operation"""
        async with self._state_lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if (self.stats.last_failure_time and 
                    datetime.now() - self.stats.last_failure_time > timedelta(seconds=self.recovery_timeout)):
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' half-open - testing recovery")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            return False
    
    @asynccontextmanager
    async def protected_call(self):
        """Context manager for protected calls with circuit breaker logic"""
        if not await self._can_attempt():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        
        try:
            yield
            await self._record_success()
        except self.expected_exception as e:
            await self._record_failure(e)
            raise
        except Exception as e:
            # Unexpected exceptions should still be recorded but not suppressed
            await self._record_failure(e)
            logger.error(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise

class CircuitBreakerOpenError(VirtuosoError):
    """Raised when circuit breaker is open"""
    pass

class ErrorRecoveryManager:
    """
    Centralized error recovery management system.
    
    Provides structured error handling, retry logic, and recovery strategies
    for different components of the application.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default recovery strategies for common scenarios"""
        
        # API recovery strategies
        self.recovery_strategies["api_general"] = RecoveryStrategy(
            retry_attempts=3,
            retry_delay=1.0,
            backoff_multiplier=2.0,
            recoverable_exceptions=(APIConnectionError, ConnectionError, TimeoutError)
        )
        
        self.recovery_strategies["api_rate_limited"] = RecoveryStrategy(
            retry_attempts=5,
            retry_delay=5.0,
            backoff_multiplier=1.5,
            max_delay=30.0,
            recoverable_exceptions=(APIConnectionError,)
        )
        
        self.recovery_strategies["database"] = RecoveryStrategy(
            retry_attempts=2,
            retry_delay=0.5,
            backoff_multiplier=2.0,
            recoverable_exceptions=(DatabaseError, ConnectionError)
        )
        
        # Configuration errors are usually not recoverable by retry
        self.recovery_strategies["configuration"] = RecoveryStrategy(
            retry_attempts=0,
            recoverable_exceptions=()
        )
    
    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]
    
    def add_recovery_strategy(self, name: str, strategy: RecoveryStrategy):
        """Add a custom recovery strategy"""
        self.recovery_strategies[name] = strategy
        logger.info(f"Added recovery strategy '{name}'")
    
    async def execute_with_recovery(
        self,
        operation: Callable,
        strategy_name: str = "api_general",
        circuit_breaker_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute an operation with error recovery and optional circuit breaker protection.
        
        Args:
            operation: The async function to execute
            strategy_name: Name of the recovery strategy to use
            circuit_breaker_name: Optional circuit breaker name
            context: Optional context information for logging
            **kwargs: Additional arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            The final exception if all recovery attempts fail
        """
        strategy = self.recovery_strategies.get(strategy_name)
        if not strategy:
            logger.warning(f"Unknown recovery strategy '{strategy_name}', using default")
            strategy = self.recovery_strategies["api_general"]
        
        circuit_breaker = None
        if circuit_breaker_name:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)
        
        last_exception = None
        context_str = f" ({context})" if context else ""
        
        for attempt in range(strategy.retry_attempts + 1):
            try:
                if circuit_breaker:
                    async with circuit_breaker.protected_call():
                        result = await operation(**kwargs)
                        if attempt > 0:
                            logger.info(f"Operation succeeded on attempt {attempt + 1}{context_str}")
                        return result
                else:
                    result = await operation(**kwargs)
                    if attempt > 0:
                        logger.info(f"Operation succeeded on attempt {attempt + 1}{context_str}")
                    return result
                    
            except strategy.recoverable_exceptions as e:
                last_exception = e
                
                if attempt < strategy.retry_attempts:
                    delay = min(
                        strategy.retry_delay * (strategy.backoff_multiplier ** attempt),
                        strategy.max_delay
                    )
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed{context_str}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {strategy.retry_attempts + 1} attempts failed{context_str}. "
                        f"Final error: {e}"
                    )
                    
            except CircuitBreakerOpenError as e:
                logger.warning(f"Circuit breaker prevented operation{context_str}: {e}")
                raise
                
            except Exception as e:
                # Non-recoverable exception
                logger.error(f"Non-recoverable error{context_str}: {e}")
                raise
        
        # If we get here, all retry attempts failed
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Operation failed after {strategy.retry_attempts + 1} attempts{context_str}")

# Decorator for easy error recovery
def with_error_recovery(
    strategy_name: str = "api_general",
    circuit_breaker_name: Optional[str] = None,
    context: Optional[Union[str, Callable]] = None
):
    """
    Decorator to add error recovery to async functions.
    
    Args:
        strategy_name: Recovery strategy to use
        circuit_breaker_name: Optional circuit breaker name
        context: Context string or function that returns context
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get context information
            if callable(context):
                context_info = context(*args, **kwargs)
            elif isinstance(context, str):
                context_info = context
            else:
                context_info = f"{func.__name__}"
            
            # Use global error recovery manager
            recovery_manager = _get_global_recovery_manager()
            
            async def operation(**op_kwargs):
                return await func(*args, **op_kwargs)
            
            return await recovery_manager.execute_with_recovery(
                operation=operation,
                strategy_name=strategy_name,
                circuit_breaker_name=circuit_breaker_name,
                context={"function": func.__name__, "details": context_info},
                **kwargs
            )
        return wrapper
    return decorator

# Global instance
_global_recovery_manager: Optional[ErrorRecoveryManager] = None

def _get_global_recovery_manager() -> ErrorRecoveryManager:
    """Get or create the global error recovery manager"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = ErrorRecoveryManager()
    return _global_recovery_manager

# Public API
def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager"""
    return _get_global_recovery_manager()

def create_recovery_strategy(
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay: float = 60.0,
    recoverable_exceptions: tuple = (APIConnectionError, ConnectionError, TimeoutError),
    circuit_breaker_enabled: bool = True
) -> RecoveryStrategy:
    """Factory function to create custom recovery strategies"""
    return RecoveryStrategy(
        retry_attempts=retry_attempts,
        retry_delay=retry_delay,
        backoff_multiplier=backoff_multiplier,
        max_delay=max_delay,
        recoverable_exceptions=recoverable_exceptions,
        circuit_breaker_enabled=circuit_breaker_enabled
    )

# Specific error handlers for common patterns
class SpecificErrorHandlers:
    """Collection of specific error handlers for common scenarios"""
    
    @staticmethod
    async def handle_api_error(
        operation: Callable,
        api_name: str,
        operation_name: str,
        **kwargs
    ) -> Any:
        """Handle API-specific errors with appropriate recovery"""
        recovery_manager = get_error_recovery_manager()
        
        return await recovery_manager.execute_with_recovery(
            operation=operation,
            strategy_name="api_general",
            circuit_breaker_name=f"api_{api_name}",
            context={"api": api_name, "operation": operation_name},
            **kwargs
        )
    
    @staticmethod
    async def handle_rate_limited_api(
        operation: Callable,
        api_name: str,
        **kwargs
    ) -> Any:
        """Handle rate-limited API calls with longer delays"""
        recovery_manager = get_error_recovery_manager()
        
        return await recovery_manager.execute_with_recovery(
            operation=operation,
            strategy_name="api_rate_limited",
            circuit_breaker_name=f"api_{api_name}_rate",
            context={"api": api_name, "type": "rate_limited"},
            **kwargs
        )
    
    @staticmethod
    async def handle_database_operation(
        operation: Callable,
        operation_name: str,
        **kwargs
    ) -> Any:
        """Handle database operations with appropriate recovery"""
        recovery_manager = get_error_recovery_manager()
        
        return await recovery_manager.execute_with_recovery(
            operation=operation,
            strategy_name="database",
            circuit_breaker_name="database",
            context={"operation": operation_name, "type": "database"},
            **kwargs
        ) 