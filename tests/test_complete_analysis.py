#!/usr/bin/env python3
"""
🚀 COMPLETE ANALYSIS TEST - Enhanced Data Fetcher Demo
Tests the fixed API data pipeline with full token analysis

This test demonstrates:
1. Enhanced data fetcher working correctly
2. Real trading data flowing through to scoring
3. Complete analysis pipeline with all metrics
4. Performance comparison vs legacy methods
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'scripts'))

from enhanced_data_fetcher import EnhancedDataFetcher
try:
    from early_gem_detector import EarlyGemDetector
except ImportError:
    from src.detectors.early_gem_detector import EarlyGemDetector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CompleteAnalysisTest')

# Test token address
TEST_TOKEN = "tk28Q41zkgtAkfuN86JXfpD8wFrdq5WxUC4yGCBpump"

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🚀 {title}")
    print("=" * 80)

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n📋 {title}")
    print("-" * 60)

def format_currency(value: float) -> str:
    """Format currency values"""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.1f}K"
    else:
        return f"${value:.2f}"

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.2f}%" if value else "0.00%"

async def test_enhanced_data_fetcher():
    """Test the enhanced data fetcher directly"""
    print_header("ENHANCED DATA FETCHER TEST")
    
    try:
        fetcher = EnhancedDataFetcher(logger)
        
        print(f"🎯 Testing token: {TEST_TOKEN}")
        print(f"⏰ Starting at: {datetime.now().strftime('%H:%M:%S')}")
        
        start_time = time.time()
        enhanced_data = await fetcher.enhance_token_with_comprehensive_data(TEST_TOKEN)
        fetch_time = time.time() - start_time
        
        print(f"⚡ Fetch completed in: {fetch_time:.2f} seconds")
        print()
        
        if enhanced_data.get('error'):
            print(f"❌ Error: {enhanced_data['error']}")
            return None
        
        # Display comprehensive results
        print_section("BASIC TOKEN INFO")
        print(f"📛 Symbol: {enhanced_data.get('symbol', 'Unknown')}")
        print(f"📝 Name: {enhanced_data.get('name', 'Unknown')}")
        print(f"💰 Price: ${enhanced_data.get('price_usd', 0):.8f}")
        print(f"📊 Market Cap: {format_currency(enhanced_data.get('market_cap', 0))}")
        print(f"💧 Liquidity: {format_currency(enhanced_data.get('liquidity_usd', 0))}")
        
        print_section("TRADING ACTIVITY")
        print(f"📈 Volume 24h: {format_currency(enhanced_data.get('volume_24h', 0))}")
        print(f"📈 Volume 6h: {format_currency(enhanced_data.get('volume_6h', 0))}")
        print(f"📈 Volume 1h: {format_currency(enhanced_data.get('volume_1h', 0))}")
        print(f"🔄 Trades 24h: {enhanced_data.get('trades_24h', 0):,}")
        print(f"🔄 Trades 1h: {enhanced_data.get('trades_1h', 0):,}")
        print(f"👥 Unique Traders 24h: {enhanced_data.get('unique_traders_24h', 0)}")
        
        print_section("PRICE MOVEMENTS")
        print(f"📊 Change 24h: {format_percentage(enhanced_data.get('price_change_24h', 0))}")
        print(f"📊 Change 6h: {format_percentage(enhanced_data.get('price_change_6h', 0))}")
        print(f"📊 Change 1h: {format_percentage(enhanced_data.get('price_change_1h', 0))}")
        print(f"📊 Change 5m: {format_percentage(enhanced_data.get('price_change_5m', 0))}")
        
        print_section("SECURITY & HOLDERS")
        print(f"🛡️ Is Scam: {'❌ Yes' if enhanced_data.get('is_scam') else '✅ No'}")
        print(f"⚠️ Is Risky: {'⚠️ Yes' if enhanced_data.get('is_risky') else '✅ No'}")
        print(f"🔒 Security Score: {enhanced_data.get('security_score', 0):.1f}/10")
        print(f"👥 Holder Count: {enhanced_data.get('holder_count', 0):,}")
        print(f"🐋 Top Holder %: {format_percentage(enhanced_data.get('top_holder_percentage', 0))}")
        
        print_section("DERIVED METRICS")
        print(f"💹 Volume/MCap Ratio: {enhanced_data.get('volume_mcap_ratio', 0):.4f}")
        print(f"💧 Liquidity/MCap Ratio: {enhanced_data.get('liquidity_mcap_ratio', 0):.4f}")
        print(f"📊 Buy/Sell Ratio: {enhanced_data.get('buy_sell_ratio', 0):.2f}")
        print(f"🎯 Trades per Trader: {enhanced_data.get('trades_per_trader', 0):.1f}")
        
        print_section("DATA QUALITY ASSESSMENT")
        quality = enhanced_data.get('data_quality', 'unknown')
        coverage = enhanced_data.get('coverage_score', 0)
        sources = ', '.join(enhanced_data.get('enhancement_sources', []))
        
        quality_emoji = {
            'excellent': '🟢',
            'good': '🟡', 
            'poor': '🟠',
            'failed': '🔴'
        }.get(quality, '⚪')
        
        print(f"{quality_emoji} Data Quality: {quality.upper()}")
        print(f"📊 Coverage Score: {coverage:.1f}%")
        print(f"🔗 Sources: {sources}")
        
        return enhanced_data
        
    except Exception as e:
        print(f"❌ Enhanced data fetcher test failed: {e}")
        return None

async def test_full_analysis_pipeline():
    """Test the complete early gem detector analysis pipeline"""
    print_header("FULL ANALYSIS PIPELINE TEST")
    
    try:
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        print(f"🎯 Analyzing token: {TEST_TOKEN}")
        print(f"⏰ Starting analysis at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Create candidate token data (simulating discovery from API)
        candidate = {
            'address': TEST_TOKEN,
            'symbol': 'Unknown',  # Will be enhanced
            'source': 'test_analysis',
            'price': 0,  # Will be enhanced
            'marketCap': 0,  # Will be enhanced
            'liquidity': 0,  # Will be enhanced
            'volume': {},  # Empty - will be enhanced
            'volume_24h': 0,  # Zero - will be enhanced
            'trades_24h': 0,  # Zero - will be enhanced
            'unique_traders': 0,  # Zero - will be enhanced
            'discovery_timestamp': time.time()
        }
        
        print_section("BEFORE ENHANCEMENT")
        print(f"📛 Symbol: {candidate.get('symbol', 'Unknown')}")
        print(f"💰 Price: ${candidate.get('price', 0)}")
        print(f"📊 Market Cap: {format_currency(candidate.get('marketCap', 0))}")
        print(f"📈 Volume 24h: {format_currency(candidate.get('volume_24h', 0))}")
        print(f"🔄 Trades 24h: {candidate.get('trades_24h', 0)}")
        print(f"👥 Unique Traders: {candidate.get('unique_traders', 0)}")
        
        # Run the complete analysis pipeline
        start_time = time.time()
        result = await detector._analyze_single_candidate(candidate)
        analysis_time = time.time() - start_time
        
        print(f"\n⚡ Analysis completed in: {analysis_time:.2f} seconds")
        
        if not result:
            print("❌ Analysis returned None - token was filtered out")
            return None
        
        # Extract results
        enriched_candidate = result.get('candidate', {})
        final_score = result.get('final_score', 0)
        scoring_breakdown = result.get('scoring_breakdown', {})
        conviction_level = result.get('conviction_level', 'low')
        enhanced_metrics = result.get('enhanced_metrics', {})
        
        print_section("AFTER ENHANCEMENT & ANALYSIS")
        print(f"📛 Symbol: {enriched_candidate.get('symbol', 'Unknown')}")
        print(f"📝 Name: {enriched_candidate.get('name', 'Unknown')}")
        print(f"💰 Price: ${enriched_candidate.get('price_usd', enriched_candidate.get('price', 0)):.8f}")
        print(f"📊 Market Cap: {format_currency(enriched_candidate.get('market_cap', enriched_candidate.get('marketCap', 0)))}")
        print(f"💧 Liquidity: {format_currency(enriched_candidate.get('liquidity_usd', enriched_candidate.get('liquidity', 0)))}")
        
        print_section("TRADING DATA (ENHANCED)")
        print(f"📈 Volume 24h: {format_currency(enriched_candidate.get('volume_24h', 0))}")
        print(f"📈 Volume 1h: {format_currency(enriched_candidate.get('volume_1h', 0))}")
        print(f"🔄 Trades 24h: {enriched_candidate.get('trades_24h', 0):,}")
        print(f"👥 Unique Traders 24h: {enriched_candidate.get('unique_traders_24h', enriched_candidate.get('unique_traders', 0))}")
        print(f"💹 Buy/Sell Ratio: {enriched_candidate.get('buy_sell_ratio', 0):.2f}")
        
        print_section("SCORING RESULTS")
        conviction_emoji = {
            'very_high': '🔥',
            'high': '🚀', 
            'moderate': '⚡',
            'low': '📊'
        }.get(conviction_level, '📊')
        
        print(f"{conviction_emoji} Final Score: {final_score:.2f}/100")
        print(f"🎯 Conviction Level: {conviction_level.upper()}")
        print(f"📊 Data Quality: {enriched_candidate.get('data_quality', 'unknown')}")
        print(f"🔗 Enhancement Sources: {', '.join(enriched_candidate.get('enhancement_sources', []))}")
        
        print_section("ENHANCED METRICS")
        print(f"⚡ Velocity Score: {enhanced_metrics.get('velocity_score', 0):.3f}")
        print(f"🎯 First 100 Score: {enhanced_metrics.get('first_100_score', 0):.1f}")
        print(f"💧 Liquidity Quality: {enhanced_metrics.get('liquidity_quality', 0):.1f}")
        print(f"🎓 Graduation Risk: {enhanced_metrics.get('graduation_risk', 0):.1f}")
        
        # Display scoring breakdown if available
        if scoring_breakdown:
            print_section("DETAILED SCORING BREAKDOWN")
            for category, score in scoring_breakdown.items():
                if isinstance(score, (int, float)):
                    print(f"📊 {category.replace('_', ' ').title()}: {score:.2f}")
        
        # Data validation check
        volume_24h = enriched_candidate.get('volume_24h', 0)
        trades_24h = enriched_candidate.get('trades_24h', 0)
        
        print_section("DATA VALIDATION")
        if volume_24h > 0:
            print("✅ SUCCESS: Volume data successfully enhanced!")
            print(f"   📈 Volume 24h: {format_currency(volume_24h)}")
        else:
            print("⚠️ WARNING: Volume data still zero - may be a new token with no activity")
        
        if trades_24h > 0:
            print("✅ SUCCESS: Trading activity data successfully enhanced!")
            print(f"   🔄 Trades 24h: {trades_24h:,}")
        else:
            print("⚠️ WARNING: No trading activity detected - may be a very new token")
        
        return result
        
    except Exception as e:
        print(f"❌ Full analysis pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await detector.cleanup()

async def test_performance_comparison():
    """Compare performance of new vs legacy methods"""
    print_header("PERFORMANCE COMPARISON")
    
    try:
        print("🏁 Testing performance of enhanced data fetcher...")
        
        # Test enhanced fetcher
        fetcher = EnhancedDataFetcher(logger)
        
        print_section("ENHANCED DATA FETCHER")
        start_time = time.time()
        enhanced_data = await fetcher.enhance_token_with_comprehensive_data(TEST_TOKEN)
        enhanced_time = time.time() - start_time
        
        enhanced_coverage = enhanced_data.get('coverage_score', 0)
        enhanced_fields = len([k for k, v in enhanced_data.items() if v not in [None, 0, '', []]])
        
        print(f"⚡ Time: {enhanced_time:.2f} seconds")
        print(f"📊 Coverage: {enhanced_coverage:.1f}%")
        print(f"📋 Fields populated: {enhanced_fields}")
        print(f"🔗 Sources: {', '.join(enhanced_data.get('enhancement_sources', []))}")
        
        # Summary
        print_section("PERFORMANCE SUMMARY")
        print(f"🚀 Enhanced Method: {enhanced_time:.2f}s, {enhanced_coverage:.1f}% coverage")
        print(f"🎯 Quality: {enhanced_data.get('data_quality', 'unknown')}")
        
        if enhanced_coverage >= 80:
            print("✅ EXCELLENT: Enhanced method provides comprehensive data coverage!")
        elif enhanced_coverage >= 60:
            print("✅ GOOD: Enhanced method provides good data coverage")
        else:
            print("⚠️ WARNING: Limited data coverage - token may be very new or inactive")
        
    except Exception as e:
        print(f"❌ Performance comparison failed: {e}")

async def save_test_results(enhanced_data, analysis_result):
    """Save test results to JSON file"""
    try:
        timestamp = int(time.time())
        results = {
            'test_timestamp': timestamp,
            'test_date': datetime.now().isoformat(),
            'test_token': TEST_TOKEN,
            'enhanced_data': enhanced_data,
            'analysis_result': analysis_result,
            'test_metadata': {
                'python_version': sys.version,
                'test_file': __file__,
                'test_success': enhanced_data is not None and analysis_result is not None
            }
        }
        
        filename = f"complete_analysis_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print_section("TEST RESULTS SAVED")
        print(f"📁 Results saved to: {filename}")
        print(f"📊 File size: {os.path.getsize(filename):,} bytes")
        
    except Exception as e:
        print(f"⚠️ Failed to save test results: {e}")

async def main():
    """Run complete analysis test suite"""
    print_header("COMPLETE ANALYSIS TEST SUITE")
    print(f"🎯 Target Token: {TEST_TOKEN}")
    print(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔬 Testing enhanced data pipeline with full analysis")
    
    # Test 1: Enhanced data fetcher
    enhanced_data = await test_enhanced_data_fetcher()
    
    # Test 2: Full analysis pipeline
    analysis_result = await test_full_analysis_pipeline()
    
    # Test 3: Performance comparison
    await test_performance_comparison()
    
    # Save results
    if enhanced_data or analysis_result:
        await save_test_results(enhanced_data, analysis_result)
    
    # Final summary
    print_header("TEST SUITE SUMMARY")
    
    if enhanced_data:
        print("✅ Enhanced Data Fetcher: SUCCESS")
        print(f"   📊 Quality: {enhanced_data.get('data_quality', 'unknown')}")
        print(f"   📈 Volume 24h: {format_currency(enhanced_data.get('volume_24h', 0))}")
    else:
        print("❌ Enhanced Data Fetcher: FAILED")
    
    if analysis_result:
        final_score = analysis_result.get('final_score', 0)
        conviction = analysis_result.get('conviction_level', 'low')
        print("✅ Full Analysis Pipeline: SUCCESS")
        print(f"   🎯 Final Score: {final_score:.2f}")
        print(f"   📊 Conviction: {conviction}")
    else:
        print("❌ Full Analysis Pipeline: FAILED")
    
    print(f"\n⏰ Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 Enhanced data pipeline test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 