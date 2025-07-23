#!/usr/bin/env python3
"""
Test API tracking statistics fix
"""

import os
import sys
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from utils.enhanced_structured_logger import APICallType

async def test_api_tracking():
    """Test that API tracking is working properly"""
    print("🧪 Testing API tracking statistics fix\n")
    
    # Test 1: Check APICallType enum
    print("1️⃣ Testing APICallType enum:")
    try:
        print(f"   ✅ APICallType.BATCH = {APICallType.BATCH.value}")
        print(f"   ✅ APICallType.BATCH_METADATA = {APICallType.BATCH_METADATA.value}")
    except AttributeError as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Create BirdeyeAPI instance and check api_call_tracker
    print("\n2️⃣ Testing BirdeyeAPI api_call_tracker:")
    try:
        # Create BirdeyeAPI instance (it will use test mode if no API key)
        birdeye = BirdeyeAPI()
        
        # Check if api_call_tracker exists
        if hasattr(birdeye, 'api_call_tracker'):
            print(f"   ✅ api_call_tracker exists")
            print(f"   📊 Initial stats: {birdeye.api_call_tracker}")
        else:
            print(f"   ❌ api_call_tracker not found")
            
    except Exception as e:
        print(f"   ⚠️  Could not create BirdeyeAPI: {e}")
    
    # Test 3: Check early_gem_detector imports
    print("\n3️⃣ Testing early_gem_detector imports:")
    try:
        from early_gem_detector import EarlyGemDetector
        print("   ✅ Successfully imported EarlyGemDetector")
        
        # Check if _capture_api_usage_stats method exists
        if hasattr(EarlyGemDetector, '_capture_api_usage_stats'):
            print("   ✅ _capture_api_usage_stats method exists")
        else:
            print("   ❌ _capture_api_usage_stats method not found")
            
    except Exception as e:
        print(f"   ❌ Import error: {e}")
    
    print("\n✅ API tracking fix test completed!")

if __name__ == "__main__":
    asyncio.run(test_api_tracking())