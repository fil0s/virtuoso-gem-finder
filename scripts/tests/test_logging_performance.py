#!/usr/bin/env python3
"""
Logging Performance Test Script

Benchmarks different logging modes to demonstrate optimization benefits.
"""

import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.logging_config import create_logger, LoggingMode, logging_metrics
from services.logger_setup import LoggerSetup

def benchmark_logger(logger, name: str, message_count: int = 1000):
    """Benchmark a logger implementation"""
    print(f"\n🔍 Testing {name} ({message_count:,} messages)")
    
    # Reset metrics
    if hasattr(logging_metrics, 'reset'):
        logging_metrics.reset()
    
    start_time = time.time()
    
    # Test different log levels
    for i in range(message_count):
        if i % 4 == 0:
            logger.debug(f"Debug message {i} - processing token data")
        elif i % 4 == 1:
            logger.info(f"Info message {i} - operation completed")
        elif i % 4 == 2:
            logger.warning(f"Warning message {i} - rate limit approaching")
        else:
            logger.error(f"Error message {i} - API call failed")
    
    # Test lazy evaluation (for optimized logger)
    if hasattr(logger, 'debug') and hasattr(logger.debug, '__call__'):
        for i in range(100):
            logger.debug(lambda: f"Lazy evaluation test {i} - {expensive_operation()}")
    
    end_time = time.time()
    duration = (end_time - start_time) * 1000  # Convert to milliseconds
    
    print(f"   ⏱️  Duration: {duration:.2f} ms")
    print(f"   📊 Messages/sec: {message_count / (duration/1000):,.0f}")
    
    # Get file size if possible
    log_files = list(Path("logs").glob("*.log"))
    if log_files:
        file_size = sum(f.stat().st_size for f in log_files) / 1024 / 1024  # MB
        print(f"   💾 Log file size: {file_size:.2f} MB")
    
    # Performance metrics if available
    if hasattr(logging_metrics, 'get_efficiency_stats'):
        stats = logging_metrics.get_efficiency_stats()
        if stats['total_messages'] > 0:
            print(f"   📈 Log efficiency: {stats['log_efficiency']:.1%}")
            print(f"   🎯 Sampling rate: {stats['sampling_rate']:.1%}")
    
    return duration, file_size if log_files else 0

def expensive_operation():
    """Simulate an expensive operation for lazy evaluation testing"""
    return "expensive_result_" + str(time.time())

def cleanup_logs():
    """Clean up log files before testing"""
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except:
                pass

def main():
    print("🚀 Virtuoso Gem Hunter - Logging Performance Benchmark")
    print("=" * 60)
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    results = {}
    message_count = 2000
    
    print(f"📊 Testing with {message_count:,} log messages per mode")
    
    # Test 1: Standard Logging
    print("\n" + "="*60)
    cleanup_logs()
    os.environ['LOGGING_MODE'] = 'standard'
    standard_logger = LoggerSetup('StandardTest', log_level='DEBUG')
    results['Standard'] = benchmark_logger(standard_logger.logger, "Standard Logging", message_count)
    
    # Test 2: Optimized Logging
    print("\n" + "="*60)
    cleanup_logs()
    os.environ['LOGGING_MODE'] = 'optimized'
    try:
        optimized_logger = create_logger('OptimizedTest', mode=LoggingMode.OPTIMIZED)
        results['Optimized'] = benchmark_logger(optimized_logger, "Optimized Logging", message_count)
    except ImportError as e:
        print(f"⚠️  Optimized logging not available: {e}")
        results['Optimized'] = (0, 0)
    
    # Test 3: Production Logging
    print("\n" + "="*60)
    cleanup_logs()
    os.environ['LOGGING_MODE'] = 'production'
    try:
        production_logger = create_logger('ProductionTest', mode=LoggingMode.PRODUCTION)
        results['Production'] = benchmark_logger(production_logger, "Production Logging", message_count)
    except ImportError as e:
        print(f"⚠️  Production logging not available: {e}")
        results['Production'] = (0, 0)
    
    # Test 4: Development Logging
    print("\n" + "="*60)
    cleanup_logs()
    os.environ['LOGGING_MODE'] = 'development'
    try:
        dev_logger = create_logger('DevelopmentTest', mode=LoggingMode.DEVELOPMENT)
        results['Development'] = benchmark_logger(dev_logger, "Development Logging", message_count)
    except ImportError as e:
        print(f"⚠️  Development logging not available: {e}")
        results['Development'] = (0, 0)
    
    # Test 5: Minimal Logging
    print("\n" + "="*60)
    cleanup_logs()
    os.environ['LOGGING_MODE'] = 'minimal'
    try:
        minimal_logger = create_logger('MinimalTest', mode=LoggingMode.MINIMAL)
        results['Minimal'] = benchmark_logger(minimal_logger, "Minimal Logging", message_count)
    except ImportError as e:
        print(f"⚠️  Minimal logging not available: {e}")
        results['Minimal'] = (0, 0)
    
    # Results Summary
    print("\n" + "="*60)
    print("📊 PERFORMANCE SUMMARY")
    print("="*60)
    
    # Find baseline (standard)
    baseline_time, baseline_size = results.get('Standard', (1, 1))
    
    print(f"{'Mode':<12} {'Time (ms)':<12} {'Improvement':<12} {'Size (MB)':<12} {'Reduction':<12}")
    print("-" * 60)
    
    for mode, (duration, size) in results.items():
        if duration > 0:
            improvement = (baseline_time - duration) / baseline_time * 100
            size_reduction = (baseline_size - size) / baseline_size * 100 if baseline_size > 0 else 0
            
            print(f"{mode:<12} {duration:<12.2f} {improvement:>+6.1f}%{'':<5} {size:<12.2f} {size_reduction:>+6.1f}%")
        else:
            print(f"{mode:<12} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12}")
    
    # Recommendations
    print("\n🎯 RECOMMENDATIONS")
    print("="*60)
    
    best_performance = min(results.items(), key=lambda x: x[1][0] if x[1][0] > 0 else float('inf'))
    smallest_logs = min(results.items(), key=lambda x: x[1][1] if x[1][1] > 0 else float('inf'))
    
    if best_performance[1][0] > 0:
        print(f"🏆 Best Performance: {best_performance[0]} ({best_performance[1][0]:.2f} ms)")
    
    if smallest_logs[1][1] > 0:
        print(f"💾 Smallest Logs: {smallest_logs[0]} ({smallest_logs[1][1]:.2f} MB)")
    
    print("\n📋 Usage Recommendations:")
    print("• Development: Use 'development' mode for debugging")
    print("• Testing: Use 'optimized' mode for performance testing")
    print("• Production: Use 'production' mode for live deployment")
    print("• High Volume: Use 'minimal' mode for maximum performance")
    
    print("\n✅ Test completed! Check logs/ directory for output files.")

if __name__ == "__main__":
    main() 