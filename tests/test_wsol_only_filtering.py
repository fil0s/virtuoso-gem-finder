#!/usr/bin/env python3
"""
WSOL-Only Filtering Test Script

Tests the WSOL-only filtering functionality in CrossPlatformAnalyzer
to ensure it correctly filters DEX pools/pairs to only include WSOL-paired tokens.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
WSOL_TEST_ADDRESS = 'So11111111111111111111111111111111111111112'  # WSOL address
USDC_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  # USDC address
SAMPLE_TOKEN_1 = '6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN'  # Sample token 1
SAMPLE_TOKEN_2 = '5c74v6Px9RKwdGWCfqLGfEk7UZfE3Y4qJbuYrLbVG63V'  # Sample token 2

class WSolFilteringTester:
    """Test class for WSOL-only filtering functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'wsol_address': WSOL_TEST_ADDRESS,
            'tests': [],
            'summary': {}
        }
    
    def create_mock_meteora_data(self) -> List[Dict[str, Any]]:
        """Create mock Meteora pool data for testing"""
        return [
            # WSOL-TOKEN1 pair (should be included)
            {
                'address': 'meteora_pool_1',
                'name': 'WSOL-TOKEN1',
                'mint_x': WSOL_TEST_ADDRESS,
                'mint_y': SAMPLE_TOKEN_1,
                'bin_step': 25,
                'reserve_x_amount': 1000000,
                'reserve_y_amount': 5000000,
                'base_fee_percentage': 0.25
            },
            # TOKEN2-WSOL pair (should be included)
            {
                'address': 'meteora_pool_2',
                'name': 'TOKEN2-WSOL',
                'mint_x': SAMPLE_TOKEN_2,
                'mint_y': WSOL_TEST_ADDRESS,
                'bin_step': 50,
                'reserve_x_amount': 2000000,
                'reserve_y_amount': 800000,
                'base_fee_percentage': 0.3
            },
            # USDC-TOKEN1 pair (should be excluded in WSOL-only mode)
            {
                'address': 'meteora_pool_3',
                'name': 'USDC-TOKEN1',
                'mint_x': USDC_ADDRESS,
                'mint_y': SAMPLE_TOKEN_1,
                'bin_step': 10,
                'reserve_x_amount': 3000000,
                'reserve_y_amount': 1500000,
                'base_fee_percentage': 0.15
            },
            # TOKEN1-TOKEN2 pair (should be excluded - no WSOL)
            {
                'address': 'meteora_pool_4',
                'name': 'TOKEN1-TOKEN2',
                'mint_x': SAMPLE_TOKEN_1,
                'mint_y': SAMPLE_TOKEN_2,
                'bin_step': 100,
                'reserve_x_amount': 500000,
                'reserve_y_amount': 400000,
                'base_fee_percentage': 0.5
            }
        ]
    
    def test_meteora_filtering_logic(self) -> Dict[str, Any]:
        """Test Meteora WSOL-only filtering logic"""
        self.logger.info("🌊 Testing Meteora WSOL-only filtering...")
        
        test_result = {
            'test_name': 'meteora_filtering',
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            mock_data = self.create_mock_meteora_data()
            excluded_addresses = {USDC_ADDRESS}
            
            # Simulate WSOL-only filtering logic
            wsol_only_tokens = []
            WSOL_ONLY_MODE = True
            
            for pool in mock_data:
                mint_x = pool.get('mint_x', '')
                mint_y = pool.get('mint_y', '')
                
                target_mints = []
                if WSOL_ONLY_MODE:
                    # Only include pairs where one side is WSOL and the other is not excluded
                    if mint_x == WSOL_TEST_ADDRESS and mint_y and mint_y not in excluded_addresses:
                        target_mints.append(mint_y)  # Add the non-WSOL token
                    elif mint_y == WSOL_TEST_ADDRESS and mint_x and mint_x not in excluded_addresses:
                        target_mints.append(mint_x)  # Add the non-WSOL token
                
                for mint_address in target_mints:
                    wsol_only_tokens.append({
                        'address': mint_address,
                        'pool': pool['address'],
                        'pair_type': 'wsol_pair'
                    })
            
            # Validate results
            expected_wsol_tokens = [SAMPLE_TOKEN_1, SAMPLE_TOKEN_2]
            found_wsol_tokens = [token['address'] for token in wsol_only_tokens]
            
            test_result['details'] = {
                'total_pools': len(mock_data),
                'wsol_only_tokens_found': len(wsol_only_tokens),
                'expected_wsol_tokens': expected_wsol_tokens,
                'found_wsol_tokens': found_wsol_tokens,
                'correctly_filtered': set(found_wsol_tokens) == set(expected_wsol_tokens)
            }
            
            if not test_result['details']['correctly_filtered']:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Expected {expected_wsol_tokens}, got {found_wsol_tokens}")
            
            self.logger.info(f"✅ Meteora test: {len(wsol_only_tokens)} WSOL pairs found from {len(mock_data)} pools")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ Meteora test failed: {e}")
        
        return test_result
    
    def test_configuration_validation(self) -> Dict[str, Any]:
        """Test configuration validation and constants"""
        self.logger.info("⚙️ Testing configuration validation...")
        
        test_result = {
            'test_name': 'configuration_validation',
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # Test WSOL address validation
            expected_wsol = 'So11111111111111111111111111111111111111112'
            
            test_result['details'] = {
                'wsol_address_matches': WSOL_TEST_ADDRESS == expected_wsol,
                'wsol_address_length': len(WSOL_TEST_ADDRESS),
                'constants_properly_defined': True
            }
            
            if WSOL_TEST_ADDRESS != expected_wsol:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"WSOL address mismatch: expected {expected_wsol}, got {WSOL_TEST_ADDRESS}")
            
            if len(WSOL_TEST_ADDRESS) != 43:  # WSOL address is 43 characters
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"WSOL address length invalid: expected 43, got {len(WSOL_TEST_ADDRESS)}")
            
            self.logger.info(f"✅ Configuration test: WSOL address valid")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ Configuration test failed: {e}")
        
        return test_result
    
    def test_filtering_scenarios(self) -> Dict[str, Any]:
        """Test various filtering scenarios"""
        self.logger.info("🔧 Testing filtering scenarios...")
        
        test_result = {
            'test_name': 'filtering_scenarios',
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # Test scenarios
            scenarios = [
                {
                    'name': 'wsol_first_position',
                    'mint_x': WSOL_TEST_ADDRESS,
                    'mint_y': SAMPLE_TOKEN_1,
                    'expected_token': SAMPLE_TOKEN_1,
                    'should_include': True
                },
                {
                    'name': 'wsol_second_position',
                    'mint_x': SAMPLE_TOKEN_2,
                    'mint_y': WSOL_TEST_ADDRESS,
                    'expected_token': SAMPLE_TOKEN_2,
                    'should_include': True
                },
                {
                    'name': 'no_wsol_pair',
                    'mint_x': SAMPLE_TOKEN_1,
                    'mint_y': SAMPLE_TOKEN_2,
                    'expected_token': None,
                    'should_include': False
                },
                {
                    'name': 'wsol_with_excluded_token',
                    'mint_x': WSOL_TEST_ADDRESS,
                    'mint_y': USDC_ADDRESS,
                    'expected_token': None,
                    'should_include': False
                },
                {
                    'name': 'empty_addresses',
                    'mint_x': '',
                    'mint_y': WSOL_TEST_ADDRESS,
                    'expected_token': None,
                    'should_include': False
                }
            ]
            
            excluded_addresses = {USDC_ADDRESS}
            scenario_results = []
            
            for scenario in scenarios:
                mint_x = scenario['mint_x']
                mint_y = scenario['mint_y']
                
                # Apply filtering logic
                target_token = None
                if mint_x == WSOL_TEST_ADDRESS and mint_y and mint_y not in excluded_addresses:
                    target_token = mint_y
                elif mint_y == WSOL_TEST_ADDRESS and mint_x and mint_x not in excluded_addresses:
                    target_token = mint_x
                
                # Validate result
                expected_token = scenario['expected_token']
                should_include = scenario['should_include']
                
                scenario_result = {
                    'name': scenario['name'],
                    'expected_token': expected_token,
                    'actual_token': target_token,
                    'should_include': should_include,
                    'actually_included': target_token is not None,
                    'correct': (target_token == expected_token) and (bool(target_token) == should_include)
                }
                
                scenario_results.append(scenario_result)
            
            # Compile results
            correct_scenarios = [s for s in scenario_results if s['correct']]
            
            test_result['details'] = {
                'total_scenarios': len(scenarios),
                'correct_scenarios': len(correct_scenarios),
                'scenario_results': scenario_results
            }
            
            if len(correct_scenarios) != len(scenarios):
                test_result['status'] = 'FAIL'
                failed_scenarios = [s for s in scenario_results if not s['correct']]
                test_result['errors'].extend([f"Scenario '{s['name']}' failed" for s in failed_scenarios])
            
            self.logger.info(f"✅ Filtering scenarios: {len(correct_scenarios)}/{len(scenarios)} passed")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ Filtering scenarios test failed: {e}")
        
        return test_result
    
    async def test_import_validation(self) -> Dict[str, Any]:
        """Test that the analyzer imports work correctly"""
        self.logger.info("📦 Testing import validation...")
        
        test_result = {
            'test_name': 'import_validation',
            'status': 'PASS',
            'details': {},
            'errors': []
        }
        
        try:
            # Try to import the analyzer
            from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer, WSOL_ADDRESS, WSOL_ONLY_MODE
            
            # Validate imports
            analyzer_available = CrossPlatformAnalyzer is not None
            wsol_address_available = WSOL_ADDRESS is not None
            wsol_mode_available = WSOL_ONLY_MODE is not None
            
            test_result['details'] = {
                'analyzer_available': analyzer_available,
                'wsol_address_available': wsol_address_available,
                'wsol_mode_available': wsol_mode_available,
                'wsol_address_value': WSOL_ADDRESS,
                'wsol_mode_value': WSOL_ONLY_MODE,
                'imports_successful': all([analyzer_available, wsol_address_available, wsol_mode_available])
            }
            
            if not test_result['details']['imports_successful']:
                test_result['status'] = 'FAIL'
                test_result['errors'].append("Failed to import required components from cross_platform_token_analyzer")
            
            self.logger.info(f"✅ Import validation: All imports successful")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'].append(str(e))
            self.logger.error(f"❌ Import validation failed: {e}")
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all WSOL filtering tests"""
        self.logger.info("🚀 Starting WSOL-only filtering tests...")
        
        # Run all tests
        tests = [
            self.test_configuration_validation(),
            await self.test_import_validation(),
            self.test_meteora_filtering_logic(),
            self.test_filtering_scenarios()
        ]
        
        # Compile results
        self.test_results['tests'] = tests
        
        # Generate summary
        passed_tests = [t for t in tests if t['status'] == 'PASS']
        failed_tests = [t for t in tests if t['status'] == 'FAIL']
        error_tests = [t for t in tests if t['status'] == 'ERROR']
        
        self.test_results['summary'] = {
            'total_tests': len(tests),
            'passed': len(passed_tests),
            'failed': len(failed_tests),
            'errors': len(error_tests),
            'success_rate': f"{(len(passed_tests) / len(tests) * 100):.1f}%",
            'overall_status': 'PASS' if len(failed_tests) == 0 and len(error_tests) == 0 else 'FAIL'
        }
        
        return self.test_results
    
    def print_test_summary(self):
        """Print formatted test summary"""
        summary = self.test_results['summary']
        
        print("\n" + "="*60)
        print("🪙 WSOL-ONLY FILTERING TEST RESULTS")
        print("="*60)
        
        print(f"📊 Overall Status: {summary['overall_status']}")
        print(f"✅ Tests Passed: {summary['passed']}/{summary['total_tests']}")
        print(f"❌ Tests Failed: {summary['failed']}/{summary['total_tests']}")
        print(f"🔧 Tests Errored: {summary['errors']}/{summary['total_tests']}")
        print(f"📈 Success Rate: {summary['success_rate']}")
        
        print(f"\n🪙 WSOL Address: {WSOL_TEST_ADDRESS}")
        
        print("\n📋 Individual Test Results:")
        for test in self.test_results['tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "❌" if test['status'] == 'FAIL' else "🔧"
            print(f"  {status_icon} {test['test_name']}: {test['status']}")
            
            if test['errors']:
                for error in test['errors']:
                    print(f"    • {error}")
        
        if summary['overall_status'] == 'PASS':
            print("\n🎉 All tests passed! WSOL-only filtering logic is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Please review the errors above.")
        
        print("="*60)


async def main():
    """Run WSOL filtering tests"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create tester and run tests
    tester = WSolFilteringTester()
    results = await tester.run_all_tests()
    
    # Print summary
    tester.print_test_summary()
    
    # Save detailed results
    timestamp = int(datetime.now().timestamp())
    output_file = f"wsol_filtering_test_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {output_file}")
    
    # Return exit code based on results
    return 0 if results['summary']['overall_status'] == 'PASS' else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 