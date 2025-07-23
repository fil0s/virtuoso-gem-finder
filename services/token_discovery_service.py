#!/usr/bin/env python3
"""
Token Discovery Service
Extracted from EarlyGemDetector to separate concerns
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Enhanced structured logging
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage

class TokenDiscoveryService:
    """
    Service responsible for discovering tokens from various platforms
    Extracted from EarlyGemDetector for better separation of concerns
    """
    
    def __init__(self, moralis_connector=None, sol_bonding_detector=None, config: Dict[str, Any] = None, debug_mode: bool = False):
        self.moralis_connector = moralis_connector
        self.sol_bonding_detector = sol_bonding_detector
        self.config = config or {}
        self.debug_mode = debug_mode or os.getenv('DISCOVERY_VERBOSE', '').lower() == 'true'
        
        # Traditional logger for backward compatibility
        self.logger = logging.getLogger('TokenDiscoveryService')
        
        # Enhanced structured logger
        self.enhanced_logger = create_enhanced_logger(
            "TokenDiscoveryService",
            log_level="DEBUG" if self.debug_mode else "INFO"
        )
        
        # Create service session context
        self.session_id = self.enhanced_logger.new_scan_context(
            strategy="multi-platform-token-discovery",
            timeframe="service_session",
        )
        
        # Discovery statistics with enhanced logging
        self.discovery_stats = {
            'moralis_calls': 0,
            'pump_fun_tokens': 0,
            'launchlab_tokens': 0,
            'birdeye_trending': 0,
            'total_discovered': 0
        }
        
        # Initialize service with structured logging
        self.enhanced_logger.info("Token Discovery Service initialized",
                                moralis_available=bool(self.moralis_connector),
                                sol_bonding_available=bool(self.sol_bonding_detector),
                                debug_mode=self.debug_mode,
                                session_id=self.session_id)
        
        if self.debug_mode:
            self.enhanced_logger.debug("Debug mode activated for token discovery",
                                     debug_features=["detailed_validation", "platform_tracking", "performance_monitoring"])
    
    def _is_valid_early_candidate(self, token: Dict[str, Any]) -> bool:
        """
        Validate if a token is a valid early-stage candidate
        Extracted from EarlyGemDetector._is_valid_early_candidate
        """
        required_fields = ['address', 'symbol']
        
        # Enhanced validation with structured logging
        with self.enhanced_logger.stage_context(DetectionStage.VALIDATION,
                                               operation="candidate_validation"):
            if self.debug_mode:
                self.enhanced_logger.debug("Validating token candidate",
                                         token_address=token.get('address', 'unknown'),
                                         token_symbol=token.get('symbol', 'unknown'))
            
            # Check required fields
            for field in required_fields:
                if not token.get(field):
                    self.enhanced_logger.debug("Token validation failed - missing field",
                                             missing_field=field,
                                             validation_result="rejected")
                    self.logger.debug(f"Token missing required field: {field}")
                    return False
        
            # Validate address format (basic Solana address validation)
            address = token['address']
            if not isinstance(address, str) or len(address) < 32:
                self.enhanced_logger.debug("Token validation failed - invalid address",
                                         address=address[:10] + "..." if len(address) > 10 else address,
                                         address_length=len(address) if isinstance(address, str) else 0,
                                         validation_result="rejected")
                self.logger.debug(f"Invalid address format: {address}")
                return False
        
            # Check for obvious scam indicators
            symbol = token.get('symbol', '').upper()
            scam_indicators = ['SCAM', 'FAKE', 'TEST', 'RUGPULL']
            if any(indicator in symbol for indicator in scam_indicators):
                self.enhanced_logger.debug("Token validation failed - scam indicator detected",
                                         symbol=symbol,
                                         scam_indicators_found=[ind for ind in scam_indicators if ind in symbol],
                                         validation_result="rejected")
                self.logger.debug(f"Token symbol contains scam indicator: {symbol}")
                return False
            
            # Validation passed
            self.enhanced_logger.debug("Token validation passed",
                                     token_address=address,
                                     token_symbol=symbol,
                                     validation_result="accepted")
            
            return True
    
    def _convert_moralis_bonding_to_candidate(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Moralis bonding curve token to standardized candidate format
        Extracted from EarlyGemDetector._convert_moralis_bonding_to_candidate
        """
        try:
            candidate = {
                'address': token.get('mint', token.get('address', '')),
                'symbol': token.get('symbol', 'Unknown'),
                'name': token.get('name', token.get('symbol', 'Unknown')),
                'platforms': ['pump.fun'],
                'discovery_method': 'moralis_bonding',
                'timestamp': datetime.now().isoformat(),
                'raw_data': token
            }
            
            # Add financial metrics if available
            if 'market_cap' in token:
                candidate['market_cap'] = token['market_cap']
            if 'liquidity' in token:
                candidate['liquidity'] = token['liquidity']
            if 'volume_24h' in token:
                candidate['volume_24h'] = token['volume_24h']
            
            return candidate
            
        except Exception as e:
            self.logger.error(f"Error converting Moralis bonding token: {e}")
            return None
    
    def _convert_moralis_graduated_to_candidate(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Moralis graduated token to standardized candidate format
        Extracted from EarlyGemDetector._convert_moralis_graduated_to_candidate
        """
        try:
            candidate = {
                'address': token.get('mint', token.get('address', '')),
                'symbol': token.get('symbol', 'Unknown'),
                'name': token.get('name', token.get('symbol', 'Unknown')),
                'platforms': ['pump.fun', 'raydium'],
                'discovery_method': 'moralis_graduated',
                'timestamp': datetime.now().isoformat(),
                'graduated': True,
                'raw_data': token
            }
            
            # Add graduation metrics
            if 'graduation_time' in token:
                candidate['graduation_time'] = token['graduation_time']
            if 'final_market_cap' in token:
                candidate['final_market_cap'] = token['final_market_cap']
            
            return candidate
            
        except Exception as e:
            self.logger.error(f"Error converting Moralis graduated token: {e}")
            return None
    
    async def fetch_moralis_bonding_tokens(self) -> List[Dict[str, Any]]:
        """
        Fetch bonding curve tokens from Moralis
        Extracted from EarlyGemDetector._fetch_moralis_bonding_tokens
        """
        if not self.moralis_connector:
            self.logger.warning("Moralis connector not available")
            return []
        
        try:
            self.logger.info("🔍 Fetching Moralis bonding curve tokens...")
            
            # Get fresh bonding curve tokens
            bonding_tokens = await self.moralis_connector.get_pump_fun_tokens(
                limit=50,
                sort_by='created_at',
                filter_graduated=False
            )
            
            candidates = []
            for token in bonding_tokens:
                candidate = self._convert_moralis_bonding_to_candidate(token)
                if candidate and self._is_valid_early_candidate(candidate):
                    candidates.append(candidate)
            
            self.discovery_stats['moralis_calls'] += 1
            self.discovery_stats['pump_fun_tokens'] += len(candidates)
            
            self.logger.info(f"✅ Found {len(candidates)} valid bonding curve candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error fetching Moralis bonding tokens: {e}")
            return []
    
    async def discover_pump_fun_stage0(self) -> List[Dict[str, Any]]:
        """
        Stage 0 Pump.fun discovery with SOL bonding curve integration
        Extracted from EarlyGemDetector._discover_pump_fun_stage0
        """
        if not self.sol_bonding_detector:
            self.logger.warning("SOL bonding detector not available")
            return []
        
        try:
            self.logger.info("🎯 Stage 0: SOL Bonding Curve Discovery")
            
            # Get SOL bonding curve candidates
            sol_candidates = await self.sol_bonding_detector.get_sol_bonding_candidates(limit=20)
            
            candidates = []
            for sol_token in sol_candidates:
                candidate = {
                    'address': sol_token.get('token_address', ''),
                    'symbol': sol_token.get('symbol', 'Unknown'),
                    'platforms': ['pump.fun', 'raydium'],
                    'discovery_method': 'sol_bonding_curve',
                    'timestamp': datetime.now().isoformat(),
                    'estimated_sol_raised': sol_token.get('estimated_sol_raised', 0),
                    'graduation_progress': sol_token.get('graduation_progress_pct', 0),
                    'raw_data': sol_token
                }
                
                if self._is_valid_early_candidate(candidate):
                    candidates.append(candidate)
            
            self.discovery_stats['pump_fun_tokens'] += len(candidates)
            
            self.logger.info(f"✅ Stage 0 discovered {len(candidates)} SOL bonding candidates")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Error in Stage 0 discovery: {e}")
            return []
    
    async def discover_early_tokens(self) -> List[Dict[str, Any]]:
        """
        Main token discovery method that orchestrates all discovery sources
        Extracted from EarlyGemDetector.discover_early_tokens
        """
        self.logger.info("🚀 Starting comprehensive early token discovery...")
        
        all_candidates = []
        
        # Discovery tasks
        discovery_tasks = []
        
        # Stage 0: SOL bonding curves
        discovery_tasks.append(self.discover_pump_fun_stage0())
        
        # Moralis bonding tokens
        discovery_tasks.append(self.fetch_moralis_bonding_tokens())
        
        # Execute discovery tasks concurrently
        try:
            discovery_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            for i, result in enumerate(discovery_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Discovery task {i} failed: {result}")
                    continue
                
                if isinstance(result, list):
                    all_candidates.extend(result)
                    
        except Exception as e:
            self.logger.error(f"Error during discovery: {e}")
        
        # Deduplicate candidates
        unique_candidates = self._deduplicate_candidates(all_candidates)
        
        self.discovery_stats['total_discovered'] = len(unique_candidates)
        
        self.logger.info(f"✅ Discovery complete: {len(unique_candidates)} unique candidates found")
        return unique_candidates
    
    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate candidates based on address
        Extracted from EarlyGemDetector._deduplicate_candidates
        """
        seen_addresses = set()
        unique_candidates = []
        
        for candidate in candidates:
            address = candidate.get('address', '')
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                unique_candidates.append(candidate)
        
        duplicates_removed = len(candidates) - len(unique_candidates)
        if duplicates_removed > 0:
            self.logger.info(f"🔄 Removed {duplicates_removed} duplicate candidates")
        
        return unique_candidates
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return {
            **self.discovery_stats,
            'last_discovery': datetime.now().isoformat()
        }
    
    def reset_stats(self):
        """Reset discovery statistics"""
        self.discovery_stats = {k: 0 for k in self.discovery_stats.keys()}