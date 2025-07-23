#!/usr/bin/env python3
"""
Starter Plan Optimized Early Gem Detector
========================================

This script runs the Early Gem Detector optimized for Birdeye starter plan limitations.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.starter_plan_optimizer import StarterPlanOptimizer
from early_gem_detector import EarlyGemDetector

async def run_starter_plan_detector():
    """Run the detector with starter plan optimizations"""
    
    print("🚀 EARLY GEM DETECTOR - STARTER PLAN OPTIMIZED")
    print("=" * 60)
    print("📊 Optimized for Birdeye Starter Plan limitations:")
    print("   • Rate limit: 30 requests/minute")
    print("   • Individual calls only (no batch endpoints)")
    print("   • Extended caching to reduce API calls")
    print("   • Lightweight analysis mode")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = StarterPlanOptimizer()
    
    # Create starter plan configuration
    starter_config = optimizer.create_starter_plan_config()
    detector_config = optimizer.create_optimized_detector_config()
    
    # Initialize detector with starter plan optimizations
    detector = EarlyGemDetector(
        debug=False,
        starter_plan_mode=True,
        config_overrides=detector_config
    )
    
    # Run detection cycle with optimizations
    print("🔍 Running starter plan optimized detection cycle...")
    
    try:
        results = await detector.run_detection_cycle()
        
        print("✅ Starter plan detection completed successfully!")
        print(f"📊 Results: {len(results.get('tokens', []))} tokens analyzed")
        print(f"💰 API calls minimized for starter plan efficiency")
        
    except Exception as e:
        print(f"❌ Error in starter plan detection: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Configure logging for starter plan
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the optimized detector
    asyncio.run(run_starter_plan_detector())
