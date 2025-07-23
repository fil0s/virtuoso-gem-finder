#!/usr/bin/env python3
"""
API Data Limitations Investigation Script

This script investigates why smart trader identification is failing by:
1. Examining raw BirdEye API responses for top traders
2. Analyzing whale detection logic step-by-step
3. Showing why tokens fail whale criteria
4. Providing data-driven threshold recommendations

Usage: python scripts/investigate_api_data_limitations.py
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from services.smart_money_detector import SmartMoneyDetector
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager

class APIDataInvestigator:
    """Investigates API data limitations for smart trader identification"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup("APIDataInvestigator")
        self.logger = self.logger_setup.logger
        self.config_manager = ConfigManager()
        self.birdeye_api = None
        self.whale_tracker = None
        self.smart_money_detector = None
        
        # Tokens from the recent failed run
        self.test_tokens = [
            "9doRRAik5gvhbEwjbZDbZR6GxXSAfdoomyJR57xKpump",
            "CreiuhfwdWCN5mJbMJtA9bBpYQrQF2tCBuZwSPWfpump",
            "JosjEXh69RckgSs2AWsN1xN8zmiSHxBuJjHLURJnHhg",
            "JDzPbXboQYWVmdxXS3LbvjM52RtsV1QaSv2AzoCiai2o",
            "Bybit2vBJGhPF52GBdNaQfUJ6ZpThSgHBobjWZpLPb4B",
            "Hax9LTgsQkze1YFychnBLtFH8gYbQKtKfWKKg2SP6gdD",
            "fRfKGCriduzDwSudCwpL7ySCEiboNuryhZDVJtr1a1C"
        ]
        
        # Threshold levels for comparison
        self.threshold_levels = {
            "Level 1": {"min_whale_volume": 500000, "min_smart_traders": 3},
            "Level 2": {"min_whale_volume": 400000, "min_smart_traders": 2},
            "Level 3": {"min_whale_volume": 300000, "min_smart_traders": 2},
            "Level 4": {"min_whale_volume": 200000, "min_smart_traders": 1},
            "Level 5": {"min_whale_volume": 100000, "min_smart_traders": 1}
        }
    
    async def initialize_services(self):
        """Initialize API services"""
        try:
            self.logger.info("🔧 Initializing API services...")
            
            # Check API key
            api_key = os.getenv('BIRDEYE_API_KEY')
            if not api_key:
                raise ValueError("BIRDEYE_API_KEY environment variable not set")
            
            # Initialize supporting services
            from core.cache_manager import CacheManager
            from services.rate_limiter_service import RateLimiterService
            
            cache_manager = CacheManager()
            rate_limiter = RateLimiterService()
            
            # Create config for BirdeyeAPI
            config = {
                'api_key': api_key,
                'base_url': 'https://public-api.birdeye.so',
                'rate_limit': 100,
                'request_timeout_seconds': 20,
                'cache_ttl_default_seconds': 300,
                'cache_ttl_error_seconds': 60,
                'max_retries': 3,
                'backoff_factor': 2
            }
            
            # Create logger for BirdeyeAPI
            birdeye_logger_setup = LoggerSetup("BirdeyeAPI")
            birdeye_logger = birdeye_logger_setup.logger
            
            # Initialize BirdEye API with proper parameters
            self.birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
            
            # Initialize whale tracker with proper parameters
            whale_logger_setup = LoggerSetup("WhaleTracker")
            whale_logger = whale_logger_setup.logger
            self.whale_tracker = WhaleSharkMovementTracker(self.birdeye_api, whale_logger)
            
            # Initialize smart money detector with proper parameters
            smart_logger_setup = LoggerSetup("SmartMoneyDetector")
            smart_logger = smart_logger_setup.logger
            self.smart_money_detector = SmartMoneyDetector(self.whale_tracker, smart_logger)
            
            self.logger.info("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize services: {e}")
            return False
    
    async def fetch_raw_trader_data(self, token_address: str) -> Optional[Dict]:
        """Fetch raw top traders data from BirdEye API"""
        try:
            self.logger.info(f"📡 Fetching raw trader data for {token_address[:8]}...")
            
            # Use the same parameters as the strategy
            params = {
                'address': token_address,
                'type': '24h',
                'sort_by': 'volume',
                'sort_type': 'desc',
                'limit': 10,
                'offset': 0
            }
            
            # Fetch data using the optimized method
            response = await self.birdeye_api.get_top_traders_optimized(
                token_address=token_address,
                time_frame='24h',
                sort_by='volume',
                sort_type='desc',
                limit=10,
                offset=0
            )
            
            if response and isinstance(response, list):
                # Direct list response
                self.logger.info(f"✅ Got {len(response)} traders for {token_address[:8]}")
                return {'data': response}
            elif response and isinstance(response, dict):
                # Check different possible response structures
                if 'data' in response:
                    data = response['data']
                    if isinstance(data, list):
                        self.logger.info(f"✅ Got {len(data)} traders for {token_address[:8]}")
                        return response
                    elif isinstance(data, dict) and 'items' in data:
                        items = data['items']
                        self.logger.info(f"✅ Got {len(items)} traders for {token_address[:8]}")
                        return {'data': items}
                elif 'items' in response:
                    items = response['items']
                    self.logger.info(f"✅ Got {len(items)} traders for {token_address[:8]}")
                    return {'data': items}
                elif 'success' in response and response.get('success'):
                    # BirdEye format with success flag
                    self.logger.info(f"✅ Got successful response for {token_address[:8]}")
                    return response
                else:
                    self.logger.warning(f"⚠️ Unexpected response structure for {token_address[:8]}: {list(response.keys())}")
                    return response  # Return anyway for analysis
            else:
                self.logger.warning(f"⚠️ No data returned for {token_address[:8]}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching trader data for {token_address[:8]}: {e}")
            return None
    
    def analyze_trader_data(self, token_address: str, raw_data: Dict) -> Dict:
        """Analyze trader data and calculate whale metrics"""
        analysis = {
            'token': token_address[:8],
            'total_traders': 0,
            'traders_with_volume': 0,
            'total_volume': 0,
            'whale_candidates': [],
            'volume_distribution': [],
            'data_quality_issues': []
        }
        
        try:
            traders = raw_data.get('data', [])
            analysis['total_traders'] = len(traders)
            
            if not traders:
                analysis['data_quality_issues'].append("No trader data returned")
                return analysis
            
            # Analyze each trader
            for i, trader in enumerate(traders):
                # Extract volume using the correct field names from API response
                volume_usd = float(trader.get('volume', 0))  # The main volume field
                
                trader_analysis = {
                    'rank': i + 1,
                    'address': trader.get('owner', trader.get('address', 'Unknown'))[:8],
                    'volume_24h': volume_usd,
                    'volume_usd': volume_usd,
                    'trade_count': trader.get('trade', trader.get('trades', 0)),
                    'pnl': trader.get('pnl', 0),
                    'pnl_percentage': trader.get('pnlPercentage', 0),
                    'volume_buy': trader.get('volumeBuy', 0),
                    'volume_sell': trader.get('volumeSell', 0),
                    'trade_buy': trader.get('tradeBuy', 0),
                    'trade_sell': trader.get('tradeSell', 0)
                }
                
                self.logger.debug(f"Trader {i+1}: {trader_analysis['address']} - Volume: ${volume_usd:,.2f}")
                
                # Check if this could be a whale
                volume_usd = trader_analysis['volume_usd']
                if volume_usd > 0:
                    analysis['traders_with_volume'] += 1
                    analysis['total_volume'] += volume_usd
                    
                    # Check against threshold levels
                    whale_levels = []
                    for level, thresholds in self.threshold_levels.items():
                        if volume_usd >= thresholds['min_whale_volume']:
                            whale_levels.append(level)
                    
                    trader_analysis['qualifies_as_whale'] = whale_levels
                    
                    if whale_levels:
                        analysis['whale_candidates'].append(trader_analysis)
                
                analysis['volume_distribution'].append(trader_analysis)
            
            # Calculate summary metrics
            if analysis['traders_with_volume'] > 0:
                analysis['avg_volume'] = analysis['total_volume'] / analysis['traders_with_volume']
                analysis['max_volume'] = max(t['volume_usd'] for t in analysis['volume_distribution'])
                analysis['min_volume'] = min(t['volume_usd'] for t in analysis['volume_distribution'] if t['volume_usd'] > 0)
            
        except Exception as e:
            analysis['data_quality_issues'].append(f"Analysis error: {str(e)}")
        
        return analysis
    
    async def test_whale_detection_logic(self, token_address: str, raw_data: Dict) -> Dict:
        """Test whale detection logic step by step"""
        try:
            self.logger.info(f"🐋 Testing whale detection for {token_address[:8]}...")
            
            # Use whale tracker to analyze movements
            whale_analysis = await self.whale_tracker.analyze_whale_shark_movements(
                token_address, priority_level='normal'
            )
            
            # Extract whale data from correct structure
            whale_data = whale_analysis.get('whale_analysis', {}) if whale_analysis else {}
            top_whales = whale_data.get('top_whales', [])
            whale_count = whale_data.get('count', 0)
            whale_volume = whale_data.get('total_volume', 0)
            
            return {
                'token': token_address[:8],
                'whale_analysis': whale_analysis,
                'whale_count': whale_count,
                'whale_volume': whale_volume,
                'top_whales': top_whales
            }
            
        except Exception as e:
            self.logger.error(f"❌ Whale detection error for {token_address[:8]}: {e}")
            return {
                'token': token_address[:8],
                'error': str(e),
                'whale_count': 0,
                'whale_volume': 0
            }
    
    async def test_smart_money_detection(self, token_address: str) -> Dict:
        """Test smart money detection logic"""
        try:
            self.logger.info(f"🧠 Testing smart money detection for {token_address[:8]}...")
            
            # Use smart money detector
            smart_analysis = await self.smart_money_detector.analyze_smart_money(
                token_address
            )
            
            # Extract smart money data from correct structure
            skilled_traders = smart_analysis.get('skilled_traders', []) if smart_analysis else []
            skill_metrics = smart_analysis.get('skill_metrics', {}) if smart_analysis else {}
            avg_skill_score = skill_metrics.get('average_skill_score', 0)
            
            return {
                'token': token_address[:8],
                'smart_analysis': smart_analysis,
                'smart_trader_count': len(skilled_traders),
                'avg_skill_score': avg_skill_score,
                'skilled_traders': skilled_traders
            }
            
        except Exception as e:
            self.logger.error(f"❌ Smart money detection error for {token_address[:8]}: {e}")
            return {
                'token': token_address[:8],
                'error': str(e),
                'smart_trader_count': 0,
                'avg_skill_score': 0
            }
    
    def generate_threshold_recommendations(self, all_analyses: List[Dict]) -> Dict:
        """Generate data-driven threshold recommendations"""
        recommendations = {
            'current_market_reality': {},
            'suggested_thresholds': {},
            'data_insights': []
        }
        
        # Analyze current market data
        all_volumes = []
        all_whale_counts = []
        all_smart_trader_counts = []
        
        for analysis in all_analyses:
            if 'trader_analysis' in analysis:
                ta = analysis['trader_analysis']
                if ta['total_volume'] > 0:
                    all_volumes.append(ta['total_volume'])
                if ta['whale_candidates']:
                    all_whale_counts.append(len(ta['whale_candidates']))
            
            if 'whale_detection' in analysis:
                wd = analysis['whale_detection']
                all_whale_counts.append(wd['whale_count'])
            
            if 'smart_money_detection' in analysis:
                smd = analysis['smart_money_detection']
                all_smart_trader_counts.append(smd['smart_trader_count'])
        
        # Calculate market reality
        if all_volumes:
            recommendations['current_market_reality']['avg_total_volume'] = sum(all_volumes) / len(all_volumes)
            recommendations['current_market_reality']['max_total_volume'] = max(all_volumes)
            recommendations['current_market_reality']['min_total_volume'] = min(all_volumes)
        
        if all_whale_counts:
            recommendations['current_market_reality']['avg_whale_count'] = sum(all_whale_counts) / len(all_whale_counts)
            recommendations['current_market_reality']['max_whale_count'] = max(all_whale_counts)
        
        if all_smart_trader_counts:
            recommendations['current_market_reality']['avg_smart_trader_count'] = sum(all_smart_trader_counts) / len(all_smart_trader_counts)
            recommendations['current_market_reality']['max_smart_trader_count'] = max(all_smart_trader_counts)
        
        # Generate suggestions
        avg_volume = recommendations['current_market_reality'].get('avg_total_volume', 0)
        if avg_volume > 0:
            recommendations['suggested_thresholds']['min_whale_volume'] = int(avg_volume * 0.1)  # 10% of average
            recommendations['suggested_thresholds']['min_smart_traders'] = 1  # Start with 1
            recommendations['data_insights'].append(f"Average total volume: ${avg_volume:,.0f}")
            recommendations['data_insights'].append(f"Suggested whale threshold: ${int(avg_volume * 0.1):,}")
        
        return recommendations
    
    async def run_investigation(self):
        """Run the complete API data investigation"""
        self.logger.info("🔍 Starting API Data Limitations Investigation")
        self.logger.info("=" * 60)
        
        # Initialize services
        if not await self.initialize_services():
            return
        
        all_analyses = []
        
        # Investigate each token
        for i, token_address in enumerate(self.test_tokens, 1):
            self.logger.info(f"\n📊 INVESTIGATING TOKEN {i}/{len(self.test_tokens)}: {token_address[:8]}...")
            self.logger.info("-" * 50)
            
            token_analysis = {
                'token_address': token_address,
                'timestamp': datetime.now().isoformat()
            }
            
            # 1. Fetch raw trader data
            raw_data = await self.fetch_raw_trader_data(token_address)
            if raw_data:
                # 2. Analyze trader data
                trader_analysis = self.analyze_trader_data(token_address, raw_data)
                token_analysis['raw_data'] = raw_data
                token_analysis['trader_analysis'] = trader_analysis
                
                # Print trader analysis
                self.logger.info(f"📈 Trader Analysis for {token_address[:8]}:")
                self.logger.info(f"   Total traders: {trader_analysis['total_traders']}")
                self.logger.info(f"   Traders with volume: {trader_analysis['traders_with_volume']}")
                self.logger.info(f"   Total volume: ${trader_analysis['total_volume']:,.0f}")
                self.logger.info(f"   Whale candidates: {len(trader_analysis['whale_candidates'])}")
                
                if trader_analysis['whale_candidates']:
                    self.logger.info("   🐋 Whale candidates:")
                    for whale in trader_analysis['whale_candidates']:
                        levels = ", ".join(whale['qualifies_as_whale'])
                        self.logger.info(f"      {whale['address']}: ${whale['volume_usd']:,.0f} ({levels})")
                
                # 3. Test whale detection logic
                whale_detection = await self.test_whale_detection_logic(token_address, raw_data)
                token_analysis['whale_detection'] = whale_detection
                
                self.logger.info(f"🐋 Whale Detection Results:")
                self.logger.info(f"   Whale count: {whale_detection['whale_count']}")
                self.logger.info(f"   Whale volume: ${whale_detection['whale_volume']:,.0f}")
                
                # 4. Test smart money detection
                smart_detection = await self.test_smart_money_detection(token_address)
                token_analysis['smart_money_detection'] = smart_detection
                
                self.logger.info(f"🧠 Smart Money Detection Results:")
                self.logger.info(f"   Smart trader count: {smart_detection['smart_trader_count']}")
                self.logger.info(f"   Avg skill score: {smart_detection['avg_skill_score']:.3f}")
                
            else:
                token_analysis['error'] = "No raw data available"
                self.logger.warning(f"⚠️ No data available for {token_address[:8]}")
            
            all_analyses.append(token_analysis)
        
        # Generate recommendations
        self.logger.info("\n💡 GENERATING RECOMMENDATIONS...")
        self.logger.info("=" * 60)
        
        recommendations = self.generate_threshold_recommendations(all_analyses)
        
        self.logger.info("📊 Current Market Reality:")
        for key, value in recommendations['current_market_reality'].items():
            if isinstance(value, float):
                self.logger.info(f"   {key}: {value:,.2f}")
            else:
                self.logger.info(f"   {key}: {value}")
        
        self.logger.info("\n🎯 Suggested Thresholds:")
        for key, value in recommendations['suggested_thresholds'].items():
            self.logger.info(f"   {key}: {value}")
        
        self.logger.info("\n🔍 Data Insights:")
        for insight in recommendations['data_insights']:
            self.logger.info(f"   • {insight}")
        
        # Save results
        results = {
            'investigation_timestamp': datetime.now().isoformat(),
            'tokens_analyzed': len(all_analyses),
            'analyses': all_analyses,
            'recommendations': recommendations
        }
        
        results_file = f"scripts/results/api_data_investigation_{int(datetime.now().timestamp())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"\n💾 Investigation results saved to: {results_file}")
        
        # Cleanup
        if self.birdeye_api:
            await self.birdeye_api.close()
        
        self.logger.info("✅ API Data Investigation Complete!")

async def main():
    """Main execution function"""
    investigator = APIDataInvestigator()
    await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())