"""
Enhanced Logger Formatter with Debug Mode

Provides different logging formats based on debug level.
"""

import logging
import os
from pathlib import Path

class EnhancedFormatter(logging.Formatter):
    """Enhanced formatter with configurable detail levels"""
    
    # Format templates for different debug levels
    FORMATS = {
        'minimal': {
            'console': '%(asctime)s | %(levelname)-7s | %(message)s',
            'file': '%(asctime)s | %(levelname)-7s | %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'standard': {
            'console': '%(asctime)s | %(levelname)-7s | %(filename)-25s | %(message)s',
            'file': '%(asctime)s | %(levelname)-7s | %(filename)-25s | %(funcName)-20s | L%(lineno)-5d | %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'detailed': {
            'console': '%(asctime)s | %(levelname)-7s | %(pathname)-40s:%(lineno)-5d | %(funcName)-20s | %(message)s',
            'file': '%(asctime)s | %(levelname)-7s | %(pathname)s:%(lineno)d | %(funcName)s | %(process)d:%(thread)d | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'debug': {
            'console': '%(asctime)s | %(levelname)-7s | %(name)-20s | %(filename)-25s:%(lineno)-5d | %(funcName)-20s | %(message)s',
            'file': '%(asctime)s | %(levelname)-7s | %(name)s | %(pathname)s:%(lineno)d | %(funcName)s | PID:%(process)d TID:%(thread)d | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S.%f'[:-3]  # Include milliseconds
        }
    }
    
    @classmethod
    def get_formatter(cls, level: str = 'standard', handler_type: str = 'console') -> logging.Formatter:
        """Get a formatter for the specified level and handler type"""
        if level not in cls.FORMATS:
            level = 'standard'
            
        format_config = cls.FORMATS[level]
        format_string = format_config.get(handler_type, format_config['console'])
        datefmt = format_config.get('datefmt', '%H:%M:%S')
        
        return logging.Formatter(format_string, datefmt=datefmt)

def setup_enhanced_logging(logger_name: str = "VirtuosoGemHunter", debug_mode: bool = False) -> logging.Logger:
    """Setup enhanced logging with debug mode support"""
    
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Determine format level based on environment or debug flag
    format_level = os.environ.get('LOG_FORMAT_LEVEL', 'standard')
    if debug_mode or '--debug' in os.sys.argv:
        format_level = 'detailed'
    if '--debug-verbose' in os.sys.argv:
        format_level = 'debug'
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_level = os.environ.get('CONSOLE_LOG_LEVEL', 'INFO')
    console_handler.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console_handler.setFormatter(EnhancedFormatter.get_formatter(format_level, 'console'))
    logger.addHandler(console_handler)
    
    # File handler (if logs directory exists)
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(logs_dir / "virtuoso_detailed.log")
        file_level = os.environ.get('FILE_LOG_LEVEL', 'DEBUG')
        file_handler.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
        file_handler.setFormatter(EnhancedFormatter.get_formatter(format_level, 'file'))
        logger.addHandler(file_handler)
    except Exception as e:
        pass  # Skip file logging if unable to create
    
    logger.setLevel(logging.DEBUG)
    return logger

def get_caller_info(depth: int = 2) -> str:
    """Get caller information for debugging"""
    import inspect
    frame = inspect.currentframe()
    try:
        for _ in range(depth):
            frame = frame.f_back
        filename = Path(frame.f_code.co_filename).name
        line_no = frame.f_lineno
        func_name = frame.f_code.co_name
        return f"{filename}:{line_no} in {func_name}()"
    except:
        return "unknown"
    finally:
        del frame

# Example usage showing different formats
if __name__ == "__main__":
    import sys
    
    print("🔧 Enhanced Logger Formatter Demo")
    print("=" * 60)
    
    # Test different format levels
    for level in ['minimal', 'standard', 'detailed', 'debug']:
        print(f"\n📋 Format Level: {level}")
        print("-" * 40)
        
        os.environ['LOG_FORMAT_LEVEL'] = level
        logger = setup_enhanced_logging(f"TestLogger_{level}")
        
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
    print("\n✅ Enhanced logging formats demonstrated!")
    print("\nUsage:")
    print("  export LOG_FORMAT_LEVEL=minimal    # Cleanest output")
    print("  export LOG_FORMAT_LEVEL=standard   # With filenames") 
    print("  export LOG_FORMAT_LEVEL=detailed   # With full paths")
    print("  export LOG_FORMAT_LEVEL=debug      # Everything including PID/TID")
    print("\nOr use command line flags:")
    print("  python script.py --debug           # Detailed format")
    print("  python script.py --debug-verbose   # Full debug format")