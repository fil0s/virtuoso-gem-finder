#!/usr/bin/env python3
"""Test script for SOL address validation fix"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sol_bonding_curve_detector import SolBondingCurveDetector
import logging


def test_sol_address_validation():
    """Test that SOL address validation uses only valid addresses"""
    print("🧪 Testing SOL address validation fix...")
    
    # Create detector instance
    detector = SolBondingCurveDetector(analysis_mode="real_data")
    
    # Test valid SOL addresses
    print("\n📍 Test 1: Valid SOL addresses")
    
    # Test case with Native SOL
    test_item_1 = {
        'baseMint': 'So11111111111111111111111111111111111111112',  # Valid SOL
        'quoteMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'   # USDC
    }
    
    result_1 = detector._is_sol_pair_optimized(test_item_1)
    print(f"   Native SOL pair detected: {result_1}")
    assert result_1 == True, "Should detect Native SOL address"
    
    # Test case with System Program SOL  
    test_item_2 = {
        'baseMint': '11111111111111111111111111111111',              # Valid System Program SOL
        'quoteMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'   # USDC
    }
    
    result_2 = detector._is_sol_pair_optimized(test_item_2)
    print(f"   System Program SOL pair detected: {result_2}")
    assert result_2 == True, "Should detect System Program SOL address"
    
    # Test case with invalid/non-SOL addresses
    print("\n📍 Test 2: Non-SOL addresses")
    
    test_item_3 = {
        'baseMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',   # USDC
        'quoteMint': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'    # USDT
    }
    
    result_3 = detector._is_sol_pair_optimized(test_item_3)
    print(f"   Non-SOL pair detected: {result_3}")
    assert result_3 == False, "Should not detect non-SOL pairs"
    
    # Test case with the old invalid truncated address (should fail now)
    print("\n📍 Test 3: Invalid truncated address")
    
    invalid_address = 'So11111111111111111111111111111111111111111'  # Truncated (43 chars instead of 44)
    
    # Check that this address is NOT in the sol_addresses set
    # We need to access the method's local variable, so let's check indirectly
    test_item_4 = {
        'baseMint': invalid_address,
        'quoteMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
    }
    
    result_4 = detector._is_sol_pair_optimized(test_item_4)
    print(f"   Invalid SOL address detected: {result_4}")
    assert result_4 == False, "Should not detect invalid/truncated SOL address"
    
    print("\n📍 Test 4: Address length validation")
    
    # Verify address lengths
    valid_native_sol = 'So11111111111111111111111111111111111111112'
    valid_system_sol = '11111111111111111111111111111111'
    invalid_truncated = 'So11111111111111111111111111111111111111111'
    
    print(f"   Native SOL length: {len(valid_native_sol)} chars")
    print(f"   System SOL length: {len(valid_system_sol)} chars")
    print(f"   Truncated SOL length: {len(invalid_truncated)} chars")
    
    # The original issue was that there was an invalid address in the sol_addresses set
    # Both valid addresses should work, and the invalid one should not
    assert valid_native_sol != invalid_truncated, "Valid and invalid addresses should be different"
    assert len(valid_system_sol) == 32, "System SOL should be 32 characters"
    
    # Most importantly: the truncated address should NOT be detected as SOL
    print(f"   ✅ Invalid address correctly rejected: {not result_4}")
    
    print("\n✅ All SOL address validation tests passed!")
    print("✅ Invalid truncated address successfully removed from validation set")


if __name__ == "__main__":
    test_sol_address_validation()