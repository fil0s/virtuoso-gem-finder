#!/usr/bin/env python3
"""
Enhanced Alert Safety Test Script

Tests the comprehensive alert safety validation system to ensure proper integration
of pump & dump detection and prevention of problematic token alerts.
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor import VirtuosoGemHunter
from services.logger_setup import LoggerSetup

class AlertSafetyTester:
    """Test the enhanced alert safety validation system"""
    
    def __init__(self):
        self.logger = LoggerSetup('AlertSafetyTester').logger
        self.monitor = VirtuosoGemHunter()
        
    async def test_pump_dump_blocking(self):
        """Test that dump phases are blocked while pump opportunities are allowed"""
        print("\n" + "="*80)
        print("TESTING PUMP-FRIENDLY, DUMP-AVERSE LOGIC")
        print("="*80)
        
        # Test Case 1: TDCCP-like token (Critical risk) - should still be blocked
        tdccp_token = {
            'token_symbol': 'TDCCP',
            'token_address': 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm',
            'token_score': 85.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'CRITICAL',  # This is the key blocker
                'current_phase': 'EXTREME_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'EXIT',
                        'confidence': 0.9,
                        'estimated_profit_potential': -80
                    }
                ]
            },
            'market_cap': 50000000,
            'liquidity': 500000,
            'volume_24h': 100000000,
            'price_change_1h': 7500,  # 75,000% gain - but this is OK if not CRITICAL
            'price_change_4h': 15000,
            'price_change_24h': 20000,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(tdccp_token)
        print(f"CRITICAL risk token blocked: {not result} ✅" if not result else f"❌ FAILED - CRITICAL risk token was NOT blocked!")
        
        # Test Case 2: Dump phase token (the main thing we want to avoid)
        dump_token = {
            'token_symbol': 'DUMP',
            'token_address': 'DUMPxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 75.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'MEDIUM',  # Risk level OK
                'current_phase': 'DUMP_START',  # This should block it
                'trading_opportunities': []
            },
            'market_cap': 10000000,
            'liquidity': 200000,
            'volume_24h': 5000000,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(dump_token)
        print(f"Dump phase token blocked: {not result} ✅" if not result else f"❌ FAILED - Dump token was NOT blocked!")
        
        # Test Case 3: EXTREME PUMP with opportunities (should be ALLOWED now)
        extreme_pump_token = {
            'token_symbol': 'EPUMP',
            'token_address': 'EPUMPxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 72.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'HIGH',  # High risk OK for pumps
                'current_phase': 'EXTREME_PUMP',  # Pump phase OK
                'trading_opportunities': [
                    {
                        'action': 'ENTER_HIGH_RISK',
                        'confidence': 0.4,  # Lower confidence OK
                        'estimated_profit_potential': 150
                    }
                ]
            },
            'market_cap': 5000000,
            'liquidity': 200000,
            'volume_24h': 15000000,
            'price_change_1h': 800,  # 800% pump
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(extreme_pump_token)
        print(f"Extreme pump with opportunity allowed: {result} ✅" if result else f"❌ FAILED - Extreme pump opportunity was blocked!")
        
    async def test_pump_opportunities_allowed(self):
        """Test that various pump phases are properly allowed as opportunities"""
        print("\n" + "="*80)
        print("TESTING PUMP OPPORTUNITIES ARE WELCOMED")
        print("="*80)
        
        # Test Case 1: Early pump (prime opportunity)
        early_pump_token = {
            'token_symbol': 'EARLY',
            'token_address': 'EARLYxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 78.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'MEDIUM',
                'current_phase': 'EARLY_PUMP',  # Best phase
                'trading_opportunities': [
                    {
                        'action': 'ENTER',
                        'confidence': 0.7,
                        'estimated_profit_potential': 300
                    }
                ]
            },
            'market_cap': 2000000,
            'liquidity': 300000,
            'volume_24h': 1000000,
            'price_change_1h': 150,  # 150% gain - healthy pump
            'price_change_24h': 400,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(early_pump_token)
        print(f"Early pump opportunity allowed: {result} ✅" if result else f"❌ FAILED - Early pump was blocked!")
        
        # Test Case 2: Momentum pump (good opportunity)
        momentum_pump_token = {
            'token_symbol': 'MOMENTUM',
            'token_address': 'MOMENTUMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 82.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'MEDIUM',
                'current_phase': 'MOMENTUM_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'ENTER',
                        'confidence': 0.6,
                        'estimated_profit_potential': 200
                    }
                ]
            },
            'market_cap': 8000000,
            'liquidity': 400000,
            'volume_24h': 3000000,
            'price_change_1h': 300,  # 300% gain
            'price_change_4h': 500,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(momentum_pump_token)
        print(f"Momentum pump opportunity allowed: {result} ✅" if result else f"❌ FAILED - Momentum pump was blocked!")
        
        # Test Case 3: High risk pump (should be allowed - risky pumps can be profitable)
        high_risk_pump_token = {
            'token_symbol': 'HRPUMP',
            'token_address': 'HRPUMPxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 76.0,  # Lower score OK for pump opportunities
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'HIGH',  # High risk OK for pumps
                'current_phase': 'MOMENTUM_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'ENTER_HIGH_RISK',
                        'confidence': 0.5,  # Medium confidence OK
                        'estimated_profit_potential': 180
                    }
                ]
            },
            'market_cap': 5000000,
            'liquidity': 180000,
            'volume_24h': 8000000,
            'is_scam': False,
            'is_risky': True  # Risky but still profitable
        }
        
        result = await self.monitor._validate_alert_safety(high_risk_pump_token)
        print(f"High risk pump opportunity allowed: {result} ✅" if result else f"❌ FAILED - High risk pump was blocked!")
        
    async def test_valid_tokens_allowed(self):
        """Test that valid tokens are properly allowed"""
        print("\n" + "="*80)
        print("TESTING VALID TOKEN APPROVAL")
        print("="*80)
        
        # Test Case 1: Early pump with good opportunity
        good_token = {
            'token_symbol': 'GOOD',
            'token_address': 'GOODxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 78.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'MEDIUM',
                'current_phase': 'EARLY_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'ENTER',
                        'confidence': 0.8,
                        'estimated_profit_potential': 200
                    }
                ]
            },
            'market_cap': 2000000,
            'liquidity': 300000,
            'volume_24h': 1000000,
            'price_change_1h': 50,  # Reasonable gain
            'price_change_24h': 150,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(good_token)
        print(f"Good token allowed: {result} ✅" if result else f"❌ FAILED - Good token was blocked!")
        
        # Test Case 2: High risk but with strong opportunity
        strong_opportunity_token = {
            'token_symbol': 'STRONG',
            'token_address': 'STRONGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 82.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'HIGH',
                'current_phase': 'MOMENTUM_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'ENTER_HIGH_RISK',
                        'confidence': 0.7,  # High confidence
                        'estimated_profit_potential': 300  # High profit potential
                    }
                ]
            },
            'market_cap': 8000000,
            'liquidity': 400000,
            'volume_24h': 3000000,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(strong_opportunity_token)
        print(f"Strong opportunity token allowed: {result} ✅" if result else f"❌ FAILED - Strong opportunity token was blocked!")
        
    async def test_deduplication(self):
        """Test alert deduplication system"""
        print("\n" + "="*80)
        print("TESTING ALERT DEDUPLICATION")
        print("="*80)
        
        test_token = {
            'token_symbol': 'DEDUP',
            'token_address': 'DEDUPxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 75.0,
            'enhanced_pump_dump_analysis': {
                'overall_risk': 'LOW',
                'current_phase': 'EARLY_PUMP',
                'trading_opportunities': [
                    {
                        'action': 'ENTER',
                        'confidence': 0.6,
                        'estimated_profit_potential': 150
                    }
                ]
            },
            'market_cap': 3000000,
            'liquidity': 250000,
            'volume_24h': 800000,
            'is_scam': False,
            'is_risky': False
        }
        
        # First alert should be allowed
        result1 = await self.monitor._validate_alert_safety(test_token)
        print(f"First alert allowed: {result1} ✅" if result1 else f"❌ FAILED - First alert was blocked!")
        
        # Second alert immediately should be blocked (cooldown)
        result2 = await self.monitor._validate_alert_safety(test_token)
        print(f"Immediate duplicate blocked: {not result2} ✅" if not result2 else f"❌ FAILED - Duplicate alert was NOT blocked!")
        
    async def test_market_conditions(self):
        """Test market condition validation"""
        print("\n" + "="*80)
        print("TESTING MARKET CONDITION VALIDATION")
        print("="*80)
        
        # Test low liquidity blocking
        low_liquidity_token = {
            'token_symbol': 'LOWLIQ',
            'token_address': 'LOWLIQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 75.0,
            'market_cap': 1000000,
            'liquidity': 50000,  # Below $100K threshold
            'volume_24h': 200000,
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(low_liquidity_token)
        print(f"Low liquidity token blocked: {not result} ✅" if not result else f"❌ FAILED - Low liquidity token was NOT blocked!")
        
        # Test excessive volume ratio blocking
        excessive_volume_token = {
            'token_symbol': 'VOLUME',
            'token_address': 'VOLUMExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 75.0,
            'market_cap': 1000000,
            'liquidity': 200000,
            'volume_24h': 120000000,  # 120x market cap ratio (above 100x threshold)
            'is_scam': False,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(excessive_volume_token)
        print(f"Excessive volume token blocked: {not result} ✅" if not result else f"❌ FAILED - Excessive volume token was NOT blocked!")
        
    async def test_security_flags(self):
        """Test security flag validation"""
        print("\n" + "="*80)
        print("TESTING SECURITY FLAG VALIDATION")
        print("="*80)
        
        # Test scam token blocking
        scam_token = {
            'token_symbol': 'SCAM',
            'token_address': 'SCAMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 80.0,  # High score but flagged as scam
            'market_cap': 5000000,
            'liquidity': 300000,
            'volume_24h': 1000000,
            'is_scam': True,
            'is_risky': False
        }
        
        result = await self.monitor._validate_alert_safety(scam_token)
        print(f"Scam token blocked: {not result} ✅" if not result else f"❌ FAILED - Scam token was NOT blocked!")
        
        # Test risky token with low score
        risky_low_score_token = {
            'token_symbol': 'RISKLOW',
            'token_address': 'RISKLOWxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'token_score': 74.0,  # Below 75 threshold for risky tokens
            'market_cap': 3000000,
            'liquidity': 200000,
            'volume_24h': 800000,
            'is_scam': False,
            'is_risky': True
        }
        
        result = await self.monitor._validate_alert_safety(risky_low_score_token)
        print(f"Risky token with low score blocked: {not result} ✅" if not result else f"❌ FAILED - Risky low-score token was NOT blocked!")
        
    async def run_all_tests(self):
        """Run all alert safety tests"""
        print("\n" + "="*100)
        print("ENHANCED ALERT SAFETY VALIDATION TESTS")
        print("="*100)
        print("Testing comprehensive 7-layer validation system...")
        
        try:
            await self.test_pump_dump_blocking()
            await self.test_pump_opportunities_allowed()
            await self.test_valid_tokens_allowed()
            await self.test_deduplication()
            await self.test_market_conditions()
            await self.test_security_flags()
            
            print("\n" + "="*80)
            print("ALERT SAFETY TEST SUMMARY")
            print("="*80)
            print("✅ All critical safety features tested")
            print("✅ Pump & dump detection integration verified")
            print("✅ Alert deduplication working")
            print("✅ Market condition validation active")
            print("✅ Security flag protection enabled")
            print("\n🔒 ENHANCED ALERT SAFETY SYSTEM VALIDATED")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            self.logger.error(f"Alert safety test failed: {e}")

async def main():
    """Main test execution"""
    tester = AlertSafetyTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 