#!/usr/bin/env python3
"""
Early Gem Detector - Simplified Version for Testing
"""

import asyncio
import logging
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple test version - just check if the architecture works
class SimpleEarlyGemDetector:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = self._setup_logging()
        self.logger.info("🚀 Simple Early Gem Detector initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('SimpleEarlyGemDetector')
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - 🚀 SIMPLE - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def test_scoring_system(self):
        """Test the early gem focused scoring system"""
        try:
            # Load EarlyGemFocusedScoring
            import importlib.util
            script_dir = os.path.dirname(os.path.abspath(__file__))
            scorer_path = os.path.join(script_dir, 'early_gem_focused_scoring.py')
            
            spec = importlib.util.spec_from_file_location("early_gem_focused_scoring", scorer_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            EarlyGemFocusedScoring = module.EarlyGemFocusedScoring
            scorer = EarlyGemFocusedScoring()
            
            self.logger.info("✅ Early Gem Focused Scoring loaded successfully")
            
            # Test with dummy data
            test_candidate = {
                'address': 'TEST123456789',
                'symbol': 'TESTGEM',
                'name': 'Test Gem Token',
                'source': 'test',
                'estimated_age_minutes': 15,
                'platforms': ['test_platform'],
                'price': 0.000123,
                'market_cap': 75000,
                'volume_24h': 8500,
                'liquidity': 5500
            }
            
            # Minimal analysis data
            overview_data = {
                'price': 0.000123,
                'market_cap': 75000,
                'volume_24h': 8500,
                'liquidity': 5500
            }
            
            whale_analysis = {'whale_activity_score': 0}
            volume_price_analysis = {'volume_trend': 'increasing', 'price_momentum': 'positive'}
            community_boost_analysis = {'community_score': 0}
            security_analysis = {'security_score': 85, 'risk_factors': []}
            trading_activity = {'recent_activity_score': 5, 'buy_sell_ratio': 1.2}
            dex_analysis = {'dex_presence_score': 5, 'liquidity_quality_score': 7}
            
            # Test scoring
            final_score, scoring_breakdown = scorer.calculate_final_score(
                test_candidate, overview_data, whale_analysis, volume_price_analysis,
                community_boost_analysis, security_analysis, trading_activity,
                dex_analysis, {}
            )
            
            self.logger.info(f"🎯 TEST SCORING RESULTS:")
            self.logger.info(f"   📊 Final Score: {final_score:.1f}/100")
            
            if 'early_platform_analysis' in scoring_breakdown:
                early_score = scoring_breakdown['early_platform_analysis'].get('score', 0)
                self.logger.info(f"   🔥 Early Platform Score: {early_score:.1f}/50")
            
            if 'momentum_analysis' in scoring_breakdown:
                momentum_score = scoring_breakdown['momentum_analysis'].get('score', 0)
                self.logger.info(f"   📈 Momentum Score: {momentum_score:.1f}/38")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Scoring test failed: {e}")
            return False


async def main():
    """Main entry point for Simple Early Gem Detector"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Early Gem Detector - Test Version')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    print("🚀 SIMPLE EARLY GEM DETECTOR - Test Version")
    print("=" * 50)
    print("   Testing core early gem scoring functionality")
    print()
    
    detector = SimpleEarlyGemDetector(debug_mode=args.debug)
    
    # Test the scoring system
    success = detector.test_scoring_system()
    
    if success:
        print("✅ Early Gem Detector core functionality working!")
        print("   Ready to integrate with full BirdeyeAPI discovery")
    else:
        print("❌ Core functionality test failed")


if __name__ == "__main__":
    asyncio.run(main())
