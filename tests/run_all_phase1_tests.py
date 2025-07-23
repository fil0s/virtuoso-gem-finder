#!/usr/bin/env python3
"""
Run all Phase 1 implementation tests
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# Improve path handling to avoid import errors
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from tests.test_cache_fix import test_cache_functionality
    from tests.test_whale_fix import test_whale_activity_analyzer
    from tests.test_quality_gates import test_quality_gates
    from tests.test_social_bonus_cap import test_social_bonus_cap
    from tests.test_phase1_integration import test_phase1_integration
except ImportError as e:
    print(f"Import error: {e}")
    print("This script must be run from the project root directory with: python -m tests.run_all_phase1_tests")
    sys.exit(1)

async def run_all_tests():
    """Run all Phase 1 tests sequentially"""
    print("\n" + "=" * 60)
    print("RUNNING ALL PHASE 1 TESTS")
    print("=" * 60)
    
    start_time = time.time()
    
    # Test 1: Cache Fix
    print("\n🔍 TEST 1: Cache System Fix")
    print("-" * 60)
    await test_cache_functionality()
    
    # Test 2: Whale Analysis Fix
    print("\n🔍 TEST 2: Whale Analysis Error Handling")
    print("-" * 60)
    await test_whale_activity_analyzer()
    
    # Test 3: Quality Gates
    print("\n🔍 TEST 3: Quality Gates Implementation")
    print("-" * 60)
    await test_quality_gates()
    
    # Test 4: Social Media Bonus Capping
    print("\n🔍 TEST 4: Social Media Bonus Capping")
    print("-" * 60)
    test_social_bonus_cap()
    
    # Test 5: Phase 1 Integration Test
    print("\n🔍 TEST 5: Phase 1 Integration Test")
    print("-" * 60)
    await test_phase1_integration()
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ ALL PHASE 1 TESTS COMPLETED IN {elapsed:.2f} SECONDS")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"❌ Test runner failed with error: {e}")
        sys.exit(1) 