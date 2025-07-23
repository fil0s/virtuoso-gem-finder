import logging
import logging.handlers
import json
import time
import gzip
import shutil
import asyncio
import threading
from queue import Queue, Empty
from typing import Dict, Any, Optional, Callable, Union
from pathlib import Path
import os
from datetime import datetime
from contextlib import contextmanager
import functools

class JSONFormatter(logging.Formatter):
    """High-performance JSON formatter with lazy evaluation"""
    
    def __init__(self, include_extra_fields=True):
        super().__init__()
        self.include_extra_fields = include_extra_fields
        
    def format(self, record):
        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if enabled
        if self.include_extra_fields:
            # Token context
            if hasattr(record, 'token') and record.token:
                log_entry['token'] = record.token
            if hasattr(record, 'address') and record.address:
                log_entry['address'] = record.address
            if hasattr(record, 'event') and record.event:
                log_entry['event'] = record.event
                
            # Performance metrics
            if hasattr(record, 'duration_ms'):
                log_entry['duration_ms'] = record.duration_ms
            if hasattr(record, 'api_calls'):
                log_entry['api_calls'] = record.api_calls
            if hasattr(record, 'cache_hit'):
                log_entry['cache_hit'] = record.cache_hit
                
            # Operation context
            if hasattr(record, 'operation_id'):
                log_entry['operation_id'] = record.operation_id
            if hasattr(record, 'scan_id'):
                log_entry['scan_id'] = record.scan_id
                
        return json.dumps(log_entry, separators=(',', ':'))

class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that compresses old log files"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def doRollover(self):
        """Override to compress rotated files"""
        super().doRollover()
        
        # Compress the most recent backup file
        if self.backupCount > 0:
            backup_file = f"{self.baseFilename}.1"
            if os.path.exists(backup_file):
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_file)
                
                # Rename subsequent files
                for i in range(2, self.backupCount + 1):
                    old_file = f"{self.baseFilename}.{i}.gz"
                    new_file = f"{self.baseFilename}.{i+1}.gz"
                    if os.path.exists(old_file):
                        if os.path.exists(new_file):
                            os.remove(new_file)
                        os.rename(old_file, new_file)

class AsyncLogHandler:
    """Asynchronous log handler using queue for non-blocking logging"""
    
    def __init__(self, handler, queue_size=10000):
        self.handler = handler
        self.queue = Queue(maxsize=queue_size)
        self.worker_thread = None
        self.shutdown_event = threading.Event()
        self.start()
        
    def start(self):
        """Start the worker thread"""
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
    def _worker(self):
        """Worker thread that processes log records"""
        while not self.shutdown_event.is_set():
            try:
                record = self.queue.get(timeout=1.0)
                if record is None:  # Shutdown signal
                    break
                self.handler.handle(record)
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                # Log error to stderr to avoid recursion
                print(f"AsyncLogHandler error: {e}", file=__import__('sys').stderr)
                
    def handle(self, record):
        """Handle a log record asynchronously"""
        try:
            self.queue.put_nowait(record)
        except:
            # Queue full, drop the record (or handle differently)
            pass
            
    def shutdown(self):
        """Shutdown the async handler"""
        self.shutdown_event.set()
        self.queue.put(None)  # Signal worker to stop
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)

class LogSampler:
    """Samples log messages to reduce volume"""
    
    def __init__(self, sample_rate: float = 0.1):
        self.sample_rate = sample_rate
        self.counter = 0
        
    def should_log(self, record) -> bool:
        """Determine if record should be logged based on sampling"""
        if record.levelno >= logging.WARNING:
            return True  # Always log warnings and errors
            
        self.counter += 1
        return (self.counter % int(1/self.sample_rate)) == 0

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger, operation_name: str, level=logging.INFO, **kwargs):
        self.logger = logger
        self.operation_name = operation_name
        self.level = level
        self.start_time = None
        self.extra_fields = kwargs
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        extra = {
            'operation': self.operation_name,
            'duration_ms': round(duration_ms, 2),
            **self.extra_fields
        }
        
        if exc_type:
            extra['error'] = str(exc_val)
            self.logger.error(f"Operation '{self.operation_name}' failed", extra=extra)
        else:
            self.logger.log(self.level, f"Operation '{self.operation_name}' completed", extra=extra)

class SafeContextFormatter(logging.Formatter):
    """Formatter that safely handles missing context fields"""
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
        
    def format(self, record):
        # Add missing context fields with defaults
        if not hasattr(record, 'token'):
            record.token = ''
        if not hasattr(record, 'address'):
            record.address = ''
        if not hasattr(record, 'event'):
            record.event = ''
            
        return super().format(record)

