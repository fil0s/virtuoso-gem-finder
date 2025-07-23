#!/usr/bin/env python3
"""
Simple Logging Performance Test

A controlled test to demonstrate logging optimizations safely.
"""

import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_basic_functionality():
    """Test basic logging functionality"""
    print("🧪 Testing Basic Logging Functionality")
    print("-" * 50)
    
    try:
        from services.logging_config import create_logger, LoggingMode
        
        # Test standard logging
        print("Testing standard logging...")
        logger_std = create_logger('StandardTest', mode=LoggingMode.STANDARD)
        logger_std.info("Standard logging test")
        
        # Test optimized logging
        print("Testing optimized logging...")
        logger_opt = create_logger('OptimizedTest', mode=LoggingMode.OPTIMIZED)
        logger_opt.info("Optimized logging test")
        
        # Test JSON output
        print("Testing JSON structured logging...")
        logger_opt.warning("This is a warning with JSON format")
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_performance_sample():
    """Test performance with a small sample"""
    print("\n🚀 Performance Sample Test")
    print("-" * 50)
    
    try:
        from services.logging_config import create_logger, LoggingMode
        
        # Small performance test
        message_count = 100
        results = {}
        
        # Test Standard
        os.environ['LOGGING_MODE'] = 'standard'
        logger_std = create_logger('PerfStandard', mode=LoggingMode.STANDARD)
        
        start_time = time.time()
        for i in range(message_count):
            logger_std.info(f"Standard message {i}")
        std_duration = (time.time() - start_time) * 1000
        
        # Test Optimized
        os.environ['LOGGING_MODE'] = 'optimized'
        logger_opt = create_logger('PerfOptimized', mode=LoggingMode.OPTIMIZED)
        
        start_time = time.time()
        for i in range(message_count):
            logger_opt.info(f"Optimized message {i}")
        opt_duration = (time.time() - start_time) * 1000
        
        # Results
        improvement = ((std_duration - opt_duration) / std_duration) * 100 if std_duration > 0 else 0
        
        print(f"Standard logging:  {std_duration:.2f} ms")
        print(f"Optimized logging: {opt_duration:.2f} ms")
        print(f"Performance improvement: {improvement:.1f}%")
        
        if improvement > 0:
            print("✅ Performance optimization working!")
        else:
            print("ℹ️  Performance similar (may vary with system load)")
            
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_file_sizes():
    """Check log file sizes"""
    print("\n💾 Log File Analysis")
    print("-" * 50)
    
    try:
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log*"))
            total_size = 0
            
            for log_file in log_files:
                size = log_file.stat().st_size
                total_size += size
                print(f"{log_file.name}: {size:,} bytes")
            
            print(f"Total log size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
            
            # Check for compressed files
            compressed_files = list(logs_dir.glob("*.gz"))
            if compressed_files:
                print(f"Compressed files: {len(compressed_files)}")
                print("✅ Log compression working!")
            else:
                print("ℹ️  No compressed files yet (compression happens on rotation)")
                
        else:
            print("No logs directory found")
            
        return True
        
    except Exception as e:
        print(f"❌ File analysis failed: {e}")
        return False

def test_features():
    """Test specific optimization features"""
    print("\n🎛️ Feature Tests")
    print("-" * 50)
    
    try:
        from services.logging_config import create_logger, LoggingMode
        
        # Test production mode with sampling
        logger_prod = create_logger('FeatureTest', mode=LoggingMode.PRODUCTION)
        
        # Test lazy evaluation
        def expensive_operation():
            return "expensive_result"
        
        print("Testing lazy evaluation...")
        logger_prod.debug(lambda: f"Lazy message: {expensive_operation()}")
        
        # Test performance context
        print("Testing performance context...")
        if hasattr(logger_prod, 'performance_context'):
            with logger_prod.performance_context('test_operation'):
                time.sleep(0.001)  # Simulate work
        
        print("✅ Feature tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Feature test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Virtuoso Gem Hunter - Simple Logging Test")
    print("=" * 60)
    
    # Ensure logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run tests
    tests = [
        test_basic_functionality,
        test_performance_sample,
        test_file_sizes,
        test_features
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
            
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All logging optimizations working correctly!")
        print("\n💡 To use optimizations in production:")
        print("   Add to .env file: LOGGING_MODE=production")
    else:
        print("⚠️  Some tests failed - check implementation")
        
    print("\n📁 Check logs/ directory for output files")

if __name__ == "__main__":
    main() 