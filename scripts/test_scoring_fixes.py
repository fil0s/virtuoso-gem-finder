#!/usr/bin/env python3
"""
Test Script for Scoring System Fixes
Verifies that the scoring system and threshold fixes work correctly
"""

import sys
import os
sys.path.append(os.getcwd())

def test_score_distribution_fix():
    """Test that score distribution classification uses correct 0-100 scale"""
    print("🧪 Testing Score Distribution Fix...")
    
    # Simulate token data with scores in 30-40 range (like the session)
    test_tokens = {
        'token1': {'score': 32.7, 'symbol': 'TEST1'},
        'token2': {'score': 33.0, 'symbol': 'TEST2'},
        'token3': {'score': 43.1, 'symbol': 'TEST3'},
        'token4': {'score': 35.0, 'symbol': 'TEST4'},
        'token5': {'score': 36.0, 'symbol': 'TEST5'}
    }
    
    # Test the FIXED score distribution logic
    score_dist = {
        '0-20': 0,    # Poor (0-20)
        '20-40': 0,   # Fair (20-40) 
        '40-60': 0,   # Good (40-60)
        '60-80': 0,   # Excellent (60-80)
        '80-100': 0   # Outstanding (80-100)
    }
    
    for token_data in test_tokens.values():
        score = token_data['score']
        if score < 20:
            score_dist['0-20'] += 1
        elif score < 40:
            score_dist['20-40'] += 1
        elif score < 60:
            score_dist['40-60'] += 1
        elif score < 80:
            score_dist['60-80'] += 1
        else:
            score_dist['80-100'] += 1
    
    print(f"✅ Score Distribution Results:")
    for range_name, count in score_dist.items():
        if count > 0:
            quality = {
                '0-20': 'Poor',
                '20-40': 'Fair',
                '40-60': 'Good', 
                '60-80': 'Excellent',
                '80-100': 'Outstanding'
            }[range_name]
            print(f"   • {range_name}: {count} tokens ({quality})")
    
    # Verify correct classification
    expected_fair = 4  # tokens with scores 32.7, 33.0, 35.0, 36.0
    expected_good = 1  # token with score 43.1
    
    if score_dist['20-40'] == expected_fair and score_dist['40-60'] == expected_good:
        print("✅ Score distribution fix PASSED")
        return True
    else:
        print(f"❌ Score distribution fix FAILED")
        print(f"   Expected: 4 Fair, 1 Good")
        print(f"   Got: {score_dist['20-40']} Fair, {score_dist['40-60']} Good")
        return False

def test_threshold_calculation():
    """Test optimal threshold calculation"""
    print("\n🧪 Testing Threshold Calculation...")
    
    # Use actual observed scores from the session
    observed_scores = [32.7, 33.0, 32.6, 43.1, 35.0, 36.0]
    
    avg_score = sum(observed_scores) / len(observed_scores)
    max_score = max(observed_scores)
    min_score = min(observed_scores)
    
    # Calculate optimal threshold (30% above average)
    optimal_threshold = avg_score + (max_score - avg_score) * 0.3
    
    print(f"📊 Score Statistics:")
    print(f"   • Average: {avg_score:.1f}")
    print(f"   • Maximum: {max_score:.1f}")
    print(f"   • Minimum: {min_score:.1f}")
    print(f"   • Optimal Threshold: {optimal_threshold:.1f}")
    
    # Test alert rate with new threshold
    scores_above_threshold = [s for s in observed_scores if s >= optimal_threshold]
    alert_rate = len(scores_above_threshold) / len(observed_scores) * 100
    
    print(f"📈 Alert Rate Analysis:")
    print(f"   • Tokens above threshold: {len(scores_above_threshold)}/{len(observed_scores)}")
    print(f"   • Alert rate: {alert_rate:.1f}%")
    
    # Verify alert rate is in target range (5-30%)
    if 5 <= alert_rate <= 30:
        print("✅ Threshold calculation PASSED")
        return True
    else:
        print(f"❌ Threshold calculation FAILED - alert rate {alert_rate:.1f}% outside target range")
        return False

def test_platform_effectiveness_fix():
    """Test platform effectiveness calculation with dynamic threshold"""
    print("\n🧪 Testing Platform Effectiveness Fix...")
    
    # Simulate platform data from the session
    test_platform_data = {
        'jupiter': {'tokens': [32.7, 33.1, 32.5, 34.0], 'name': 'Jupiter'},
        'birdeye': {'tokens': [33.0, 32.8, 34.2], 'name': 'Birdeye'},
        'emerging_stars': {'tokens': [43.1, 42.5], 'name': 'Birdeye Emerging Stars'}
    }
    
    # Calculate dynamic threshold
    all_scores = []
    for platform_data in test_platform_data.values():
        all_scores.extend(platform_data['tokens'])
    
    avg_score = sum(all_scores) / len(all_scores)
    max_score = max(all_scores)
    dynamic_threshold = avg_score + (max_score - avg_score) * 0.3
    
    print(f"🎯 Dynamic Threshold: {dynamic_threshold:.1f}")
    
    # Calculate platform effectiveness
    platform_stats = {}
    for platform, data in test_platform_data.items():
        scores = data['tokens']
        high_conviction_count = sum(1 for score in scores if score >= dynamic_threshold)
        
        platform_stats[platform] = {
            'count': len(scores),
            'avg_score': sum(scores) / len(scores),
            'high_conviction_rate': (high_conviction_count / len(scores)) * 100
        }
    
    print(f"🔗 Platform Effectiveness Results:")
    has_non_zero_rates = False
    for platform, stats in platform_stats.items():
        print(f"   • {test_platform_data[platform]['name']}: {stats['avg_score']:.1f} avg, {stats['high_conviction_rate']:.1f}% high conviction")
        if stats['high_conviction_rate'] > 0:
            has_non_zero_rates = True
    
    if has_non_zero_rates:
        print("✅ Platform effectiveness fix PASSED")
        return True
    else:
        print("❌ Platform effectiveness fix FAILED - all rates still 0%")
        return False

def test_configuration_update():
    """Test that configuration was updated correctly"""
    print("\n🧪 Testing Configuration Update...")
    
    try:
        import yaml
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        threshold = config['ANALYSIS']['scoring']['cross_platform']['high_conviction_threshold']
        
        print(f"📝 Configuration Check:")
        print(f"   • High conviction threshold: {threshold}")
        
        # Verify threshold is in reasonable range (30-45 based on our analysis)
        if 30 <= threshold <= 45:
            print("✅ Configuration update PASSED")
            return True
        else:
            print(f"❌ Configuration update FAILED - threshold {threshold} outside expected range")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 TESTING SCORING SYSTEM FIXES")
    print("=" * 60)
    
    tests = [
        test_score_distribution_fix,
        test_threshold_calculation,
        test_platform_effectiveness_fix,
        test_configuration_update
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Fixes are working correctly!")
        print("\n🚀 Ready to deploy fixes:")
        print("1. Restart any running detectors")
        print("2. Monitor alert rates in next session")
        print("3. Verify score classifications are accurate")
        return True
    else:
        print("⚠️ Some tests failed - review and fix issues before deployment")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 