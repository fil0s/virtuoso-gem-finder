"""
Logging Configuration Management

Provides centralized configuration for logging with optimization options.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum

class LoggingMode(Enum):
    """Logging optimization modes"""
    STANDARD = "standard"           # Basic logging (current implementation)
    OPTIMIZED = "optimized"         # High-performance logging
    PRODUCTION = "production"       # Production-ready with all optimizations
    DEVELOPMENT = "development"     # Development mode with verbose logging
    MINIMAL = "minimal"            # Minimal logging for performance testing

class LoggingConfig:
    """Centralized logging configuration"""
    
    DEFAULT_CONFIGS = {
        LoggingMode.STANDARD: {
            'enable_async': False,
            'enable_json': False,
            'enable_compression': False,
            'enable_sampling': False,
            'sample_rate': 1.0,
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'max_file_size_mb': 10,
            'backup_count': 10
        },
        LoggingMode.OPTIMIZED: {
            'enable_async': True,
            'enable_json': True,
            'enable_compression': True,
            'enable_sampling': False,
            'sample_rate': 1.0,
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'max_file_size_mb': 20,
            'backup_count': 15
        },
        LoggingMode.PRODUCTION: {
            'enable_async': True,
            'enable_json': True,
            'enable_compression': True,
            'enable_sampling': True,
            'sample_rate': 0.1,  # Sample 10% of debug messages
            'console_level': 'WARNING',
            'file_level': 'INFO',
            'max_file_size_mb': 50,
            'backup_count': 20
        },
        LoggingMode.DEVELOPMENT: {
            'enable_async': False,  # Synchronous for immediate feedback
            'enable_json': False,   # Human-readable for development
            'enable_compression': False,
            'enable_sampling': False,
            'sample_rate': 1.0,
            'console_level': 'DEBUG',
            'file_level': 'DEBUG',
            'max_file_size_mb': 5,
            'backup_count': 5
        },
        LoggingMode.MINIMAL: {
            'enable_async': True,
            'enable_json': False,
            'enable_compression': False,
            'enable_sampling': True,
            'sample_rate': 0.01,  # Sample only 1% of debug messages
            'console_level': 'ERROR',
            'file_level': 'WARNING',
            'max_file_size_mb': 100,
            'backup_count': 5
        }
    }
    
    @classmethod
    def get_config(cls, mode: Optional[LoggingMode] = None) -> Dict[str, Any]:
        """Get logging configuration for specified mode"""
        
        # Determine mode from environment or default
        if mode is None:
            mode_str = os.environ.get('LOGGING_MODE', 'standard').lower()
            try:
                mode = LoggingMode(mode_str)
            except ValueError:
                mode = LoggingMode.STANDARD
                
        config = cls.DEFAULT_CONFIGS[mode].copy()
        
        # Override with environment variables
        config.update(cls._get_env_overrides())
        
        return config
    
    @classmethod
    def _get_env_overrides(cls) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Boolean flags
        if os.environ.get('LOGGING_ENABLE_ASYNC'):
            overrides['enable_async'] = os.environ.get('LOGGING_ENABLE_ASYNC', '').lower() == 'true'
            
        if os.environ.get('LOGGING_ENABLE_JSON'):
            overrides['enable_json'] = os.environ.get('LOGGING_ENABLE_JSON', '').lower() == 'true'
            
        if os.environ.get('LOGGING_ENABLE_COMPRESSION'):
            overrides['enable_compression'] = os.environ.get('LOGGING_ENABLE_COMPRESSION', '').lower() == 'true'
            
        if os.environ.get('LOGGING_ENABLE_SAMPLING'):
            overrides['enable_sampling'] = os.environ.get('LOGGING_ENABLE_SAMPLING', '').lower() == 'true'
            
        # Numeric values
        if os.environ.get('LOGGING_SAMPLE_RATE'):
            try:
                overrides['sample_rate'] = float(os.environ.get('LOGGING_SAMPLE_RATE'))
            except ValueError:
                pass
                
        if os.environ.get('LOGGING_MAX_FILE_SIZE_MB'):
            try:
                overrides['max_file_size_mb'] = int(os.environ.get('LOGGING_MAX_FILE_SIZE_MB'))
            except ValueError:
                pass
                
        if os.environ.get('LOGGING_BACKUP_COUNT'):
            try:
                overrides['backup_count'] = int(os.environ.get('LOGGING_BACKUP_COUNT'))
            except ValueError:
                pass
                
        # Log levels
        if os.environ.get('CONSOLE_LOG_LEVEL'):
            overrides['console_level'] = os.environ.get('CONSOLE_LOG_LEVEL')
            
        if os.environ.get('FILE_LOG_LEVEL'):
            overrides['file_level'] = os.environ.get('FILE_LOG_LEVEL')
            
        return overrides

def create_logger(name: str, 
                 mode: Optional[LoggingMode] = None,
                 log_file: Optional[str] = None,
                 **kwargs) -> Any:
    """Factory function to create appropriate logger based on configuration"""
    
    config = LoggingConfig.get_config(mode)
    config.update(kwargs)  # Allow parameter overrides
    
    # Determine which logger implementation to use
    use_optimized = config.get('enable_async') or config.get('enable_json') or config.get('enable_compression')
    
    if use_optimized:
        from services.optimized_logger import OptimizedLogger
        return OptimizedLogger(
            name=name,
            log_file=log_file,
            log_level=config.get('file_level', 'INFO'),
            enable_async=config.get('enable_async', False),
            enable_json=config.get('enable_json', False),
            enable_compression=config.get('enable_compression', False),
            enable_sampling=config.get('enable_sampling', False),
            sample_rate=config.get('sample_rate', 1.0)
        )
    else:
        from services.logger_setup import LoggerSetup
        return LoggerSetup(
            name=name,
            log_file=log_file,
            log_level=config.get('file_level', 'INFO')
        )

# Performance monitoring utilities
class LoggingMetrics:
    """Track logging performance metrics"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all metrics"""
        self.messages_logged = 0
        self.messages_sampled = 0
        self.async_queue_size = 0
        self.file_writes = 0
        self.compression_ratio = 0.0
        self.average_log_time_ms = 0.0
        
    def increment_logged(self):
        """Increment logged messages counter"""
        self.messages_logged += 1
        
    def increment_sampled(self):
        """Increment sampled messages counter"""
        self.messages_sampled += 1
        
    def get_efficiency_stats(self) -> Dict[str, Any]:
        """Get logging efficiency statistics"""
        total_messages = self.messages_logged + self.messages_sampled
        
        return {
            'total_messages': total_messages,
            'messages_logged': self.messages_logged,
            'messages_sampled': self.messages_sampled,
            'sampling_rate': self.messages_sampled / total_messages if total_messages > 0 else 0,
            'log_efficiency': 1 - (self.messages_sampled / total_messages) if total_messages > 0 else 1,
            'average_log_time_ms': self.average_log_time_ms,
            'async_queue_size': self.async_queue_size,
            'compression_ratio': self.compression_ratio
        }

# Global metrics instance
logging_metrics = LoggingMetrics() 