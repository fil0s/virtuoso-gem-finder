"""
Optimized Logging System for Virtuoso Gem Hunter
Addresses performance issues, duplicate handlers, and excessive log volume.
"""

import logging
import logging.handlers
import json
import time
import threading
import contextvars
from typing import Dict, Any, Optional, Union
from pathlib import Path
import gzip
import os
from datetime import datetime
import queue
import atexit

# Context variables for request tracing
scan_id = contextvars.ContextVar('scan_id', default=None)
operation_id = contextvars.ContextVar('operation_id', default=None)
cycle_number = contextvars.ContextVar('cycle_number', default=None)

class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Custom rotating file handler that compresses rotated logs."""
    
    def doRollover(self):
        """Override to compress the rotated file."""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}.gz"
                dfn = f"{self.baseFilename}.{i+1}.gz"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            # Compress the current log file
            dfn = f"{self.baseFilename}.1.gz"
            if os.path.exists(dfn):
                os.remove(dfn)
            
            # Compress the rotated file
            with open(self.baseFilename, 'rb') as f_in:
                with gzip.open(dfn, 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(self.baseFilename)
        
        if not self.delay:
            self.stream = self._open()

class SampledCacheLogger:
    """Sampling logger for high-frequency cache operations."""
    
    def __init__(self, logger: logging.Logger, sample_rate: float = 0.01):
        self.logger = logger
        self.sample_rate = sample_rate  # Log 1% of operations by default
        self.counter = 0
        self.last_sample_time = time.time()
        self.operations_since_sample = 0
        
    def should_log(self) -> bool:
        """Determine if this operation should be logged."""
        self.counter += 1
        self.operations_since_sample += 1
        
        # Time-based sampling (at least one log per minute)
        current_time = time.time()
        if current_time - self.last_sample_time > 60:
            self.last_sample_time = current_time
            self.operations_since_sample = 0
            return True
            
        # Rate-based sampling
        if self.counter % max(1, int(1/self.sample_rate)) == 0:
            return True
            
        return False
    
    def log_cache_operation(self, operation: str, key: str, result: bool = True):
        """Log cache operation with sampling."""
        if self.should_log():
            self.logger.debug("Cache operation sampled", extra={
                'cache_operation': operation,
                'cache_key': key[:50],  # Truncate long keys
                'cache_result': result,
                'operations_since_sample': self.operations_since_sample,
                'counter': self.counter
            })

class PerformanceContextFormatter(logging.Formatter):
    """Formatter that includes performance context and structured data."""
    
    def format(self, record):
        # Add context variables
        record.scan_id = scan_id.get()
        record.operation_id = operation_id.get()
        record.cycle_number = cycle_number.get()
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            record.performance = {
                'duration_ms': record.duration_ms,
                'memory_mb': getattr(record, 'memory_mb', None),
                'api_calls': getattr(record, 'api_calls', None)
            }
        
        # Format as JSON for structured logging
        log_data = {
            'timestamp': record.timestamp,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'scan_id': record.scan_id,
            'operation_id': record.operation_id,
            'cycle_number': record.cycle_number,
        }
        
        # Add extra fields
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'message', 'scan_id', 'operation_id', 
                              'cycle_number', 'timestamp'] and not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, separators=(',', ':'))

class SimpleConsoleFormatter(logging.Formatter):
    """Simple formatter for console output with emoji indicators."""
    
    LEVEL_COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    
    LEVEL_EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
    }
    
    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelname, '')
        emoji = self.LEVEL_EMOJIS.get(record.levelname, '')
        reset = '\033[0m'
        
        # Include cycle context if available
        context = ""
        if cycle_number.get():
            context = f" [Cycle {cycle_number.get()}]"
        
        return f"{color}{emoji} {record.getMessage()}{context}{reset}"

class VirtuosoLogger:
    """Unified high-performance logger for Virtuoso Gem Hunter."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.logger = logging.getLogger("VirtuosoGemHunter")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Initialize cache logger with sampling
        self.cache_logger = SampledCacheLogger(self.logger, sample_rate=0.02)
        
        # Performance tracking
        self.performance_stats = {
            'logs_written': 0,
            'cache_operations': 0,
            'api_calls': 0,
            'start_time': time.time()
        }
        
        # Register cleanup
        atexit.register(self._cleanup)
    
    def _setup_handlers(self):
        """Setup optimized log handlers."""
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Main application log (compressed rotation)
        main_handler = CompressingRotatingFileHandler(
            "logs/virtuoso_main.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(PerformanceContextFormatter())
        
        # API-specific log (separate for monitoring)
        api_handler = CompressingRotatingFileHandler(
            "logs/virtuoso_api.log", 
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(PerformanceContextFormatter())
        api_handler.addFilter(lambda record: 'api' in record.name.lower() or 
                             hasattr(record, 'api_call') or 
                             hasattr(record, 'endpoint'))
        
        # Error-only log (for monitoring)
        error_handler = CompressingRotatingFileHandler(
            "logs/virtuoso_errors.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(PerformanceContextFormatter())
        
        # Console handler (warnings and above only)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(SimpleConsoleFormatter())
        
        # Add handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(api_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """Get a child logger with the specified name."""
        if name:
            return self.logger.getChild(name)
        return self.logger
    
    def set_log_level(self, level: Union[str, int]):
        """Dynamically adjust log level."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)
        
        # Also adjust file handlers (but keep console at WARNING+)
        for handler in self.logger.handlers:
            if not isinstance(handler, logging.StreamHandler) or hasattr(handler, 'baseFilename'):
                handler.setLevel(level)
    
    def log_cache_operation(self, operation: str, key: str, result: bool = True):
        """Log cache operation with sampling."""
        self.performance_stats['cache_operations'] += 1
        self.cache_logger.log_cache_operation(operation, key, result)
    
    def log_api_call(self, endpoint: str, duration_ms: float, success: bool = True, **kwargs):
        """Log API call with performance metrics."""
        self.performance_stats['api_calls'] += 1
        self.performance_stats['logs_written'] += 1
        
        self.logger.info("API call completed", extra={
            'api_call': True,
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'success': success,
            **kwargs
        })
    
    def log_performance(self, operation: str, duration_ms: float, **metrics):
        """Log performance metrics for operations."""
        self.logger.info(f"Performance: {operation}", extra={
            'performance': True,
            'operation': operation,
            'duration_ms': duration_ms,
            **metrics
        })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        runtime = time.time() - self.performance_stats['start_time']
        return {
            **self.performance_stats,
            'runtime_seconds': runtime,
            'logs_per_minute': (self.performance_stats['logs_written'] / runtime) * 60,
            'api_calls_per_minute': (self.performance_stats['api_calls'] / runtime) * 60
        }
    
    def _cleanup(self):
        """Cleanup on shutdown."""
        stats = self.get_performance_stats()
        self.logger.info("Logger shutdown", extra={
            'shutdown': True,
            'final_stats': stats
        })
    
    def set_context(self, scan_id_val: str = None, operation_id_val: str = None, cycle_number_val: int = None):
        """Set logging context for current operation."""
        if scan_id_val:
            scan_id.set(scan_id_val)
        if operation_id_val:
            operation_id.set(operation_id_val)
        if cycle_number_val:
            cycle_number.set(cycle_number_val)

# Global logger instance
_logger_instance = None

def get_optimized_logger(name: str = None) -> logging.Logger:
    """Get the optimized logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VirtuosoLogger()
    return _logger_instance.get_logger(name)

def set_logging_context(scan_id_val: str = None, operation_id_val: str = None, cycle_number_val: int = None):
    """Set logging context for current operation."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VirtuosoLogger()
    _logger_instance.set_context(scan_id_val, operation_id_val, cycle_number_val)

def log_cache_operation(operation: str, key: str, result: bool = True):
    """Log cache operation with sampling."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VirtuosoLogger()
    _logger_instance.log_cache_operation(operation, key, result)

def log_api_call(endpoint: str, duration_ms: float, success: bool = True, **kwargs):
    """Log API call with performance metrics."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VirtuosoLogger()
    _logger_instance.log_api_call(endpoint, duration_ms, success, **kwargs)

def log_performance(operation: str, duration_ms: float, **metrics):
    """Log performance metrics for operations."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = VirtuosoLogger()
    _logger_instance.log_performance(operation, duration_ms, **metrics)

# Performance decorator
def log_execution_time(operation_name: str):
    """Decorator to automatically log execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, success=True)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, success=False, error=str(e))
                raise
        return wrapper
    return decorator

# Async performance decorator
def log_async_execution_time(operation_name: str):
    """Decorator to automatically log async execution time."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, success=True)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_performance(operation_name, duration_ms, success=False, error=str(e))
                raise
        return wrapper
    return decorator