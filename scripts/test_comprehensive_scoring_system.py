#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE SCORING SYSTEM TEST

Production-readiness validation for the interaction-based scoring system.
This test covers all components, interactions, edge cases, and integration points.

Test Categories:
1. Traditional Components Calculation
2. Factor Normalization & Extraction
3. Interaction Detection (Danger, Amplification, Contradiction)
4. Score Modification Logic
5. Integration with Main Detector
6. Edge Cases & Error Handling
7. Performance & Memory Usage
8. Fallback System Validation
"""

import asyncio
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.interaction_based_scoring_system import (
    InteractionBasedScorer, FactorValues, InteractionType, RiskLevel
)

class ScoringSystemTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scorer = InteractionBasedScorer(debug_mode=True)
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {},
            'edge_case_results': {},
            'integration_results': {}
        }
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", 
                       expected_value: Any = None, actual_value: Any = None):
        """Log test result with details"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
            
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'expected': expected_value,
            'actual': actual_value,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"{status} {test_name}")
        if details:
            print(f"    📝 {details}")
        if not passed and expected_value is not None:
            print(f"    🎯 Expected: {expected_value}")
            print(f"    📊 Actual: {actual_value}")
        print()

    def test_traditional_components_calculation(self) -> bool:
        """Test traditional component calculations"""
        print("🔍 Testing Traditional Components Calculation...")
        
        # Test Case 1: High-quality token
        try:
            candidate = {
                'platforms': ['jupiter', 'raydium', 'orca', 'meteora'],
                'cross_platform_score': 32
            }
            
            overview_data = {
                'market_cap': 1500000,
                'liquidity': 750000,
                'price_change_24h': 25.5,
                'holders': 1200
            }
            
            whale_analysis = {
                'whale_concentration': 45,
                'smart_money_detected': True
            }
            
            volume_price_analysis = {
                'volume_trend': 'increasing',
                'price_momentum': 'bullish'
            }
            
            security_analysis = {
                'security_score': 85,
                'risk_factors': ['low_liquidity']
            }
            
            vlr_analysis = {
                'vlr_ratio': 6.5,
                'vlr_score': 12
            }
            
            # Import the detector to test traditional components
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            detector = HighConvictionTokenDetector(debug_mode=True)
            
            components = detector._calculate_traditional_components(
                candidate, overview_data, whale_analysis, volume_price_analysis,
                {}, security_analysis, {}, {}, vlr_analysis
            )
            
            # Validate components
            expected_ranges = {
                'base_score': (30, 40),
                'overview_score': (15, 20),
                'whale_score': (10, 15),
                'volume_score': (10, 15),
                'security_score': (6, 10),
                'vlr_score': (8, 15)
            }
            
            all_valid = True
            for component, (min_val, max_val) in expected_ranges.items():
                actual_val = components.get(component, 0)
                if not (min_val <= actual_val <= max_val):
                    all_valid = False
                    self.log_test_result(
                        f"Traditional Component {component}",
                        False,
                        f"Value {actual_val} not in expected range {min_val}-{max_val}",
                        f"{min_val}-{max_val}",
                        actual_val
                    )
            
            if all_valid:
                total_score = sum(components.values())
                self.log_test_result(
                    "Traditional Components Calculation",
                    True,
                    f"All components in expected ranges. Total: {total_score}",
                    "70-120",
                    total_score
                )
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test_result(
                "Traditional Components Calculation",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_factor_normalization(self) -> bool:
        """Test factor value extraction and normalization"""
        print("🔍 Testing Factor Normalization...")
        
        try:
            # Test Case: Various factor values
            test_cases = [
                {
                    'name': 'High VLR + Low Liquidity (Danger)',
                    'raw_vlr': 15.2,
                    'raw_liquidity': 45000,
                    'smart_money': True,
                    'platforms': 3,
                    'expected_vlr_ratio': 0.76,  # 15.2/20
                    'expected_liquidity': 0.045,  # 45000/1000000
                    'expected_smart_money': 0.7   # Base detection
                },
                {
                    'name': 'Optimal Values (Amplification)',
                    'raw_vlr': 6.5,
                    'raw_liquidity': 800000,
                    'smart_money': True,
                    'platforms': 4,
                    'expected_vlr_ratio': 0.325,  # 6.5/20
                    'expected_liquidity': 0.8,    # 800000/1000000
                    'expected_smart_money': 0.9   # Base + bonuses
                }
            ]
            
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            detector = HighConvictionTokenDetector(debug_mode=True)
            
            all_passed = True
            for test_case in test_cases:
                candidate = {'platforms': ['platform'] * test_case['platforms']}
                overview_data = {'liquidity': test_case['raw_liquidity']}
                whale_analysis = {'smart_money_detected': test_case['smart_money']}
                vlr_analysis = {'vlr_ratio': test_case['raw_vlr']}
                
                factors = detector._extract_factor_values(
                    candidate, overview_data, whale_analysis, {}, {}, vlr_analysis
                )
                
                # Check VLR normalization
                vlr_diff = abs(factors.vlr_ratio - test_case['expected_vlr_ratio'])
                if vlr_diff > 0.01:
                    self.log_test_result(
                        f"VLR Normalization - {test_case['name']}",
                        False,
                        f"VLR ratio difference: {vlr_diff}",
                        test_case['expected_vlr_ratio'],
                        factors.vlr_ratio
                    )
                    all_passed = False
                
                # Check liquidity normalization
                liq_diff = abs(factors.liquidity - test_case['expected_liquidity'])
                if liq_diff > 0.01:
                    self.log_test_result(
                        f"Liquidity Normalization - {test_case['name']}",
                        False,
                        f"Liquidity difference: {liq_diff}",
                        test_case['expected_liquidity'],
                        factors.liquidity
                    )
                    all_passed = False
            
            if all_passed:
                self.log_test_result(
                    "Factor Normalization",
                    True,
                    "All normalization tests passed"
                )
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test_result(
                "Factor Normalization",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_danger_detection(self) -> bool:
        """Test danger interaction detection"""
        print("🔍 Testing Danger Detection...")
        
        try:
            # Test Case 1: Pump & Dump Pattern
            pump_dump_factors = FactorValues(
                vlr_ratio=0.76,  # VLR 15.2 normalized
                liquidity=0.045,  # $45K normalized
                raw_vlr=15.2,
                raw_liquidity=45000,
                platforms_count=3
            )
            
            interactions = self.scorer._detect_danger_interactions(pump_dump_factors)
            
            # Should detect critical danger
            critical_dangers = [i for i in interactions if i.risk_level == RiskLevel.CRITICAL]
            if not critical_dangers:
                self.log_test_result(
                    "Pump & Dump Detection",
                    False,
                    "No critical danger detected for pump & dump pattern",
                    "1+ critical danger",
                    len(critical_dangers)
                )
                return False
            
            # Check for manipulation detection
            manipulation_detected = any(
                'manipulation' in i.explanation.lower() or 'pump' in i.explanation.lower()
                for i in critical_dangers
            )
            
            if not manipulation_detected:
                self.log_test_result(
                    "Manipulation Pattern Detection",
                    False,
                    "Manipulation pattern not identified in danger explanations",
                    "Manipulation detected",
                    "Not detected"
                )
                return False
            
            # Test Case 2: Rug Pull Pattern
            rug_pull_factors = FactorValues(
                security_score=0.25,  # Poor security
                whale_concentration=0.85,  # High whale dominance
                platforms_count=2
            )
            
            interactions = self.scorer._detect_danger_interactions(rug_pull_factors)
            rug_pull_dangers = [i for i in interactions if 'rug' in i.explanation.lower()]
            
            if not rug_pull_dangers:
                self.log_test_result(
                    "Rug Pull Detection",
                    False,
                    "Rug pull pattern not detected",
                    "1+ rug pull danger",
                    len(rug_pull_dangers)
                )
                return False
            
            self.log_test_result(
                "Danger Detection",
                True,
                f"Detected {len(critical_dangers)} critical dangers including manipulation and rug pull patterns"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Danger Detection",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_signal_amplification(self) -> bool:
        """Test signal amplification detection"""
        print("🔍 Testing Signal Amplification...")
        
        try:
            # Test Case: Smart Money + Volume Surge
            amplification_factors = FactorValues(
                smart_money_score=0.8,  # Strong smart money
                volume_momentum=0.75,   # High volume
                cross_platform_validation=0.8,  # Well validated
                security_score=0.85,    # Good security
                platforms_count=4
            )
            
            interactions = self.scorer._detect_signal_amplifications(amplification_factors)
            
            # Should detect amplifications
            amplifications = [i for i in interactions if i.interaction_type == InteractionType.SIGNAL_AMPLIFICATION]
            
            if not amplifications:
                self.log_test_result(
                    "Signal Amplification Detection",
                    False,
                    "No amplifications detected for high-quality factors",
                    "1+ amplification",
                    len(amplifications)
                )
                return False
            
            # Check for smart money amplification
            smart_money_amp = any(
                'smart money' in i.explanation.lower() and 'volume' in i.explanation.lower()
                for i in amplifications
            )
            
            if not smart_money_amp:
                self.log_test_result(
                    "Smart Money + Volume Amplification",
                    False,
                    "Smart money + volume amplification not detected",
                    "Smart money amplification",
                    "Not detected"
                )
                return False
            
            # Validate score modifiers are amplifying (>1.0)
            amplifying_modifiers = [i.score_modifier for i in amplifications if i.score_modifier > 1.0]
            
            if not amplifying_modifiers:
                self.log_test_result(
                    "Amplification Score Modifiers",
                    False,
                    "No amplifying score modifiers found",
                    ">1.0 modifiers",
                    amplifying_modifiers
                )
                return False
            
            self.log_test_result(
                "Signal Amplification",
                True,
                f"Detected {len(amplifications)} amplifications with modifiers: {amplifying_modifiers}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Signal Amplification",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_contradiction_detection(self) -> bool:
        """Test contradiction detection"""
        print("🔍 Testing Contradiction Detection...")
        
        try:
            # Test Case: High Volume but Limited Platform Validation
            contradiction_factors = FactorValues(
                volume_momentum=0.85,   # High volume
                cross_platform_validation=0.25,  # Limited validation
                security_score=0.8,     # Good security
                whale_concentration=0.85,  # High whale concentration (contradiction with security)
                platforms_count=2
            )
            
            interactions = self.scorer._detect_contradictions(contradiction_factors)
            
            # Should detect contradictions
            contradictions = [i for i in interactions if i.interaction_type == InteractionType.CONTRADICTION]
            
            if not contradictions:
                self.log_test_result(
                    "Contradiction Detection",
                    False,
                    "No contradictions detected for conflicting factors",
                    "1+ contradiction",
                    len(contradictions)
                )
                return False
            
            # Validate score modifiers are dampening (<1.0)
            dampening_modifiers = [i.score_modifier for i in contradictions if i.score_modifier < 1.0]
            
            if not dampening_modifiers:
                self.log_test_result(
                    "Contradiction Score Modifiers",
                    False,
                    "No dampening score modifiers found",
                    "<1.0 modifiers",
                    dampening_modifiers
                )
                return False
            
            self.log_test_result(
                "Contradiction Detection",
                True,
                f"Detected {len(contradictions)} contradictions with dampening modifiers: {dampening_modifiers}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Contradiction Detection",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_score_modification_logic(self) -> bool:
        """Test score modification application logic"""
        print("🔍 Testing Score Modification Logic...")
        
        try:
            # Test Case 1: Critical Override
            base_score = 85.0
            traditional_components = {'base_score': 40, 'overview_score': 20, 'whale_score': 15, 'volume_score': 10}
            
            danger_factors = FactorValues(
                vlr_ratio=0.8,  # High VLR
                liquidity=0.04,  # Low liquidity
                raw_vlr=16.0,
                raw_liquidity=40000
            )
            
            final_score, analysis = self.scorer.calculate_interaction_based_score(
                danger_factors, traditional_components
            )
            
            # Critical override should result in very low score
            if final_score > 10:
                self.log_test_result(
                    "Critical Override Logic",
                    False,
                    f"Critical danger not properly overriding score",
                    "<10",
                    final_score
                )
                return False
            
            # Test Case 2: Amplification
            amplification_factors = FactorValues(
                smart_money_score=0.8,
                volume_momentum=0.8,
                cross_platform_validation=0.8,
                security_score=0.8,
                platforms_count=4
            )
            
            final_score_amp, analysis_amp = self.scorer.calculate_interaction_based_score(
                amplification_factors, traditional_components
            )
            
            # Amplification should increase score significantly
            baseline = sum(traditional_components.values())
            if final_score_amp <= baseline:
                self.log_test_result(
                    "Amplification Logic",
                    False,
                    f"Amplification not increasing score from baseline",
                    f">{baseline}",
                    final_score_amp
                )
                return False
            
            self.log_test_result(
                "Score Modification Logic",
                True,
                f"Critical override: {final_score:.1f}, Amplification: {final_score_amp:.1f} (from {baseline})"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Score Modification Logic",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_integration_with_detector(self) -> bool:
        """Test integration with the main high conviction detector"""
        print("🔍 Testing Integration with Main Detector...")
        
        try:
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            detector = HighConvictionTokenDetector(debug_mode=True)
            
            # Test that the main detector uses interaction-based scoring
            if not hasattr(detector, '_calculate_final_score_interaction_based'):
                self.log_test_result(
                    "Detector Integration - Method Exists",
                    False,
                    "Main detector missing interaction-based scoring method",
                    "Method exists",
                    "Method missing"
                )
                return False
            
            # Test scoring method delegation
            try:
                # Mock data for integration test
                candidate = {'platforms': ['jupiter', 'raydium'], 'address': 'test_address'}
                overview_data = {'market_cap': 500000, 'liquidity': 200000}
                whale_analysis = {'whale_concentration': 35, 'smart_money_detected': False}
                volume_analysis = {'volume_trend': 'stable'}
                security_analysis = {'security_score': 75, 'risk_factors': []}
                
                score, breakdown = detector._calculate_final_score(
                    candidate, overview_data, whale_analysis, volume_analysis,
                    {}, security_analysis, {}, {}, {}
                )
                
                # Validate score is reasonable
                if not (0 <= score <= 100):
                    self.log_test_result(
                        "Detector Integration - Score Range",
                        False,
                        f"Score {score} outside valid range",
                        "0-100",
                        score
                    )
                    return False
                
                # Validate breakdown contains interaction analysis
                if 'scoring_methodology' not in breakdown:
                    self.log_test_result(
                        "Detector Integration - Breakdown Format",
                        False,
                        "Scoring breakdown missing methodology info",
                        "Methodology present",
                        "Missing"
                    )
                    return False
                
                methodology = breakdown.get('scoring_methodology', '')
                if 'INTERACTION' not in methodology:
                    self.log_test_result(
                        "Detector Integration - Methodology",
                        False,
                        f"Methodology not interaction-based: {methodology}",
                        "INTERACTION-BASED",
                        methodology
                    )
                    return False
                
                self.log_test_result(
                    "Integration with Main Detector",
                    True,
                    f"Successfully integrated. Score: {score:.1f}, Methodology: {methodology}"
                )
                return True
                
            except Exception as method_error:
                self.log_test_result(
                    "Detector Integration - Method Execution",
                    False,
                    f"Error executing integration: {str(method_error)}",
                    "No exception",
                    str(method_error)
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Integration with Main Detector",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_edge_cases(self) -> bool:
        """Test edge cases and error handling"""
        print("🔍 Testing Edge Cases...")
        
        edge_cases_passed = 0
        total_edge_cases = 0
        
        # Edge Case 1: Empty/Null Data
        try:
            total_edge_cases += 1
            empty_factors = FactorValues()
            empty_components = {}
            
            score, analysis = self.scorer.calculate_interaction_based_score(
                empty_factors, empty_components
            )
            
            if 0 <= score <= 100:
                edge_cases_passed += 1
                self.log_test_result(
                    "Edge Case - Empty Data",
                    True,
                    f"Handled empty data gracefully. Score: {score}"
                )
            else:
                self.log_test_result(
                    "Edge Case - Empty Data",
                    False,
                    f"Invalid score for empty data: {score}",
                    "0-100",
                    score
                )
        except Exception as e:
            self.log_test_result(
                "Edge Case - Empty Data",
                False,
                f"Exception with empty data: {str(e)}",
                "Graceful handling",
                str(e)
            )
        
        # Edge Case 2: Extreme Values
        try:
            total_edge_cases += 1
            extreme_factors = FactorValues(
                vlr_ratio=1.0,  # Maximum VLR
                liquidity=0.0,  # Minimum liquidity
                smart_money_score=1.0,  # Maximum smart money
                volume_momentum=1.0,  # Maximum volume
                raw_vlr=1000.0,  # Extreme raw VLR
                raw_liquidity=1.0  # Extreme low liquidity
            )
            
            extreme_components = {'base_score': 100, 'overview_score': 100}
            
            score, analysis = self.scorer.calculate_interaction_based_score(
                extreme_factors, extreme_components
            )
            
            if 0 <= score <= 100:
                edge_cases_passed += 1
                self.log_test_result(
                    "Edge Case - Extreme Values",
                    True,
                    f"Handled extreme values. Score: {score}"
                )
            else:
                self.log_test_result(
                    "Edge Case - Extreme Values",
                    False,
                    f"Invalid score for extreme values: {score}",
                    "0-100",
                    score
                )
        except Exception as e:
            self.log_test_result(
                "Edge Case - Extreme Values",
                False,
                f"Exception with extreme values: {str(e)}",
                "Graceful handling",
                str(e)
            )
        
        # Edge Case 3: Negative Values (Should be normalized)
        try:
            total_edge_cases += 1
            negative_components = {
                'base_score': -10,
                'overview_score': -5,
                'whale_score': 15
            }
            
            normal_factors = FactorValues(vlr_ratio=0.3, liquidity=0.5)
            
            score, analysis = self.scorer.calculate_interaction_based_score(
                normal_factors, negative_components
            )
            
            if 0 <= score <= 100:
                edge_cases_passed += 1
                self.log_test_result(
                    "Edge Case - Negative Components",
                    True,
                    f"Handled negative components. Score: {score}"
                )
            else:
                self.log_test_result(
                    "Edge Case - Negative Components",
                    False,
                    f"Invalid score for negative components: {score}",
                    "0-100",
                    score
                )
        except Exception as e:
            self.log_test_result(
                "Edge Case - Negative Components",
                False,
                f"Exception with negative components: {str(e)}",
                "Graceful handling",
                str(e)
            )
        
        self.test_results['edge_case_results'] = {
            'passed': edge_cases_passed,
            'total': total_edge_cases,
            'success_rate': (edge_cases_passed / total_edge_cases) * 100 if total_edge_cases > 0 else 0
        }
        
        return edge_cases_passed == total_edge_cases

    def test_performance(self) -> bool:
        """Test performance and memory usage"""
        print("🔍 Testing Performance...")
        
        try:
            # Performance test with multiple scoring runs
            num_iterations = 100
            
            factors = FactorValues(
                vlr_ratio=0.4,
                liquidity=0.6,
                smart_money_score=0.7,
                volume_momentum=0.5,
                platforms_count=3
            )
            
            components = {
                'base_score': 24,
                'overview_score': 16,
                'whale_score': 12,
                'volume_score': 10,
                'security_score': 8
            }
            
            start_time = time.time()
            scores = []
            
            for _ in range(num_iterations):
                score, analysis = self.scorer.calculate_interaction_based_score(factors, components)
                scores.append(score)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time_per_score = total_time / num_iterations
            
            # Performance thresholds
            max_avg_time = 0.01  # 10ms per scoring operation
            
            performance_passed = avg_time_per_score < max_avg_time
            
            self.test_results['performance_metrics'] = {
                'total_time': total_time,
                'avg_time_per_score': avg_time_per_score,
                'iterations': num_iterations,
                'scores_range': [min(scores), max(scores)],
                'consistent_results': len(set(scores)) == 1,  # All scores should be identical for same input
                'performance_threshold_met': performance_passed
            }
            
            self.log_test_result(
                "Performance Test",
                performance_passed,
                f"Avg time per score: {avg_time_per_score*1000:.2f}ms, Consistent results: {len(set(scores)) == 1}",
                f"<{max_avg_time*1000}ms",
                f"{avg_time_per_score*1000:.2f}ms"
            )
            
            return performance_passed
            
        except Exception as e:
            self.log_test_result(
                "Performance Test",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    def test_fallback_system(self) -> bool:
        """Test fallback system validation"""
        print("🔍 Testing Fallback System...")
        
        try:
            from scripts.high_conviction_token_detector import HighConvictionTokenDetector
            detector = HighConvictionTokenDetector(debug_mode=True)
            
            # Test fallback method exists
            if not hasattr(detector, '_calculate_final_score_linear_fallback'):
                self.log_test_result(
                    "Fallback System - Method Exists",
                    False,
                    "Fallback method missing",
                    "Method exists",
                    "Method missing"
                )
                return False
            
            # Test fallback produces reasonable results
            candidate = {'platforms': ['jupiter', 'raydium']}
            overview_data = {'market_cap': 300000, 'liquidity': 150000}
            whale_analysis = {'whale_concentration': 40}
            
            fallback_score, fallback_breakdown = detector._calculate_final_score_linear_fallback(
                candidate, overview_data, whale_analysis, {}, {}, {}, {}, {}, {}
            )
            
            # Validate fallback score
            if not (0 <= fallback_score <= 200):  # Linear can exceed 100
                self.log_test_result(
                    "Fallback System - Score Range",
                    False,
                    f"Fallback score {fallback_score} outside reasonable range",
                    "0-200",
                    fallback_score
                )
                return False
            
            # Validate fallback breakdown indicates the mathematical flaw
            methodology = fallback_breakdown.get('scoring_methodology', '')
            if 'LINEAR' not in methodology or 'FLAW' not in methodology:
                self.log_test_result(
                    "Fallback System - Flaw Warning",
                    False,
                    f"Fallback not properly warning about mathematical flaw: {methodology}",
                    "LINEAR FLAW warning",
                    methodology
                )
                return False
            
            self.log_test_result(
                "Fallback System",
                True,
                f"Fallback working correctly. Score: {fallback_score}, Methodology: {methodology}"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Fallback System",
                False,
                f"Exception: {str(e)}",
                "No exception",
                str(e)
            )
            return False

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        print("🧪 COMPREHENSIVE SCORING SYSTEM TEST")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Test suite
        test_functions = [
            self.test_traditional_components_calculation,
            self.test_factor_normalization,
            self.test_danger_detection,
            self.test_signal_amplification,
            self.test_contradiction_detection,
            self.test_score_modification_logic,
            self.test_integration_with_detector,
            self.test_edge_cases,
            self.test_performance,
            self.test_fallback_system
        ]
        
        # Run all tests
        for test_func in test_functions:
            try:
                test_func()
            except Exception as e:
                self.log_test_result(
                    f"Test Function {test_func.__name__}",
                    False,
                    f"Unexpected exception: {str(e)}",
                    "No exception",
                    str(e)
                )
                print(f"⚠️ Exception in {test_func.__name__}: {e}")
                traceback.print_exc()
        
        end_time = time.time()
        total_test_time = end_time - start_time
        
        # Calculate final results
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        
        self.test_results['summary'] = {
            'total_test_time': total_test_time,
            'success_rate': success_rate,
            'production_ready': success_rate >= 90,  # 90% pass rate for production readiness
            'critical_failures': [
                test for test in self.test_results['test_details'] 
                if not test['passed'] and any(keyword in test['test_name'].lower() 
                for keyword in ['integration', 'danger', 'modification'])
            ]
        }
        
        return self.test_results

    def print_final_report(self):
        """Print comprehensive test report"""
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST REPORT")
        print("=" * 60)
        
        results = self.test_results
        summary = results['summary']
        
        print(f"📊 Overall Results:")
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   Passed: {results['passed_tests']} ✅")
        print(f"   Failed: {results['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Test Time: {summary['total_test_time']:.2f}s")
        print()
        
        # Production readiness assessment
        if summary['production_ready']:
            print("🚀 PRODUCTION READINESS: ✅ READY")
            print("   System meets production quality standards (≥90% pass rate)")
        else:
            print("⚠️ PRODUCTION READINESS: ❌ NOT READY")
            print("   System requires fixes before production deployment")
        print()
        
        # Critical failures
        if summary['critical_failures']:
            print("🚨 Critical Failures:")
            for failure in summary['critical_failures']:
                print(f"   ❌ {failure['test_name']}: {failure['details']}")
            print()
        
        # Performance metrics
        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            print("⚡ Performance Metrics:")
            print(f"   Average time per score: {perf['avg_time_per_score']*1000:.2f}ms")
            print(f"   Consistent results: {'✅' if perf['consistent_results'] else '❌'}")
            print(f"   Performance threshold met: {'✅' if perf['performance_threshold_met'] else '❌'}")
            print()
        
        # Edge case results
        if 'edge_case_results' in results:
            edge = results['edge_case_results']
            print("🔍 Edge Case Handling:")
            print(f"   Passed: {edge['passed']}/{edge['total']}")
            print(f"   Success rate: {edge['success_rate']:.1f}%")
            print()
        
        # Failed tests detail
        failed_tests = [test for test in results['test_details'] if not test['passed']]
        if failed_tests:
            print("❌ Failed Tests Details:")
            for test in failed_tests:
                print(f"   • {test['test_name']}")
                print(f"     Details: {test['details']}")
                if test['expected'] and test['actual']:
                    print(f"     Expected: {test['expected']}")
                    print(f"     Actual: {test['actual']}")
                print()
        
        # Recommendations
        print("💡 Recommendations:")
        if summary['success_rate'] >= 95:
            print("   🎯 Excellent! System is highly robust and ready for production.")
        elif summary['success_rate'] >= 90:
            print("   ✅ Good! System meets production standards with minor issues.")
        elif summary['success_rate'] >= 80:
            print("   ⚠️ Review failed tests and fix critical issues before deployment.")
        else:
            print("   🚨 Significant issues detected. Requires major fixes before production.")
        
        print("=" * 60)

def main():
    """Main test execution"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive test
    tester = ScoringSystemTester()
    
    async def run_test():
        results = await tester.run_comprehensive_test()
        tester.print_final_report()
        
        # Save results to file
        results_file = Path("test_results") / f"comprehensive_scoring_test_{int(time.time())}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results saved to: {results_file}")
        
        return results['summary']['production_ready']
    
    # Run the test
    production_ready = asyncio.run(run_test())
    
    # Exit with appropriate code
    sys.exit(0 if production_ready else 1)

if __name__ == "__main__":
    main() 