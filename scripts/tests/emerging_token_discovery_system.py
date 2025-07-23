#!/usr/bin/env python3
"""
🚀 Emerging Token Discovery System
Specialized detection for new and emerging tokens through Meteora + Jupiter cross-platform analysis

Features:
- New pool detection on Meteora
- Recent token integration tracking on Jupiter  
- Growth rate analysis vs absolute metrics
- Risk-adjusted emerging token scoring
- Multi-stage validation pipeline
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import aiohttp
from dataclasses import dataclass

# Import existing connectors
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.tests.test_jupiter_meteora_cross_platform_integration import (
    JupiterConnector, 
    MeteoraConnector,
    JupiterMeteoraIntegratedAnalyzer
)

# Import exclusion logic from main system
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.early_token_detection import MAJOR_TOKENS_TO_EXCLUDE, is_major_token, filter_major_tokens

# Add comprehensive exclusion set for emerging token discovery
EMERGING_TOKEN_EXCLUSIONS = MAJOR_TOKENS_TO_EXCLUDE.copy()

# Additional exclusions specific to emerging token discovery
EMERGING_TOKEN_EXCLUSIONS.update({
    # Common base tokens that appear in pools but aren't emerging
    'So11111111111111111111111111111111111111112',   # SOL
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
    '2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk',  # ETH
    '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',  # BTC
    '3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh',  # WBTC
    '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',  # WETH
})

# Common base token symbols to help with pool parsing
BASE_TOKEN_SYMBOLS = {
    'SOL', 'USDC', 'USDT', 'ETH', 'BTC', 'WBTC', 'WETH', 'DAI', 'BUSD', 'FRAX'
}

def is_excluded_token(address: str) -> bool:
    """Check if a token should be excluded from emerging token discovery"""
    return address in EMERGING_TOKEN_EXCLUSIONS

def filter_excluded_tokens(tokens: List[Dict]) -> List[Dict]:
    """Filter out excluded tokens from emerging token candidates"""
    filtered_tokens = []
    excluded_count = 0
    
    for token in tokens:
        address = token.get('address', '')
        symbol = token.get('symbol', 'Unknown')
        
        if is_excluded_token(address):
            excluded_count += 1
            continue
            
        filtered_tokens.append(token)
    
    if excluded_count > 0:
        print(f"🚫 Filtered out {excluded_count} excluded tokens")
    
    return filtered_tokens

@dataclass
class EmergingTokenSignal:
    """Data class for emerging token signals"""
    address: str
    symbol: str
    discovery_source: str
    signal_strength: float
    risk_level: str
    metadata: Dict
    timestamp: datetime


class EmergingTokenDiscoverySystem:
    """Advanced system for discovering new and emerging tokens"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize connectors
        self.jupiter = JupiterConnector()
        self.meteora = MeteoraConnector()
        
        # Emerging token specific configuration
        self.emerging_config = {
            'meteora_filters': {
                'min_volume_24h': 10000,        # Lower threshold for emerging
                'max_pool_age_hours': 168,      # Max 1 week old
                'min_vlr': 2.0,                 # Volume-to-Liquidity Ratio
                'max_tvl': 500000,              # Focus on smaller pools
                'min_trade_count': 50,          # Some activity required
                'min_growth_rate': 1.5          # 150% volume growth
            },
            'jupiter_filters': {
                'min_liquidity_score': 3,       # Lower threshold
                'max_price_impact': 0.1,        # 10% max slippage
                'max_route_complexity': 6,      # Reasonable routing
                'min_quote_success_rate': 0.8,  # 80% quote success
                'max_token_age_days': 30        # Focus on recent tokens
            },
            'scoring': {
                'cross_platform_bonus': 5,      # Bonus for multi-platform
                'new_pool_bonus': 3,            # Bonus for very new pools
                'high_growth_bonus': 4,         # Bonus for high growth
                'liquidity_establishment_bonus': 3  # Bonus for quick liquidity
            },
            'risk_thresholds': {
                'low_risk_score': 15,           # High confidence emerging
                'medium_risk_score': 10,        # Medium confidence
                'high_risk_score': 5            # Speculative
            }
        }
        
        # Historical data for comparison
        self.historical_data = {
            'previous_jupiter_tokens': set(),
            'previous_meteora_pools': set(),
            'token_first_seen': {},
            'pool_creation_times': {}
        }
        
    async def discover_emerging_meteora_tokens(self, hours_back: int = 24) -> List[Dict]:
        """Discover tokens in newly created high-activity pools"""
        
        self.logger.info(f"🌊 Discovering emerging tokens from Meteora (last {hours_back}h)")
        
        try:
            # Get all pools sorted by volume
            all_pools = await self.meteora.get_trending_pools_by_volume(limit=100)
            
            if not all_pools:
                self.logger.warning("No Meteora pools data available")
                return []
            
            emerging_candidates = []
            current_time = datetime.now()
            seen_tokens = set()  # Track seen tokens to prevent duplicates
            
            for pool in all_pools:
                # Extract pool metrics
                volume_24h = pool.get('volume_24h', 0)
                tvl = pool.get('tvl', 1)  # Avoid division by zero
                pool_name = pool.get('pool_name', '')
                
                # Calculate key metrics
                vlr = volume_24h / tvl if tvl > 0 else 0
                
                # Apply emerging token filters
                filters = self.emerging_config['meteora_filters']
                
                if (volume_24h >= filters['min_volume_24h'] and
                    vlr >= filters['min_vlr'] and
                    tvl <= filters['max_tvl']):
                    
                    # Extract all potential token addresses and symbols from pool
                    token_candidates = self._extract_tokens_from_pool(pool, pool_name)
                    
                    for token_address, token_symbol in token_candidates:
                        # Skip if we've already seen this token
                        if token_address in seen_tokens:
                            continue
                            
                        # Skip excluded tokens (stablecoins, infrastructure tokens)
                        if is_excluded_token(token_address):
                            continue
                            
                        # Skip if symbol is a known base token
                        if token_symbol in BASE_TOKEN_SYMBOLS:
                            continue
                            
                        # Calculate emerging score
                        emerging_score = self._calculate_meteora_emerging_score(pool, vlr)
                        
                        emerging_token = {
                            'address': token_address,
                            'symbol': token_symbol,
                            'pool_data': pool,
                            'vlr': vlr,
                            'emerging_score': emerging_score,
                            'discovery_source': 'meteora_emerging',
                            'discovery_time': current_time.isoformat(),
                            'risk_indicators': self._assess_meteora_risk(pool, vlr)
                        }
                        
                        emerging_candidates.append(emerging_token)
                        seen_tokens.add(token_address)
            
            # Sort by emerging score
            emerging_candidates.sort(key=lambda x: x['emerging_score'], reverse=True)
            
            self.logger.info(f"🔍 Found {len(emerging_candidates)} emerging Meteora candidates (after deduplication)")
            return emerging_candidates[:20]  # Top 20
            
        except Exception as e:
            self.logger.error(f"Error discovering emerging Meteora tokens: {e}")
            return []
    
    async def discover_emerging_jupiter_tokens(self) -> List[Dict]:
        """Find tokens showing early liquidity establishment on Jupiter"""
        
        self.logger.info("🪐 Discovering emerging tokens from Jupiter")
        
        try:
            # Get current Jupiter token list
            current_tokens = await self.jupiter.get_all_tokens()
            
            if not current_tokens:
                self.logger.warning("No Jupiter tokens data available")
                return []
            
            # Identify recently added tokens (compare with historical data)
            current_addresses = {token.get('address') for token in current_tokens if token.get('address')}
            
            if not self.historical_data['previous_jupiter_tokens']:
                # First run - store current tokens and return subset for analysis
                self.historical_data['previous_jupiter_tokens'] = current_addresses
                analysis_tokens = current_tokens[:50]  # Analyze subset on first run
            else:
                # Find newly added tokens
                new_addresses = current_addresses - self.historical_data['previous_jupiter_tokens']
                analysis_tokens = [t for t in current_tokens if t.get('address') in new_addresses]
                
                # Update historical data
                self.historical_data['previous_jupiter_tokens'] = current_addresses
            
            self.logger.info(f"📊 Analyzing {len(analysis_tokens)} Jupiter tokens for emerging signals")
            
            emerging_candidates = []
            seen_tokens = set()  # Track seen tokens to prevent duplicates
            
            # Analyze tokens in batches to avoid overwhelming the API
            batch_size = 10
            for i in range(0, len(analysis_tokens), batch_size):
                batch = analysis_tokens[i:i + batch_size]
                
                for token in batch:
                    token_address = token.get('address')
                    token_symbol = token.get('symbol', 'Unknown')
                    
                    if not token_address:
                        continue
                    
                    # Skip if we've already seen this token
                    if token_address in seen_tokens:
                        continue
                        
                    # Skip excluded tokens (stablecoins, infrastructure tokens)
                    if is_excluded_token(token_address):
                        continue
                        
                    # Skip if symbol is a known base token
                    if token_symbol in BASE_TOKEN_SYMBOLS:
                        continue
                    
                    try:
                        # Test liquidity and tradability
                        quote_analysis = await self._analyze_jupiter_token_liquidity(token_address)
                        
                        if quote_analysis and self._meets_emerging_jupiter_criteria(quote_analysis):
                            emerging_score = self._calculate_jupiter_emerging_score(quote_analysis)
                            
                            emerging_token = {
                                'address': token_address,
                                'symbol': token_symbol,
                                'quote_analysis': quote_analysis,
                                'emerging_score': emerging_score,
                                'discovery_source': 'jupiter_emerging',
                                'discovery_time': datetime.now().isoformat(),
                                'risk_indicators': self._assess_jupiter_risk(quote_analysis)
                            }
                            
                            emerging_candidates.append(emerging_token)
                            seen_tokens.add(token_address)
                            
                    except Exception as e:
                        self.logger.debug(f"Error analyzing Jupiter token {token_address}: {e}")
                        continue
                
                # Small delay between batches
                await asyncio.sleep(0.5)
            
            # Sort by emerging score
            emerging_candidates.sort(key=lambda x: x['emerging_score'], reverse=True)
            
            self.logger.info(f"🔍 Found {len(emerging_candidates)} emerging Jupiter candidates")
            return emerging_candidates[:15]  # Top 15
            
        except Exception as e:
            self.logger.error(f"Error discovering emerging Jupiter tokens: {e}")
            return []
    
    async def _analyze_jupiter_token_liquidity(self, token_address: str) -> Optional[Dict]:
        """Analyze a specific token's liquidity on Jupiter"""
        
        try:
            # Use a standard quote amount (0.1 SOL equivalent)
            quote_params = {
                'inputMint': 'So11111111111111111111111111111111111111112',  # SOL
                'outputMint': token_address,
                'amount': 100000000,  # 0.1 SOL in lamports
                'slippageBps': 1000   # 10% slippage tolerance
            }
            
            quote_data = await self.jupiter._make_tracked_request(self.jupiter.base_urls['quote'], quote_params)
            
            if not quote_data:
                return None
            
            # Analyze the quote for emerging token signals
            analysis = {
                'is_tradeable': True,
                'input_amount': quote_params['amount'],
                'output_amount': int(quote_data.get('outAmount', 0)),
                'price_impact_pct': float(quote_data.get('priceImpactPct', 0)),
                'route_plan': quote_data.get('routePlan', []),
                'route_complexity': len(quote_data.get('routePlan', [])),
                'slippage_bps': quote_data.get('slippageBps', 0),
                'other_amount_threshold': quote_data.get('otherAmountThreshold', 0),
                'swap_mode': quote_data.get('swapMode', 'ExactIn'),
            }
            
            # Calculate liquidity metrics
            analysis['liquidity_score'] = self._calculate_liquidity_score(analysis)
            analysis['activity_score'] = self._calculate_activity_score(analysis)
            analysis['trending_score'] = (analysis['liquidity_score'] + analysis['activity_score']) / 2
            
            return analysis
            
        except Exception as e:
            self.logger.debug(f"Failed to analyze Jupiter token {token_address}: {e}")
            return None
    
    def _extract_tokens_from_pool(self, pool: Dict, pool_name: str) -> List[Tuple[str, str]]:
        """Extract all potential token addresses and symbols from pool data"""
        token_candidates = []
        
        # Method 1: Extract from pool name (e.g., 'CUDIS-SOL' -> ['CUDIS', 'SOL'])
        if pool_name and '-' in pool_name:
            parts = pool_name.split('-')
            if len(parts) == 2:
                token1_symbol, token2_symbol = parts[0].strip(), parts[1].strip()
                
                # Try to get addresses from pool data
                pool_address = pool.get('address', '')
                token_a_address = pool.get('token_a_address', '')
                token_b_address = pool.get('token_b_address', '')
                
                # If we have token addresses, use them
                if token_a_address and token_b_address:
                    token_candidates.append((token_a_address, token1_symbol))
                    token_candidates.append((token_b_address, token2_symbol))
                else:
                    # Fallback: use pool address with parsed symbol
                    # Prefer the non-base token as the emerging candidate
                    if token1_symbol not in BASE_TOKEN_SYMBOLS:
                        token_candidates.append((pool_address, token1_symbol))
                    if token2_symbol not in BASE_TOKEN_SYMBOLS:
                        token_candidates.append((pool_address, token2_symbol))
        
        # Method 2: Extract from direct pool data fields
        if not token_candidates:
            # Fallback to pool address with extracted symbol
            pool_address = pool.get('address', '')
            if pool_address:
                symbol = self._extract_token_from_pool_name(pool_name)
                if symbol and symbol != 'Unknown':
                    token_candidates.append((pool_address, symbol))
        
        return token_candidates
    
    def _extract_token_from_pool_name(self, pool_name: str) -> str:
        """Extract the main token symbol from pool name (e.g., 'TOKEN-SOL' -> 'TOKEN')"""
        if not pool_name or '-' not in pool_name:
            return 'Unknown'
        
        # Split and take the first part (assuming format like "TOKEN-SOL")
        parts = pool_name.split('-')
        main_token = parts[0].strip()
        
        # Filter out common base tokens
        if main_token in BASE_TOKEN_SYMBOLS and len(parts) > 1:
            return parts[1].strip()
        
        return main_token
    
    def _calculate_meteora_emerging_score(self, pool: Dict, vlr: float) -> float:
        """Calculate emerging score for Meteora pool"""
        score = 0.0
        
        # Base VLR score (Volume-to-Liquidity Ratio)
        if vlr > 20: score += 8
        elif vlr > 10: score += 6
        elif vlr > 5: score += 4
        elif vlr > 2: score += 2
        
        # Volume score (adjusted for emerging tokens)
        volume_24h = pool.get('volume_24h', 0)
        if volume_24h > 500000: score += 4
        elif volume_24h > 100000: score += 3
        elif volume_24h > 50000: score += 2
        elif volume_24h > 10000: score += 1
        
        # TVL score (smaller pools get bonus for high activity)
        tvl = pool.get('tvl', 0)
        if tvl < 50000 and volume_24h > 50000: score += 3  # Small pool, high volume
        elif tvl < 100000 and volume_24h > 100000: score += 2
        
        # Fee generation score
        fee_24h = pool.get('fee_24h', 0)
        if fee_24h > 1000: score += 2
        elif fee_24h > 500: score += 1
        
        return min(score, 15)  # Cap at 15
    
    def _calculate_jupiter_emerging_score(self, quote_analysis: Dict) -> float:
        """Calculate emerging score for Jupiter token"""
        score = 0.0
        
        # Liquidity score
        liquidity_score = quote_analysis.get('liquidity_score', 0)
        score += liquidity_score
        
        # Activity score  
        activity_score = quote_analysis.get('activity_score', 0)
        score += activity_score
        
        # Price impact bonus (lower is better for emerging tokens)
        price_impact = quote_analysis.get('price_impact_pct', 100)
        if price_impact < 2: score += 3
        elif price_impact < 5: score += 2
        elif price_impact < 10: score += 1
        
        # Route complexity bonus (simpler is better)
        route_complexity = quote_analysis.get('route_complexity', 10)
        if route_complexity <= 2: score += 2
        elif route_complexity <= 4: score += 1
        
        return min(score, 15)  # Cap at 15
    
    def _calculate_liquidity_score(self, analysis: Dict) -> float:
        """Calculate liquidity score from quote analysis"""
        if not analysis.get('is_tradeable'):
            return 0
        
        price_impact = analysis.get('price_impact_pct', 100)
        route_complexity = analysis.get('route_complexity', 10)
        
        # Base score from price impact
        if price_impact < 1: score = 10
        elif price_impact < 2: score = 8
        elif price_impact < 5: score = 6
        elif price_impact < 10: score = 4
        else: score = 2
        
        # Adjust for route complexity
        if route_complexity > 5: score *= 0.7
        elif route_complexity > 3: score *= 0.85
        
        return max(0, min(score, 10))
    
    def _calculate_activity_score(self, analysis: Dict) -> float:
        """Calculate activity score from quote analysis"""
        # For emerging tokens, successful routing is the main activity indicator
        if analysis.get('is_tradeable'):
            base_score = 8
            
            # Bonus for good liquidity
            if analysis.get('price_impact_pct', 100) < 5:
                base_score += 2
            
            return min(base_score, 10)
        
        return 0
    
    def _meets_emerging_jupiter_criteria(self, quote_analysis: Dict) -> bool:
        """Check if Jupiter token meets emerging criteria"""
        filters = self.emerging_config['jupiter_filters']
        
        return (
            quote_analysis.get('is_tradeable', False) and
            quote_analysis.get('liquidity_score', 0) >= filters['min_liquidity_score'] and
            quote_analysis.get('price_impact_pct', 100) <= filters['max_price_impact'] * 100 and
            quote_analysis.get('route_complexity', 10) <= filters['max_route_complexity']
        )
    
    def _assess_meteora_risk(self, pool: Dict, vlr: float) -> Dict:
        """Assess risk indicators for Meteora emerging token"""
        risk_indicators = {
            'liquidity_risk': 'LOW',
            'volume_risk': 'LOW', 
            'age_risk': 'MEDIUM',
            'overall_risk': 'MEDIUM'
        }
        
        tvl = pool.get('tvl', 0)
        volume_24h = pool.get('volume_24h', 0)
        
        # Liquidity risk
        if tvl < 10000: risk_indicators['liquidity_risk'] = 'HIGH'
        elif tvl < 50000: risk_indicators['liquidity_risk'] = 'MEDIUM'
        
        # Volume risk (too high VLR can indicate manipulation)
        if vlr > 50: risk_indicators['volume_risk'] = 'HIGH'
        elif vlr > 20: risk_indicators['volume_risk'] = 'MEDIUM'
        
        # Overall risk assessment
        high_risks = sum(1 for risk in risk_indicators.values() if risk == 'HIGH')
        if high_risks >= 2:
            risk_indicators['overall_risk'] = 'HIGH'
        elif high_risks == 1:
            risk_indicators['overall_risk'] = 'MEDIUM'
        else:
            risk_indicators['overall_risk'] = 'LOW'
        
        return risk_indicators
    
    def _assess_jupiter_risk(self, quote_analysis: Dict) -> Dict:
        """Assess risk indicators for Jupiter emerging token"""
        risk_indicators = {
            'liquidity_risk': 'LOW',
            'slippage_risk': 'LOW',
            'routing_risk': 'LOW',
            'overall_risk': 'MEDIUM'
        }
        
        # Liquidity risk
        liquidity_score = quote_analysis.get('liquidity_score', 0)
        if liquidity_score < 3: risk_indicators['liquidity_risk'] = 'HIGH'
        elif liquidity_score < 5: risk_indicators['liquidity_risk'] = 'MEDIUM'
        
        # Slippage risk
        price_impact = quote_analysis.get('price_impact_pct', 100)
        if price_impact > 10: risk_indicators['slippage_risk'] = 'HIGH'
        elif price_impact > 5: risk_indicators['slippage_risk'] = 'MEDIUM'
        
        # Routing risk
        route_complexity = quote_analysis.get('route_complexity', 10)
        if route_complexity > 6: risk_indicators['routing_risk'] = 'HIGH'
        elif route_complexity > 4: risk_indicators['routing_risk'] = 'MEDIUM'
        
        # Overall risk assessment
        high_risks = sum(1 for risk in risk_indicators.values() if risk == 'HIGH')
        if high_risks >= 2:
            risk_indicators['overall_risk'] = 'HIGH'
        elif high_risks == 1:
            risk_indicators['overall_risk'] = 'MEDIUM'
        else:
            risk_indicators['overall_risk'] = 'LOW'
        
        return risk_indicators
    
    async def find_cross_platform_emerging_tokens(self, meteora_tokens: List[Dict], jupiter_tokens: List[Dict]) -> List[Dict]:
        """Find tokens that appear on both platforms - highest confidence emerging tokens"""
        
        self.logger.info("🔍 Finding cross-platform emerging tokens")
        
        cross_platform_tokens = []
        meteora_addresses = {token['address']: token for token in meteora_tokens}
        
        for jupiter_token in jupiter_tokens:
            jupiter_address = jupiter_token['address']
            
            if jupiter_address in meteora_addresses:
                meteora_token = meteora_addresses[jupiter_address]
                
                # Combine data from both platforms
                combined_token = {
                    'address': jupiter_address,
                    'symbol': jupiter_token['symbol'],
                    'platforms': ['meteora_emerging', 'jupiter_emerging'],
                    'platform_count': 2,
                    'meteora_data': meteora_token,
                    'jupiter_data': jupiter_token,
                    'combined_score': meteora_token['emerging_score'] + jupiter_token['emerging_score'],
                    'cross_platform_bonus': self.emerging_config['scoring']['cross_platform_bonus'],
                    'total_score': meteora_token['emerging_score'] + jupiter_token['emerging_score'] + 
                                 self.emerging_config['scoring']['cross_platform_bonus'],
                    'discovery_sources': ['meteora_emerging', 'jupiter_emerging'],
                    'risk_assessment': self._assess_combined_risk(meteora_token, jupiter_token),
                    'discovery_time': datetime.now().isoformat()
                }
                
                cross_platform_tokens.append(combined_token)
        
        # Sort by total score
        cross_platform_tokens.sort(key=lambda x: x['total_score'], reverse=True)
        
        self.logger.info(f"🎯 Found {len(cross_platform_tokens)} cross-platform emerging tokens")
        return cross_platform_tokens
    
    def _assess_combined_risk(self, meteora_token: Dict, jupiter_token: Dict) -> Dict:
        """Assess combined risk from both platforms"""
        meteora_risk = meteora_token.get('risk_indicators', {})
        jupiter_risk = jupiter_token.get('risk_indicators', {})
        
        # Cross-platform validation reduces overall risk
        combined_risk = {
            'meteora_risk': meteora_risk.get('overall_risk', 'MEDIUM'),
            'jupiter_risk': jupiter_risk.get('overall_risk', 'MEDIUM'),
            'cross_platform_validation': True,
            'overall_risk': 'MEDIUM'  # Default for cross-platform
        }
        
        # If both platforms show LOW risk, overall is LOW
        if (meteora_risk.get('overall_risk') == 'LOW' and 
            jupiter_risk.get('overall_risk') == 'LOW'):
            combined_risk['overall_risk'] = 'LOW'
        
        # If either platform shows HIGH risk, overall is MEDIUM (cross-platform helps)
        elif (meteora_risk.get('overall_risk') == 'HIGH' or 
              jupiter_risk.get('overall_risk') == 'HIGH'):
            combined_risk['overall_risk'] = 'MEDIUM'
        
        return combined_risk
    
    async def run_emerging_token_discovery(self) -> Dict:
        """Run the complete emerging token discovery pipeline"""
        
        self.logger.info("🚀 Starting Emerging Token Discovery System")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # Stage 1: Platform-specific discovery
            self.logger.info("📊 Stage 1: Platform-specific discovery")
            meteora_emerging = await self.discover_emerging_meteora_tokens()
            jupiter_emerging = await self.discover_emerging_jupiter_tokens()
            
            # Stage 2: Cross-platform validation
            self.logger.info("🔍 Stage 2: Cross-platform validation")
            cross_platform_emerging = await self.find_cross_platform_emerging_tokens(
                meteora_emerging, jupiter_emerging
            )
            
            # Stage 3: Risk assessment and filtering
            self.logger.info("⚖️ Stage 3: Risk assessment")
            risk_filtered_tokens = self._apply_risk_filters(
                meteora_emerging, jupiter_emerging, cross_platform_emerging
            )
            
            # Generate comprehensive results
            duration = time.time() - start_time
            
            results = {
                'discovery_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': round(duration, 2),
                    'status': 'SUCCESS'
                },
                'discovery_results': {
                    'meteora_emerging_count': len(meteora_emerging),
                    'jupiter_emerging_count': len(jupiter_emerging), 
                    'cross_platform_count': len(cross_platform_emerging),
                    'risk_filtered_count': len(risk_filtered_tokens)
                },
                'emerging_tokens': {
                    'meteora_only': meteora_emerging,
                    'jupiter_only': jupiter_emerging,
                    'cross_platform': cross_platform_emerging,
                    'risk_filtered': risk_filtered_tokens
                },
                'risk_analysis': self._generate_risk_analysis(
                    meteora_emerging, jupiter_emerging, cross_platform_emerging
                ),
                'recommendations': self._generate_recommendations(
                    meteora_emerging, jupiter_emerging, cross_platform_emerging
                )
            }
            
            # Save results
            timestamp = int(time.time())
            filename = f"scripts/tests/emerging_token_discovery_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"\n🎯 EMERGING TOKEN DISCOVERY COMPLETE:")
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info(f"Meteora Emerging: {len(meteora_emerging)}")
            self.logger.info(f"Jupiter Emerging: {len(jupiter_emerging)}")
            self.logger.info(f"Cross-Platform: {len(cross_platform_emerging)}")
            self.logger.info(f"Results saved to: {filename}")
            
            # Display top emerging tokens
            self._display_top_emerging_tokens(cross_platform_emerging, meteora_emerging, jupiter_emerging)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in emerging token discovery: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def _apply_risk_filters(self, meteora_tokens: List[Dict], jupiter_tokens: List[Dict], 
                           cross_platform_tokens: List[Dict]) -> List[Dict]:
        """Apply risk-based filtering to emerging tokens"""
        
        # First, apply exclusion filters to all token lists
        meteora_tokens = filter_excluded_tokens(meteora_tokens)
        jupiter_tokens = filter_excluded_tokens(jupiter_tokens)
        cross_platform_tokens = filter_excluded_tokens(cross_platform_tokens)
        
        risk_thresholds = self.emerging_config['risk_thresholds']
        filtered_tokens = []
        seen_addresses = set()  # Final deduplication check
        
        # Process cross-platform tokens (highest priority)
        for token in cross_platform_tokens:
            address = token.get('address', '')
            if address and address not in seen_addresses:
                if token['total_score'] >= risk_thresholds['high_risk_score']:
                    token['confidence_level'] = self._determine_confidence_level(token['total_score'])
                    filtered_tokens.append(token)
                    seen_addresses.add(address)
        
        # Process single-platform tokens with higher scores
        single_platform_candidates = []
        
        # High-scoring Meteora tokens
        for token in meteora_tokens:
            address = token.get('address', '')
            if (address and address not in seen_addresses and
                token['emerging_score'] >= risk_thresholds['medium_risk_score']):
                token['confidence_level'] = 'MEDIUM'
                token['platform_count'] = 1
                single_platform_candidates.append(token)
                seen_addresses.add(address)
        
        # High-scoring Jupiter tokens
        for token in jupiter_tokens:
            address = token.get('address', '')
            if (address and address not in seen_addresses and
                token['emerging_score'] >= risk_thresholds['medium_risk_score']):
                token['confidence_level'] = 'MEDIUM'
                token['platform_count'] = 1
                single_platform_candidates.append(token)
                seen_addresses.add(address)
        
        # Add top single-platform tokens
        single_platform_candidates.sort(key=lambda x: x['emerging_score'], reverse=True)
        filtered_tokens.extend(single_platform_candidates[:10])  # Top 10 single-platform
        
        self.logger.info(f"🎯 Final filtered tokens: {len(filtered_tokens)} (after exclusion and risk filtering)")
        
        return filtered_tokens
    
    def _determine_confidence_level(self, total_score: float) -> str:
        """Determine confidence level based on total score"""
        thresholds = self.emerging_config['risk_thresholds']
        
        if total_score >= thresholds['low_risk_score']:
            return 'HIGH'
        elif total_score >= thresholds['medium_risk_score']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_risk_analysis(self, meteora_tokens: List[Dict], jupiter_tokens: List[Dict], 
                               cross_platform_tokens: List[Dict]) -> Dict:
        """Generate comprehensive risk analysis"""
        
        risk_analysis = {
            'overall_risk_distribution': {
                'LOW': 0, 'MEDIUM': 0, 'HIGH': 0
            },
            'platform_risk_comparison': {
                'meteora_avg_risk': 'MEDIUM',
                'jupiter_avg_risk': 'MEDIUM',
                'cross_platform_avg_risk': 'LOW'
            },
            'risk_factors': {
                'liquidity_concerns': 0,
                'high_volatility_indicators': 0,
                'new_token_warnings': len(meteora_tokens) + len(jupiter_tokens)
            }
        }
        
        # Count risk distribution
        all_tokens = meteora_tokens + jupiter_tokens + cross_platform_tokens
        for token in all_tokens:
            risk_indicators = token.get('risk_indicators', {})
            overall_risk = risk_indicators.get('overall_risk', 'MEDIUM')
            risk_analysis['overall_risk_distribution'][overall_risk] += 1
        
        return risk_analysis
    
    def _generate_recommendations(self, meteora_tokens: List[Dict], jupiter_tokens: List[Dict], 
                                 cross_platform_tokens: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        if cross_platform_tokens:
            recommendations.append(f"✅ {len(cross_platform_tokens)} cross-platform emerging tokens found - highest confidence")
            
        if len(meteora_tokens) > len(jupiter_tokens):
            recommendations.append("🌊 Meteora showing more emerging activity - focus on DEX volume analysis")
        elif len(jupiter_tokens) > len(meteora_tokens):
            recommendations.append("🪐 Jupiter showing more emerging activity - focus on liquidity establishment")
            
        if len(cross_platform_tokens) > 5:
            recommendations.append("🎯 Strong emerging token market - consider portfolio allocation")
        elif len(cross_platform_tokens) < 2:
            recommendations.append("⚠️ Limited cross-platform validation - exercise extra caution")
            
        recommendations.append("🚨 All emerging tokens carry HIGH risk - use appropriate position sizing")
        recommendations.append("📊 Monitor these tokens for 24-48h before significant investment")
        
        return recommendations
    
    def _display_top_emerging_tokens(self, cross_platform: List[Dict], meteora: List[Dict], jupiter: List[Dict]):
        """Display formatted table of top emerging tokens"""
        
        self.logger.info("\n🏆 TOP EMERGING TOKENS:")
        self.logger.info("+" + "-" * 100 + "+")
        self.logger.info("| Rank | Symbol      | Platforms | Score | Risk  | Discovery Source                |")
        self.logger.info("+" + "-" * 100 + "+")
        
        rank = 1
        
        # Cross-platform tokens first (highest confidence)
        for token in cross_platform[:5]:
            symbol = token['symbol'][:10].ljust(10)
            platforms = str(token['platform_count']).ljust(8)
            score = f"{token['total_score']:.1f}".ljust(5)
            risk = token.get('risk_assessment', {}).get('overall_risk', 'MED')[:4].ljust(5)
            source = "Meteora + Jupiter".ljust(30)
            
            self.logger.info(f"| {rank:4d} | {symbol} | {platforms} | {score} | {risk} | {source} |")
            rank += 1
        
        # Top single-platform tokens
        single_platform = sorted(meteora + jupiter, key=lambda x: x['emerging_score'], reverse=True)
        for token in single_platform[:5]:
            if rank > 10:  # Limit display
                break
                
            symbol = token['symbol'][:10].ljust(10)
            platforms = "1".ljust(8)
            score = f"{token['emerging_score']:.1f}".ljust(5)
            risk = token.get('risk_indicators', {}).get('overall_risk', 'MED')[:4].ljust(5)
            source = token['discovery_source'][:30].ljust(30)
            
            self.logger.info(f"| {rank:4d} | {symbol} | {platforms} | {score} | {risk} | {source} |")
            rank += 1
        
        self.logger.info("+" + "-" * 100 + "+")


async def main():
    """Main function to run the emerging token discovery system"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize and run the discovery system
    discovery_system = EmergingTokenDiscoverySystem(logger=logger)
    results = await discovery_system.run_emerging_token_discovery()
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 