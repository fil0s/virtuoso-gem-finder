"""
Structlog Setup for Virtuoso Gem Hunter

Provides structured logging with excellent performance and flexibility.
"""

import os
import sys
import structlog
from structlog import get_logger
from pathlib import Path
import logging
from typing import Any, Dict

def setup_structlog(
    env: str = None,
    log_file: str = None,
    include_timestamp: bool = True,
    include_caller_info: bool = True
):
    """
    Setup structlog for the project with appropriate processors based on environment.
    
    Args:
        env: Environment ('development', 'production', 'testing')
        log_file: Optional log file path
        include_timestamp: Whether to include timestamps
        include_caller_info: Whether to include file/line info
    """
    
    # Determine environment
    if env is None:
        env = os.environ.get('LOGGING_MODE', 'development')
    
    # Check if we're in debug mode
    debug_mode = '--debug' in sys.argv or env == 'development'
    
    # Common processors for all environments
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add caller info for debugging
    if include_caller_info and debug_mode:
        processors.append(structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ))
    
    # Development vs Production processors
    if env == 'development':
        # Human-readable console output
        processors.extend([
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.RichTracebackFormatter(
                    show_locals=True
                )
            )
        ])
    else:
        # Production - JSON output
        processors.extend([
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup stdlib logging integration
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if debug_mode else logging.INFO,
    )
    
    # Add file handler if specified
    if log_file:
        try:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file {log_file}: {e}")


class VirtuosoStructLogger:
    """
    Enhanced logger for Virtuoso Gem Hunter using structlog.
    
    Provides context management, performance tracking, and API call batching.
    """
    
    def __init__(self, name: str = "VirtuosoGemHunter"):
        self.logger = get_logger(name)
        self._contexts = []
        self._api_batch = {}
        
    def bind(self, **kwargs) -> 'VirtuosoStructLogger':
        """Bind context variables that will be included in all subsequent logs."""
        new_logger = VirtuosoStructLogger()
        new_logger.logger = self.logger.bind(**kwargs)
        return new_logger
    
    def unbind(self, *keys) -> 'VirtuosoStructLogger':
        """Remove context variables."""
        new_logger = VirtuosoStructLogger()
        new_logger.logger = self.logger.unbind(*keys)
        return new_logger
    
    # Convenience methods that preserve context
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)
    
    # Enhanced methods for your use case
    def log_api_call(self, endpoint: str, status: str, response_time_ms: int, 
                     token_address: str = None, **extra):
        """Log API call with structured data."""
        self.logger.info(
            "api_call",
            endpoint=endpoint,
            status=status,
            response_time_ms=response_time_ms,
            token_address=token_address,
            **extra
        )
    
    def log_token_analysis(self, token_address: str, stage: int, score: float, 
                          passed: bool, **metrics):
        """Log token analysis progress."""
        self.logger.info(
            "token_analysis",
            token_address=token_address,
            stage=stage,
            score=score,
            passed=passed,
            **metrics
        )
    
    def log_high_conviction(self, token_address: str, score: float, 
                           reasons: list, alert_sent: bool = False):
        """Log high conviction token discovery."""
        self.logger.info(
            "🎯 HIGH CONVICTION TOKEN",
            token_address=token_address,
            score=score,
            conviction_reasons=reasons,
            alert_sent=alert_sent,
            event_type="high_conviction"
        )
    
    def log_cycle_summary(self, cycle_num: int, total_cycles: int, 
                         duration_sec: float, tokens_analyzed: int, 
                         high_conviction_count: int, **stats):
        """Log cycle completion summary."""
        self.logger.info(
            f"Cycle {cycle_num}/{total_cycles} completed",
            cycle_num=cycle_num,
            total_cycles=total_cycles,
            duration_sec=duration_sec,
            tokens_analyzed=tokens_analyzed,
            high_conviction_count=high_conviction_count,
            **stats
        )
    
    def log_rate_limit(self, service: str, reset_time: int = None, 
                      remaining: int = None):
        """Log rate limit events."""
        self.logger.warning(
            f"Rate limit reached for {service}",
            service=service,
            reset_time=reset_time,
            remaining_calls=remaining,
            event_type="rate_limit"
        )
    
    def with_context(self, operation: str, **context):
        """Context manager for operation tracking."""
        import time
        from contextlib import contextmanager
        
        @contextmanager
        def _context():
            start_time = time.time()
            bound_logger = self.bind(
                operation=operation,
                operation_start=start_time,
                **context
            )
            
            bound_logger.info(f"Starting {operation}")
            try:
                yield bound_logger
                duration = time.time() - start_time
                bound_logger.info(
                    f"Completed {operation}",
                    duration_sec=duration,
                    status="success"
                )
            except Exception as e:
                duration = time.time() - start_time
                bound_logger.error(
                    f"Failed {operation}",
                    duration_sec=duration,
                    status="error",
                    error=str(e)
                )
                raise
        
        return _context()


# Example usage
if __name__ == "__main__":
    print("🔧 Structlog Setup Demo")
    print("=" * 60)
    
    # Test development mode
    print("\n📋 Development Mode (Human Readable):")
    setup_structlog(env='development')
    logger = VirtuosoStructLogger("demo")
    
    # Bind context that persists
    logger = logger.bind(scan_id="scan_123", session_id="session_456")
    
    logger.info("Starting token analysis", tokens_count=89)
    logger.log_api_call("/defi/token/metadata", "success", 245, "tokenABC123")
    logger.log_high_conviction("tokenXYZ789", 92.5, ["volume_spike", "whale_accumulation"])
    logger.warning("Rate limit approaching", calls_remaining=50)
    
    # Test with context manager
    with logger.with_context("batch_api_operation", batch_size=50) as ctx_logger:
        ctx_logger.info("Processing batch", progress=0.5)
    
    print("\n📋 Production Mode (JSON):")
    setup_structlog(env='production')
    prod_logger = VirtuosoStructLogger("demo")
    
    prod_logger.info("Starting token analysis", tokens_count=89)
    prod_logger.log_cycle_summary(1, 9, 289.5, 15, 2, api_calls=95)