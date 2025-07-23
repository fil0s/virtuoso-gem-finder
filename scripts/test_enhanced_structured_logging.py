#!/usr/bin/env python3
"""
Test Enhanced Structured Logging System
Comprehensive testing and demonstration of the new logging capabilities
"""

import sys
import os
import time
import asyncio
import json
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_structured_logger import (
    create_enhanced_logger, 
    DetectionStage, 
    APICallType
)


class EnhancedLoggingTester:
    """Test the enhanced structured logging system"""
    
    def __init__(self):
        self.logger = create_enhanced_logger(
            "LoggingTester",
            log_level="DEBUG",
            enable_performance_tracking=True,
            enable_api_tracking=True,
            enable_context_tracking=True
        )
        
    async def run_comprehensive_test(self):
        """Run comprehensive test of all logging features"""
        print("🧪 TESTING ENHANCED STRUCTURED LOGGING SYSTEM")
        print("=" * 60)
        
        # Start a new scan context
        scan_id = self.logger.new_scan_context(
            strategy="comprehensive_logging_test",
            timeframe="test_scenario"
        )
        
        print(f"📊 Scan ID: {scan_id}")
        print("📋 Watch the structured JSON output below:")
        print("-" * 60)
        
        try:
            # Test stage-based logging
            await self._test_stage_contexts()
            
            # Test API call tracking
            await self._test_api_call_tracking()
            
            # Test token processing logging
            await self._test_token_processing()
            
            # Test validation logging
            await self._test_validation_logging()
            
            # Test cache operations
            await self._test_cache_operations()
            
            # Test error handling
            await self._test_error_handling()
            
            # Test alert logging
            await self._test_alert_logging()
            
            # Generate comprehensive performance summary
            self.logger.log_performance_summary(
                test_scenario="comprehensive_test_complete",
                total_test_duration="calculated_automatically"
            )
            
            print("-" * 60)
            print("✅ All tests completed successfully!")
            print("📊 Check the JSON logs above for structured output")
            
        except Exception as e:
            self.logger.error("Test failed", 
                            error=str(e),
                            test_type="comprehensive_test")
            raise
    
    async def _test_stage_contexts(self):
        """Test stage-based context tracking"""
        print("\n🔍 Testing Stage Contexts...")
        
        # Simulate the 4-stage gem detection process
        stages = [
            (DetectionStage.STAGE_0_DISCOVERY, {"tokens_to_discover": 1000}),
            (DetectionStage.STAGE_1_BASIC_FILTER, {"filter_criteria": "basic_validation"}),
            (DetectionStage.STAGE_2_BATCH_ENRICHMENT, {"batch_size": 50}),
            (DetectionStage.STAGE_3_DETAILED_ANALYSIS, {"analysis_depth": "deep"}),
            (DetectionStage.STAGE_4_FINAL_SCORING, {"scoring_algorithm": "enhanced_gem_scoring"})
        ]
        
        for stage, context in stages:
            with self.logger.stage_context(stage, **context):
                # Simulate stage processing time
                processing_time = 0.1 + (hash(stage.value) % 5) * 0.1
                await asyncio.sleep(processing_time)
                
                self.logger.info(f"Processing {stage.value}",
                               stage_processing_time=processing_time,
                               stage_status="active")
    
    async def _test_api_call_tracking(self):
        """Test API call context tracking"""
        print("\n📡 Testing API Call Tracking...")
        
        # Simulate different types of API calls
        api_calls = [
            (APICallType.TOKEN_DISCOVERY, "birdeye/defi/tokenlist", 0, {"source": "birdeye"}),
            (APICallType.BATCH_METADATA, "birdeye/defi/multi_metadata", 25, {"batch_size": 25}),
            (APICallType.BATCH_PRICE, "birdeye/defi/multi_price", 25, {"price_type": "current"}),
            (APICallType.INDIVIDUAL_METADATA, "birdeye/defi/metadata", 1, {"detailed": True}),
            (APICallType.INDIVIDUAL_PRICE, "birdeye/defi/price", 1, {"include_history": False}),
            (APICallType.VALIDATION, "internal/token_validator", 100, {"validation_type": "comprehensive"})
        ]
        
        for call_type, endpoint, token_count, extra_context in api_calls:
            with self.logger.api_call_context(
                call_type, 
                endpoint, 
                token_count=token_count if token_count > 0 else None,
                **extra_context
            ):
                # Simulate API call duration
                call_duration = 0.05 + (hash(endpoint) % 10) * 0.02
                await asyncio.sleep(call_duration)
                
                self.logger.debug(f"API call to {endpoint} completed",
                                api_response_size=1024 + (hash(endpoint) % 5000),
                                api_status_code=200)
    
    async def _test_token_processing(self):
        """Test token processing statistics logging"""
        print("\n🪙 Testing Token Processing...")
        
        # Simulate token processing through different stages
        processing_scenarios = [
            {
                "stage": DetectionStage.STAGE_0_DISCOVERY,
                "tokens_input": 1000,
                "tokens_output": 800,
                "tokens_filtered": 200,
                "filter_reasons": {"invalid_format": 100, "excluded_tokens": 50, "duplicates": 50}
            },
            {
                "stage": DetectionStage.STAGE_1_BASIC_FILTER,
                "tokens_input": 800,
                "tokens_output": 400,
                "tokens_filtered": 400,
                "filter_reasons": {"low_volume": 200, "new_token": 100, "insufficient_liquidity": 100}
            },
            {
                "stage": DetectionStage.STAGE_2_BATCH_ENRICHMENT,
                "tokens_input": 400,
                "tokens_output": 350,
                "tokens_filtered": 50,
                "filter_reasons": {"api_error": 30, "insufficient_data": 20}
            },
            {
                "stage": DetectionStage.STAGE_3_DETAILED_ANALYSIS,
                "tokens_input": 350,
                "tokens_output": 100,
                "tokens_filtered": 250,
                "filter_reasons": {"low_confidence": 150, "risk_too_high": 100}
            },
            {
                "stage": DetectionStage.STAGE_4_FINAL_SCORING,
                "tokens_input": 100,
                "tokens_output": 15,
                "tokens_filtered": 85,
                "filter_reasons": {"below_threshold": 75, "already_alerted": 10}
            }
        ]
        
        for scenario in processing_scenarios:
            self.logger.log_token_processing(
                stage=scenario["stage"],
                tokens_input=scenario["tokens_input"],
                tokens_output=scenario["tokens_output"],
                tokens_filtered=scenario["tokens_filtered"],
                filter_reasons=scenario["filter_reasons"],
                processing_efficiency=round((scenario["tokens_output"] / scenario["tokens_input"]) * 100, 2)
            )
    
    async def _test_validation_logging(self):
        """Test validation statistics logging"""
        print("\n✅ Testing Validation Logging...")
        
        # Simulate validation report
        validation_report = {
            "total_input": 1000,
            "valid_count": 750,
            "filtered_count": 250,
            "invalid_format": 100,
            "excluded_tokens": 75,
            "duplicates_removed": 75,
            "validation_time_ms": 45.2,
            "filters_applied": ["format_validation", "exclusion_filtering", "duplicate_removal"],
            "validation_success_rate": 75.0,
            "api_calls_saved": 250
        }
        
        self.logger.log_validation_stats(
            validation_report,
            validator_version="enhanced_v1.0",
            validation_strategy="comprehensive"
        )
    
    async def _test_cache_operations(self):
        """Test cache operation logging"""
        print("\n💾 Testing Cache Operations...")
        
        # Simulate various cache operations
        cache_operations = [
            ("get", "token_metadata_So111...", True, 300),
            ("get", "token_price_DezXAZ...", False, None),
            ("set", "token_metadata_DezXAZ...", False, 600),
            ("get", "validation_result_EPjFW...", True, 120),
            ("delete", "expired_token_data", False, None),
            ("get", "batch_result_hash_abc123", True, 180)
        ]
        
        for operation, cache_key, hit, ttl in cache_operations:
            self.logger.log_cache_operation(
                operation=operation,
                cache_key=cache_key,
                hit=hit,
                ttl=ttl,
                cache_size_mb=12.4 + (hash(cache_key) % 10)
            )
    
    async def _test_error_handling(self):
        """Test error handling and logging"""
        print("\n⚠️  Testing Error Handling...")
        
        # Test different types of errors
        try:
            with self.logger.stage_context(DetectionStage.ERROR_HANDLING,
                                         error_test=True):
                # Simulate a recoverable error
                self.logger.warning("Simulated rate limit warning",
                                  rate_limit_remaining=5,
                                  retry_after_seconds=2,
                                  error_type="rate_limit_warning")
                
                # Simulate an API error
                raise Exception("Simulated API connection error")
                
        except Exception as e:
            self.logger.error("Handled expected test error",
                            error_message=str(e),
                            error_type="simulated_test_error",
                            recovery_action="logged_and_continuing")
    
    async def _test_alert_logging(self):
        """Test alert generation logging"""
        print("\n🚨 Testing Alert Logging...")
        
        # Simulate gem detection alerts
        test_alerts = [
            {
                "alert_type": "high_confidence_gem",
                "token_address": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
                "confidence_score": 0.89,
                "alert_data": {
                    "price_change_24h": 156.8,
                    "volume_change_24h": 245.2,
                    "market_cap": 1250000,
                    "liquidity_usd": 185000,
                    "holder_count": 1250,
                    "age_hours": 12.5,
                    "risk_score": 0.15,
                    "gem_indicators": ["high_volume", "growing_holders", "strong_liquidity"]
                }
            },
            {
                "alert_type": "medium_confidence_gem",
                "token_address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "confidence_score": 0.72,
                "alert_data": {
                    "price_change_24h": 45.2,
                    "volume_change_24h": 78.5,
                    "market_cap": 450000,
                    "liquidity_usd": 65000,
                    "holder_count": 890,
                    "age_hours": 6.2,
                    "risk_score": 0.25,
                    "gem_indicators": ["moderate_volume", "new_token"]
                }
            }
        ]
        
        for alert in test_alerts:
            self.logger.log_alert(
                alert_type=alert["alert_type"],
                token_address=alert["token_address"],
                confidence_score=alert["confidence_score"],
                alert_data=alert["alert_data"],
                telegram_sent=True,
                alert_channel="gem_alerts"
            )
    
    def demonstrate_context_tracking(self):
        """Demonstrate context tracking capabilities"""
        print("\n🔍 Testing Context Tracking...")
        
        # Show current context
        context = self.logger.get_current_context()
        
        self.logger.info("Context tracking demonstration",
                        current_context_keys=list(context.keys()),
                        context_stack_depth=len(self.logger.context_stack),
                        **context)


async def main():
    """Main test function"""
    print("🚀 Enhanced Structured Logging Test Suite")
    print("=" * 60)
    print("This test demonstrates all features of the enhanced logging system.")
    print("Each operation will output structured JSON logs with comprehensive context.")
    print()
    
    tester = EnhancedLoggingTester()
    
    try:
        await tester.run_comprehensive_test()
        
        # Demonstrate context tracking
        tester.demonstrate_context_tracking()
        
        print("\n" + "=" * 60)
        print("🎉 ENHANCED LOGGING TEST COMPLETE!")
        print("=" * 60)
        print()
        print("✅ ALL FEATURES TESTED:")
        print("   📊 Stage-based context tracking")
        print("   📡 API call monitoring and timing")
        print("   🪙 Token processing statistics")
        print("   ✅ Validation logging")
        print("   💾 Cache operation tracking")
        print("   ⚠️  Error handling and recovery")
        print("   🚨 Alert generation logging")
        print("   🔍 Contextual debugging")
        print("   📈 Performance metrics collection")
        print()
        print("🚀 Ready for integration with your gem detection system!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))