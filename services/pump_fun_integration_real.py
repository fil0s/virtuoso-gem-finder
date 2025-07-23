#!/usr/bin/env python3
"""
🔥 REAL PUMP.FUN INTEGRATION - WORKING VERSION
Uses actual API calls to fetch live pump.fun tokens
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

class RealPumpFunIntegration:
    """Real pump.fun integration that fetches live tokens via API"""
    
    def __init__(self):
        self.logger = logging.getLogger('RealPumpFunIntegration')
        
        # Initialize real API client
        from services.pump_fun_api_client import PumpFunAPIClient
        self.api_client = PumpFunAPIClient()
        
        # Performance tracking
        self.tokens_fetched = 0
        self.api_calls_made = 0
        self.ultra_early_detected = 0
        
        # Cache for deduplication
        self.recent_tokens = set()
        self.last_fetch_time = 0
        
        self.logger.info("🔥 REAL Pump.fun integration initialized with live API client")
    
    async def get_stage0_priority_queue(self) -> List[Dict]:
        """🚀 WORKING: Get real Stage 0 tokens from live pump.fun API"""
        try:
            self.logger.info("🔍 Fetching LIVE Stage 0 tokens from pump.fun API...")
            
            # Fetch latest tokens from real API
            latest_tokens = await self.api_client.get_latest_tokens(limit=30)
            
            if not latest_tokens:
                self.logger.warning("⚠️ No tokens returned from pump.fun API")
                return []
            
            # Filter for Stage 0 (ultra-early) tokens
            stage0_tokens = []
            
            for token in latest_tokens:
                try:
                    # Stage 0 criteria: Very recent launches (< 2 hours)
                    age_minutes = token.get('estimated_age_minutes', 9999)
                    market_cap = token.get('market_cap', 0)
                    
                    # Stage 0 filters
                    if (age_minutes <= 120 and  # Less than 2 hours old
                        market_cap > 0 and       # Has some market cap
                        market_cap < 100000):    # Not too large yet
                        
                        # Enhanced Stage 0 token data
                        enhanced_token = {
                            **token,
                            'stage0_priority': self._calculate_stage0_priority(token),
                            'recommended_action': 'IMMEDIATE_ANALYSIS',
                            'ultra_early_bonus': age_minutes <= 10,
                            'stage0_score': self._calculate_stage0_score(token),
                            'bonding_curve_velocity': market_cap / max(age_minutes, 1),  # MC per minute
                            'graduation_eta_hours': self._estimate_graduation_time(token)
                        }
                        
                        stage0_tokens.append(enhanced_token)
                        
                        # Track ultra-early detections
                        if age_minutes <= 5:
                            self.ultra_early_detected += 1
                            self.logger.info(f"🚨 ULTRA-EARLY STAGE 0: {token['symbol']} - {age_minutes:.1f} min old!")
                        
                except Exception as e:
                    self.logger.debug(f"Error processing token: {e}")
                    continue
            
            # Sort by priority (newest and highest velocity first)
            stage0_tokens.sort(key=lambda x: (
                -x.get('stage0_priority', 0),
                -x.get('bonding_curve_velocity', 0),
                x.get('estimated_age_minutes', 9999)
            ))
            
            self.tokens_fetched += len(stage0_tokens)
            self.api_calls_made += 1
            self.last_fetch_time = time.time()
            
            self.logger.info(f"✅ Found {len(stage0_tokens)} REAL Stage 0 tokens from pump.fun")
            
            # Log top candidates
            for i, token in enumerate(stage0_tokens[:3]):
                symbol = token.get('symbol', 'UNKNOWN')
                age = token.get('estimated_age_minutes', 0)
                mc = token.get('market_cap', 0)
                priority = token.get('stage0_priority', 0)
                self.logger.info(f"   {i+1}. {symbol} - {age:.1f}min old, ${mc:,.0f} MC, priority: {priority}")
            
            return stage0_tokens
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching Stage 0 tokens: {e}")
            return []
    
    def _calculate_stage0_priority(self, token: Dict) -> int:
        """Calculate Stage 0 priority score"""
        priority = 0
        
        age_minutes = token.get('estimated_age_minutes', 9999)
        market_cap = token.get('market_cap', 0)
        volume_24h = token.get('volume_24h', 0)
        
        # Age bonus (fresher = higher priority)
        if age_minutes <= 5:
            priority += 50      # Ultra-fresh
        elif age_minutes <= 15:
            priority += 40      # Very fresh
        elif age_minutes <= 60:
            priority += 30      # Fresh
        elif age_minutes <= 120:
            priority += 20      # Recent
        
        # Market cap sweet spot
        if 1000 <= market_cap <= 50000:
            priority += 30      # Optimal range
        elif market_cap < 1000:
            priority += 20      # Very early
        elif market_cap <= 100000:
            priority += 10      # Still interesting
        
        # Volume indicator
        if volume_24h > 5000:
            priority += 20      # High activity
        elif volume_24h > 1000:
            priority += 10      # Good activity
        
        return priority
    
    def _calculate_stage0_score(self, token: Dict) -> float:
        """Calculate comprehensive Stage 0 score"""
        score = 50.0  # Base Stage 0 score
        
        age_minutes = token.get('estimated_age_minutes', 9999)
        market_cap = token.get('market_cap', 0)
        
        # Ultra-early bonus
        if age_minutes <= 5:
            score += 25
        elif age_minutes <= 15:
            score += 20
        elif age_minutes <= 60:
            score += 15
        
        # Market cap progression bonus
        if market_cap > 0:
            velocity = market_cap / max(age_minutes, 1)
            if velocity > 500:   # $500/minute growth
                score += 20
            elif velocity > 200: # $200/minute growth
                score += 15
            elif velocity > 100: # $100/minute growth
                score += 10
        
        return min(score, 100)  # Cap at 100
    
    def _estimate_graduation_time(self, token: Dict) -> float:
        """Estimate hours to graduation based on current velocity"""
        try:
            market_cap = token.get('market_cap', 0)
            age_minutes = token.get('estimated_age_minutes', 1)
            
            if market_cap <= 0 or age_minutes <= 0:
                return 999  # Unknown
            
            # Current velocity ($/minute)
            velocity_per_minute = market_cap / age_minutes
            
            # Graduation threshold
            graduation_threshold = 69000  # $69K
            remaining = graduation_threshold - market_cap
            
            if remaining <= 0:
                return 0  # Already graduated
            
            if velocity_per_minute <= 0:
                return 999  # No growth
            
            # Estimate minutes to graduation
            minutes_to_graduation = remaining / velocity_per_minute
            hours_to_graduation = minutes_to_graduation / 60
            
            return round(hours_to_graduation, 1)
            
        except:
            return 999
    
    async def get_trending_tokens(self) -> List[Dict]:
        """Get trending pump.fun tokens for comparison"""
        try:
            trending = await self.api_client.get_trending_tokens()
            
            # Add trending-specific metadata
            for token in trending:
                token['source'] = 'pump_fun_trending'
                token['discovery_method'] = 'trending_api'
            
            return trending
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching trending tokens: {e}")
            return []
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get real integration statistics"""
        api_stats = self.api_client.get_api_stats()
        
        return {
            'service_name': 'Real Pump.fun API',
            'integration_type': 'LIVE_API_CALLS',
            'tokens_fetched': self.tokens_fetched,
            'api_calls_made': self.api_calls_made,
            'ultra_early_detected': self.ultra_early_detected,
            'last_fetch_time': self.last_fetch_time,
            'api_client_stats': api_stats,
            'endpoints_used': list(self.api_client.endpoints.keys()),
            'base_url': self.api_client.BASE_URL,
            'status': 'ACTIVE_LIVE_API',
            'total_calls': api_stats.get('api_calls_made', 0)
        }
    
    async def test_api_connectivity(self) -> bool:
        """Test if pump.fun API is accessible"""
        try:
            self.logger.info("🧪 Testing pump.fun API connectivity...")
            
            test_tokens = await self.api_client.get_latest_tokens(limit=5)
            
            if test_tokens:
                self.logger.info(f"✅ API connectivity test passed - got {len(test_tokens)} tokens")
                return True
            else:
                self.logger.warning("⚠️ API connectivity test failed - no tokens returned")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API connectivity test failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup integration resources"""
        try:
            await self.api_client.cleanup()
            self.logger.info("🧹 Real pump.fun integration cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Integration factory function
async def create_real_pump_fun_integration() -> RealPumpFunIntegration:
    """Create and test real pump.fun integration"""
    integration = RealPumpFunIntegration()
    
    # Test connectivity
    connected = await integration.test_api_connectivity()
    
    if connected:
        integration.logger.info("🔥 Real pump.fun integration ready for production!")
    else:
        integration.logger.warning("⚠️ Pump.fun API connectivity issues detected")
    
    return integration 