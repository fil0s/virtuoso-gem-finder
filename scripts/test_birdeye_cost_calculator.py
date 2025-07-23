#!/usr/bin/env python3
"""
Test script for BirdEye Cost Calculator
Demonstrates the difference between HTTP request tracking and actual compute unit costs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_cost_calculator import BirdEyeCostCalculator
import logging

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_batch_cost_formula():
    """Test the batch cost formula with examples from documentation"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("🧮 BirdEye Batch Cost Formula Test")
    print("=" * 50)
    
    # Test case from BirdEye documentation
    print("\n📊 Example from BirdEye docs: 5 tokens using multi_price")
    cost = calculator.calculate_batch_cost('/defi/multi_price', 5)
    expected = 19  # 5^0.8 × 5 = 18.8 → 19 (rounded up)
    print(f"Calculated cost: {cost} CUs")
    print(f"Expected cost: {expected} CUs")
    print(f"Formula verification: 5^0.8 × 5 = {pow(5, 0.8) * 5:.2f} → {cost} CUs")
    
    # Test various batch sizes
    print("\n📈 Batch Cost Analysis for /defi/multi_price")
    print("-" * 50)
    print("Tokens | Batch Cost | Individual Cost | Savings | Efficiency")
    print("-" * 50)
    
    for num_tokens in [1, 5, 10, 20, 30, 50, 100]:
        batch_cost = calculator.calculate_batch_cost('/defi/multi_price', num_tokens)
        individual_cost = num_tokens * 10  # Assuming 10 CUs per individual call
        savings = individual_cost - batch_cost
        efficiency = (savings / individual_cost * 100) if individual_cost > 0 else 0
        
        print(f"{num_tokens:6d} | {batch_cost:10d} | {individual_cost:13d} | {savings:7d} | {efficiency:8.1f}%")

