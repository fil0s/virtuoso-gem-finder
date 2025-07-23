#!/usr/bin/env python3
"""
Test Enhanced Pre-Filter Display with PrettyTable
Demonstrates the improved pre-filter analysis visualization
"""

import sys
import os
sys.path.append(os.getcwd())

from scripts.high_conviction_token_detector import HighConvictionTokenDetector

def test_enhanced_pre_filter_display():
    """Test the enhanced pre-filter display with mock data"""
    
    print("🧪 TESTING ENHANCED PRE-FILTER DISPLAY")
    print("=" * 60)
    
    # Initialize detector
    detector = HighConvictionTokenDetector(debug_mode=True)
    
    # Create mock pre-filter statistics similar to your actual data
    mock_pre_filter_stats = {
        'total_candidates_evaluated': 50,
        'total_candidates_passed': 0,
        'total_candidates_filtered': 50,
        'filter_pass_rate': 0.0,
        'filtered_tokens': {},
        'filter_reasons': {
            'market_cap_too_low': 45,
            'market_cap_too_high': 5,
            'volume_too_low': 45,
            'insufficient_platforms': 0,
            'top_30_limit': 0
        },
        'missed_opportunities': [
            {
                'address': '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr',
                'symbol': 'POPCAT',
                'score': 63.0,
                'filter_reason': 'market_cap_too_high',
                'market_cap': 274627615,
                'volume_24h': 18127513
            },
            {
                'address': 'ABC123...',
                'symbol': 'TESTCOIN',
                'score': 55.2,
                'filter_reason': 'market_cap_too_low',
                'market_cap': 75000,
                'volume_24h': 120000
            },
            {
                'address': 'DEF456...',
                'symbol': 'ANOTHERCOIN',
                'score': 52.8,
                'filter_reason': 'volume_too_low',
                'market_cap': 250000,
                'volume_24h': 85000
            }
        ],
        'filter_effectiveness': {
            'avg_score_passed': 0.0,
            'avg_score_filtered': 33.0,
            'highest_filtered_score': 63.0
        }
    }
    
    # Set the mock data in the detector
    detector.session_stats['pre_filter_analysis'] = mock_pre_filter_stats
    
    print("📊 Mock data setup complete. Testing enhanced display...")
    print()
    
    # Test the enhanced display
    try:
        detector._display_pre_filter_analysis()
        print("\n✅ Enhanced pre-filter display test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 COMPARISON: Before vs After")
    print("=" * 60)
    print("BEFORE (Text-based):")
    print("- Hard to scan information")
    print("- No clear prioritization")
    print("- Difficult to spot optimization opportunities")
    print("- No risk assessment for recommendations")
    print()
    print("AFTER (PrettyTable-based):")
    print("- ✅ Clear tabular organization")
    print("- ✅ Color-coded status indicators")
    print("- ✅ Impact level assessments")
    print("- ✅ Risk-rated recommendations")
    print("- ✅ Detailed opportunity analysis")
    print("- ✅ Quantified filter effectiveness")
    print()
    print("🚀 The enhanced display makes it much easier to:")
    print("  • Quickly identify the most restrictive filters")
    print("  • Spot high-value tokens being filtered incorrectly")
    print("  • Get actionable optimization recommendations")
    print("  • Understand filter performance at a glance")

if __name__ == '__main__':
    test_enhanced_pre_filter_display() 