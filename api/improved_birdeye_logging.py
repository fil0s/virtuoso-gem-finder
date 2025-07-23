"""
Improved BirdEye API Logging Integration

Provides cleaner logging for BirdEye API calls with reduced verbosity and better batching.
"""

import time
from typing import Dict, Any, Optional
from utils.improved_logger import improved_logger

class BirdEyeLoggerMixin:
    """Mixin to add improved logging to BirdEye API connector"""
    
    def __init_logging__(self):
        """Initialize improved logging for BirdEye API"""
        self.improved_logger = improved_logger
        self.batch_operation_id = None
        self.current_batch_size = 0
        self.batch_start_time = None
        
    def log_batch_start(self, operation_name: str, total_addresses: int):
        """Log the start of a batch operation"""
        self.batch_operation_id = f"batch_{operation_name}_{int(time.time())}"
        self.current_batch_size = total_addresses
        self.batch_start_time = time.time()
        
        self.improved_logger.start_progress(
            self.batch_operation_id, 
            total_addresses, 
            f"BirdEye {operation_name} batch"
        )
        
    def log_batch_progress(self, completed: int = 1):
        """Log progress of batch operation"""
        if self.batch_operation_id:
            self.improved_logger.update_progress(self.batch_operation_id, completed)
            
    def log_batch_complete(self, endpoint: str, successful: int, total: int):
        """Log completion of batch operation"""
        if self.batch_operation_id:
            self.improved_logger.finish_progress(self.batch_operation_id)
            
        duration = time.time() - self.batch_start_time if self.batch_start_time else 0
        success_rate = (successful / total * 100) if total > 0 else 0
        
        if success_rate >= 90:
            self.improved_logger.info(f"✅ BirdEye batch {endpoint}: {successful}/{total} successful ({success_rate:.1f}%) in {duration:.1f}s")
        else:
            self.improved_logger.warning(f"⚠️ BirdEye batch {endpoint}: {successful}/{total} successful ({success_rate:.1f}%) in {duration:.1f}s")
            
        # Reset batch tracking
        self.batch_operation_id = None
        self.current_batch_size = 0
        self.batch_start_time = None
    
    def log_api_call_improved(self, endpoint: str, status_code: int, response_time_ms: int, address: Optional[str] = None):
        """Log individual API call with improved batching"""
        status = "success" if status_code == 200 else "error"
        
        # Use the improved logger's batching
        self.improved_logger.log_api_call(
            endpoint=f"BirdEye{endpoint}", 
            status=status, 
            response_time=response_time_ms,
            address=address
        )
        
        # Also handle rate limits specially
        if status_code == 429:
            self.improved_logger.log_rate_limit("BirdEye")
    
    def log_cycle_start(self, cycle_num: int, total_cycles: int):
        """Log the start of a detection cycle"""
        self.improved_logger.info(f"🔍 Starting detection cycle {cycle_num}/{total_cycles}")
        
    def log_stage_transition(self, stage_num: int, stage_name: str, tokens_remaining: int):
        """Log transition between analysis stages"""
        self.improved_logger.info(f"📊 Stage {stage_num}: {stage_name} | {tokens_remaining} tokens remaining")
        
    def log_high_conviction_found(self, token_address: str, score: float, conviction_reasons: list):
        """Log when a high conviction token is found"""
        reasons = ", ".join(conviction_reasons[:3])  # First 3 reasons
        self.improved_logger.info(f"🎯 HIGH CONVICTION: {token_address} | Score: {score:.1f} | {reasons}")
        
    def log_error_batch(self, errors: Dict[str, list]):
        """Log multiple errors in a batched format"""
        for error_type, error_list in errors.items():
            if error_list:
                count = len(error_list)
                sample_error = error_list[0] if error_list else "Unknown"
                self.improved_logger.error(f"❌ {error_type}: {count} errors | Sample: {sample_error}")


def replace_structured_logging(birdeye_instance):
    """Replace existing structured logging with improved logging"""
    
    # Replace the _track_api_call method
    original_track = birdeye_instance._track_api_call
    
    def improved_track_api_call(endpoint: str, status_code: int, response_time_ms: int, num_tokens: int = 1, is_batch: bool = False):
        # Call original tracking for metrics
        original_track(endpoint, status_code, response_time_ms, num_tokens, is_batch)
        
        # Use improved logging instead of structured_logger
        if hasattr(birdeye_instance, 'log_api_call_improved'):
            birdeye_instance.log_api_call_improved(endpoint, status_code, response_time_ms)
    
    birdeye_instance._track_api_call = improved_track_api_call
    
    # Add the mixin methods
    for method_name in dir(BirdEyeLoggerMixin):
        if not method_name.startswith('_') and callable(getattr(BirdEyeLoggerMixin, method_name)):
            setattr(birdeye_instance, method_name, getattr(BirdEyeLoggerMixin, method_name).__get__(birdeye_instance))
    
    # Initialize improved logging
    birdeye_instance.__init_logging__()
    
    return birdeye_instance


# Configuration for different log levels based on environment
LOG_CONFIGS = {
    "development": {
        "api_batch_size": 10,
        "progress_update_interval": 5,
        "show_individual_errors": True,
        "log_level": "DEBUG"
    },
    "production": {
        "api_batch_size": 50,
        "progress_update_interval": 25,
        "show_individual_errors": False,
        "log_level": "INFO"
    },
    "testing": {
        "api_batch_size": 5,
        "progress_update_interval": 1,
        "show_individual_errors": True,
        "log_level": "INFO"
    }
}