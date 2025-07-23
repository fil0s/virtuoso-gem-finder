#!/usr/bin/env python3
"""
Age-Aware Confidence System Test

Test the new age-aware confidence system that rewards early detection
instead of penalizing new tokens for limited data availability.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

class AgeAwareConfidenceTester:
    """Test the age-aware confidence system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the test"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AGE_AWARE_TEST - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios with different ages and data availability"""
        return [
            {
                'name': 'ULTRA_EARLY_WITH_MOMENTUM',
                'description': 'Brand new token (5 min) with strong momentum signals',
                'estimated_age_minutes': 5,
                'volume_5m': 15000,
                'volume_15m': 8000,
                'price_change_5m': 45.2,
                'trades_5m': 120,
                'expected_level': 'EARLY_DETECTION',
                'expected_bonus': True
            },
            {
                'name': 'ULTRA_EARLY_LIMITED_DATA',
                'description': 'Very new token (15 min) with minimal data (just one timeframe)',
                'estimated_age_minutes': 15,
                'volume_5m': 5000,
                'price_change_5m': 12.1,
                'expected_level': 'MEDIUM',  # Should be MEDIUM (neutral) not EARLY_DETECTION
                'expected_bonus': False
            },
            {
                'name': 'ULTRA_EARLY_NO_MOMENTUM',
                'description': 'Brand new token (8 min) with NO meaningful momentum',
                'estimated_age_minutes': 8,
                'volume_24h': 1000,  # Only 24h data, no short-term activity
                'price_change_24h': 2.1,
                'expected_level': 'LOW',  # Should be LOW - no short-term momentum
                'expected_bonus': False
            },
            {
                'name': 'EARLY_GOOD_DATA',
                'description': 'Early token (45 min) with good data coverage',
                'estimated_age_minutes': 45,
                'volume_5m': 12000,
                'volume_15m': 18000,
                'volume_30m': 25000,
                'volume_1h': 35000,
                'price_change_5m': 8.5,
                'price_change_15m': 15.2,
                'price_change_1h': 22.8,
                'trades_5m': 85,
                'trades_1h': 180,
                'expected_level': 'HIGH',
                'expected_bonus': False
            },
            {
                'name': 'EARLY_LIMITED_DATA',
                'description': 'Early token (90 min) with limited data',
                'estimated_age_minutes': 90,
                'volume_5m': 3000,
                'volume_1h': 8000,
                'price_change_5m': 5.2,
                'expected_level': 'MEDIUM',
                'expected_penalty': 'SLIGHT'
            },
            {
                'name': 'ESTABLISHED_EXCELLENT_DATA',
                'description': 'Established token (4 hours) with excellent data',
                'estimated_age_minutes': 240,
                'volume_5m': 25000,
                'volume_15m': 35000,
                'volume_30m': 45000,
                'volume_1h': 65000,
                'volume_6h': 180000,
                'volume_24h': 450000,
                'price_change_5m': 3.2,
                'price_change_15m': 8.1,
                'price_change_1h': 12.5,
                'price_change_6h': 25.8,
                'trades_5m': 150,
                'trades_1h': 320,
                'trades_6h': 850,
                'expected_level': 'HIGH',
                'expected_bonus': False
            },
            {
                'name': 'ESTABLISHED_POOR_DATA',
                'description': 'Established token (6 hours) with poor data quality',
                'estimated_age_minutes': 360,
                'volume_5m': 1000,
                'price_change_5m': 1.2,
                'expected_level': 'LOW',
                'expected_penalty': 'MODERATE'
            },
            {
                'name': 'MATURE_EXCELLENT_DATA',
                'description': 'Mature token (18 hours) with full data coverage',
                'estimated_age_minutes': 1080,
                'volume_5m': 45000,
                'volume_15m': 55000,
                'volume_30m': 65000,
                'volume_1h': 85000,
                'volume_6h': 280000,
                'volume_24h': 850000,
                'price_change_5m': 2.1,
                'price_change_15m': 4.5,
                'price_change_30m': 6.8,
                'price_change_1h': 8.2,
                'price_change_6h': 15.5,
                'price_change_24h': 35.2,
                'trades_5m': 180,
                'trades_15m': 220,
                'trades_1h': 450,
                'trades_6h': 1200,
                'trades_24h': 3500,
                'expected_level': 'HIGH',
                'expected_bonus': False
            },
            {
                'name': 'MATURE_POOR_DATA',
                'description': 'Mature token (24+ hours) with concerning data gaps',
                'estimated_age_minutes': 1440,
                'volume_5m': 500,
                'volume_1h': 2000,
                'price_change_5m': 0.5,
                'expected_level': 'VERY_LOW',
                'expected_penalty': 'SIGNIFICANT'
            }
        ]
    
    async def run_comprehensive_test(self):
        """Run comprehensive age-aware confidence testing"""
        self.logger.info("🧪 Starting Age-Aware Confidence System Test")
        self.logger.info("=" * 80)
        
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        # Create test scenarios
        scenarios = self.create_test_scenarios()
        
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            self.logger.info(f"\n🧪 TEST {i}/{len(scenarios)}: {scenario['name']}")
            self.logger.info(f"📝 Description: {scenario['description']}")
            
            # Create test candidate
            candidate = self._create_test_candidate(scenario)
            
            # Test confidence assessment
            confidence_data = detector._assess_velocity_data_confidence(candidate)
            
            # Analyze results
            result = self._analyze_test_result(scenario, confidence_data)
            results.append(result)
            
            # Display results
            self._display_test_result(scenario, confidence_data, result)
        
        # Display summary
        self._display_test_summary(results)
        
        return results
    
    def _create_test_candidate(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test candidate from scenario data"""
        candidate = {
            'symbol': f"TEST_{scenario['name']}",
            'address': f"test_address_{scenario['name'].lower()}",
            'estimated_age_minutes': scenario['estimated_age_minutes']
        }
        
        # Add all volume, price change, and trade data
        for key, value in scenario.items():
            if key.startswith(('volume_', 'price_change_', 'trades_')):
                candidate[key] = value
        
        return candidate
    
    def _analyze_test_result(self, scenario: Dict[str, Any], confidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results against expectations"""
        actual_level = confidence_data.get('level', 'UNKNOWN')
        expected_level = scenario.get('expected_level', 'UNKNOWN')
        
        # Check if level matches expectation
        level_correct = actual_level == expected_level
        
        # Check bonus/penalty expectations
        threshold_adjustment = confidence_data.get('threshold_adjustment', 1.0)
        has_bonus = threshold_adjustment < 1.0
        has_penalty = threshold_adjustment > 1.0
        
        expected_bonus = scenario.get('expected_bonus', False)
        expected_penalty = scenario.get('expected_penalty', None)
        
        bonus_correct = (expected_bonus and has_bonus) or (not expected_bonus and not has_bonus)
        penalty_correct = True  # Default to correct unless specific penalty expected
        
        if expected_penalty == 'SLIGHT':
            penalty_correct = 1.0 < threshold_adjustment <= 1.1
        elif expected_penalty == 'MODERATE':
            penalty_correct = 1.1 < threshold_adjustment <= 1.2
        elif expected_penalty == 'SIGNIFICANT':
            penalty_correct = threshold_adjustment > 1.2
        elif expected_penalty is None:
            penalty_correct = threshold_adjustment <= 1.05  # Allow small adjustments
        
        return {
            'scenario_name': scenario['name'],
            'age_minutes': scenario['estimated_age_minutes'],
            'expected_level': expected_level,
            'actual_level': actual_level,
            'level_correct': level_correct,
            'expected_bonus': expected_bonus,
            'has_bonus': has_bonus,
            'bonus_correct': bonus_correct,
            'expected_penalty': expected_penalty,
            'threshold_adjustment': threshold_adjustment,
            'penalty_correct': penalty_correct,
            'overall_success': level_correct and bonus_correct and penalty_correct,
            'confidence_data': confidence_data
        }
    
    def _display_test_result(self, scenario: Dict[str, Any], confidence_data: Dict[str, Any], result: Dict[str, Any]):
        """Display individual test result"""
        age_category = confidence_data.get('age_category', 'UNKNOWN')
        level = confidence_data.get('level', 'UNKNOWN')
        icon = confidence_data.get('icon', '❓')
        threshold_adj = confidence_data.get('threshold_adjustment', 1.0)
        reason = confidence_data.get('assessment_reason', 'No reason provided')
        
        success_icon = "✅" if result['overall_success'] else "❌"
        
        self.logger.info(f"   {success_icon} Result: {icon} {level} ({age_category})")
        self.logger.info(f"   📊 Age: {scenario['estimated_age_minutes']:.1f} minutes")
        self.logger.info(f"   🎯 Threshold Adjustment: {threshold_adj:.3f}")
        self.logger.info(f"   💭 Assessment: {reason}")
        
        # Show expectation vs reality
        if not result['level_correct']:
            self.logger.warning(f"   ⚠️  Expected {result['expected_level']}, got {result['actual_level']}")
        
        if not result['bonus_correct']:
            self.logger.warning(f"   ⚠️  Bonus expectation failed: expected={result['expected_bonus']}, actual={result['has_bonus']}")
        
        if not result['penalty_correct']:
            self.logger.warning(f"   ⚠️  Penalty expectation failed: expected={result['expected_penalty']}, actual={threshold_adj:.3f}")
    
    def _display_test_summary(self, results: List[Dict[str, Any]]):
        """Display comprehensive test summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎯 AGE-AWARE CONFIDENCE SYSTEM TEST SUMMARY")
        self.logger.info("=" * 80)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['overall_success'])
        success_rate = (successful_tests / total_tests) * 100
        
        self.logger.info(f"📊 Overall Results: {successful_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        # Category breakdown
        categories = {}
        for result in results:
            age = result['age_minutes']
            if age <= 30:
                cat = 'ULTRA_EARLY'
            elif age <= 120:
                cat = 'EARLY'
            elif age <= 720:
                cat = 'ESTABLISHED'
            else:
                cat = 'MATURE'
            
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if result['overall_success']:
                categories[cat]['passed'] += 1
        
        self.logger.info("\n📈 Results by Age Category:")
        for cat, stats in categories.items():
            rate = (stats['passed'] / stats['total']) * 100
            self.logger.info(f"   {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Key improvements verification
        self.logger.info("\n🚀 Key Improvements Verified:")
        
        # Check for early detection bonuses
        early_detection_count = sum(1 for r in results 
                                  if r['confidence_data'].get('level') == 'EARLY_DETECTION')
        self.logger.info(f"   ✅ Early Detection Bonuses: {early_detection_count} tokens received EARLY_DETECTION status")
        
        # Check that new tokens aren't penalized
        ultra_early_penalties = sum(1 for r in results 
                                  if r['age_minutes'] <= 30 and r['threshold_adjustment'] > 1.1)
        self.logger.info(f"   ✅ No Ultra-Early Penalties: {ultra_early_penalties} ultra-early tokens penalized (should be 0)")
        
        # Check mature token quality control
        mature_quality_control = sum(1 for r in results 
                                   if r['age_minutes'] > 720 and r['confidence_data'].get('level') == 'VERY_LOW')
        self.logger.info(f"   ✅ Mature Token Quality Control: {mature_quality_control} mature tokens flagged for poor data")
        
        if success_rate >= 90:
            self.logger.info("\n🎉 AGE-AWARE CONFIDENCE SYSTEM: EXCELLENT PERFORMANCE!")
        elif success_rate >= 80:
            self.logger.info("\n✅ AGE-AWARE CONFIDENCE SYSTEM: GOOD PERFORMANCE")
        else:
            self.logger.warning("\n⚠️  AGE-AWARE CONFIDENCE SYSTEM: NEEDS IMPROVEMENT")
        
        return success_rate

async def main():
    """Run the age-aware confidence system test"""
    tester = AgeAwareConfidenceTester()
    results = await tester.run_comprehensive_test()
    
    # Return success code
    success_rate = sum(1 for r in results if r['overall_success']) / len(results) * 100
    return 0 if success_rate >= 90 else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 