def test_session_tracking():
    """Test session tracking with realistic API usage"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n🎯 Session Tracking Test")
    print("=" * 50)
    
    # Simulate our 10-scan session
    print("\nSimulating 10-scan session with 30 tokens per scan...")
    
    for scan in range(10):
        print(f"\n--- Scan {scan + 1} ---")
        
        # Token discovery (using individual calls)
        calculator.track_api_call('/defi/v3/token/list', 1, is_batch=False)
        calculator.track_api_call('/defi/v2/tokens/new_listing', 1, is_batch=False)
        
        # Token analysis (using batch calls)
        tokens_per_scan = 30
        
        # Price data (batch)
        price_cost = calculator.track_api_call('/defi/multi_price', tokens_per_scan, is_batch=True)
        
        # Overview data (individual calls - no batch API available)
        overview_cost = calculator.track_api_call('/defi/token_overview', tokens_per_scan, is_batch=False)
        
        # Security data (individual calls)
        security_cost = calculator.track_api_call('/defi/token_security', tokens_per_scan, is_batch=False)
        
        # OHLCV data (individual calls)
        ohlcv_cost = calculator.track_api_call('/defi/v3/ohlcv', tokens_per_scan, is_batch=False)
        
        scan_total = price_cost + overview_cost + security_cost + ohlcv_cost
        print(f"Scan {scan + 1} total: {scan_total} CUs")
    
    # Get session summary
    summary = calculator.get_session_summary()
    
    print("\n📊 Session Summary")
    print("-" * 50)
    print(f"Total HTTP Requests: {summary['total_http_requests']}")
    print(f"Total Compute Units: {summary['total_compute_units']}")
    print(f"Avg CUs per Request: {summary['avg_cus_per_request']}")
    print(f"Batch Savings: {summary['batch_savings_cus']} CUs")
    print(f"Batch Efficiency: {summary['batch_efficiency_percent']}%")
    
    print("\n🔝 Top Cost Endpoints:")
    for endpoint_data in summary['top_cost_endpoints']:
        print(f"  {endpoint_data['endpoint']}: {endpoint_data['total_cus']} CUs "
              f"({endpoint_data['calls']} calls, {endpoint_data['avg_cus_per_call']} CUs/call)")

def test_optimization_opportunities():
    """Test optimization opportunities with additional batch endpoints"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n🚀 Optimization Opportunities")
    print("=" * 50)
    
    # Current approach vs optimized approach
    tokens = 30
    
    print(f"\nAnalyzing {tokens} tokens:")
    print("\n--- CURRENT APPROACH ---")
    
    # Current: individual calls for most endpoints
    current_total = 0
    current_total += calculator.calculate_batch_cost('/defi/multi_price', tokens)  # We do batch this
    current_total += calculator.get_individual_cost('/defi/token_overview') * tokens  # Individual
    current_total += calculator.get_individual_cost('/defi/token_security') * tokens  # Individual
    current_total += calculator.get_individual_cost('/defi/v3/ohlcv') * tokens  # Individual
    
    print(f"Multi-price (batch): {calculator.calculate_batch_cost('/defi/multi_price', tokens)} CUs")
    print(f"Overview (individual): {calculator.get_individual_cost('/defi/token_overview') * tokens} CUs")
    print(f"Security (individual): {calculator.get_individual_cost('/defi/token_security') * tokens} CUs")
    print(f"OHLCV (individual): {calculator.get_individual_cost('/defi/v3/ohlcv') * tokens} CUs")
    print(f"TOTAL: {current_total} CUs")
    
    print("\n--- OPTIMIZED APPROACH ---")
    
    # Optimized: use batch endpoints where available
    optimized_total = 0
    optimized_total += calculator.calculate_batch_cost('/defi/multi_price', tokens)  # Already batched
    optimized_total += calculator.calculate_batch_cost('/defi/v3/token/meta-data/multiple', tokens)  # Could batch
    optimized_total += calculator.get_individual_cost('/defi/token_security') * tokens  # No batch available
    optimized_total += calculator.get_individual_cost('/defi/v3/ohlcv') * tokens  # No batch available
    
    print(f"Multi-price (batch): {calculator.calculate_batch_cost('/defi/multi_price', tokens)} CUs")
    print(f"Meta-data (batch): {calculator.calculate_batch_cost('/defi/v3/token/meta-data/multiple', tokens)} CUs")
    print(f"Security (individual): {calculator.get_individual_cost('/defi/token_security') * tokens} CUs")
    print(f"OHLCV (individual): {calculator.get_individual_cost('/defi/v3/ohlcv') * tokens} CUs")
    print(f"TOTAL: {optimized_total} CUs")
    
    savings = current_total - optimized_total
    efficiency = (savings / current_total * 100) if current_total > 0 else 0
    
    print(f"\n💰 OPTIMIZATION RESULTS:")
    print(f"Current cost: {current_total} CUs")
    print(f"Optimized cost: {optimized_total} CUs")
    print(f"Savings: {savings} CUs ({efficiency:.1f}%)")

