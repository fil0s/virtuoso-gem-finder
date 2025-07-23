#!/usr/bin/env python3
"""
Comprehensive Debug Analysis for Smart Money Whale Strategy

This script provides detailed debugging and analysis of the SmartMoneyWhaleStrategy,
tracking every step, API call, and decision to understand exactly how the strategy works.
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.strategies.smart_money_whale_strategy import SmartMoneyWhaleStrategy
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


class SmartMoneyWhaleDebugger:
    """Comprehensive debugger for SmartMoneyWhaleStrategy"""
    
    def __init__(self):
        # Setup enhanced logging
        self.logger_setup = LoggerSetup("SmartMoneyWhaleDebugger", log_level="DEBUG")
        self.logger = self.logger_setup.logger
        
        # Debug tracking
        self.debug_data = {
            "execution_steps": [],
            "api_calls": [],
            "filtering_decisions": [],
            "scoring_details": [],
            "final_analysis": {},
            "performance_metrics": {}
        }
        
        # API call tracking
        self.api_call_count = 0
        self.total_api_time = 0.0
        
    async def run_comprehensive_debug(self):
        """Run comprehensive debugging analysis of the strategy."""
        
        self.logger.info("🔍 COMPREHENSIVE SMART MONEY WHALE STRATEGY DEBUG")
        self.logger.info("=" * 80)
        
        try:
            # Initialize services with debugging
            birdeye_api = await self._initialize_services_with_debug()
            
            # Initialize strategy with debugging hooks
            strategy = await self._initialize_strategy_with_debug()
            
            # Execute strategy with comprehensive debugging
            scan_id = f"debug_smart_money_whale_{int(time.time())}"
            tokens = await self._execute_strategy_with_debug(strategy, birdeye_api, scan_id)
            
            # Analyze results comprehensively
            await self._analyze_results_comprehensively(tokens)
            
            # Generate debug report
            await self._generate_debug_report(scan_id)
            
        except Exception as e:
            self.logger.error(f"❌ Debug analysis failed: {e}")
            raise
    
    async def _initialize_services_with_debug(self) -> BirdeyeAPI:
        """Initialize services with debug tracking."""
        
        self.logger.info("\n🔧 STEP 1: SERVICE INITIALIZATION")
        self.logger.info("-" * 40)
        
        step_start = time.time()
        
        # Initialize core components
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        self.logger.info("✅ Cache manager initialized")
        self.logger.info("✅ Rate limiter initialized")
        
        # Get API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY not found in environment")
        
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        self.logger.info(f"✅ API key loaded: {masked_key}")
        
        # Initialize BirdeyeAPI with debugging
        birdeye_config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'request_timeout_seconds': 30,
            'use_rate_limiting': True
        }
        
        birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        # Hook into API calls for tracking
        original_make_request = birdeye_api._make_request
        
        async def debug_make_request(endpoint, **kwargs):
            call_start = time.time()
            self.api_call_count += 1
            
            self.logger.debug(f"🌐 API CALL #{self.api_call_count}: {endpoint}")
            self.logger.debug(f"   Parameters: {kwargs}")
            
            try:
                result = await original_make_request(endpoint, **kwargs)
                call_time = time.time() - call_start
                self.total_api_time += call_time
                
                self.logger.debug(f"   ✅ Success in {call_time:.2f}s")
                self.logger.debug(f"   Response size: {len(str(result)) if result else 0} chars")
                
                # Track API call
                self.debug_data["api_calls"].append({
                    "call_number": self.api_call_count,
                    "endpoint": endpoint,
                    "parameters": kwargs,
                    "execution_time": call_time,
                    "success": True,
                    "response_size": len(str(result)) if result else 0
                })
                
                return result
                
            except Exception as e:
                call_time = time.time() - call_start
                self.total_api_time += call_time
                
                self.logger.error(f"   ❌ Failed in {call_time:.2f}s: {e}")
                
                # Track failed API call
                self.debug_data["api_calls"].append({
                    "call_number": self.api_call_count,
                    "endpoint": endpoint,
                    "parameters": kwargs,
                    "execution_time": call_time,
                    "success": False,
                    "error": str(e)
                })
                
                raise
        
        birdeye_api._make_request = debug_make_request
        
        step_time = time.time() - step_start
        self.logger.info(f"✅ Service initialization completed in {step_time:.2f}s")
        
        self.debug_data["execution_steps"].append({
            "step": "service_initialization",
            "duration": step_time,
            "components": ["cache_manager", "rate_limiter", "birdeye_api"]
        })
        
        return birdeye_api
    
    async def _initialize_strategy_with_debug(self) -> SmartMoneyWhaleStrategy:
        """Initialize strategy with debug hooks."""
        
        self.logger.info("\n🐋 STEP 2: STRATEGY INITIALIZATION")
        self.logger.info("-" * 40)
        
        step_start = time.time()
        
        strategy = SmartMoneyWhaleStrategy(logger=self.logger)
        
        # Display strategy configuration
        self.logger.info("📋 Strategy Configuration:")
        self.logger.info(f"   Name: {strategy.name}")
        self.logger.info(f"   Description: {strategy.description}")
        
        self.logger.info("\n🎯 API Parameters:")
        for key, value in strategy.api_parameters.items():
            self.logger.info(f"   {key}: {value}")
        
        self.logger.info("\n🐋🧠 Whale & Smart Money Criteria:")
        for key, value in strategy.whale_smart_money_criteria.items():
            if isinstance(value, float) and 0 < value < 1:
                self.logger.info(f"   {key}: {value:.1%}")
            elif isinstance(value, (int, float)):
                self.logger.info(f"   {key}: {value:,}" if value >= 1000 else f"   {key}: {value}")
            else:
                self.logger.info(f"   {key}: {value}")
        
        self.logger.info("\n⚠️ Risk Management:")
        for key, value in strategy.risk_management.items():
            if isinstance(value, float) and 0 < value < 1:
                self.logger.info(f"   {key}: {value:.1%}")
            else:
                self.logger.info(f"   {key}: {value}")
        
        step_time = time.time() - step_start
        self.logger.info(f"\n✅ Strategy initialization completed in {step_time:.2f}s")
        
        self.debug_data["execution_steps"].append({
            "step": "strategy_initialization", 
            "duration": step_time,
            "configuration": {
                "api_parameters": strategy.api_parameters,
                "criteria": strategy.whale_smart_money_criteria,
                "risk_management": strategy.risk_management
            }
        })
        
        return strategy
    
    async def _execute_strategy_with_debug(self, strategy: SmartMoneyWhaleStrategy, 
                                         birdeye_api: BirdeyeAPI, scan_id: str) -> List[Dict[str, Any]]:
        """Execute strategy with comprehensive step-by-step debugging."""
        
        self.logger.info("\n🚀 STEP 3: STRATEGY EXECUTION")
        self.logger.info("-" * 40)
        
        execution_start = time.time()
        
        # Step 3.1: Initialize whale and smart money services
        self.logger.info("\n🔧 3.1: Initializing Whale & Smart Money Services")
        service_start = time.time()
        
        await strategy._initialize_whale_smart_money_services(birdeye_api)
        
        service_time = time.time() - service_start
        self.logger.info(f"✅ Services initialized in {service_time:.2f}s")
        self.logger.info(f"   🐋 Whale/Shark Tracker: {strategy._whale_shark_tracker is not None}")
        self.logger.info(f"   🧠 Smart Money Detector: {strategy._smart_money_detector is not None}")
        
        # Step 3.2: Get initial token universe
        self.logger.info("\n🌐 3.2: Getting Initial Token Universe")
        universe_start = time.time()
        api_calls_before = self.api_call_count
        
        initial_tokens = await strategy._get_initial_token_universe(birdeye_api)
        
        universe_time = time.time() - universe_start
        api_calls_used = self.api_call_count - api_calls_before
        
        self.logger.info(f"✅ Initial universe retrieved in {universe_time:.2f}s")
        self.logger.info(f"   📊 Tokens found: {len(initial_tokens)}")
        self.logger.info(f"   🌐 API calls used: {api_calls_used}")
        
        if initial_tokens:
            # Show sample tokens
            self.logger.info("\n📝 Sample tokens from initial universe:")
            for i, token in enumerate(initial_tokens[:5]):
                symbol = token.get('symbol', 'UNKNOWN')
                volume = token.get('volume24h', 0)
                liquidity = token.get('liquidity', 0)
                self.logger.info(f"   {i+1}. {symbol}: Vol=${volume:,.0f}, Liq=${liquidity:,.0f}")
        
        self.debug_data["filtering_decisions"].append({
            "step": "initial_universe",
            "tokens_before": "N/A",
            "tokens_after": len(initial_tokens),
            "duration": universe_time,
            "api_calls": api_calls_used,
            "sample_tokens": [t.get('symbol', 'UNKNOWN') for t in initial_tokens[:10]]
        })
        
        if not initial_tokens:
            self.logger.warning("❌ No tokens in initial universe - stopping execution")
            return []
        
        # Step 3.3: Filter by whale activity
        self.logger.info("\n🐋 3.3: Filtering by Whale Activity")
        whale_start = time.time()
        api_calls_before = self.api_call_count
        
        whale_tokens = await self._debug_whale_filtering(strategy, initial_tokens, birdeye_api, scan_id)
        
        whale_time = time.time() - whale_start
        api_calls_used = self.api_call_count - api_calls_before
        
        self.logger.info(f"✅ Whale filtering completed in {whale_time:.2f}s")
        self.logger.info(f"   🐋 Whale-active tokens: {len(whale_tokens)}")
        self.logger.info(f"   🌐 API calls used: {api_calls_used}")
        self.logger.info(f"   📉 Filtering ratio: {len(whale_tokens)/len(initial_tokens):.1%}")
        
        if not whale_tokens:
            self.logger.warning("❌ No tokens passed whale filtering")
            return []
        
        # Step 3.4: Filter by smart money activity
        self.logger.info("\n🧠 3.4: Filtering by Smart Money Activity")
        smart_start = time.time()
        api_calls_before = self.api_call_count
        
        smart_tokens = await self._debug_smart_money_filtering(strategy, whale_tokens, birdeye_api, scan_id)
        
        smart_time = time.time() - smart_start
        api_calls_used = self.api_call_count - api_calls_before
        
        self.logger.info(f"✅ Smart money filtering completed in {smart_time:.2f}s")
        self.logger.info(f"   🧠 Smart money tokens: {len(smart_tokens)}")
        self.logger.info(f"   🌐 API calls used: {api_calls_used}")
        self.logger.info(f"   📉 Filtering ratio: {len(smart_tokens)/len(whale_tokens):.1%}")
        
        if not smart_tokens:
            self.logger.warning("❌ No tokens passed smart money filtering")
            return []
        
        # Step 3.5: Apply confluence analysis
        self.logger.info("\n🤝 3.5: Applying Confluence Analysis")
        confluence_start = time.time()
        
        confluence_tokens = await self._debug_confluence_analysis(strategy, smart_tokens, scan_id)
        
        confluence_time = time.time() - confluence_start
        
        self.logger.info(f"✅ Confluence analysis completed in {confluence_time:.2f}s")
        self.logger.info(f"   🎯 High-confluence tokens: {len(confluence_tokens)}")
        self.logger.info(f"   📉 Filtering ratio: {len(confluence_tokens)/len(smart_tokens):.1%}")
        
        if not confluence_tokens:
            self.logger.warning("❌ No tokens passed confluence analysis")
            return []
        
        # Step 3.6: Final processing and ranking
        self.logger.info("\n🏆 3.6: Final Processing and Ranking")
        final_start = time.time()
        
        final_tokens = await self._debug_final_processing(strategy, confluence_tokens, birdeye_api, scan_id)
        
        final_time = time.time() - final_start
        
        self.logger.info(f"✅ Final processing completed in {final_time:.2f}s")
        self.logger.info(f"   🏆 Final tokens: {len(final_tokens)}")
        
        execution_time = time.time() - execution_start
        self.logger.info(f"\n🎉 STRATEGY EXECUTION COMPLETED in {execution_time:.2f}s")
        self.logger.info(f"   📊 Total tokens processed: {len(initial_tokens)} → {len(final_tokens)}")
        self.logger.info(f"   🌐 Total API calls: {self.api_call_count}")
        self.logger.info(f"   ⏱️ Total API time: {self.total_api_time:.2f}s")
        
        # Store execution summary
        self.debug_data["execution_steps"].append({
            "step": "strategy_execution",
            "duration": execution_time,
            "total_api_calls": self.api_call_count,
            "total_api_time": self.total_api_time,
            "tokens_processed": {
                "initial": len(initial_tokens),
                "whale_filtered": len(whale_tokens),
                "smart_money_filtered": len(smart_tokens),
                "confluence_filtered": len(confluence_tokens),
                "final": len(final_tokens)
            }
        })
        
        return final_tokens
    
    async def _debug_whale_filtering(self, strategy: SmartMoneyWhaleStrategy, 
                                   tokens: List[Dict[str, Any]], 
                                   birdeye_api: BirdeyeAPI, scan_id: str) -> List[Dict[str, Any]]:
        """Debug whale activity filtering in detail."""
        
        whale_tokens = []
        whale_details = []
        
        self.logger.info(f"🔍 Analyzing whale activity for {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens):
            token_start = time.time()
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('address', '')
            
            self.logger.debug(f"\n🐋 Token {i+1}/{len(tokens)}: {symbol} ({address[:8]}...)")
            
            try:
                # Analyze whale movements
                whale_analysis = await strategy._whale_shark_tracker.analyze_whale_shark_movements(
                    address, priority_level="normal"
                )
                
                # Check criteria
                meets_criteria = strategy._meets_whale_activity_criteria(whale_analysis, token)
                
                whales = whale_analysis.get("whales", [])
                whale_volume = whale_analysis.get("whale_analysis", {}).get("total_volume", 0)
                confidence = whale_analysis.get("confidence", 0.0)
                
                token_time = time.time() - token_start
                
                self.logger.debug(f"   🐋 Whales found: {len(whales)}")
                self.logger.debug(f"   💰 Whale volume: ${whale_volume:,.0f}")
                self.logger.debug(f"   📊 Confidence: {confidence:.2%}")
                self.logger.debug(f"   ✅ Meets criteria: {meets_criteria}")
                self.logger.debug(f"   ⏱️ Analysis time: {token_time:.2f}s")
                
                whale_details.append({
                    "symbol": symbol,
                    "address": address,
                    "whale_count": len(whales),
                    "whale_volume": whale_volume,
                    "confidence": confidence,
                    "meets_criteria": meets_criteria,
                    "analysis_time": token_time
                })
                
                if meets_criteria:
                    token["whale_analysis"] = whale_analysis
                    token["whale_activity_detected"] = True
                    whale_tokens.append(token)
                    
                    self.logger.info(f"✅ {symbol}: {len(whales)} whales, ${whale_volume:,.0f} volume")
                else:
                    reasons = []
                    if len(whales) < strategy.whale_smart_money_criteria["min_whale_count"]:
                        reasons.append(f"whale count ({len(whales)} < {strategy.whale_smart_money_criteria['min_whale_count']})")
                    if whale_volume < strategy.whale_smart_money_criteria["min_whale_volume"]:
                        reasons.append(f"volume (${whale_volume:,.0f} < ${strategy.whale_smart_money_criteria['min_whale_volume']:,.0f})")
                    if confidence < strategy.whale_smart_money_criteria["whale_confidence_threshold"]:
                        reasons.append(f"confidence ({confidence:.1%} < {strategy.whale_smart_money_criteria['whale_confidence_threshold']:.1%})")
                    
                    self.logger.debug(f"❌ {symbol}: Failed - {', '.join(reasons)}")
                
            except Exception as e:
                self.logger.warning(f"❌ {symbol}: Error analyzing whale activity - {e}")
                whale_details.append({
                    "symbol": symbol,
                    "address": address,
                    "error": str(e),
                    "meets_criteria": False
                })
        
        # Summary statistics
        total_whales = sum(len(d.get("whales", [])) if "whales" in str(d) else d.get("whale_count", 0) for d in whale_details)
        avg_confidence = sum(d.get("confidence", 0) for d in whale_details) / len(whale_details) if whale_details else 0
        
        self.logger.info(f"\n📊 Whale Filtering Summary:")
        self.logger.info(f"   🐋 Total whales detected: {total_whales}")
        self.logger.info(f"   📊 Average confidence: {avg_confidence:.1%}")
        self.logger.info(f"   ✅ Tokens passing filter: {len(whale_tokens)}/{len(tokens)} ({len(whale_tokens)/len(tokens):.1%})")
        
        self.debug_data["filtering_decisions"].append({
            "step": "whale_filtering",
            "tokens_before": len(tokens),
            "tokens_after": len(whale_tokens),
            "total_whales_detected": total_whales,
            "average_confidence": avg_confidence,
            "whale_details": whale_details
        })
        
        return whale_tokens
    
    async def _debug_smart_money_filtering(self, strategy: SmartMoneyWhaleStrategy,
                                         tokens: List[Dict[str, Any]],
                                         birdeye_api: BirdeyeAPI, scan_id: str) -> List[Dict[str, Any]]:
        """Debug smart money filtering in detail."""
        
        smart_money_tokens = []
        smart_money_details = []
        
        self.logger.info(f"🔍 Analyzing smart money activity for {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens):
            token_start = time.time()
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('address', '')
            
            self.logger.debug(f"\n🧠 Token {i+1}/{len(tokens)}: {symbol} ({address[:8]}...)")
            
            try:
                # Analyze smart money (reuses whale data - no additional API calls!)
                smart_money_analysis = await strategy._smart_money_detector.analyze_smart_money(
                    address, priority_level="normal"
                )
                
                # Check criteria
                meets_criteria = strategy._meets_smart_money_criteria(smart_money_analysis, token)
                
                skill_metrics = smart_money_analysis.get("skill_metrics", {})
                skilled_count = skill_metrics.get("skilled_count", 0)
                avg_skill_score = skill_metrics.get("average_skill_score", 0.0)
                skill_quality = smart_money_analysis.get("smart_money_insights", {}).get("skill_quality", "unknown")
                
                token_time = time.time() - token_start
                
                self.logger.debug(f"   🧠 Skilled traders: {skilled_count}")
                self.logger.debug(f"   🎯 Avg skill score: {avg_skill_score:.2f}")
                self.logger.debug(f"   🏆 Skill quality: {skill_quality}")
                self.logger.debug(f"   ✅ Meets criteria: {meets_criteria}")
                self.logger.debug(f"   ⏱️ Analysis time: {token_time:.2f}s")
                
                smart_money_details.append({
                    "symbol": symbol,
                    "address": address,
                    "skilled_count": skilled_count,
                    "avg_skill_score": avg_skill_score,
                    "skill_quality": skill_quality,
                    "meets_criteria": meets_criteria,
                    "analysis_time": token_time
                })
                
                if meets_criteria:
                    token["smart_money_analysis"] = smart_money_analysis
                    token["smart_money_detected"] = True
                    smart_money_tokens.append(token)
                    
                    self.logger.info(f"✅ {symbol}: {skilled_count} skilled traders, {avg_skill_score:.2f} avg score")
                else:
                    reasons = []
                    if skilled_count < strategy.whale_smart_money_criteria["min_smart_traders"]:
                        reasons.append(f"trader count ({skilled_count} < {strategy.whale_smart_money_criteria['min_smart_traders']})")
                    if avg_skill_score < strategy.whale_smart_money_criteria["smart_money_skill_threshold"]:
                        reasons.append(f"skill score ({avg_skill_score:.2f} < {strategy.whale_smart_money_criteria['smart_money_skill_threshold']:.2f})")
                    if skill_quality == "low":
                        reasons.append("low skill quality")
                    
                    self.logger.debug(f"❌ {symbol}: Failed - {', '.join(reasons)}")
                
            except Exception as e:
                self.logger.warning(f"❌ {symbol}: Error analyzing smart money - {e}")
                smart_money_details.append({
                    "symbol": symbol,
                    "address": address,
                    "error": str(e),
                    "meets_criteria": False
                })
        
        # Summary statistics
        total_skilled_traders = sum(d.get("skilled_count", 0) for d in smart_money_details)
        avg_skill_score = sum(d.get("avg_skill_score", 0) for d in smart_money_details) / len(smart_money_details) if smart_money_details else 0
        
        self.logger.info(f"\n📊 Smart Money Filtering Summary:")
        self.logger.info(f"   🧠 Total skilled traders: {total_skilled_traders}")
        self.logger.info(f"   🎯 Average skill score: {avg_skill_score:.3f}")
        self.logger.info(f"   ✅ Tokens passing filter: {len(smart_money_tokens)}/{len(tokens)} ({len(smart_money_tokens)/len(tokens):.1%})")
        
        self.debug_data["filtering_decisions"].append({
            "step": "smart_money_filtering",
            "tokens_before": len(tokens),
            "tokens_after": len(smart_money_tokens),
            "total_skilled_traders": total_skilled_traders,
            "average_skill_score": avg_skill_score,
            "smart_money_details": smart_money_details
        })
        
        return smart_money_tokens
    
    async def _debug_confluence_analysis(self, strategy: SmartMoneyWhaleStrategy,
                                       tokens: List[Dict[str, Any]], scan_id: str) -> List[Dict[str, Any]]:
        """Debug confluence analysis in detail."""
        
        confluence_tokens = []
        confluence_details = []
        
        self.logger.info(f"🔍 Analyzing confluence for {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens):
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('address', '')
            
            self.logger.debug(f"\n🤝 Token {i+1}/{len(tokens)}: {symbol} ({address[:8]}...)")
            
            try:
                whale_analysis = token.get("whale_analysis", {})
                smart_money_analysis = token.get("smart_money_analysis", {})
                
                # Calculate confluence score
                confluence_score = strategy._calculate_confluence_score(whale_analysis, smart_money_analysis)
                token["confluence_score"] = confluence_score
                
                # Check confluence criteria
                meets_criteria = confluence_score >= strategy.whale_smart_money_criteria["min_confluence_score"]
                
                self.logger.debug(f"   🤝 Confluence score: {confluence_score:.3f}")
                self.logger.debug(f"   🎯 Required score: {strategy.whale_smart_money_criteria['min_confluence_score']:.3f}")
                self.logger.debug(f"   ✅ Meets criteria: {meets_criteria}")
                
                if meets_criteria:
                    token["high_confluence"] = True
                    confluence_bonus = confluence_score * strategy.whale_smart_money_criteria["confluence_bonus_multiplier"]
                    token["confluence_bonus"] = confluence_bonus
                    confluence_tokens.append(token)
                    
                    self.logger.info(f"✅ {symbol}: {confluence_score:.3f} confluence, {confluence_bonus:.2f}x bonus")
                else:
                    self.logger.debug(f"❌ {symbol}: {confluence_score:.3f} < {strategy.whale_smart_money_criteria['min_confluence_score']:.3f}")
                
                confluence_details.append({
                    "symbol": symbol,
                    "address": address,
                    "confluence_score": confluence_score,
                    "meets_criteria": meets_criteria,
                    "confluence_bonus": confluence_bonus if meets_criteria else 1.0
                })
                
            except Exception as e:
                self.logger.warning(f"❌ {symbol}: Error in confluence analysis - {e}")
                confluence_details.append({
                    "symbol": symbol,
                    "address": address,
                    "error": str(e),
                    "meets_criteria": False
                })
        
        # Summary statistics
        avg_confluence = sum(d.get("confluence_score", 0) for d in confluence_details) / len(confluence_details) if confluence_details else 0
        max_confluence = max((d.get("confluence_score", 0) for d in confluence_details), default=0)
        
        self.logger.info(f"\n📊 Confluence Analysis Summary:")
        self.logger.info(f"   🤝 Average confluence: {avg_confluence:.3f}")
        self.logger.info(f"   🎯 Maximum confluence: {max_confluence:.3f}")
        self.logger.info(f"   ✅ High-confluence tokens: {len(confluence_tokens)}/{len(tokens)} ({len(confluence_tokens)/len(tokens):.1%})")
        
        self.debug_data["filtering_decisions"].append({
            "step": "confluence_analysis",
            "tokens_before": len(tokens),
            "tokens_after": len(confluence_tokens),
            "average_confluence": avg_confluence,
            "max_confluence": max_confluence,
            "confluence_details": confluence_details
        })
        
        return confluence_tokens
    
    async def _debug_final_processing(self, strategy: SmartMoneyWhaleStrategy,
                                    tokens: List[Dict[str, Any]],
                                    birdeye_api: BirdeyeAPI, scan_id: str) -> List[Dict[str, Any]]:
        """Debug final processing and ranking in detail."""
        
        self.logger.info(f"🔍 Final processing for {len(tokens)} tokens...")
        
        # Process with base strategy (enrichment)
        processed_tokens = await strategy.process_results(tokens, birdeye_api, scan_id)
        
        # Rank by combined signals
        final_tokens = await strategy._rank_by_whale_smart_money_signals(processed_tokens)
        
        # Detailed scoring analysis
        scoring_details = []
        
        for i, token in enumerate(final_tokens):
            symbol = token.get('symbol', 'UNKNOWN')
            
            # Extract scoring components
            combined_score = token.get("combined_whale_smart_money_score", 0)
            whale_score = strategy._get_whale_score(token)
            smart_money_score = strategy._get_smart_money_score(token)
            confluence_score = token.get("confluence_score", 0)
            confluence_bonus = token.get("confluence_bonus", 1.0)
            
            # Extract signal strengths
            analysis = token.get("strategy_analysis", {})
            whale_strength = analysis.get("whale_signal_strength", "unknown")
            smart_money_strength = analysis.get("smart_money_signal_strength", "unknown")
            confluence_level = analysis.get("confluence_level", "unknown")
            conviction_level = analysis.get("conviction_level", "unknown")
            risk_level = analysis.get("risk_assessment", "unknown")
            
            self.logger.debug(f"\n🏆 Token {i+1}: {symbol}")
            self.logger.debug(f"   🎯 Combined Score: {combined_score:.1f}")
            self.logger.debug(f"   🐋 Whale Score: {whale_score:.1f} ({whale_strength})")
            self.logger.debug(f"   🧠 Smart Money Score: {smart_money_score:.1f} ({smart_money_strength})")
            self.logger.debug(f"   🤝 Confluence: {confluence_score:.3f} ({confluence_level})")
            self.logger.debug(f"   📈 Confluence Bonus: {confluence_bonus:.2f}x")
            self.logger.debug(f"   💪 Conviction: {conviction_level}")
            self.logger.debug(f"   ⚠️ Risk: {risk_level}")
            
            scoring_details.append({
                "rank": i + 1,
                "symbol": symbol,
                "combined_score": combined_score,
                "whale_score": whale_score,
                "smart_money_score": smart_money_score,
                "confluence_score": confluence_score,
                "confluence_bonus": confluence_bonus,
                "whale_strength": whale_strength,
                "smart_money_strength": smart_money_strength,
                "confluence_level": confluence_level,
                "conviction_level": conviction_level,
                "risk_level": risk_level
            })
        
        self.debug_data["scoring_details"] = scoring_details
        
        return final_tokens
    
    async def _analyze_results_comprehensively(self, tokens: List[Dict[str, Any]]):
        """Comprehensive analysis of final results."""
        
        self.logger.info("\n📊 COMPREHENSIVE RESULTS ANALYSIS")
        self.logger.info("=" * 60)
        
        if not tokens:
            self.logger.warning("❌ No tokens to analyze")
            return
        
        # Overall statistics
        total_whales = sum(len(t.get('whale_analysis', {}).get('whales', [])) for t in tokens)
        total_smart_traders = sum(t.get('smart_money_analysis', {}).get('skill_metrics', {}).get('skilled_count', 0) for t in tokens)
        avg_confluence = sum(t.get('confluence_score', 0) for t in tokens) / len(tokens)
        avg_combined_score = sum(t.get('combined_whale_smart_money_score', 0) for t in tokens) / len(tokens)
        
        self.logger.info(f"📈 PORTFOLIO STATISTICS:")
        self.logger.info(f"   🏆 Total tokens: {len(tokens)}")
        self.logger.info(f"   🐋 Total whales: {total_whales}")
        self.logger.info(f"   🧠 Total smart traders: {total_smart_traders}")
        self.logger.info(f"   🤝 Average confluence: {avg_confluence:.3f}")
        self.logger.info(f"   🎯 Average combined score: {avg_combined_score:.1f}")
        
        # Detailed token analysis
        self.logger.info(f"\n🏆 TOP DISCOVERED TOKENS:")
        self.logger.info("-" * 80)
        
        for i, token in enumerate(tokens[:10], 1):
            symbol = token.get('symbol', 'UNKNOWN')
            address = token.get('address', '')[:8] + '...'
            
            # Strategy metrics
            combined_score = token.get('combined_whale_smart_money_score', 0)
            confluence_score = token.get('confluence_score', 0)
            whale_count = len(token.get('whale_analysis', {}).get('whales', []))
            smart_traders = token.get('smart_money_analysis', {}).get('skill_metrics', {}).get('skilled_count', 0)
            
            # Market metrics
            price = token.get('priceUsd', 0)
            volume_24h = token.get('volume24h', 0)
            liquidity = token.get('liquidity', 0)
            market_cap = token.get('marketCap', 0)
            holders = token.get('holder', 0)
            
            # Strategy analysis
            analysis = token.get('strategy_analysis', {})
            conviction = analysis.get('conviction_level', 'unknown')
            risk = analysis.get('risk_assessment', 'unknown')
            
            self.logger.info(f"\n#{i} {symbol} ({address})")
            self.logger.info(f"   🎯 Score: {combined_score:.1f} | 🤝 Confluence: {confluence_score:.3f}")
            self.logger.info(f"   🐋 Whales: {whale_count} | 🧠 Smart Traders: {smart_traders}")
            self.logger.info(f"   💪 Conviction: {conviction} | ⚠️ Risk: {risk}")
            self.logger.info(f"   💰 Price: ${price:.6f} | 📊 Vol: ${volume_24h:,.0f}")
            self.logger.info(f"   💧 Liquidity: ${liquidity:,.0f} | 🏦 MCap: ${market_cap:,.0f}")
            self.logger.info(f"   👥 Holders: {holders:,}")
        
        # Risk distribution analysis
        risk_distribution = {}
        conviction_distribution = {}
        
        for token in tokens:
            analysis = token.get('strategy_analysis', {})
            risk = analysis.get('risk_assessment', 'unknown')
            conviction = analysis.get('conviction_level', 'unknown')
            
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            conviction_distribution[conviction] = conviction_distribution.get(conviction, 0) + 1
        
        self.logger.info(f"\n📊 RISK DISTRIBUTION:")
        for risk, count in risk_distribution.items():
            self.logger.info(f"   {risk}: {count} tokens ({count/len(tokens):.1%})")
        
        self.logger.info(f"\n💪 CONVICTION DISTRIBUTION:")
        for conviction, count in conviction_distribution.items():
            self.logger.info(f"   {conviction}: {count} tokens ({count/len(tokens):.1%})")
        
        # Store final analysis
        self.debug_data["final_analysis"] = {
            "total_tokens": len(tokens),
            "total_whales": total_whales,
            "total_smart_traders": total_smart_traders,
            "average_confluence": avg_confluence,
            "average_combined_score": avg_combined_score,
            "risk_distribution": risk_distribution,
            "conviction_distribution": conviction_distribution,
            "top_tokens": tokens[:5]
        }
    
    async def _generate_debug_report(self, scan_id: str):
        """Generate comprehensive debug report."""
        
        self.logger.info("\n📝 GENERATING DEBUG REPORT")
        self.logger.info("=" * 40)
        
        # Performance metrics
        total_execution_time = sum(step.get("duration", 0) for step in self.debug_data["execution_steps"])
        
        self.debug_data["performance_metrics"] = {
            "total_execution_time": total_execution_time,
            "total_api_calls": self.api_call_count,
            "total_api_time": self.total_api_time,
            "api_efficiency": (self.total_api_time / total_execution_time) if total_execution_time > 0 else 0,
            "avg_api_call_time": self.total_api_time / self.api_call_count if self.api_call_count > 0 else 0
        }
        
        # Save comprehensive debug report
        report_file = Path("scripts/results") / f"smart_money_whale_debug_{scan_id}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.debug_data, f, indent=2, default=str)
            
            self.logger.info(f"✅ Debug report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save debug report: {e}")
        
        # Summary
        self.logger.info(f"\n🎉 DEBUG ANALYSIS COMPLETE")
        self.logger.info(f"   ⏱️ Total time: {total_execution_time:.2f}s")
        self.logger.info(f"   🌐 API calls: {self.api_call_count}")
        self.logger.info(f"   💾 Report saved: {report_file.name}")


async def main():
    """Main execution function."""
    
    debugger = SmartMoneyWhaleDebugger()
    birdeye_api = None
    
    try:
        await debugger.run_comprehensive_debug()
        
    except KeyboardInterrupt:
        debugger.logger.info("\n🛑 Debug analysis interrupted by user")
        
    except Exception as e:
        debugger.logger.error(f"❌ Debug analysis failed: {e}")
        raise
        
    finally:
        # Ensure proper cleanup of any remaining sessions
        if hasattr(debugger, 'birdeye_api') and debugger.birdeye_api:
            try:
                await debugger.birdeye_api.close()
                debugger.logger.info("✅ API connections properly closed")
            except Exception as e:
                debugger.logger.warning(f"⚠️  Warning during API cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())