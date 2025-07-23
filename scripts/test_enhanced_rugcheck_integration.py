#!/usr/bin/env python3
"""
Enhanced RugCheck Integration Test

This script demonstrates the new RugCheck capabilities that can help optimize
Birdeye API usage by pre-filtering and routing tokens based on quality assessment.
"""

import asyncio
import logging
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.rugcheck_connector import RugCheckConnector
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from utils.logger_setup import LoggerSetup


class EnhancedRugCheckDemo:
    
    def __init__(self):
        # Setup logging
        logger_setup = LoggerSetup("EnhancedRugCheckDemo")
        self.logger = logger_setup.logger
        
        # Setup configuration
        self.config_manager = ConfigManager()
        
        # Initialize connectors
        self.rugcheck = RugCheckConnector(logger=self.logger)
        
        # Test token addresses (mix of different quality levels)
        self.test_tokens = [
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC - high quality
            "So11111111111111111111111111111111111111112",   # SOL - high quality  
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",   # mSOL - medium quality
            # Add more test tokens as needed
        ]
    
    async def demo_token_age_optimization(self):
        """Demonstrate token age-based timeframe optimization"""
        print("\n🕐 DEMO: Token Age-Based Timeframe Optimization")
        print("=" * 60)
        
        for token_address in self.test_tokens:
            try:
                # Get token age information
                age_info = await self.rugcheck.get_token_age_info(token_address)
                
                # Get optimal timeframe
                optimal_timeframe = await self.rugcheck.get_optimal_birdeye_timeframe(token_address)
                
                print(f"\nToken: {token_address[:8]}...")
                print(f"  Age: {age_info.get('age_days', 'Unknown')} days")
                print(f"  Category: {age_info.get('age_category', 'Unknown')}")
                print(f"  Optimal Timeframe: {optimal_timeframe}")
                print(f"  💡 This saves Birdeye API calls by avoiding long timeframes for new tokens!")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    async def demo_pre_validation(self):
        """Demonstrate pre-validation before Birdeye analysis"""
        print("\n🔍 DEMO: Pre-Validation for Birdeye Analysis")
        print("=" * 60)
        
        # Pre-validate tokens
        validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(self.test_tokens)
        
        print(f"\nValidated {len(self.test_tokens)} tokens:")
        
        for token_address, result in validation_results.items():
            print(f"\nToken: {token_address[:8]}...")
            print(f"  Recommended for Analysis: {'✅' if result['recommended_for_analysis'] else '❌'}")
            print(f"  Priority: {result['analysis_priority'].upper()}")
            print(f"  Liquidity Pools: {'✅' if result['liquidity_pools_healthy'] else '❌'}")
            print(f"  Holder Distribution: {'✅' if result['holder_distribution_healthy'] else '❌'}")
            print(f"  Trading Patterns: {'✅' if result['trading_patterns_clean'] else '❌'}")
            print(f"  Contract Verified: {'✅' if result['contract_verified'] else '❌'}")
            
            if result['reasons']:
                print(f"  Issues: {', '.join(result['reasons'])}")
        
        # Show potential API call savings
        recommended_count = sum(1 for r in validation_results.values() if r['recommended_for_analysis'])
        saved_calls = len(self.test_tokens) - recommended_count
        
        print(f"\n💰 SAVINGS ANALYSIS:")
        print(f"  Total tokens: {len(self.test_tokens)}")
        print(f"  Recommended for analysis: {recommended_count}")
        print(f"  Potential Birdeye API calls saved: {saved_calls}")
        print(f"  💡 This prevents expensive analysis on low-quality tokens!")
    
    async def demo_quality_routing(self):
        """Demonstrate quality-based token routing"""
        print("\n🎯 DEMO: Quality-Based Token Routing")
        print("=" * 60)
        
        # Create mock token data
        mock_tokens = [
            {"address": addr, "symbol": f"TOKEN_{i}", "name": f"Test Token {i}"}
            for i, addr in enumerate(self.test_tokens)
        ]
        
        # Get security analysis for routing
        rugcheck_results = {}
        for token_address in self.test_tokens:
            try:
                result = await self.rugcheck.analyze_token_security(token_address)
                rugcheck_results[token_address] = result
            except Exception as e:
                print(f"  ⚠️ Could not analyze {token_address[:8]}...: {e}")
        
        # Get validation results
        validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(self.test_tokens)
        
        # Route tokens by quality
        routing = self.rugcheck.route_tokens_by_quality(
            mock_tokens, 
            rugcheck_results, 
            validation_results
        )
        
        print(f"\n📊 ROUTING RESULTS:")
        print(f"  🏆 Premium Analysis: {len(routing['premium_analysis'])} tokens")
        print(f"     → Full Birdeye analysis (OHLCV, transactions, holders, etc.)")
        
        print(f"  📈 Standard Analysis: {len(routing['standard_analysis'])} tokens") 
        print(f"     → Basic Birdeye analysis (price, volume, basic metrics)")
        
        print(f"  📊 Minimal Analysis: {len(routing['minimal_analysis'])} tokens")
        print(f"     → Price-only analysis (cheapest API calls)")
        
        print(f"  🚫 Skip Analysis: {len(routing['skip_analysis'])} tokens")
        print(f"     → No Birdeye API calls (security risks detected)")
        
        # Show detailed breakdown
        for category, tokens in routing.items():
            if tokens:
                print(f"\n{category.upper().replace('_', ' ')}:")
                for token in tokens:
                    addr = token['address']
                    rugcheck_result = rugcheck_results.get(addr)
                    risk_level = rugcheck_result.risk_level.value if rugcheck_result else 'unknown'
                    print(f"  • {token['symbol']} ({addr[:8]}...) - Risk: {risk_level}")
    
    async def demo_integration_workflow(self):
        """Demonstrate complete integration workflow"""
        print("\n🔄 DEMO: Complete Integration Workflow")
        print("=" * 60)
        
        start_time = time.time()
        
        print("Step 1: Token Discovery (simulated)")
        discovered_tokens = [
            {"address": addr, "symbol": f"DISCOVERED_{i}", "volume_24h": 1000000 + i * 100000}
            for i, addr in enumerate(self.test_tokens)
        ]
        print(f"  📝 Discovered {len(discovered_tokens)} tokens")
        
        print("\nStep 2: RugCheck Security Analysis")
        rugcheck_results = await self.rugcheck.batch_analyze_tokens(self.test_tokens)
        secure_tokens = [token for token in discovered_tokens 
                        if rugcheck_results.get(token['address'], {}).is_healthy]
        print(f"  🛡️ {len(secure_tokens)} tokens passed security checks")
        
        print("\nStep 3: Pre-Validation for Birdeye Analysis")
        validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(
            [token['address'] for token in secure_tokens]
        )
        validated_tokens = [token for token in secure_tokens 
                           if validation_results.get(token['address'], {}).get('recommended_for_analysis')]
        print(f"  🔍 {len(validated_tokens)} tokens recommended for detailed analysis")
        
        print("\nStep 4: Quality-Based Routing")
        routing = self.rugcheck.route_tokens_by_quality(
            validated_tokens, rugcheck_results, validation_results
        )
        print(f"  🎯 Tokens routed by analysis priority")
        
        print("\nStep 5: Optimized Birdeye API Usage")
        total_api_calls_saved = 0
        
        # Premium analysis: Full API calls
        premium_calls = len(routing['premium_analysis']) * 5  # Assume 5 calls per premium token
        
        # Standard analysis: Reduced API calls  
        standard_calls = len(routing['standard_analysis']) * 3  # Assume 3 calls per standard token
        
        # Minimal analysis: Minimal API calls
        minimal_calls = len(routing['minimal_analysis']) * 1  # Assume 1 call per minimal token
        
        # Skipped: No API calls
        skipped_calls = len(routing['skip_analysis']) * 0
        
        total_optimized_calls = premium_calls + standard_calls + minimal_calls + skipped_calls
        total_naive_calls = len(discovered_tokens) * 5  # If we analyzed all tokens fully
        
        saved_calls = total_naive_calls - total_optimized_calls
        savings_percentage = (saved_calls / total_naive_calls) * 100 if total_naive_calls > 0 else 0
        
        print(f"  📊 Naive approach: {total_naive_calls} API calls")
        print(f"  📊 Optimized approach: {total_optimized_calls} API calls")  
        print(f"  💰 API calls saved: {saved_calls} ({savings_percentage:.1f}%)")
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️ Total workflow time: {elapsed_time:.2f} seconds")
        
        print(f"\n✨ BENEFITS:")
        print(f"  • Prevented analysis of {len(discovered_tokens) - len(secure_tokens)} risky tokens")
        print(f"  • Saved {saved_calls} expensive API calls ({savings_percentage:.1f}% reduction)")
        print(f"  • Focused resources on {len(routing['premium_analysis'])} high-quality opportunities")
        print(f"  • Reduced false positives and improved analysis efficiency")

    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        print("🚀 ENHANCED RUGCHECK INTEGRATION DEMO")
        print("=" * 70)
        print("Demonstrating how RugCheck API can optimize Birdeye API usage")
        
        try:
            await self.demo_token_age_optimization()
            await self.demo_pre_validation()
            await self.demo_quality_routing()
            await self.demo_integration_workflow()
            
            print("\n🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
            print("\nTo implement these optimizations in your system:")
            print("1. Use token age info to select optimal Birdeye timeframes")
            print("2. Pre-validate tokens before expensive Birdeye analysis")
            print("3. Route tokens by quality to optimize API resource allocation")
            print("4. Combine all techniques for maximum efficiency")
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            print(f"\n❌ Demo failed: {e}")


async def main():
    """Main demo function"""
    demo = EnhancedRugCheckDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main()) 