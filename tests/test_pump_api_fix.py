#!/usr/bin/env python3
"""Test script for Pump.fun API 503 error handling fix"""

import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pump_fun_api_client import PumpFunAPIClient


async def test_503_error_handling():
    """Test that 503 errors are handled correctly without duplication"""
    print("🧪 Testing Pump.fun API 503 error handling...")
    
    # Create mock logger
    mock_logger = MagicMock()
    
    # Test case 1: 503 error with FALLBACK_MODE = True
    print("\n📍 Test 1: 503 error with FALLBACK_MODE enabled")
    client = PumpFunAPIClient(fallback_mode=True)
    
    # Mock the session to return 503
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call _make_request directly to test 503 handling
        result = await client._make_request(client.endpoints['trending'])
        
        print(f"   Result type: {type(result)}")
        print(f"   Result is dict: {isinstance(result, dict)}")
        print(f"   Has 'data' key: {'data' in result if isinstance(result, dict) else 'N/A'}")
        print(f"   API available: {client.api_available}")
        
        # Verify fallback was called
        assert isinstance(result, list), "Should return fallback data (list)"
        assert len(result) > 0, "Fallback should return mock tokens"
        assert client.api_available is False, "API should be marked unavailable"
        print(f"   Fallback returned {len(result)} mock tokens")
        print("   ✅ Fallback mode handled correctly")
    
    # Test case 2: 503 error with FALLBACK_MODE = False
    print("\n📍 Test 2: 503 error with FALLBACK_MODE disabled")
    client2 = PumpFunAPIClient(fallback_mode=False)
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call _make_request directly to test 503 handling
        result = await client2._make_request(client2.endpoints['trending'])
        
        print(f"   Result type: {type(result)}")
        print(f"   Result value: {result}")
        print(f"   API available: {client2.api_available}")
        
        # Verify empty list is returned
        assert result == [], "Should return empty list when fallback disabled"
        assert client2.api_available is False, "API should be marked unavailable"
        print("   ✅ Non-fallback mode handled correctly")
    
    # Test case 3: Successful response (200)
    print("\n📍 Test 3: Successful 200 response")
    client3 = PumpFunAPIClient()
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": [{"mint": "test123", "symbol": "TEST"}]}
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call _make_request directly to test successful response
        result = await client3._make_request(client3.endpoints['trending'])
        
        print(f"   Result type: {type(result)}")
        print(f"   API available: {client3.api_available}")
        
        assert isinstance(result, dict), "Should return API data"
        assert client3.api_available is True, "API should be marked available"
        print("   ✅ Successful response handled correctly")
    
    print("\n✅ All Pump.fun API 503 error handling tests passed!")


if __name__ == "__main__":
    asyncio.run(test_503_error_handling())