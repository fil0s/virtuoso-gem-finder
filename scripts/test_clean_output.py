#!/usr/bin/env python3
"""
Test script to verify clean output formatting
"""

import asyncio
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_clean_output():
    """Test the clean output formatting"""
    
    print("🧪 TESTING CLEAN OUTPUT FORMATTING")
    print("=" * 50)
    
    # Configure logging to prevent double output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Prevent duplicate logging
    logging.getLogger().handlers = [logging.StreamHandler(sys.stdout)]
    
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        print("\n✅ Initializing detector with clean formatting...")
        detector = HighConvictionTokenDetector(debug_mode=False)
        
        # Set clean formatting mode
        detector.set_formatting_mode(compact=False, use_colors=True)
        
        print("\n🔍 Running single detection cycle...")
        result = await detector.run_detection_cycle()
        
        print("\n" + "=" * 50)
        print("✅ CLEAN OUTPUT TEST COMPLETED")
        print("=" * 50)
        print(f"📊 Scan Results:")
        print(f"  • Status: {result.get('status', 'unknown')}")
        print(f"  • Duration: {result.get('cycle_duration_seconds', 0):.1f}s")
        print(f"  • Tokens Analyzed: {result.get('total_analyzed', 0)}")
        print(f"  • High Conviction: {result.get('high_conviction_candidates', 0)}")
        print(f"  • New Candidates: {result.get('new_candidates', 0)}")
        
        # Clean up
        await detector.cleanup()
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_clean_output()) 