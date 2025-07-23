#!/usr/bin/env python3
"""
Test script to demonstrate the futuristic dashboard
"""

import asyncio
import time
from datetime import datetime

# Import the futuristic dashboard
try:
    from dashboard_styled import create_futuristic_dashboard
    print("✅ Futuristic dashboard imported successfully")
except ImportError as e:
    print(f"❌ Failed to import futuristic dashboard: {e}")
    exit(1)

async def test_futuristic_dashboard():
    """Test the futuristic dashboard with mock data"""
    
    print("🌌 Testing Futuristic Dashboard")
    print("=" * 50)
    
    # Create dashboard instance
    dashboard = create_futuristic_dashboard()
    
    # Simulate multiple detection cycles
    for cycle in range(1, 4):
        print(f"\n🔄 Simulating Cycle {cycle}/3...")
        
        # Mock detection result
        mock_result = {
            'total_analyzed': 150 + (cycle * 25),
            'high_conviction_tokens': [
                {
                    'symbol': f'TOKEN{cycle}A',
                    'score': 85.5 + cycle,
                    'market_cap': 500000 + (cycle * 100000),
                    'source': 'birdeye',
                    'platform': 'raydium',
                    'address': f'0x1234567890abcdef{cycle}'
                },
                {
                    'symbol': f'GEM{cycle}B',
                    'score': 78.2 + cycle,
                    'market_cap': 300000 + (cycle * 50000),
                    'source': 'moralis',
                    'platform': 'orca',
                    'address': f'0xabcdef1234567890{cycle}'
                }
            ],
            'alerts_sent': 2,
            'cycle_time': 45.5 + cycle,
            'all_candidates': [
                {'symbol': f'CAND{cycle}1', 'score': 65.0, 'platform': 'raydium'},
                {'symbol': f'CAND{cycle}2', 'score': 72.0, 'platform': 'orca'},
                {'symbol': f'CAND{cycle}3', 'score': 58.0, 'platform': 'birdeye'}
            ]
        }
        
        # Mock detector with session stats
        mock_detector = type('MockDetector', (), {
            'session_stats': {
                'api_usage_by_service': {
                    'birdeye': {'total_calls': 50 + cycle, 'batch_calls': 30 + cycle, 'successful_calls': 48 + cycle, 'avg_response_time_ms': 120},
                    'moralis': {'total_calls': 30 + cycle, 'batch_calls': 20 + cycle, 'successful_calls': 28 + cycle, 'avg_response_time_ms': 200},
                    'raydium': {'total_calls': 25 + cycle, 'batch_calls': 15 + cycle, 'successful_calls': 23 + cycle, 'avg_response_time_ms': 150}
                }
            }
        })()
        
        # Add cycle data to dashboard
        dashboard.add_cycle_data(cycle, mock_result, mock_detector)
        
        # Wait a moment to simulate processing
        await asyncio.sleep(1)
        
        print(f"✅ Cycle {cycle} data added to dashboard")
    
    # Display the futuristic dashboard
    print("\n" + "=" * 60)
    print("🌌 DISPLAYING FUTURISTIC DASHBOARD")
    print("=" * 60)
    
    # Show full futuristic dashboard
    dashboard.display_futuristic_dashboard(3, 3)
    
    print("\n" + "=" * 60)
    print("🌌 DISPLAYING COMPACT FUTURISTIC DASHBOARD")
    print("=" * 60)
    
    # Show compact futuristic dashboard
    dashboard.display_compact_futuristic_dashboard(3, 3)
    
    # Save session data
    dashboard.save_session_data()
    print("\n✅ Futuristic dashboard test completed!")

if __name__ == '__main__':
    asyncio.run(test_futuristic_dashboard()) 