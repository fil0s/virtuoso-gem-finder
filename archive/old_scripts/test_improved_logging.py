#!/usr/bin/env python3
"""Test improved logging with filename column"""

from utils.improved_logger import improved_logger

def test_api_calls():
    """Test API call logging"""
    improved_logger.info("Testing API call logging with filenames")
    
    # Simulate API calls
    for i in range(3):
        improved_logger.log_api_call(
            endpoint=f"/api/endpoint_{i}",
            status="success",
            response_time=100 + i * 50,
            address=f"token_{i}"
        )
    
    improved_logger.flush_batches()

def test_progress_tracking():
    """Test progress tracking"""
    improved_logger.info("Testing progress tracking")
    
    op_id = "test_operation"
    improved_logger.start_progress(op_id, 50, "Processing items")
    improved_logger.update_progress(op_id, 25)
    improved_logger.finish_progress(op_id)

def test_different_levels():
    """Test different log levels"""
    improved_logger.debug("Debug message - detailed information")
    improved_logger.info("Info message - general information")
    improved_logger.warning("Warning message - something to watch")
    improved_logger.error("Error message - something went wrong")

if __name__ == "__main__":
    print("🔧 Testing Improved Logger with Filename Column")
    print("=" * 80)
    
    test_different_levels()
    print()
    test_api_calls()
    print()
    test_progress_tracking()
    
    print("\n✅ Test completed!")