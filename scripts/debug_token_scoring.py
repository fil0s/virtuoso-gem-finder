#!/usr/bin/env python3
"""
Debug script to analyze detailed scoring breakdown for high conviction tokens
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.append('.')

from scripts.high_conviction_token_detector import HighConvictionTokenDetector

class TokenScoringAnalyzer:
    def __init__(self):
        self.detector = None
        
    async def analyze_token_scoring(self, token_addresses: List[str]):
        """Analyze detailed scoring for specific tokens"""
        print("🔍 DETAILED TOKEN SCORING ANALYSIS")
        print("=" * 80)
        
        # Initialize detector
        self.detector = HighConvictionTokenDetector(debug_mode=True)
        
        for i, address in enumerate(token_addresses, 1):
            print(f"\n{i}. ANALYZING TOKEN: {address}")
            print("-" * 60)
            
            try:
                # Create a mock candidate with the address
                candidate = {
                    'address': address,
                    'symbol': 'Unknown',
                    'score': 0,  # Base score from cross-platform analysis
                    'platforms': ['dexscreener', 'birdeye'],  # Mock platforms
                    'discovery_method': 'manual_debug'
                }
                
                # Perform detailed analysis
                analysis = await self.detector._perform_detailed_analysis(candidate, 'debug_scan')
                
                if analysis:
                    self._print_detailed_scoring_breakdown(analysis)
                else:
                    print("❌ Failed to analyze token")
                    
            except Exception as e:
                print(f"❌ Error analyzing {address}: {e}")
                
        await self.detector.cleanup()
        
    def _print_detailed_scoring_breakdown(self, analysis: Dict[str, Any]):
        """Print detailed scoring breakdown"""
        candidate = analysis['candidate']
        final_score = analysis['final_score']
        
        print(f"🏷️  TOKEN: {candidate.get('symbol', 'Unknown')} ({candidate.get('name', 'Unknown')})")
        print(f"📍 ADDRESS: {candidate['address']}")
        print(f"🎯 FINAL SCORE: {final_score:.1f}")
        print()
        
        # Calculate component scores manually based on the scoring logic
        self._calculate_and_display_component_scores(
            candidate,
            analysis['overview_data'],
            analysis['whale_analysis'],
            analysis['volume_price_analysis'],
            analysis['community_boost_analysis'],
            analysis['security_analysis'],
            analysis['trading_activity']
        )
        
    def _calculate_and_display_component_scores(self, candidate, overview_data, whale_analysis, 
                                              volume_price_analysis, community_boost_analysis,
                                              security_analysis, trading_activity):
        """Calculate and display component scores with detailed breakdown"""
        
        # Base score from cross-platform analysis
        base_score = candidate.get('score', 0)
        print(f"📊 BASE SCORE (Cross-Platform): {base_score:.1f}")
        platforms = candidate.get('platforms', [])
        print(f"   • Platforms: {', '.join(platforms)} ({len(platforms)} platforms)")
        if len(platforms) >= 2:
            cross_platform_bonus = (len(platforms) - 1) * 8.0
            print(f"   • Cross-platform bonus: +{cross_platform_bonus:.1f}")
        print()
        
        # Overview scoring (0-20 points)
        overview_score = 0
        print("📈 OVERVIEW ANALYSIS (Max: 20 points)")
        if overview_data:
            market_cap = overview_data.get('market_cap', 0)
            print(f"   • Market Cap: ${market_cap:,.0f}")
            if market_cap > 1000000:
                overview_score += 5
                print("     ✅ > $1M: +5 points")
            elif market_cap > 100000:
                overview_score += 3
                print("     ✅ > $100K: +3 points")
            elif market_cap > 10000:
                overview_score += 1
                print("     ✅ > $10K: +1 point")
            else:
                print("     ❌ < $10K: +0 points")
                
            liquidity = overview_data.get('liquidity', 0)
            print(f"   • Liquidity: ${liquidity:,.0f}")
            if liquidity > 500000:
                overview_score += 5
                print("     ✅ > $500K: +5 points")
            elif liquidity > 100000:
                overview_score += 3
                print("     ✅ > $100K: +3 points")
            elif liquidity > 10000:
                overview_score += 1
                print("     ✅ > $10K: +1 point")
            else:
                print("     ❌ < $10K: +0 points")
                
            price_change_1h = overview_data.get('price_change_1h', 0)
            price_change_24h = overview_data.get('price_change_24h', 0)
            print(f"   • Price Change 1h: {price_change_1h:+.1f}%")
            if price_change_1h > 10:
                overview_score += 3
                print("     ✅ > 10%: +3 points")
            elif price_change_1h > 5:
                overview_score += 2
                print("     ✅ > 5%: +2 points")
            elif price_change_1h > 0:
                overview_score += 1
                print("     ✅ > 0%: +1 point")
            else:
                print("     ❌ ≤ 0%: +0 points")
                
            print(f"   • Price Change 24h: {price_change_24h:+.1f}%")
            if price_change_24h > 20:
                overview_score += 3
                print("     ✅ > 20%: +3 points")
            elif price_change_24h > 10:
                overview_score += 2
                print("     ✅ > 10%: +2 points")
            elif price_change_24h > 0:
                overview_score += 1
                print("     ✅ > 0%: +1 point")
            else:
                print("     ❌ ≤ 0%: +0 points")
                
            holders = overview_data.get('holders', 0)
            print(f"   • Holders: {holders:,}")
            if holders > 1000:
                overview_score += 4
                print("     ✅ > 1000: +4 points")
            elif holders > 100:
                overview_score += 2
                print("     ✅ > 100: +2 points")
            elif holders > 10:
                overview_score += 1
                print("     ✅ > 10: +1 point")
            else:
                print("     ❌ ≤ 10: +0 points")
        else:
            print("   ❌ No overview data available")
            
        print(f"   🎯 OVERVIEW TOTAL: {overview_score:.1f}/20")
        print()
        
        # Whale analysis scoring (0-15 points)
        whale_score = 0
        print("🐋 WHALE ANALYSIS (Max: 15 points)")
        if whale_analysis:
            whale_concentration = whale_analysis.get('whale_concentration', 0)
            print(f"   • Whale Concentration: {whale_concentration:.1f}%")
            if 20 <= whale_concentration <= 60:
                whale_score += 8
                print("     ✅ Sweet spot (20-60%): +8 points")
            elif 10 <= whale_concentration <= 80:
                whale_score += 5
                print("     ✅ Acceptable (10-80%): +5 points")
            elif whale_concentration > 0:
                whale_score += 2
                print("     ⚠️ Sub-optimal: +2 points")
            else:
                print("     ❌ No data: +0 points")
                
            smart_money = whale_analysis.get('smart_money_detected', False)
            print(f"   • Smart Money Detected: {smart_money}")
            if smart_money:
                whale_score += 7
                print("     ✅ Smart money found: +7 points")
            else:
                print("     ❌ No smart money: +0 points")
        else:
            print("   ❌ No whale analysis data available")
            
        print(f"   🎯 WHALE TOTAL: {whale_score:.1f}/15")
        print()
        
        # Volume/Price analysis scoring (0-15 points)
        volume_score = 0
        print("📊 VOLUME/PRICE ANALYSIS (Max: 15 points)")
        if volume_price_analysis:
            volume_trend = volume_price_analysis.get('volume_trend', 'stable')
            print(f"   • Volume Trend: {volume_trend}")
            if volume_trend == 'increasing':
                volume_score += 8
                print("     ✅ Increasing: +8 points")
            elif volume_trend == 'stable':
                volume_score += 4
                print("     ⚠️ Stable: +4 points")
            else:
                print("     ❌ Decreasing: +0 points")
                
            price_momentum = volume_price_analysis.get('price_momentum', 'neutral')
            print(f"   • Price Momentum: {price_momentum}")
            if price_momentum == 'bullish':
                volume_score += 7
                print("     ✅ Bullish: +7 points")
            elif price_momentum == 'neutral':
                volume_score += 3
                print("     ⚠️ Neutral: +3 points")
            else:
                print("     ❌ Bearish: +0 points")
        else:
            print("   ❌ No volume/price analysis data available")
            
        print(f"   🎯 VOLUME/PRICE TOTAL: {volume_score:.1f}/15")
        print()
        
        # Community analysis scoring (0-10 points)
        community_score = 0
        print("👥 COMMUNITY ANALYSIS (Max: 10 points)")
        if community_boost_analysis:
            social_score = community_boost_analysis.get('social_score', 0)
            community_score = min(10, social_score * 1.5)
            print(f"   • Social Score: {social_score:.1f}")
            print(f"   • Scaled Score: {community_score:.1f}")
        else:
            print("   ❌ No community analysis data available")
            
        print(f"   🎯 COMMUNITY TOTAL: {community_score:.1f}/10")
        print()
        
        # Security analysis scoring (0-10 points)
        security_score = 0
        print("🔒 SECURITY ANALYSIS (Max: 10 points)")
        if security_analysis:
            security_score_raw = security_analysis.get('security_score', 100)
            security_score = (security_score_raw / 100) * 10
            print(f"   • Raw Security Score: {security_score_raw:.1f}/100")
            print(f"   • Scaled Score: {security_score:.1f}/10")
            
            risk_factors = security_analysis.get('risk_factors', [])
            if risk_factors:
                penalty = len(risk_factors) * 2
                security_score -= penalty
                print(f"   • Risk Factors: {len(risk_factors)} (-{penalty} points)")
                for factor in risk_factors:
                    print(f"     - {factor}")
            security_score = max(0, security_score)
        else:
            print("   ❌ No security analysis data available")
            
        print(f"   🎯 SECURITY TOTAL: {security_score:.1f}/10")
        print()
        
        # Trading activity scoring (0-10 points)
        trading_score = 0
        print("💹 TRADING ACTIVITY (Max: 10 points)")
        if trading_activity:
            activity_score = trading_activity.get('recent_activity_score', 0)
            trading_score = min(10, activity_score / 10)
            print(f"   • Recent Activity Score: {activity_score:.1f}")
            print(f"   • Scaled Score: {trading_score:.1f}")
            
            buy_sell_ratio = trading_activity.get('buy_sell_ratio', 0)
            print(f"   • Buy/Sell Ratio: {buy_sell_ratio:.2f}")
            if buy_sell_ratio > 1.5:
                bonus = 3
                trading_score += bonus
                print(f"     ✅ > 1.5: +{bonus} points")
            elif buy_sell_ratio > 1.0:
                bonus = 1
                trading_score += bonus
                print(f"     ✅ > 1.0: +{bonus} point")
            else:
                print("     ❌ ≤ 1.0: +0 points")
                
            trading_score = min(10, trading_score)
        else:
            print("   ❌ No trading activity data available")
            
        print(f"   🎯 TRADING TOTAL: {trading_score:.1f}/10")
        print()
        
        # Final calculation
        calculated_final = base_score + overview_score + whale_score + volume_score + community_score + security_score + trading_score
        calculated_final = min(100, calculated_final)
        
        print("🎯 FINAL SCORE BREAKDOWN:")
        print(f"   • Base (Cross-Platform): {base_score:.1f}")
        print(f"   • Overview Analysis: {overview_score:.1f}")
        print(f"   • Whale Analysis: {whale_score:.1f}")
        print(f"   • Volume/Price Analysis: {volume_score:.1f}")
        print(f"   • Community Analysis: {community_score:.1f}")
        print(f"   • Security Analysis: {security_score:.1f}")
        print(f"   • Trading Activity: {trading_score:.1f}")
        print(f"   ─────────────────────────")
        print(f"   🏆 TOTAL: {calculated_final:.1f}/100")
        print()

async def main():
    """Main function to analyze token scoring"""
    # Token addresses from the recent scan
    token_addresses = [
        "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT - 43.0
        "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg",  # GOR - 41.5
        "3dk9CNre8tmv6bbNXd5F6dgkNnEzsyQ7sPhVT8kKpump",  # Fartcat - 35.5
        "Cwn9d1E636CPBTgtPXZAuqn6TgUh6mPpUMBr3w7kpump",  # OILCOIN - 32.5
        "8BmHnfjHKkWKTBroPMXdr617VLSzMjdUQYaMUcJfpump",  # Giga - 28.5
        "95fRjLnCXVAviW9uAFejzMTtwgGtpM9ux39B3hbApump",  # italo - 26.0
    ]
    
    analyzer = TokenScoringAnalyzer()
    await analyzer.analyze_token_scoring(token_addresses)

if __name__ == "__main__":
    asyncio.run(main()) 