class OptimizedLogger:
    """High-performance logger with advanced features"""
    
    def __init__(self, 
                 name: str,
                 log_file: Optional[str] = None,
                 log_level: str = "INFO",
                 enable_async: bool = True,
                 enable_json: bool = True,
                 enable_compression: bool = True,
                 enable_sampling: bool = False,
                 sample_rate: float = 0.1):
        
        self.name = name
        self.logger = logging.getLogger(name)
        self.async_handlers = []
        self.sampler = LogSampler(sample_rate) if enable_sampling else None
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_logger(log_file, log_level, enable_async, enable_json, enable_compression)
            
        # Performance tracking
        self._setup_performance_tracking()
        
    def _setup_logger(self, log_file, log_level, enable_async, enable_json, enable_compression):
        """Setup the logger with optimized handlers"""
        
        # Set log level
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Determine log file path
        if log_file is None:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / "virtuoso_gem_hunter.log"
            
        # Console handler (always synchronous for immediate feedback)
        console_handler = logging.StreamHandler()
        console_level = os.environ.get('CONSOLE_LOG_LEVEL', 'INFO')
        console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
        
        if enable_json:
            console_handler.setFormatter(JSONFormatter(include_extra_fields=False))
        else:
            console_handler.setFormatter(SafeContextFormatter())
            
        self.logger.addHandler(console_handler)
        
        # File handler with optional async and compression
        if enable_compression:
            file_handler = CompressingRotatingFileHandler(
                log_file,
                maxBytes=20*1024*1024,  # 20MB
                backupCount=15
            )
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=20*1024*1024,
                backupCount=15
            )
            
        file_level = os.environ.get('FILE_LOG_LEVEL', 'DEBUG')
        file_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
        
        if enable_json:
            file_handler.setFormatter(JSONFormatter(include_extra_fields=True))
        else:
            file_format = ('%(asctime)s [%(levelname)s] [%(name)s.%(funcName)s] '
                          '[%(token)s/%(address)s] [%(event)s] - %(message)s')
            file_handler.setFormatter(SafeContextFormatter(fmt=file_format))
            
        # Optionally wrap file handler in async handler
        if enable_async:
            async_handler = AsyncLogHandler(file_handler)
            self.async_handlers.append(async_handler)
            # Add a custom handler that forwards to async handler
            self._add_async_file_handler(async_handler)
        else:
            self.logger.addHandler(file_handler)
            
        self.logger.info(f"OptimizedLogger '{self.name}' initialized - Async: {enable_async}, JSON: {enable_json}, Compression: {enable_compression}")
        
    def _add_async_file_handler(self, async_handler):
        """Add a handler that forwards to async handler"""
        class AsyncForwarder(logging.Handler):
            def __init__(self, async_handler):
                super().__init__()
                self.async_handler = async_handler
                
            def handle(self, record):
                self.async_handler.handle(record)
                
        forwarder = AsyncForwarder(async_handler)
        forwarder.setLevel(async_handler.handler.level)
        self.logger.addHandler(forwarder)
        
    def _setup_performance_tracking(self):
        """Setup performance tracking utilities"""
        self._operation_stack = []
        
    def _should_log(self, level: int) -> bool:
        """Check if message should be logged based on sampling"""
        if not self.sampler:
            return True
            
        # Create a dummy record for sampling decision
        record = logging.LogRecord(
            name=self.name,
            level=level,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None
        )
        return self.sampler.should_log(record)
        
    def debug(self, msg: Union[str, Callable], *args, **kwargs):
        """Optimized debug logging with lazy evaluation"""
        if not self.logger.isEnabledFor(logging.DEBUG) or not self._should_log(logging.DEBUG):
            return
            
        if callable(msg):
            msg = msg()  # Lazy evaluation
            
        self.logger.debug(msg, *args, **kwargs)
        
    def info(self, msg: Union[str, Callable], *args, **kwargs):
        """Optimized info logging with lazy evaluation"""
        if not self.logger.isEnabledFor(logging.INFO) or not self._should_log(logging.INFO):
            return
            
        if callable(msg):
            msg = msg()
            
        self.logger.info(msg, *args, **kwargs)
        
    def warning(self, msg: Union[str, Callable], *args, **kwargs):
        """Optimized warning logging"""
        if callable(msg):
            msg = msg()
            
        self.logger.warning(msg, *args, **kwargs)
        
    def error(self, msg: Union[str, Callable], *args, exc_info=None, **kwargs):
        """Optimized error logging"""
        if callable(msg):
            msg = msg()
            
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
        
    def critical(self, msg: Union[str, Callable], *args, exc_info=None, **kwargs):
        """Optimized critical logging"""
        if callable(msg):
            msg = msg()
            
        self.logger.critical(msg, *args, exc_info=exc_info, **kwargs)
        
    @contextmanager
    def performance_context(self, operation_name: str, level=logging.INFO, **kwargs):
        """Context manager for performance logging"""
        perf_logger = PerformanceLogger(self.logger, operation_name, level, **kwargs)
        with perf_logger:
            yield perf_logger
            
    def set_context(self, **kwargs):
        """Set context fields for subsequent log messages"""
        # This would require thread-local storage for proper implementation
        pass
        
    def shutdown(self):
        """Shutdown async handlers"""
        for handler in self.async_handlers:
            handler.shutdown()
            
    def change_log_level(self, component: str, level: str):
        """Dynamically change log level"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if component == 'console':
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(log_level)
        elif component == 'file':
            for handler in self.logger.handlers:
                if isinstance(handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)):
                    handler.setLevel(log_level)
        elif component == 'all':
            self.logger.setLevel(log_level)
            
        self.info(f"Log level changed: {component} -> {level}")

# Lazy evaluation helper
def lazy_format(template: str, *args, **kwargs):
    """Create a lazy-evaluated format function"""
    return lambda: template.format(*args, **kwargs)

# Performance timing decorator
def log_performance(logger, operation_name: str = None):
    """Decorator for automatic performance logging"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with logger.performance_context(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator