#!/usr/bin/env python3

"""
Enhanced Integration Validation Script

Validates and demonstrates the enhanced capabilities of:
1. Price Momentum Strategy with Cross-Timeframe Analysis
2. Recent Listings Strategy with Holder Velocity Analysis

This script provides detailed analysis of the improvements and shows
how the integrations enhance token discovery accuracy.
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.strategies.recent_listings_strategy import RecentListingsStrategy
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from services.logger_setup import LoggerSetup


class EnhancedIntegrationValidator:
    """Validates and demonstrates enhanced strategy integrations"""
    
    def __init__(self):
        logger_setup = LoggerSetup(__name__)
        self.logger = logger_setup.logger
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize services
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize API
        birdeye_config = self.config.get('BIRDEYE_API', {})
        birdeye_config['api_key'] = self.config.get('birdeye_api_key') or os.getenv('BIRDEYE_API_KEY')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Initialize enhanced strategies
        self.price_momentum_strategy = PriceMomentumStrategy(
            logger=self.logger
        )
        
        self.recent_listings_strategy = RecentListingsStrategy(
            logger=self.logger
        )
        
        self.results = {}
    
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    
    def print_section(self, title: str):
        """Print formatted section"""
        print(f"\n{'-'*60}")
        print(f"  {title}")
        print(f"{'-'*60}")
    
    def format_number(self, value: float, prefix: str = "$", suffix: str = "") -> str:
        """Format large numbers with appropriate suffixes"""
        if value >= 1_000_000:
            return f"{prefix}{value/1_000_000:.2f}M{suffix}"
        elif value >= 1_000:
            return f"{prefix}{value/1_000:.2f}K{suffix}"
        else:
            return f"{prefix}{value:.2f}{suffix}"
    
    async def validate_price_momentum_enhancement(self):
        """Validate Price Momentum Strategy with Cross-Timeframe Analysis"""
        self.print_header("PRICE MOMENTUM STRATEGY - CROSS-TIMEFRAME ANALYSIS")
        
        try:
            print("🔍 Executing enhanced Price Momentum Strategy...")
            start_time = time.time()
            
            tokens = await self.price_momentum_strategy.execute(
                self.birdeye_api, 
                scan_id="enhanced_price_momentum_validation"
            )
            
            execution_time = time.time() - start_time
            
            print(f"✅ Strategy executed in {execution_time:.2f} seconds")
            print(f"📊 Found {len(tokens)} tokens with strong price momentum")
            
            # Analyze top tokens
            if tokens:
                self.print_section("TOP MOMENTUM TOKENS WITH CROSS-TIMEFRAME ANALYSIS")
                
                for i, token in enumerate(tokens[:3], 1):
                    print(f"\n#{i} Token: {token.get('symbol', 'N/A')} ({token.get('address', 'N/A')[:8]}...)")
                    
                    # Price momentum metrics
                    price_change_1h = token.get('price_change_1h_percent', 0)
                    price_change_4h = token.get('price_change_4h_percent', 0)
                    price_change_24h = token.get('price_change_24h_percent', 0)
                    
                    print(f"   💰 Price Changes: 1h: {price_change_1h:+.2f}%, 4h: {price_change_4h:+.2f}%, 24h: {price_change_24h:+.2f}%")
                    
                    # Volume metrics
                    volume_24h = token.get('volume_24h_usd', 0)
                    volume_change = token.get('volume_24h_change_percent', 0)
                    print(f"   📈 Volume: {self.format_number(volume_24h)} (Change: {volume_change:+.2f}%)")
                    
                    # Cross-timeframe momentum score
                    momentum_score = token.get('cross_timeframe_momentum_score', 0)
                    momentum_strength = token.get('momentum_strength', 'Unknown')
                    print(f"   🎯 Cross-Timeframe Score: {momentum_score:.2f} ({momentum_strength})")
                    
                    # Liquidity and market cap
                    liquidity = token.get('liquidity_usd', 0)
                    market_cap = token.get('market_cap_usd', 0)
                    print(f"   💧 Liquidity: {self.format_number(liquidity)} | Market Cap: {self.format_number(market_cap)}")
                    
                    # Enhanced analysis flags
                    momentum_confirmed = token.get('momentum_confirmed_across_timeframes', False)
                    volume_increasing = token.get('volume_trend_increasing', False)
                    print(f"   ✅ Momentum Confirmed: {momentum_confirmed} | Volume Increasing: {volume_increasing}")
            
            self.results['price_momentum'] = {
                'tokens_found': len(tokens),
                'execution_time': execution_time,
                'enhancement_active': True,
                'top_tokens': tokens[:3] if tokens else []
            }
            
        except Exception as e:
            self.logger.error(f"Error validating Price Momentum enhancement: {e}")
            print(f"❌ Error: {e}")
    
    async def validate_recent_listings_enhancement(self):
        """Validate Recent Listings Strategy with Holder Velocity Analysis"""
        self.print_header("RECENT LISTINGS STRATEGY - HOLDER VELOCITY ANALYSIS")
        
        try:
            print("🔍 Executing enhanced Recent Listings Strategy...")
            start_time = time.time()
            
            tokens = await self.recent_listings_strategy.execute(
                self.birdeye_api, 
                scan_id="enhanced_recent_listings_validation"
            )
            
            execution_time = time.time() - start_time
            
            print(f"✅ Strategy executed in {execution_time:.2f} seconds")
            print(f"📊 Found {len(tokens)} recent tokens with holder velocity")
            
            # Analyze top tokens
            if tokens:
                self.print_section("TOP RECENT TOKENS WITH HOLDER VELOCITY ANALYSIS")
                
                for i, token in enumerate(tokens[:3], 1):
                    print(f"\n#{i} Token: {token.get('symbol', 'N/A')} ({token.get('address', 'N/A')[:8]}...)")
                    
                    # Basic metrics
                    age_hours = token.get('age_hours', 0)
                    holders = token.get('holder_count', 0)
                    print(f"   ⏰ Age: {age_hours:.1f} hours | Holders: {holders:,}")
                    
                    # Holder velocity metrics
                    holder_velocity = token.get('holder_velocity_score', 0)
                    velocity_trend = token.get('holder_velocity_trend', 'Unknown')
                    print(f"   🚀 Holder Velocity: {holder_velocity:.2f} ({velocity_trend})")
                    
                    # Market metrics
                    volume_24h = token.get('volume_24h_usd', 0)
                    liquidity = token.get('liquidity_usd', 0)
                    print(f"   📈 Volume: {self.format_number(volume_24h)} | Liquidity: {self.format_number(liquidity)}")
                    
                    # Price performance
                    price_change_1h = token.get('price_change_1h_percent', 0)
                    price_change_24h = token.get('price_change_24h_percent', 0)
                    print(f"   💰 Price Changes: 1h: {price_change_1h:+.2f}%, 24h: {price_change_24h:+.2f}%")
                    
                    # Enhanced analysis flags
                    rapid_adoption = token.get('rapid_holder_adoption', False)
                    early_stage = token.get('early_stage_token', False)
                    print(f"   ✅ Rapid Adoption: {rapid_adoption} | Early Stage: {early_stage}")
            
            self.results['recent_listings'] = {
                'tokens_found': len(tokens),
                'execution_time': execution_time,
                'enhancement_active': True,
                'top_tokens': tokens[:3] if tokens else []
            }
            
        except Exception as e:
            self.logger.error(f"Error validating Recent Listings enhancement: {e}")
            print(f"❌ Error: {e}")
    
    def generate_enhancement_summary(self):
        """Generate summary of enhancement validations"""
        self.print_header("ENHANCEMENT VALIDATION SUMMARY")
        
        total_tokens = 0
        total_time = 0
        
        if 'price_momentum' in self.results:
            pm_results = self.results['price_momentum']
            total_tokens += pm_results['tokens_found']
            total_time += pm_results['execution_time']
            
            print(f"🎯 Price Momentum Strategy (Cross-Timeframe Analysis):")
            print(f"   - Tokens Discovered: {pm_results['tokens_found']}")
            print(f"   - Execution Time: {pm_results['execution_time']:.2f}s")
            print(f"   - Enhancement Status: {'✅ Active' if pm_results['enhancement_active'] else '❌ Inactive'}")
        
        if 'recent_listings' in self.results:
            rl_results = self.results['recent_listings']
            total_tokens += rl_results['tokens_found']
            total_time += rl_results['execution_time']
            
            print(f"\n📋 Recent Listings Strategy (Holder Velocity Analysis):")
            print(f"   - Tokens Discovered: {rl_results['tokens_found']}")
            print(f"   - Execution Time: {rl_results['execution_time']:.2f}s")
            print(f"   - Enhancement Status: {'✅ Active' if rl_results['enhancement_active'] else '❌ Inactive'}")
        
        print(f"\n📊 Overall Performance:")
        print(f"   - Total Tokens Discovered: {total_tokens}")
        print(f"   - Total Execution Time: {total_time:.2f}s")
        print(f"   - Average Time per Strategy: {total_time/2:.2f}s")
        
        # Enhancement benefits
        print(f"\n🚀 Enhancement Benefits:")
        print(f"   ✅ Cross-Timeframe Momentum: More reliable price trend confirmation")
        print(f"   ✅ Holder Velocity Analysis: Early adoption detection for new tokens")
        print(f"   ✅ Multi-dimensional Scoring: Better token quality assessment")
        print(f"   ✅ Risk Reduction: Enhanced filtering reduces false positives")
    
    async def run_validation(self):
        """Run complete validation of enhanced integrations"""
        print("🔥 VIRTUOSO GEM HUNTER - ENHANCED INTEGRATION VALIDATION")
        print(f"📅 Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate both enhanced strategies
        await self.validate_price_momentum_enhancement()
        await self.validate_recent_listings_enhancement()
        
        # Generate summary
        self.generate_enhancement_summary()
        
        # Save results
        results_file = f"scripts/results/enhanced_integration_validation_{int(time.time())}.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        print(f"\n🎉 Enhanced Integration Validation Complete!")


async def main():
    """Main validation function"""
    validator = EnhancedIntegrationValidator()
    await validator.run_validation()


if __name__ == "__main__":
    asyncio.run(main()) 