def test_monthly_cost_estimation():
    """Test monthly cost estimation"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n💳 Monthly Cost Estimation")
    print("=" * 50)
    
    # Based on our 10-scan session
    scans_per_day = 24 * 6  # Every 10 minutes
    tokens_per_scan = 30
    
    # Estimate daily CUs
    daily_cus = 0
    
    # Per scan costs (using current approach)
    scan_cost = (
        calculator.calculate_batch_cost('/defi/multi_price', tokens_per_scan) +
        calculator.get_individual_cost('/defi/token_overview') * tokens_per_scan +
        calculator.get_individual_cost('/defi/token_security') * tokens_per_scan +
        calculator.get_individual_cost('/defi/v3/ohlcv') * tokens_per_scan +
        calculator.get_individual_cost('/defi/v3/token/list') +
        calculator.get_individual_cost('/defi/v2/tokens/new_listing')
    )
    
    daily_cus = scan_cost * scans_per_day
    
    print(f"Scans per day: {scans_per_day}")
    print(f"Tokens per scan: {tokens_per_scan}")
    print(f"CUs per scan: {scan_cost}")
    print(f"Daily CUs: {daily_cus:,}")
    
    # Cost estimation (assuming $10 per million CUs)
    cost_estimate = calculator.estimate_monthly_cost(daily_cus, 10.0)
    
    print(f"\n💰 Cost Estimates (at $10/million CUs):")
    print(f"Daily cost: ${cost_estimate['cost_per_day_usd']}")
    print(f"Monthly cost: ${cost_estimate['monthly_cost_usd']}")
    print(f"Monthly CUs: {cost_estimate['monthly_cus']:,}")

def test_enhanced_batch_methods():
    """Test the newly implemented batch methods and their cost efficiency"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n🚀 Enhanced Batch Methods Test")
    print("=" * 50)
    
    # Test the additional batch endpoints
    test_endpoints = [
        '/defi/price_volume/multi',
        '/defi/v3/token/meta-data/multiple', 
        '/defi/v3/token/trade-data/multiple',
        '/defi/v3/token/market-data/multiple',
        '/defi/v3/pair/overview/multiple'
    ]
    
    print("\n📊 Batch Cost Analysis for New Endpoints")
    print("-" * 60)
    print("Endpoint                              | Tokens | Batch Cost | Individual | Savings")
    print("-" * 60)
    
    for endpoint in test_endpoints:
        if endpoint in calculator.ENDPOINT_COSTS:
            config = calculator.ENDPOINT_COSTS[endpoint]
            if isinstance(config, dict):
                base_cu = config['base_cu']
                n_max = config['n_max']
                
                # Test with different batch sizes
                for tokens in [10, 20, n_max]:
                    if tokens <= n_max:
                        batch_cost = calculator.calculate_batch_cost(endpoint, tokens)
                        individual_cost = tokens * (base_cu * 2)  # Estimated individual cost
                        savings = individual_cost - batch_cost
                        
                        print(f"{endpoint[:35]:<35} | {tokens:6d} | {batch_cost:10d} | {individual_cost:10d} | {savings:7d}")
    
    print("\n💡 Key Insights:")
    print("- Batch endpoints show significant savings as token count increases")
    print("- Trade and market data endpoints (20 token limit) are perfect for focused analysis")
    print("- Metadata endpoint (50 token limit) ideal for overview data")
    print("- Price/volume endpoint (50 token limit) excellent for market monitoring")

