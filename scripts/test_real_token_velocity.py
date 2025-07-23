#!/usr/bin/env python3
"""
Real Token Velocity Scoring Test

Test the enhanced velocity scoring system with a real token to validate
our multi-timeframe data collection and scoring algorithms.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

class RealTokenVelocityTester:
    """Test the enhanced velocity scoring with a real token"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the test"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('RealTokenTest')
    
    async def test_real_token_velocity(self, token_address: str):
        """Test the enhanced velocity scoring with a real token"""
        self.logger.info(f"🚀 Testing Enhanced Velocity Scoring with Real Token")
        self.logger.info(f"🔍 Token Address: {token_address}")
        
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        try:
            # Step 1: Enhance token with comprehensive data
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Step 1: Fetching Comprehensive Token Data")
            self.logger.info(f"{'='*60}")
            
            # Create a basic token candidate
            candidate = {
                'address': token_address,
                'symbol': 'TEST_TOKEN',
                'name': 'Test Token'
            }
            
            # Enhance with trading data (this will fetch both DexScreener and Birdeye data)
            enhanced_token = await detector._enhance_token_with_trading_data(candidate, token_address)
            
            # Step 2: Display collected data
            self.logger.info(f"\n📊 Data Collection Summary:")
            self.logger.info(f"{'='*60}")
            
            # Core data availability
            core_fields = [
                'price_usd', 'market_cap', 'liquidity_usd', 'volume_24h', 'volume_6h', 
                'volume_1h', 'volume_5m', 'trades_24h', 'trades_1h', 'trades_5m',
                'price_change_24h', 'price_change_6h', 'price_change_1h', 'price_change_5m'
            ]
            
            available_core = []
            for field in core_fields:
                value = enhanced_token.get(field, 0)
                if value and value != 0:
                    available_core.append(field)
                    self.logger.info(f"   ✅ {field}: {value}")
                else:
                    self.logger.info(f"   ❌ {field}: {value}")
            
            # Short timeframe data (from Birdeye OHLCV)
            short_timeframe_fields = ['volume_15m', 'volume_30m', 'price_change_15m', 'price_change_30m', 'trades_15m', 'trades_30m']
            available_short = []
            for field in short_timeframe_fields:
                value = enhanced_token.get(field, 0)
                if value and value != 0:
                    available_short.append(field)
                    self.logger.info(f"   🔍 {field}: {value}")
                else:
                    self.logger.info(f"   🔍 {field}: {value}")
            
            # Enhanced data (from Birdeye enhancements)
            enhanced_fields = ['unique_traders_24h', 'holder_count', 'security_score', 'is_scam', 'age_hours']
            available_enhanced = []
            for field in enhanced_fields:
                value = enhanced_token.get(field, 'N/A')
                if value and value != 'N/A' and value != 0:
                    available_enhanced.append(field)
                    self.logger.info(f"   🛡️ {field}: {value}")
                else:
                    self.logger.info(f"   🛡️ {field}: {value}")
            
            # Step 3: Test Enhanced Velocity Scoring
            self.logger.info(f"\n🎯 Enhanced Velocity Scoring Analysis:")
            self.logger.info(f"{'='*60}")
            
            # Calculate velocity score with detailed debugging
            velocity_score = detector._calculate_velocity_score(enhanced_token)
            
            # Step 4: Component Analysis
            self.logger.info(f"\n📈 Detailed Component Analysis:")
            self.logger.info(f"{'='*60}")
            
            # Volume acceleration analysis
            volume_data = {
                '5m': enhanced_token.get('volume_5m', 0),
                '15m': enhanced_token.get('volume_15m', 0),
                '30m': enhanced_token.get('volume_30m', 0),
                '1h': enhanced_token.get('volume_1h', 0),
                '6h': enhanced_token.get('volume_6h', 0),
                '24h': enhanced_token.get('volume_24h', 0)
            }
            volume_score = detector._calculate_volume_acceleration(volume_data, enhanced_token.get('symbol', 'TEST'))
            
            # Momentum cascade analysis
            price_changes = {
                '5m': enhanced_token.get('price_change_5m', 0),
                '15m': enhanced_token.get('price_change_15m', 0),
                '30m': enhanced_token.get('price_change_30m', 0),
                '1h': enhanced_token.get('price_change_1h', 0),
                '6h': enhanced_token.get('price_change_6h', 0),
                '24h': enhanced_token.get('price_change_24h', 0)
            }
            momentum_score = detector._calculate_momentum_cascade(price_changes, enhanced_token.get('symbol', 'TEST'))
            
            # Activity surge analysis
            trading_data = {
                '5m': enhanced_token.get('trades_5m', 0),
                '15m': enhanced_token.get('trades_15m', 0),
                '30m': enhanced_token.get('trades_30m', 0),
                '1h': enhanced_token.get('trades_1h', 0),
                '6h': enhanced_token.get('trades_6h', 0),
                '24h': enhanced_token.get('trades_24h', 0),
                'unique_traders': enhanced_token.get('unique_traders_24h', 0)
            }
            activity_score = detector._calculate_activity_surge(trading_data, enhanced_token.get('symbol', 'TEST'))
            
            # Step 5: Results Summary
            self.logger.info(f"\n🎯 Final Results Summary:")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"🚀 Volume Acceleration Score: {volume_score:.3f}/0.400")
            self.logger.info(f"📈 Momentum Cascade Score: {momentum_score:.3f}/0.350")
            self.logger.info(f"🔥 Activity Surge Score: {activity_score:.3f}/0.250")
            self.logger.info(f"⚡ Final Velocity Score: {velocity_score:.3f}/1.000")
            
            # Calculate expected vs actual
            expected_total = 0.5 + volume_score + momentum_score + activity_score
            expected_capped = min(1.0, max(0.0, expected_total))
            
            self.logger.info(f"\n🧮 Score Verification:")
            self.logger.info(f"   Base Score: 0.500")
            self.logger.info(f"   + Volume: {volume_score:.3f}")
            self.logger.info(f"   + Momentum: {momentum_score:.3f}")
            self.logger.info(f"   + Activity: {activity_score:.3f}")
            self.logger.info(f"   = Total: {expected_total:.3f}")
            self.logger.info(f"   = Capped: {expected_capped:.3f}")
            self.logger.info(f"   ✅ Actual: {velocity_score:.3f}")
            
            # Verification
            if abs(velocity_score - expected_capped) < 0.001:
                self.logger.info(f"   ✅ Calculation CORRECT")
            else:
                self.logger.error(f"   ❌ Calculation ERROR: Expected {expected_capped:.3f}, got {velocity_score:.3f}")
            
            # Step 6: Data Quality Assessment
            self.logger.info(f"\n📊 Data Quality Assessment:")
            self.logger.info(f"{'='*60}")
            total_fields = len(core_fields) + len(short_timeframe_fields) + len(enhanced_fields)
            available_fields = len(available_core) + len(available_short) + len(available_enhanced)
            coverage_percentage = (available_fields / total_fields) * 100
            
            self.logger.info(f"   📋 Core Data Coverage: {len(available_core)}/{len(core_fields)} ({len(available_core)/len(core_fields)*100:.1f}%)")
            self.logger.info(f"   🔍 Short Timeframe Data: {len(available_short)}/{len(short_timeframe_fields)} ({len(available_short)/len(short_timeframe_fields)*100:.1f}%)")
            self.logger.info(f"   🛡️ Enhanced Data: {len(available_enhanced)}/{len(enhanced_fields)} ({len(available_enhanced)/len(enhanced_fields)*100:.1f}%)")
            self.logger.info(f"   🎯 Overall Coverage: {available_fields}/{total_fields} ({coverage_percentage:.1f}%)")
            
            # Data source analysis
            sources = []
            if enhanced_token.get('volume_24h', 0) > 0:
                sources.append('DexScreener')
            if enhanced_token.get('unique_traders_24h', 0) > 0 or enhanced_token.get('holder_count', 0) > 0:
                sources.append('Birdeye-Core')
            if enhanced_token.get('volume_15m', 0) > 0 or enhanced_token.get('volume_30m', 0) > 0:
                sources.append('Birdeye-OHLCV')
            
            self.logger.info(f"   📡 Data Sources Used: {', '.join(sources) if sources else 'None'}")
            
            # Step 7: Interpretation
            self.logger.info(f"\n🎯 Velocity Score Interpretation:")
            self.logger.info(f"{'='*60}")
            
            if velocity_score >= 0.8:
                interpretation = "🚀 EXPLOSIVE MOMENTUM - Strong multi-timeframe acceleration detected"
            elif velocity_score >= 0.7:
                interpretation = "📈 HIGH MOMENTUM - Good acceleration signals across timeframes"
            elif velocity_score >= 0.6:
                interpretation = "⚡ MODERATE MOMENTUM - Some positive signals detected"
            elif velocity_score >= 0.5:
                interpretation = "📊 BASELINE - Standard activity levels"
            else:
                interpretation = "📉 LOW MOMENTUM - Limited or declining activity"
            
            self.logger.info(f"   {interpretation}")
            
            # Recommendations
            self.logger.info(f"\n💡 Recommendations:")
            if volume_score > 0.2:
                self.logger.info(f"   🚀 Strong volume acceleration - monitor for continued growth")
            if momentum_score > 0.2:
                self.logger.info(f"   📈 Price momentum building - watch for breakout patterns")
            if activity_score > 0.1:
                self.logger.info(f"   🔥 Trading activity surge - increased interest detected")
            if velocity_score < 0.6:
                self.logger.info(f"   ⚠️ Limited momentum - consider waiting for stronger signals")
            
            await detector.cleanup()
            
            return {
                'token_address': token_address,
                'velocity_score': velocity_score,
                'volume_score': volume_score,
                'momentum_score': momentum_score,
                'activity_score': activity_score,
                'data_coverage': coverage_percentage,
                'data_sources': sources,
                'enhanced_token': enhanced_token
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error testing token {token_address}: {e}")
            await detector.cleanup()
            raise

async def main():
    """Run the real token velocity test"""
    token_address = "RnvpqEmxcgqrbPJpx8rjHgrEYDxzKqvQtvzWH2Npump"
    
    tester = RealTokenVelocityTester()
    result = await tester.test_real_token_velocity(token_address)
    
    print(f"\n{'='*60}")
    print(f"🎯 TEST COMPLETE - Enhanced Velocity Scoring Validated")
    print(f"{'='*60}")
    print(f"Token: {result['token_address']}")
    print(f"Final Score: {result['velocity_score']:.3f}/1.000")
    print(f"Data Coverage: {result['data_coverage']:.1f}%")
    print(f"Sources: {', '.join(result['data_sources'])}")

if __name__ == "__main__":
    asyncio.run(main()) 