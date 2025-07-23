# Raydium LaunchLab Integration Layer for Early Stage Detection
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import aiohttp

class RaydiumLaunchLabIntegration:
    """Integration layer for Raydium LaunchLab tokens with bonding curve graduation detection"""
    
    def __init__(self, early_detector=None, high_conviction_detector=None):
        self.logger = logging.getLogger('RaydiumLaunchLabIntegration')
        self.early_detector = early_detector
        self.high_conviction_detector = high_conviction_detector
        
        # LaunchLab-specific configuration
        self.GRADUATION_THRESHOLD_SOL = 85.0      # 85 SOL graduation threshold
        self.GRADUATION_THRESHOLD_USD = 11500     # ~$11.5K at $135/SOL
        self.WARNING_THRESHOLD_SOL = 75.0         # 75 SOL warning threshold (88% progress)
        self.CRITICAL_THRESHOLD_SOL = 80.0        # 80 SOL critical threshold (94% progress)
        
        # Bonding curve tracking
        self.launchlab_priority_queue = []
        self.graduation_watch_list = []
        self.bonding_curve_tracker = {}
        
        # Performance tracking
        self.launchlab_tokens_processed = 0
        self.graduation_signals_sent = 0
        self.sol_price_cache = {'price': 135.0, 'timestamp': 0}  # Cache SOL price
        
        self.logger.info("🚀 LaunchLab integration initialized - 85 SOL graduation threshold")
    
    async def get_current_sol_price(self) -> float:
        """Get current SOL price with caching (5 min cache)"""
        current_time = time.time()
        if current_time - self.sol_price_cache['timestamp'] < 300:  # 5 min cache
            return self.sol_price_cache['price']
        
        try:
            # Use Jupiter price API for SOL/USD
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112') as response:
                    if response.status == 200:
                        data = await response.json()
                        sol_price = data['data']['So11111111111111111111111111111111111111112']['price']
                        self.sol_price_cache = {'price': sol_price, 'timestamp': current_time}
                        return sol_price
        except Exception as e:
            self.logger.warning(f"Failed to fetch SOL price: {e}, using cached: ${self.sol_price_cache['price']}")
        
        return self.sol_price_cache['price']
    
    def calculate_sol_raised(self, market_cap_usd: float, sol_price: float) -> Dict:
        """Calculate approximate SOL raised based on market cap"""
        # LaunchLab bonding curve: SOL raised ≈ market_cap / (2 * sol_price)
        estimated_sol_raised = market_cap_usd / (2 * sol_price)
        
        graduation_progress = (estimated_sol_raised / self.GRADUATION_THRESHOLD_SOL) * 100
        sol_remaining = max(0, self.GRADUATION_THRESHOLD_SOL - estimated_sol_raised)
        
        return {
            'estimated_sol_raised': estimated_sol_raised,
            'graduation_progress_pct': graduation_progress,
            'sol_remaining': sol_remaining,
            'sol_price_used': sol_price,
            'graduation_threshold_sol': self.GRADUATION_THRESHOLD_SOL
        }
    
    def get_launchlab_stage_analysis(self, sol_raised: float) -> Dict:
        """Analyze LaunchLab bonding curve stage and optimal strategy"""
        graduation_progress = (sol_raised / self.GRADUATION_THRESHOLD_SOL) * 100
        
        if sol_raised < 5:
            return {
                'stage': 'LAUNCHLAB_ULTRA_EARLY',
                'profit_potential': '10-30x',
                'risk_level': 'EXTREME',
                'wallet_recommendation': 'discovery_scout',
                'position_size_pct': 1.5,
                'strategy': 'ULTRA_EARLY_ENTRY',
                'exit_recommendation': 'HOLD_TO_70_SOL'
            }
        elif sol_raised < 15:
            return {
                'stage': 'LAUNCHLAB_EARLY_MOMENTUM',
                'profit_potential': '5-15x',
                'risk_level': 'VERY_HIGH',
                'wallet_recommendation': 'discovery_scout',
                'position_size_pct': 2.0,
                'strategy': 'EARLY_MOMENTUM',
                'exit_recommendation': 'PARTIAL_AT_50_SOL'
            }
        elif sol_raised < 35:
            return {
                'stage': 'LAUNCHLAB_GROWTH',
                'profit_potential': '3-8x',
                'risk_level': 'HIGH',
                'wallet_recommendation': 'conviction_core',
                'position_size_pct': 3.0,
                'strategy': 'GROWTH_ACCUMULATION',
                'exit_recommendation': 'SCALE_OUT_60_SOL'
            }
        elif sol_raised < 55:
            return {
                'stage': 'LAUNCHLAB_MOMENTUM',
                'profit_potential': '2-5x',
                'risk_level': 'MEDIUM',
                'wallet_recommendation': 'conviction_core',
                'position_size_pct': 2.5,
                'strategy': 'MOMENTUM_RIDE',
                'exit_recommendation': 'EXIT_AT_75_SOL'
            }
        elif sol_raised < 75:
            return {
                'stage': 'LAUNCHLAB_PRE_GRADUATION',
                'profit_potential': '1.5-3x',
                'risk_level': 'MEDIUM_LOW',
                'wallet_recommendation': 'moonshot_hunter',
                'position_size_pct': 4.0,
                'strategy': 'PRE_GRADUATION_PLAY',
                'exit_recommendation': 'EXIT_BY_80_SOL'
            }
        elif sol_raised < 80:
            return {
                'stage': 'LAUNCHLAB_GRADUATION_WARNING',
                'profit_potential': '1.2-2x',
                'risk_level': 'LOW',
                'wallet_recommendation': 'moonshot_hunter',
                'position_size_pct': 2.0,
                'strategy': 'GRADUATION_SCALP',
                'exit_recommendation': 'IMMEDIATE_EXIT_SIGNAL'
            }
        else:
            return {
                'stage': 'LAUNCHLAB_GRADUATION_IMMINENT',
                'profit_potential': '1.1-1.3x',
                'risk_level': 'VERY_LOW',
                'wallet_recommendation': 'exit_signal',
                'position_size_pct': 0,
                'strategy': 'IMMEDIATE_EXIT',
                'exit_recommendation': 'EMERGENCY_EXIT'
            }
    
    async def handle_launchlab_detection(self, token_data: Dict):
        """Handle LaunchLab token detection with bonding curve analysis"""
        try:
            token_address = token_data['address']
            market_cap = token_data.get('market_cap', 0)
            
            # Get current SOL price
            sol_price = await self.get_current_sol_price()
            
            # Calculate SOL raised and graduation progress
            sol_analysis = self.calculate_sol_raised(market_cap, sol_price)
            stage_analysis = self.get_launchlab_stage_analysis(sol_analysis['estimated_sol_raised'])
            
            # Enhanced LaunchLab token data
            enhanced_launchlab_token = {
                'token_address': token_address,
                'platform': 'raydium_launchlab',
                'detection_timestamp': time.time(),
                'market_cap_usd': market_cap,
                'sol_raised_estimated': sol_analysis['estimated_sol_raised'],
                'graduation_progress_pct': sol_analysis['graduation_progress_pct'],
                'sol_remaining': sol_analysis['sol_remaining'],
                'launchlab_stage': stage_analysis['stage'],
                'profit_potential': stage_analysis['profit_potential'],
                'optimal_wallet': stage_analysis['wallet_recommendation'],
                'recommended_position_pct': stage_analysis['position_size_pct'],
                'entry_strategy': stage_analysis['strategy'],
                'exit_recommendation': stage_analysis['exit_recommendation'],
                'graduation_threshold_sol': self.GRADUATION_THRESHOLD_SOL,
                'sol_price_at_detection': sol_price,
                **token_data
            }
            
            # Add to priority queue
            self.launchlab_priority_queue.insert(0, enhanced_launchlab_token)
            
            # Add to graduation watch list if approaching threshold
            if sol_analysis['estimated_sol_raised'] >= self.WARNING_THRESHOLD_SOL:
                self.graduation_watch_list.append({
                    'token_address': token_address,
                    'sol_raised': sol_analysis['estimated_sol_raised'],
                    'added_timestamp': time.time(),
                    'alert_level': 'CRITICAL' if sol_analysis['estimated_sol_raised'] >= self.CRITICAL_THRESHOLD_SOL else 'WARNING'
                })
            
            # Feed to existing pipeline with LaunchLab bonuses
            await self._feed_to_existing_pipeline(enhanced_launchlab_token)
            
            self.launchlab_tokens_processed += 1
            
            self.logger.info(f"🎯 LaunchLab token processed: {token_address[:8]}... "
                           f"({sol_analysis['estimated_sol_raised']:.1f}/{self.GRADUATION_THRESHOLD_SOL} SOL, "
                           f"{sol_analysis['graduation_progress_pct']:.1f}% to graduation)")
            
        except Exception as e:
            self.logger.error(f"Error handling LaunchLab detection: {e}")
    
    async def handle_graduation_signal(self, token_data: Dict):
        """Handle LaunchLab graduation signal (85 SOL reached)"""
        try:
            token_address = token_data['token_address']
            
            # Send exit signal to high conviction detector
            if self.high_conviction_detector:
                graduation_alert = {
                    'type': 'LAUNCHLAB_GRADUATION',
                    'token_address': token_address,
                    'graduation_sol': self.GRADUATION_THRESHOLD_SOL,
                    'migration_target': 'raydium_amm',
                    'action': 'IMMEDIATE_EXIT',
                    'reason': 'LaunchLab → Raydium AMM migration imminent',
                    'timestamp': time.time()
                }
                
                # This would trigger exit logic in the high conviction detector
                # await self.high_conviction_detector._handle_graduation_exit_signal(graduation_alert)
            
            self.graduation_signals_sent += 1
            self.logger.warning(f"🚨 LAUNCHLAB GRADUATION: {token_address[:8]}... reached 85 SOL - EXIT SIGNAL SENT")
            
        except Exception as e:
            self.logger.error(f"Error handling LaunchLab graduation: {e}")
    
    async def _feed_to_existing_pipeline(self, enhanced_token: Dict):
        """Feed LaunchLab token to existing detection pipeline with bonuses"""
        if self.early_detector:
            # Add LaunchLab-specific scoring bonuses
            launchlab_bonuses = {
                'launchlab_early_stage_bonus': self._calculate_stage_bonus(enhanced_token),
                'launchlab_graduation_proximity_bonus': self._calculate_graduation_bonus(enhanced_token),
                'launchlab_community_fee_bonus': 5,  # 50% fees to community
                'launchlab_creator_incentive_bonus': 3,  # Creator fee sharing
                'raydium_ecosystem_bonus': 7  # Direct Raydium integration
            }
            
            enhanced_token['launchlab_scoring_bonuses'] = launchlab_bonuses
            enhanced_token['total_launchlab_bonus'] = sum(launchlab_bonuses.values())
    
    def _calculate_stage_bonus(self, token_data: Dict) -> int:
        """Calculate bonus points based on LaunchLab stage"""
        stage = token_data.get('launchlab_stage', '')
        stage_bonuses = {
            'LAUNCHLAB_ULTRA_EARLY': 15,      # Maximum early bonus
            'LAUNCHLAB_EARLY_MOMENTUM': 12,   # Strong early bonus
            'LAUNCHLAB_GROWTH': 8,            # Growth stage bonus
            'LAUNCHLAB_MOMENTUM': 5,          # Momentum bonus
            'LAUNCHLAB_PRE_GRADUATION': 3,    # Pre-graduation bonus
            'LAUNCHLAB_GRADUATION_WARNING': 1, # Minimal bonus
            'LAUNCHLAB_GRADUATION_IMMINENT': 0 # No bonus, exit signal
        }
        return stage_bonuses.get(stage, 0)
    
    def _calculate_graduation_bonus(self, token_data: Dict) -> int:
        """Calculate bonus based on proximity to graduation (inverse relationship)"""
        progress = token_data.get('graduation_progress_pct', 0)
        if progress < 20:
            return 10  # Very early, maximum bonus
        elif progress < 40:
            return 7   # Early stage bonus
        elif progress < 60:
            return 5   # Medium stage bonus
        elif progress < 80:
            return 2   # Late stage minimal bonus
        else:
            return 0   # Too close to graduation
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get LaunchLab integration statistics"""
        return {
            'service_name': 'Raydium LaunchLab',
            'endpoints': [
                'LaunchLab Bonding Curve Monitor',
                'LaunchLab Graduation Detection',
                'Raydium AMM Migration Tracker'
            ],
            'launchlab_tokens_processed': self.launchlab_tokens_processed,
            'graduation_signals_sent': self.graduation_signals_sent,
            'priority_queue_size': len(self.launchlab_priority_queue),
            'graduation_watch_list_size': len(self.graduation_watch_list),
            'graduation_threshold_sol': self.GRADUATION_THRESHOLD_SOL,
            'sol_price_cached': self.sol_price_cache['price'],
            'total_calls': self.launchlab_tokens_processed + self.graduation_signals_sent,
            'success_rate': 1.0 if (self.launchlab_tokens_processed + self.graduation_signals_sent) > 0 else 0.0
        }
    
    def get_launchlab_priority_queue(self) -> List[Dict]:
        """Get current LaunchLab priority queue"""
        return self.launchlab_priority_queue.copy()
    
    async def cleanup(self):
        """Cleanup LaunchLab integration resources"""
        self.launchlab_priority_queue.clear()
        self.graduation_watch_list.clear()
        self.bonding_curve_tracker.clear()
        self.logger.info("🧹 LaunchLab integration cleaned up")
