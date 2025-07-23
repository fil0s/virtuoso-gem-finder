#!/usr/bin/env python3
"""
Migration script to update logging to optimized system
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.optimized_logging import get_optimized_logger, set_logging_context

def test_optimized_logging():
    """Test the optimized logging system."""
    print("🧪 Testing Optimized Logging System...")
    
    # Get logger
    logger = get_optimized_logger("test")
    
    # Set context
    set_logging_context(
        scan_id_val="test_scan_001",
        operation_id_val="test_op_001", 
        cycle_number_val=1
    )
    
    # Test different log levels
    logger.debug("Debug message - should be in file only")
    logger.info("Info message - detailed operation")
    logger.warning("Warning message - should appear in console")
    logger.error("Error message - should appear in console and error log")
    
    print("✅ Optimized logging test completed!")
    print("📁 Check logs/ directory for output files:")
    print("   - virtuoso_main.log (all logs)")
    print("   - virtuoso_api.log (API-specific logs)")
    print("   - virtuoso_errors.log (warnings and errors)")
    
    return True

def show_optimized_logging_benefits():
    """Show the benefits of optimized logging."""
    print("\n🚀 Optimized Logging Benefits:")
    print("=" * 50)
    print("✅ Eliminates duplicate handlers")
    print("✅ 90% reduction in cache operation logs (sampling)")
    print("✅ Structured JSON logging for better analysis")  
    print("✅ Automatic log compression and rotation")
    print("✅ Performance context tracking")
    print("✅ Console shows only warnings/errors")
    print("✅ Separate API and error logs for monitoring")
    print("✅ Context variables for request tracing")
    print("✅ Performance decorators for timing")
    print("=" * 50)

def show_migration_instructions():
    """Show how to migrate existing code."""
    print("\n📋 Migration Instructions:")
    print("=" * 50)
    print("1. Replace existing logger setup:")
    print("   OLD: self.logger = logging.getLogger('MyClass')")
    print("   NEW: self.logger = get_optimized_logger('MyClass')")
    print()
    print("2. Add context for operations:")
    print("   set_logging_context(scan_id='scan_001', cycle_number=1)")
    print()
    print("3. Replace cache logging:")
    print("   OLD: self.logger.debug(f'Cache hit for {key}')")
    print("   NEW: log_cache_operation('hit', key, True)")
    print()
    print("4. Replace API call logging:")
    print("   OLD: self.logger.info(f'API call to {endpoint} took {time}ms')")  
    print("   NEW: log_api_call(endpoint, duration_ms, success=True)")
    print()
    print("5. Add performance decorators:")
    print("   @log_async_execution_time('token_analysis')")
    print("   async def analyze_tokens(self, tokens):")
    print("=" * 50)

def create_logging_config_example():
    """Create example logging configuration."""
    example_code = '''
# Example: Updated EarlyGemDetector initialization
from utils.optimized_logging import get_optimized_logger, set_logging_context

class EarlyGemDetector:
    def __init__(self, debug_mode=False):
        # Use optimized logger instead of custom setup
        self.logger = get_optimized_logger('EarlyGemDetector')
        
        # Set initial context
        set_logging_context(
            scan_id=f"scan_{int(time.time())}",
            operation_id="initialization"
        )
        
        self.logger.info("Early Gem Detector initializing", extra={
            'debug_mode': debug_mode,
            'initialization': True
        })

    async def run_detection_cycle(self):
        # Set cycle context
        cycle_id = f"cycle_{int(time.time())}"
        set_logging_context(
            operation_id=cycle_id,
            cycle_number=self.current_cycle
        )
        
        self.logger.info("Starting detection cycle", extra={
            'cycle_start': True,
            'cycle_number': self.current_cycle
        })
        
        # Use performance logging
        start_time = time.time()
        try:
            result = await self._do_detection()
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info("Detection cycle completed", extra={
                'cycle_complete': True,
                'duration_ms': duration_ms,
                'tokens_found': len(result.get('candidates', []))
            })
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error("Detection cycle failed", extra={
                'cycle_failed': True,
                'duration_ms': duration_ms,
                'error': str(e)
            })
            raise
'''
    
    with open('logs/optimized_logging_example.py', 'w') as f:
        f.write(example_code)
    
    print(f"\n📄 Example code written to: logs/optimized_logging_example.py")

if __name__ == "__main__":
    print("🔧 Virtuoso Gem Hunter - Optimized Logging Migration")
    print("=" * 60)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    test_optimized_logging()
    show_optimized_logging_benefits()
    show_migration_instructions()
    create_logging_config_example()
    
    print("\n🎉 Migration guide complete!")
    print("💡 Next steps:")
    print("   1. Update early_gem_detector.py to use get_optimized_logger()")
    print("   2. Update api/birdeye_connector.py cache logging")
    print("   3. Update api/batch_api_manager.py with sampling")
    print("   4. Test with: python run_3hour_detector.py --debug")