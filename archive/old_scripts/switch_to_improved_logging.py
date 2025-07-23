#!/usr/bin/env python3
"""
Switch to Improved Logging System

This script demonstrates how to integrate the improved logging system
with your existing virtuoso gem hunter application.
"""

import os
import sys
from utils.improved_logger import improved_logger

def setup_improved_logging():
    """Setup improved logging for the application"""
    
    # Set environment variables for cleaner logging
    os.environ['CONSOLE_LOG_LEVEL'] = 'INFO'
    os.environ['LOGGING_MODE'] = 'development'  # or 'production' for live use
    
    print("🔧 Improved Logging System Setup")
    print("=" * 50)
    
    # Test the improved logger
    improved_logger.info("🚀 Improved logging system initialized")
    
    # Demonstrate API call batching
    with improved_logger.operation_context("Testing API batching"):
        # Simulate multiple API calls
        for i in range(5):
            improved_logger.log_api_call(
                endpoint="/defi/v3/token/meta-data/single",
                status="success",
                response_time=250 + i * 10,
                address=f"test_address_{i}"
            )
        
        # Flush batches to see summary
        improved_logger.flush_batches()
    
    # Demonstrate progress tracking
    operation_id = "test_progress"
    improved_logger.start_progress(operation_id, 100, "Processing tokens")
    
    for i in range(0, 101, 20):
        improved_logger.update_progress(operation_id, 20)
        
    improved_logger.finish_progress(operation_id)
    
    # Demonstrate different log levels
    improved_logger.debug("Debug message - only in development mode")
    improved_logger.info("📊 Info message - general information")
    improved_logger.warning("⚠️ Warning message - something to watch")
    improved_logger.error("❌ Error message - something went wrong")
    
    print("\n✅ Improved logging system is ready!")
    print("\nKey Benefits:")
    print("• API calls are batched to reduce log verbosity")
    print("• Progress tracking for long operations")
    print("• Clean, emoji-enhanced messages")
    print("• Structured operation contexts")
    print("• Rate limit handling")
    print("• Session statistics")

def integration_example():
    """Show how to integrate with existing code"""
    
    print("\n🔧 Integration Example")
    print("=" * 50)
    
    print("""
To integrate with your existing run_3hour_detector.py:

1. Import the improved logger:
   from utils.improved_logger import improved_logger

2. Replace verbose API logging in BirdEye connector:
   from api.improved_birdeye_logging import replace_structured_logging
   birdeye_api = replace_structured_logging(birdeye_api)

3. Use progress tracking in detection cycles:
   cycle_id = "detection_cycle_1"
   improved_logger.start_progress(cycle_id, total_tokens, "Token Analysis")
   
   for token in tokens:
       # Process token
       improved_logger.update_progress(cycle_id, 1)
   
   improved_logger.finish_progress(cycle_id)

4. Log cycle summaries:
   improved_logger.log_cycle_summary(
       cycle_num=1, 
       total_cycles=9, 
       results={
           'cycle_time': 289.7,
           'total_analyzed': 15,
           'high_conviction_count': 0
       }
   )

5. Set environment variable for production:
   export LOGGING_MODE=production  # Reduces verbosity
   
   Or for development:
   export LOGGING_MODE=development  # Full verbosity
""")

if __name__ == "__main__":
    setup_improved_logging()
    integration_example()