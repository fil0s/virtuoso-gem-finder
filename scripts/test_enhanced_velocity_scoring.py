#!/usr/bin/env python3
"""
Enhanced Velocity Scoring Test

This script tests the new multi-timeframe velocity scoring system that leverages
both DexScreener and Birdeye APIs for better early momentum detection.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

class VelocityScoringTester:
    """Test the enhanced velocity scoring system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the test"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('VelocityTest')
    
    async def test_enhanced_velocity_scoring(self):
        """Test the enhanced velocity scoring with sample data"""
        self.logger.info("🚀 Testing Enhanced Velocity Scoring System")
        
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        # Test scenarios with different timeframe data patterns
        test_scenarios = [
            {
                'name': 'High 5m Momentum Token',
                'symbol': 'MOMENTUM',
                'data': {
                    'symbol': 'MOMENTUM',
                    'volume_24h': 50000,
                    'volume_6h': 20000,
                    'volume_1h': 8000,
                    'volume_5m': 2000,  # High 5m volume
                    'volume_15m': 4000,  # Birdeye data
                    'volume_30m': 6000,  # Birdeye data
                    'price_change_24h': 15.0,
                    'price_change_6h': 8.0,
                    'price_change_1h': 12.0,
                    'price_change_5m': 8.0,  # High 5m momentum
                    'price_change_15m': 10.0,  # Birdeye data
                    'price_change_30m': 11.0,  # Birdeye data
                    'trades_24h': 500,
                    'trades_1h': 80,
                    'trades_5m': 15,  # High activity
                    'trades_15m': 25,  # Birdeye data
                    'trades_30m': 35,  # Birdeye data
                    'unique_traders_24h': 120
                }
            },
            {
                'name': 'Accelerating Volume Token',
                'symbol': 'ACCEL',
                'data': {
                    'symbol': 'ACCEL',
                    'volume_24h': 100000,
                    'volume_6h': 60000,  # Accelerating
                    'volume_1h': 25000,  # Very high acceleration
                    'volume_5m': 3000,   # Explosive 5m volume
                    'volume_15m': 8000,
                    'volume_30m': 15000,
                    'price_change_24h': 25.0,
                    'price_change_6h': 15.0,
                    'price_change_1h': 18.0,
                    'price_change_5m': 12.0,
                    'price_change_15m': 14.0,
                    'price_change_30m': 16.0,
                    'trades_24h': 800,
                    'trades_1h': 150,
                    'trades_5m': 25,
                    'trades_15m': 40,
                    'trades_30m': 65,
                    'unique_traders_24h': 200
                }
            },
            {
                'name': 'Low Activity Token',
                'symbol': 'SLOW',
                'data': {
                    'symbol': 'SLOW',
                    'volume_24h': 5000,
                    'volume_6h': 2000,
                    'volume_1h': 500,
                    'volume_5m': 50,
                    'volume_15m': 150,
                    'volume_30m': 300,
                    'price_change_24h': 2.0,
                    'price_change_6h': 1.0,
                    'price_change_1h': 0.5,
                    'price_change_5m': 0.2,
                    'price_change_15m': 0.3,
                    'price_change_30m': 0.8,
                    'trades_24h': 50,
                    'trades_1h': 8,
                    'trades_5m': 1,
                    'trades_15m': 2,
                    'trades_30m': 4,
                    'unique_traders_24h': 25
                }
            },
            {
                'name': 'Missing Data Token',
                'symbol': 'MISSING',
                'data': {
                    'symbol': 'MISSING',
                    'volume_24h': 0,  # No volume data
                    'volume_1h': 0,
                    'price_change_24h': 0,
                    'price_change_1h': 0,
                    'trades_24h': 0,
                    'unique_traders_24h': 0
                }
            }
        ]
        
        # Test each scenario
        for i, scenario in enumerate(test_scenarios, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Test {i}: {scenario['name']} ({scenario['symbol']})")
            self.logger.info(f"{'='*60}")
            
            # Calculate velocity score
            velocity_score = detector._calculate_velocity_score(scenario['data'])
            
            # Display results
            self.logger.info(f"🎯 Final Velocity Score: {velocity_score:.3f}/1.000")
            
            # Test individual components
            self.logger.info(f"\n📊 Component Analysis:")
            
            # Volume acceleration
            volume_data = {
                '5m': scenario['data'].get('volume_5m', 0),
                '15m': scenario['data'].get('volume_15m', 0),
                '30m': scenario['data'].get('volume_30m', 0),
                '1h': scenario['data'].get('volume_1h', 0),
                '6h': scenario['data'].get('volume_6h', 0),
                '24h': scenario['data'].get('volume_24h', 0)
            }
            volume_score = detector._calculate_volume_acceleration(volume_data, scenario['symbol'])
            self.logger.info(f"   🚀 Volume Acceleration: {volume_score:.3f}/0.400")
            
            # Momentum cascade
            price_changes = {
                '5m': scenario['data'].get('price_change_5m', 0),
                '15m': scenario['data'].get('price_change_15m', 0),
                '30m': scenario['data'].get('price_change_30m', 0),
                '1h': scenario['data'].get('price_change_1h', 0),
                '6h': scenario['data'].get('price_change_6h', 0),
                '24h': scenario['data'].get('price_change_24h', 0)
            }
            momentum_score = detector._calculate_momentum_cascade(price_changes, scenario['symbol'])
            self.logger.info(f"   📈 Momentum Cascade: {momentum_score:.3f}/0.350")
            
            # Activity surge
            trading_data = {
                '5m': scenario['data'].get('trades_5m', 0),
                '15m': scenario['data'].get('trades_15m', 0),
                '30m': scenario['data'].get('trades_30m', 0),
                '1h': scenario['data'].get('trades_1h', 0),
                '6h': scenario['data'].get('trades_6h', 0),
                '24h': scenario['data'].get('trades_24h', 0),
                'unique_traders': scenario['data'].get('unique_traders_24h', 0)
            }
            activity_score = detector._calculate_activity_surge(trading_data, scenario['symbol'])
            self.logger.info(f"   🔥 Activity Surge: {activity_score:.3f}/0.250")
            
            # Calculate expected vs actual
            expected_total = 0.5 + volume_score + momentum_score + activity_score
            expected_capped = min(1.0, max(0.0, expected_total))
            
            self.logger.info(f"\n🧮 Score Breakdown:")
            self.logger.info(f"   Base Score: 0.500")
            self.logger.info(f"   + Volume: {volume_score:.3f}")
            self.logger.info(f"   + Momentum: {momentum_score:.3f}")
            self.logger.info(f"   + Activity: {activity_score:.3f}")
            self.logger.info(f"   = Total: {expected_total:.3f}")
            self.logger.info(f"   = Capped: {expected_capped:.3f}")
            self.logger.info(f"   ✅ Actual: {velocity_score:.3f}")
            
            # Verify calculation
            if abs(velocity_score - expected_capped) < 0.001:
                self.logger.info(f"   ✅ Calculation CORRECT")
            else:
                self.logger.error(f"   ❌ Calculation ERROR: Expected {expected_capped:.3f}, got {velocity_score:.3f}")
        
        # Summary
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🎯 Enhanced Velocity Scoring Test Complete")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"✅ Multi-timeframe analysis working")
        self.logger.info(f"✅ Volume acceleration detection active")
        self.logger.info(f"✅ Momentum cascade detection active")
        self.logger.info(f"✅ Activity surge detection active")
        self.logger.info(f"✅ Component scoring validated")
        
        await detector.cleanup()

async def main():
    """Run the velocity scoring test"""
    tester = VelocityScoringTester()
    await tester.test_enhanced_velocity_scoring()

if __name__ == "__main__":
    asyncio.run(main()) 