import logging
from logging.handlers import RotatingFileHandler
import inspect
import traceback

class LoggerSetup:
    """Custom logger setup with enhanced debugging capabilities"""
    
    def __init__(self, name: str, log_file: str = 'virtuoso_gem_finder.log'):
        self.logger = logging.getLogger(name)
        # Prevent adding multiple handlers if LoggerSetup is instantiated multiple times for the same logger name
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler with INFO level
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO) # Default to INFO for console
            console_format = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)
            
            # File handler with DEBUG level and rotation
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG) # Default to DEBUG for file
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(file_format)
            
            # Add handlers
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def get_caller_info(self) -> str:
        """Get information about the calling function"""
        stack = inspect.stack()
        # Get caller frame (index 2 because this function and the logging function are 0 and 1)
        # Need to be careful if this is called from within the logger methods themselves.
        # It might be better to pass depth or let the logger handle this if possible.
        # For now, assuming it's called before the actual log call, depth 2 is usually correct.
        # If called from self.debug, self.info etc, then it needs to be stack[3]
        
        caller_frame = None
        # Iterate up the stack to find the first frame outside this LoggerSetup class
        for i in range(2, len(stack)):
            if stack[i].filename != __file__: # Check if the frame is outside the current file
                caller_frame = stack[i]
                break
        
        if caller_frame:
            return f"{caller_frame.filename}:{caller_frame.function}:{caller_frame.lineno}"
        return "unknown_caller"

    # The enhanced logging methods (debug, info, warning, error, critical)
    # should directly use self.logger.X, and the Formatter will handle caller info if configured.
    # Overriding them to manually add caller_info can be redundant if formatter does it.
    # However, the existing code structure has them.
    # Let's refine this: the Formatter for the file handler already includes filename, lineno.
    # The custom get_caller_info and prepending it might be redundant or conflict.
    # For now, I'll keep the structure as it was in solgem.py but note this.

    def debug(self, msg: str, *args, **kwargs):
        """Enhanced debug logging with caller information"""
        # If Formatter handles caller info, this explicit call might not be needed or could be simplified.
        # caller_info = self.get_caller_info() # This would refer to this debug method's caller.
        self.logger.debug(msg, *args, **kwargs) # Caller info is handled by formatter for file log
    
    def info(self, msg: str, *args, **kwargs):
        """Enhanced info logging"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Enhanced warning logging with caller information"""
        self.logger.warning(msg, *args, **kwargs) # Caller info is handled by formatter for file log
    
    def error(self, msg: str, *args, exc_info=None, **kwargs):
        """Enhanced error logging with stack trace"""
        # The original get_caller_info might not be accurate here if used directly.
        # Rely on logger's built-in exc_info handling and formatter.
        if exc_info is True: # Allow passing exc_info=True
             self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
        elif exc_info: # If exc_info is a tuple (sys.exc_info())
            # Custom formatting of stack trace, if desired beyond logger's default
            stack_trace = ''.join(traceback.format_exception(*exc_info))
            self.logger.error(f"{msg}\nStack trace:\n{stack_trace}", *args, **kwargs)
        else:
            self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, exc_info=None, **kwargs):
        """Enhanced critical logging with stack trace and notification"""
        if exc_info is True:
            self.logger.critical(msg, *args, exc_info=exc_info, **kwargs)
        elif exc_info:
            stack_trace = ''.join(traceback.format_exception(*exc_info))
            self.logger.critical(f"{msg}\nStack trace:\n{stack_trace}", *args, **kwargs)
        else:
            self.logger.critical(msg, *args, **kwargs)

# Example of how to set console log level based on an external flag (e.g., config)
# This would typically be done where LoggerSetup is instantiated.
# def set_console_level(logger_instance, level):
#     for handler in logger_instance.logger.handlers:
#         if isinstance(handler, logging.StreamHandler): # Identify console handler
#             handler.setLevel(level) 