def test_cost_optimization_features():
    """Test cost optimization and recommendation features"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n🎯 Cost Optimization Features Test")
    print("=" * 50)
    
    # Simulate a scanning session with mixed usage patterns
    print("\nSimulating mixed usage patterns...")
    
    # Scenario 1: Heavy individual calls (inefficient)
    print("\n--- SCENARIO 1: Heavy Individual Calls (Inefficient) ---")
    calculator.reset_session()
    
    for i in range(5):
        # Individual token overview calls (expensive)
        calculator.track_api_call('/defi/token_overview', 30, is_batch=False)
        
        # Individual security calls (very expensive)
        calculator.track_api_call('/defi/token_security', 30, is_batch=False)
        
        # Some batch price calls (good)
        calculator.track_api_call('/defi/multi_price', 30, is_batch=True)
    
    inefficient_summary = calculator.get_session_summary()
    print(f"Total CUs (inefficient): {inefficient_summary['total_compute_units']}")
    print(f"Batch efficiency: {inefficient_summary['batch_efficiency_percent']}%")
    
    # Scenario 2: Optimized batch calls
    print("\n--- SCENARIO 2: Optimized Batch Calls (Efficient) ---")
    calculator.reset_session()
    
    for i in range(5):
        # Use batch metadata instead of individual overviews
        calculator.track_api_call('/defi/v3/token/meta-data/multiple', 30, is_batch=True)
        
        # Still need individual security calls (no batch available)
        calculator.track_api_call('/defi/token_security', 30, is_batch=False)
        
        # Batch price calls
        calculator.track_api_call('/defi/multi_price', 30, is_batch=True)
        
        # Add batch price/volume for better data
        calculator.track_api_call('/defi/price_volume/multi', 30, is_batch=True)
    
    efficient_summary = calculator.get_session_summary()
    print(f"Total CUs (efficient): {efficient_summary['total_compute_units']}")
    print(f"Batch efficiency: {efficient_summary['batch_efficiency_percent']}%")
    
    # Calculate optimization impact
    savings = inefficient_summary['total_compute_units'] - efficient_summary['total_compute_units']
    improvement = (savings / inefficient_summary['total_compute_units'] * 100) if inefficient_summary['total_compute_units'] > 0 else 0
    
    print(f"\n💰 OPTIMIZATION IMPACT:")
    print(f"CU Savings: {savings:,} CUs ({improvement:.1f}% reduction)")
    print(f"Efficiency Improvement: {efficient_summary['batch_efficiency_percent'] - inefficient_summary['batch_efficiency_percent']:.1f} percentage points")
    
    # Monthly cost impact
    daily_savings = savings * 144  # Assuming 144 scans per day (every 10 minutes)
    monthly_savings = daily_savings * 30
    cost_savings_usd = (monthly_savings / 1_000_000) * 10  # $10 per million CUs
    
    print(f"\n📊 MONTHLY IMPACT:")
    print(f"Daily CU savings: {daily_savings:,}")
    print(f"Monthly CU savings: {monthly_savings:,}")
    print(f"Monthly cost savings: ${cost_savings_usd:.2f}")

def test_real_world_scenarios():
    """Test real-world usage scenarios"""
    logger = setup_logging()
    calculator = BirdEyeCostCalculator(logger)
    
    print("\n\n🌍 Real-World Scenarios Test")
    print("=" * 50)
    
    scenarios = [
        {
            'name': 'Small Scale Monitoring',
            'scans_per_day': 24,  # Every hour
            'tokens_per_scan': 10,
            'description': 'Hourly monitoring of 10 key tokens'
        },
        {
            'name': 'Medium Scale Discovery', 
            'scans_per_day': 144,  # Every 10 minutes
            'tokens_per_scan': 30,
            'description': 'High-frequency discovery of 30 tokens'
        },
        {
            'name': 'Large Scale Analysis',
            'scans_per_day': 288,  # Every 5 minutes
            'tokens_per_scan': 50,
            'description': 'Intensive analysis of 50 tokens'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name'].upper()} ---")
        print(f"Description: {scenario['description']}")
        
        calculator.reset_session()
        
        # Simulate one day of usage
        tokens = scenario['tokens_per_scan']
        scans = scenario['scans_per_day']
        
        # Per scan costs (optimized approach)
        scan_cost = (
            calculator.calculate_batch_cost('/defi/multi_price', tokens) +
            calculator.calculate_batch_cost('/defi/v3/token/meta-data/multiple', min(tokens, 50)) +
            calculator.get_individual_cost('/defi/token_security') * tokens +  # No batch available
            calculator.calculate_batch_cost('/defi/price_volume/multi', min(tokens, 50)) +
            calculator.get_individual_cost('/defi/v3/token/list') +
            calculator.get_individual_cost('/defi/v2/tokens/new_listing')
        )
        
        daily_cus = scan_cost * scans
        monthly_estimate = calculator.estimate_monthly_cost(daily_cus, 10.0)
        
        print(f"Tokens per scan: {tokens}")
        print(f"Scans per day: {scans}")
        print(f"CUs per scan: {scan_cost}")
        print(f"Daily CUs: {daily_cus:,}")
        print(f"Monthly cost: ${monthly_estimate['monthly_cost_usd']}")
        
        # Efficiency assessment
        if monthly_estimate['monthly_cost_usd'] < 50:
            efficiency = "🟢 Excellent"
        elif monthly_estimate['monthly_cost_usd'] < 150:
            efficiency = "🟡 Good"
        else:
            efficiency = "🔴 Consider optimization"
        
        print(f"Cost assessment: {efficiency}")

if __name__ == "__main__":
    print("🔍 BirdEye Cost Calculator Analysis")
    print("Testing implementation of batch cost formula N^0.8 × Base CU Cost")
    print("Based on: https://docs.birdeye.so/docs/batch-token-cu-cost")
    
    test_batch_cost_formula()
    test_session_tracking()
    test_optimization_opportunities()
    test_monthly_cost_estimation()
    
    # NEW: Test the enhanced batch methods and cost optimization
    test_enhanced_batch_methods()
    test_cost_optimization_features()
    
    print("\n✅ Analysis Complete!")
    print("\nKey Findings:")
    print("1. We ARE using batch APIs correctly for multi_price")
    print("2. We are NOT implementing the cost formula for tracking")
    print("3. We could use additional batch endpoints for more savings")
    print("4. Proper cost tracking would show actual compute unit consumption")
    print("5. This explains part of our API usage discrepancy")

    test_real_world_scenarios() 