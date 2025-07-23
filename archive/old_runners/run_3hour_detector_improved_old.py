#!/usr/bin/env python3
"""
Run 3-hour detector with enhanced structured logging (structlog)
"""

import os
import sys

# Enhanced structured logging
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage

# Import and run the original detector
from run_3hour_detector import run_3hour_detector

if __name__ == "__main__":
    # Initialize enhanced structured logger
    enhanced_logger = create_enhanced_logger("run-3hour-detector-improved")
    
    # Start scan context for the enhanced improved detector
    scan_id = enhanced_logger.new_scan_context(
        strategy="3hour-detector-improved-structlog",
        timeframe="3_hours_enhanced_logging"
    )
    
    enhanced_logger.info("🚀 Starting 3-hour detector with enhanced structured logging (structlog)",
                        scan_id=scan_id,
                        logging_system="structlog",
                        enhanced_features=True)
    
    with enhanced_logger.stage_context(DetectionStage.INITIALIZATION, 
                                      operation="start_improved_detector"):
        enhanced_logger.info("Initializing improved 3-hour detector with full structlog integration")
        
        # Check for debug flags
        if "--debug" in sys.argv or "--debug-stage0" in sys.argv:
            enhanced_logger.info("🐛 Debug mode detected - enhanced structured logging with debug level")
    
    # Run the enhanced 3-hour detector
    import asyncio
    try:
        success = asyncio.run(run_3hour_detector())
        if success:
            enhanced_logger.info("🎉 Enhanced 3-hour detector completed successfully with structlog!")
        else:
            enhanced_logger.error("💥 Enhanced 3-hour detector failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        enhanced_logger.warning("⚠️ Enhanced detector interrupted by user")
        sys.exit(0)
    except Exception as e:
        enhanced_logger.error("❌ Unexpected error in enhanced detector", 
                            error=str(e),
                            error_type=type(e).__name__)
        sys.exit(1)