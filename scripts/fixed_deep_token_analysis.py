#!/usr/bin/env python3
"""
Fixed Deep Token Analysis Tool

This script provides comprehensive, in-depth analysis of specific tokens using
the ACTUAL BirdeyeAPI interface. Fixed all method signature and interface issues.

Features:
- Detailed token overview and security analysis
- Transaction volume and pattern analysis  
- Trading activity and liquidity analysis
- Risk assessment based on available data
- Comparative analysis across multiple tokens
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from utils.env_loader import load_environment
from utils.structured_logger import get_structured_logger
import yaml

# Test tokens provided by user
TEST_TOKENS = [
    "9b1BzC1af9gQBtegh5WcuFB6ARBYQk7PgURW1aogpump",
    "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump", 
    "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",
    "69G8CpUVZAxbPMiEBrfCCCH445NwFxH6PzVL693Xpump",
    "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",
    "8jFpBJoJwHkYLgNgequJJu6CMt3LkY3P6QndUupLpump"
]

class FixedDeepTokenAnalyzer:
    """Fixed deep token analyzer that works with actual BirdeyeAPI interface"""
    
    def __init__(self):
        self.logger = get_structured_logger('FixedDeepTokenAnalysis')
        self.start_time = datetime.now()
        
        # Load environment and configuration
        load_environment()
        
        # Load configuration
        config_path = project_root / "config" / "config.enhanced.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize BirdeyeAPI with proper dependencies
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI with actual working configuration
        birdeye_config = self.config.get('birdeye_api', {})
        birdeye_config['api_key'] = os.getenv('BIRDEYE_API_KEY')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        self.analysis_results = {}
        
    async def analyze_token_comprehensive(self, token_address: str) -> Dict[str, Any]:
        """Perform comprehensive analysis using available API methods"""
        self.logger.info(f"🔍 Starting comprehensive analysis for {token_address[:8]}...")
        
        analysis = {
            'token_address': token_address,
            'analysis_timestamp': datetime.now().isoformat(),
            'basic_data': {},
            'trading_analysis': {},
            'trending_analysis': {},
            'trader_analysis': {},
            'risk_assessment': {},
            'market_metrics': {},
            'errors': []
        }
        
        try:
            # 1. Basic Token Data
            analysis['basic_data'] = await self._analyze_basic_data(token_address)
            
            # 2. Trading Activity Analysis  
            analysis['trading_analysis'] = await self._analyze_trading_activity(token_address)
            
            # 3. Trending Analysis (using correct API method)
            analysis['trending_analysis'] = await self._analyze_trending_status(token_address)
            
            # 4. Trader Analysis (using correct API method)
            analysis['trader_analysis'] = await self._analyze_top_traders(token_address)
            
            # 5. Risk Assessment
            analysis['risk_assessment'] = await self._assess_risk_factors(token_address, analysis['basic_data'])
            
            # 6. Market Metrics
            analysis['market_metrics'] = await self._calculate_market_metrics(analysis)
            
            # 7. Overall Score
            analysis['overall_score'] = self._calculate_overall_score(analysis)
            
            self.logger.info(f"✅ Comprehensive analysis completed for {token_address[:8]}")
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed for {token_address}: {e}")
            analysis['errors'].append(f"Analysis failed: {str(e)}")
            
        return analysis
    
    async def _analyze_basic_data(self, token_address: str) -> Dict[str, Any]:
        """Analyze basic token data using working API methods"""
        basic_data = {
            'overview': None,
            'security': None,
            'metadata': {},
            'age_analysis': {}
        }
        
        try:
            # Get token overview - WORKING METHOD
            overview = await self.birdeye_api.get_token_overview(token_address)
            if overview:
                basic_data['overview'] = overview
                self.logger.debug(f"✅ Retrieved overview for {token_address[:8]}")
            
            # Get security data - WORKING METHOD
            security = await self.birdeye_api.get_token_security(token_address)
            if security:
                basic_data['security'] = security
                self.logger.debug(f"✅ Retrieved security data for {token_address[:8]}")
                
            # Analyze token age - WORKING METHOD
            age_days, age_category = await self.birdeye_api.get_token_age(token_address)
            basic_data['age_analysis'] = {
                'age_days': age_days,
                'age_category': age_category,
                'is_new_token': age_days < 7,
                'is_very_new': age_days < 1
            }
            
            # Extract key metrics from overview
            if overview:
                basic_data['metadata'] = {
                    'symbol': overview.get('symbol', 'Unknown'),
                    'name': overview.get('name', 'Unknown'),
                    'decimals': overview.get('decimals', 0),
                    'market_cap': overview.get('marketCap', 0),
                    'price': overview.get('price', 0),
                    'liquidity': overview.get('liquidity', 0),
                    'volume_24h': overview.get('volume', {}).get('h24', 0) if isinstance(overview.get('volume'), dict) else 0
                }
                
        except Exception as e:
            self.logger.warning(f"Error in basic data analysis for {token_address}: {e}")
            basic_data['errors'] = str(e)
            
        return basic_data
    
    async def _analyze_trading_activity(self, token_address: str) -> Dict[str, Any]:
        """Analyze trading activity using transaction data - WORKING METHODS"""
        trading_analysis = {
            'transaction_volume': 0,
            'transaction_count': 0,
            'recent_transactions': [],
            'trading_patterns': {},
            'volume_analysis': {}
        }
        
        try:
            # Get recent transactions - WORKING METHOD
            transactions = await self.birdeye_api.get_token_transactions(
                token_address, 
                limit=50, 
                max_pages=3
            )
            
            if transactions:
                trading_analysis['transaction_count'] = len(transactions)
                trading_analysis['recent_transactions'] = transactions[:10]
                
                # Calculate transaction volume - WORKING METHOD
                tx_volume = await self.birdeye_api.get_token_transaction_volume(
                    token_address,
                    limit=50,
                    max_pages=3
                )
                trading_analysis['transaction_volume'] = tx_volume
                
                # Analyze trading patterns
                trading_analysis['trading_patterns'] = self._analyze_trading_patterns(transactions)
                
                # Volume analysis
                trading_analysis['volume_analysis'] = self._analyze_volume_patterns(transactions, tx_volume)
                
                self.logger.debug(f"✅ Analyzed {len(transactions)} transactions for {token_address[:8]}")
                
        except Exception as e:
            self.logger.warning(f"Error in trading analysis for {token_address}: {e}")
            trading_analysis['errors'] = str(e)
            
        return trading_analysis
    
    async def _analyze_trending_status(self, token_address: str) -> Dict[str, Any]:
        """Analyze if token is trending using CORRECT API method signature"""
        trending_analysis = {
            'is_trending': False,
            'trending_rank': None,
            'trending_tokens_count': 0,
            'analysis_method': 'fixed_api_call'
        }
        
        try:
            # Use CORRECT method signature - no limit parameter
            trending_tokens = await self.birdeye_api.get_trending_tokens()
            
            if trending_tokens and isinstance(trending_tokens, list):
                trending_analysis['trending_tokens_count'] = len(trending_tokens)
                
                # Check if our token is in trending list
                if token_address in trending_tokens:
                    trending_analysis['is_trending'] = True
                    trending_analysis['trending_rank'] = trending_tokens.index(token_address) + 1
                    self.logger.debug(f"✅ {token_address[:8]} is trending (rank {trending_analysis['trending_rank']})")
                else:
                    self.logger.debug(f"ℹ️  {token_address[:8]} is not in trending tokens")
            else:
                self.logger.debug(f"⚠️  No trending tokens data available")
                
        except Exception as e:
            self.logger.warning(f"Error in trending analysis for {token_address}: {e}")
            trending_analysis['errors'] = str(e)
            
        return trending_analysis
    
    async def _analyze_top_traders(self, token_address: str) -> Dict[str, Any]:
        """Analyze top traders using CORRECT API method signature"""
        trader_analysis = {
            'top_traders': [],
            'trader_count': 0,
            'smart_money_detected': False,
            'analysis_method': 'fixed_api_call'
        }
        
        try:
            # Use CORRECT method signature - no limit parameter
            top_traders = await self.birdeye_api.get_top_traders(token_address)
            
            if top_traders and isinstance(top_traders, list):
                trader_analysis['top_traders'] = top_traders[:10]  # Keep top 10
                trader_analysis['trader_count'] = len(top_traders)
                
                # Analyze for smart money patterns
                smart_money_count = 0
                for trader in top_traders[:20]:  # Check top 20
                    if isinstance(trader, dict):
                        # Look for smart money indicators
                        wallet_addr = trader.get('address', '')
                        if self.birdeye_api._is_smart_money_wallet(wallet_addr):
                            smart_money_count += 1
                            
                if smart_money_count > 0:
                    trader_analysis['smart_money_detected'] = True
                    trader_analysis['smart_money_count'] = smart_money_count
                    
                self.logger.debug(f"✅ Analyzed {len(top_traders)} top traders for {token_address[:8]}")
                
            else:
                self.logger.debug(f"⚠️  No top traders data available for {token_address[:8]}")
                
        except Exception as e:
            self.logger.warning(f"Error in trader analysis for {token_address}: {e}")
            trader_analysis['errors'] = str(e)
            
        return trader_analysis

    async def _assess_risk_factors(self, token_address: str, basic_data: Dict) -> Dict[str, Any]:
        """Assess risk factors based on available data"""
        risk_assessment = {
            'risk_score': 0,
            'risk_factors': [],
            'positive_factors': [],
            'liquidity_risk': 'unknown',
            'age_risk': 'unknown',
            'volume_risk': 'unknown'
        }
        
        try:
            risk_score = 0
            
            # Age-based risk assessment
            age_data = basic_data.get('age_analysis', {})
            age_days = age_data.get('age_days', 0)
            
            if age_days < 1:
                risk_score += 30
                risk_assessment['risk_factors'].append("Very new token (< 1 day old)")
                risk_assessment['age_risk'] = 'high'
            elif age_days < 7:
                risk_score += 15
                risk_assessment['risk_factors'].append("New token (< 1 week old)")
                risk_assessment['age_risk'] = 'medium'
            else:
                risk_assessment['positive_factors'].append(f"Established token ({age_days:.1f} days old)")
                risk_assessment['age_risk'] = 'low'
                
            # Liquidity-based risk assessment
            overview = basic_data.get('overview', {})
            liquidity = overview.get('liquidity', 0) if overview else 0
            
            if liquidity < 10000:
                risk_score += 25
                risk_assessment['risk_factors'].append("Very low liquidity (< $10k)")
                risk_assessment['liquidity_risk'] = 'high'
            elif liquidity < 50000:
                risk_score += 10
                risk_assessment['risk_factors'].append("Low liquidity (< $50k)")
                risk_assessment['liquidity_risk'] = 'medium'
            else:
                risk_assessment['positive_factors'].append(f"Good liquidity (${liquidity:,.0f})")
                risk_assessment['liquidity_risk'] = 'low'
                
            # Market cap assessment
            market_cap = overview.get('marketCap', 0) if overview else 0
            if market_cap > 0:
                if market_cap < 100000:
                    risk_score += 15
                    risk_assessment['risk_factors'].append("Very low market cap (< $100k)")
                elif market_cap > 10000000:
                    risk_assessment['positive_factors'].append(f"Large market cap (${market_cap:,.0f})")
                    
            # Volume assessment
            volume_24h = overview.get('volume', {}).get('h24', 0) if overview and isinstance(overview.get('volume'), dict) else 0
            if volume_24h < 1000:
                risk_score += 20
                risk_assessment['risk_factors'].append("Very low trading volume")
                risk_assessment['volume_risk'] = 'high'
            elif volume_24h < 10000:
                risk_score += 10
                risk_assessment['risk_factors'].append("Low trading volume")
                risk_assessment['volume_risk'] = 'medium'
            else:
                risk_assessment['positive_factors'].append(f"Good trading volume (${volume_24h:,.0f})")
                risk_assessment['volume_risk'] = 'low'
                
            risk_assessment['risk_score'] = min(100, max(0, risk_score))
            
        except Exception as e:
            self.logger.warning(f"Error in risk assessment for {token_address}: {e}")
            risk_assessment['errors'] = str(e)
            
        return risk_assessment
    
    async def _calculate_market_metrics(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate derived market metrics"""
        metrics = {
            'liquidity_to_mcap_ratio': 0,
            'volume_to_liquidity_ratio': 0,
            'trading_activity_score': 0,
            'trending_boost': 0,
            'smart_money_boost': 0
        }
        
        try:
            basic_data = analysis.get('basic_data', {})
            trading_analysis = analysis.get('trading_analysis', {})
            trending_analysis = analysis.get('trending_analysis', {})
            trader_analysis = analysis.get('trader_analysis', {})
            
            overview = basic_data.get('overview', {})
            if overview:
                liquidity = overview.get('liquidity', 0)
                market_cap = overview.get('marketCap', 0)
                volume_24h = overview.get('volume', {}).get('h24', 0) if isinstance(overview.get('volume'), dict) else 0
                
                # Liquidity to market cap ratio
                if market_cap > 0:
                    metrics['liquidity_to_mcap_ratio'] = liquidity / market_cap
                    
                # Volume to liquidity ratio
                if liquidity > 0:
                    metrics['volume_to_liquidity_ratio'] = volume_24h / liquidity
                    
            # Trading activity score
            tx_count = trading_analysis.get('transaction_count', 0)
            tx_volume = trading_analysis.get('transaction_volume', 0)
            
            activity_score = 0
            if tx_count > 100:
                activity_score += 30
            elif tx_count > 50:
                activity_score += 20
            elif tx_count > 10:
                activity_score += 10
                
            if tx_volume > 50000:
                activity_score += 30
            elif tx_volume > 10000:
                activity_score += 20
            elif tx_volume > 1000:
                activity_score += 10
                
            metrics['trading_activity_score'] = min(100, activity_score)
            
            # Trending boost
            if trending_analysis.get('is_trending', False):
                rank = trending_analysis.get('trending_rank', 100)
                metrics['trending_boost'] = max(0, 20 - (rank * 0.5))  # Higher boost for better rank
                
            # Smart money boost
            if trader_analysis.get('smart_money_detected', False):
                smart_count = trader_analysis.get('smart_money_count', 0)
                metrics['smart_money_boost'] = min(15, smart_count * 3)  # Up to 15 point boost
                
        except Exception as e:
            self.logger.debug(f"Error calculating market metrics: {e}")
            
        return metrics
    
    def _calculate_overall_score(self, analysis: Dict) -> Dict[str, Any]:
        """Calculate overall token score based on all analysis factors"""
        score_breakdown = {
            'total_score': 0,
            'base_score': 0,
            'trending_bonus': 0,
            'smart_money_bonus': 0,
            'risk_penalty': 0,
            'grade': 'F'
        }
        
        try:
            # Base score from activity and fundamentals
            market_metrics = analysis.get('market_metrics', {})
            activity_score = market_metrics.get('trading_activity_score', 0)
            
            # Age bonus
            age_days = analysis.get('basic_data', {}).get('age_analysis', {}).get('age_days', 0)
            age_bonus = min(20, age_days * 0.5) if age_days > 0 else 0
            
            base_score = (activity_score * 0.7) + age_bonus
            
            # Trending bonus
            trending_bonus = market_metrics.get('trending_boost', 0)
            
            # Smart money bonus
            smart_money_bonus = market_metrics.get('smart_money_boost', 0)
            
            # Risk penalty
            risk_score = analysis.get('risk_assessment', {}).get('risk_score', 50)
            risk_penalty = risk_score * 0.3  # Reduce score based on risk
            
            total_score = base_score + trending_bonus + smart_money_bonus - risk_penalty
            total_score = max(0, min(100, total_score))
            
            # Assign grade
            if total_score >= 80:
                grade = 'A'
            elif total_score >= 70:
                grade = 'B'
            elif total_score >= 60:
                grade = 'C'
            elif total_score >= 50:
                grade = 'D'
            else:
                grade = 'F'
                
            score_breakdown.update({
                'total_score': round(total_score, 1),
                'base_score': round(base_score, 1),
                'trending_bonus': round(trending_bonus, 1),
                'smart_money_bonus': round(smart_money_bonus, 1),
                'risk_penalty': round(risk_penalty, 1),
                'grade': grade
            })
            
        except Exception as e:
            self.logger.debug(f"Error calculating overall score: {e}")
            
        return score_breakdown

    def _analyze_trading_patterns(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in trading transactions"""
        if not transactions:
            return {}
            
        patterns = {
            'buy_sell_ratio': 0,
            'average_trade_size': 0,
            'unique_traders': 0,
            'large_trades_count': 0
        }
        
        try:
            buy_count = sum(1 for tx in transactions if tx.get('side') == 'buy')
            sell_count = sum(1 for tx in transactions if tx.get('side') == 'sell')
            
            if sell_count > 0:
                patterns['buy_sell_ratio'] = buy_count / sell_count
            else:
                patterns['buy_sell_ratio'] = float('inf') if buy_count > 0 else 0
                
            # Count unique traders and trade sizes
            traders = set()
            trade_sizes = []
            
            for tx in transactions:
                if 'from' in tx and isinstance(tx['from'], dict):
                    traders.add(tx['from'].get('address', ''))
                if 'to' in tx and isinstance(tx['to'], dict):
                    traders.add(tx['to'].get('address', ''))
                    
                volume = self.birdeye_api._extract_trade_volume_usd(tx)
                if volume > 0:
                    trade_sizes.append(volume)
                    
            patterns['unique_traders'] = len(traders)
            
            if trade_sizes:
                patterns['average_trade_size'] = sum(trade_sizes) / len(trade_sizes)
                patterns['large_trades_count'] = sum(1 for size in trade_sizes if size > 10000)
                
        except Exception as e:
            self.logger.debug(f"Error analyzing trading patterns: {e}")
            
        return patterns
    
    def _analyze_volume_patterns(self, transactions: List[Dict], total_volume: float) -> Dict[str, Any]:
        """Analyze volume distribution patterns"""
        volume_analysis = {
            'total_volume': total_volume,
            'volume_concentration': 0,
            'average_volume_per_tx': 0
        }
        
        try:
            if not transactions:
                return volume_analysis
                
            trade_volumes = []
            for tx in transactions:
                volume = self.birdeye_api._extract_trade_volume_usd(tx)
                if volume > 0:
                    trade_volumes.append(volume)
                    
            if trade_volumes:
                volume_analysis['average_volume_per_tx'] = sum(trade_volumes) / len(trade_volumes)
                
                # Volume concentration analysis
                trade_volumes.sort(reverse=True)
                total_vol = sum(trade_volumes)
                
                if total_vol > 0:
                    top_10_percent_count = max(1, len(trade_volumes) // 10)
                    top_10_percent_volume = sum(trade_volumes[:top_10_percent_count])
                    volume_analysis['volume_concentration'] = top_10_percent_volume / total_vol
                    
        except Exception as e:
            self.logger.debug(f"Error analyzing volume patterns: {e}")
            
        return volume_analysis

    def _format_analysis_summary(self, analysis: Dict) -> str:
        """Format analysis results into readable summary"""
        token_addr = analysis['token_address']
        basic_data = analysis.get('basic_data', {})
        metadata = basic_data.get('metadata', {})
        risk_assessment = analysis.get('risk_assessment', {})
        trading_analysis = analysis.get('trading_analysis', {})
        trending_analysis = analysis.get('trending_analysis', {})
        trader_analysis = analysis.get('trader_analysis', {})
        overall_score = analysis.get('overall_score', {})
        
        summary = f"""
================================================================================
🔬 FIXED COMPREHENSIVE ANALYSIS: {token_addr}
================================================================================

📊 BASIC INFORMATION:
  • Symbol: {metadata.get('symbol', 'Unknown')}
  • Name: {metadata.get('name', 'Unknown')}
  • Age: {basic_data.get('age_analysis', {}).get('age_days', 0):.1f} days

💰 MARKET DATA:
  • Price: ${metadata.get('price', 0):.8f}
  • Market Cap: ${metadata.get('market_cap', 0):,.0f}
  • Liquidity: ${metadata.get('liquidity', 0):,.0f}
  • 24h Volume: ${metadata.get('volume_24h', 0):,.0f}

📈 TRADING ANALYSIS:
  • Recent Transactions: {trading_analysis.get('transaction_count', 0)}
  • Transaction Volume: ${trading_analysis.get('transaction_volume', 0):,.2f}
  • Unique Traders: {trading_analysis.get('trading_patterns', {}).get('unique_traders', 0)}
  • Buy/Sell Ratio: {trading_analysis.get('trading_patterns', {}).get('buy_sell_ratio', 0):.2f}

🔥 TRENDING STATUS:
  • Is Trending: {'✅ YES' if trending_analysis.get('is_trending') else '❌ NO'}
  • Trending Rank: {trending_analysis.get('trending_rank', 'N/A')}
  • Total Trending Tokens: {trending_analysis.get('trending_tokens_count', 0)}

🧠 SMART MONEY ANALYSIS:
  • Top Traders Found: {trader_analysis.get('trader_count', 0)}
  • Smart Money Detected: {'✅ YES' if trader_analysis.get('smart_money_detected') else '❌ NO'}
  • Smart Money Count: {trader_analysis.get('smart_money_count', 0)}

⚠️  RISK ASSESSMENT:
  • Risk Score: {risk_assessment.get('risk_score', 0)}/100
  • Liquidity Risk: {risk_assessment.get('liquidity_risk', 'Unknown').upper()}
  • Age Risk: {risk_assessment.get('age_risk', 'Unknown').upper()}
  • Volume Risk: {risk_assessment.get('volume_risk', 'Unknown').upper()}

🏆 OVERALL SCORE:
  • Grade: {overall_score.get('grade', 'F')}
  • Total Score: {overall_score.get('total_score', 0)}/100
  • Base Score: {overall_score.get('base_score', 0):.1f}
  • Trending Bonus: +{overall_score.get('trending_bonus', 0):.1f}
  • Smart Money Bonus: +{overall_score.get('smart_money_bonus', 0):.1f}
  • Risk Penalty: -{overall_score.get('risk_penalty', 0):.1f}

"""
        
        # Add risk factors
        risk_factors = risk_assessment.get('risk_factors', [])
        if risk_factors:
            summary += "🚨 RISK FACTORS:\n"
            for factor in risk_factors:
                summary += f"  • {factor}\n"
            summary += "\n"
            
        # Add positive factors
        positive_factors = risk_assessment.get('positive_factors', [])
        if positive_factors:
            summary += "✅ POSITIVE FACTORS:\n"
            for factor in positive_factors:
                summary += f"  • {factor}\n"
            summary += "\n"
        
        return summary

    async def run_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis on all test tokens"""
        print(f"🔬 Fixed Deep Token Analysis Tool")
        print("=" * 80)
        print(f"📅 Analysis started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Analyzing {len(TEST_TOKENS)} tokens with FIXED API interface\n")
        
        results = {
            'analysis_metadata': {
                'start_time': self.start_time.isoformat(),
                'tool_version': 'fixed_v1.0',
                'tokens_analyzed': len(TEST_TOKENS),
                'api_interface': 'corrected'
            },
            'token_analyses': {},
            'performance_stats': {}
        }
        
        # Analyze each token
        for i, token_address in enumerate(TEST_TOKENS, 1):
            print(f"🔍 ANALYZING TOKEN {i}/{len(TEST_TOKENS)}")
            print(f"📍 Address: {token_address}\n")
            
            try:
                analysis = await self.analyze_token_comprehensive(token_address)
                results['token_analyses'][token_address] = analysis
                
                # Print summary
                summary = self._format_analysis_summary(analysis)
                print(summary)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {token_address}: {e}")
                print(f"❌ Analysis failed for {token_address}: {e}\n")
                
        # Get performance statistics
        results['performance_stats'] = self.birdeye_api.get_api_call_statistics()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = project_root / "scripts" / "results" / f"fixed_deep_analysis_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"💾 Detailed results saved to: {results_file}")
        print(f"🎉 Fixed deep analysis complete!")
        
        return results
        
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.birdeye_api.close()
        except Exception as e:
            self.logger.debug(f"Error during cleanup: {e}")

async def main():
    """Main execution function"""
    analyzer = None
    try:
        analyzer = FixedDeepTokenAnalyzer()
        results = await analyzer.run_analysis()
        return results
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None
    finally:
        if analyzer:
            await analyzer.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 