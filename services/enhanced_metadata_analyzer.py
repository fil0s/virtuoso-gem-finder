#!/usr/bin/env python3
"""
Enhanced Metadata Analyzer

Extracts and analyzes underutilized metadata from Birdeye API responses
to provide deeper insights for token analysis and scoring.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

class EnhancedMetadataAnalyzer:
    """
    Analyzes extended metadata fields from Birdeye API responses.
    Focuses on social proof, community strength, and advanced market metrics.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def analyze_social_media_presence(self, overview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze social media and community presence from token extensions.
        
        Args:
            overview_data: Token overview response from Birdeye API
            
        Returns:
            Social media analysis results
        """
        social_analysis = {
            'social_score': 0,
            'social_channels': [],
            'community_strength': 'Unknown',
            'has_website': False,
            'has_social_media': False,
            'social_diversity_score': 0
        }
        
        try:
            extensions = overview_data.get('extensions', {})
            if not extensions:
                return social_analysis
            
            # Track available social channels
            social_channels = []
            channel_weights = {
                'website': 25,
                'twitter': 20,
                'telegram': 15,
                'discord': 15,
                'medium': 10,
                'reddit': 8,
                'github': 7
            }
            
            total_score = 0
            for channel, weight in channel_weights.items():
                if extensions.get(channel):
                    social_channels.append(channel)
                    total_score += weight
            
            social_analysis['social_channels'] = social_channels
            social_analysis['social_score'] = min(100, total_score)
            social_analysis['has_website'] = bool(extensions.get('website'))
            social_analysis['has_social_media'] = len(social_channels) > 1
            social_analysis['social_diversity_score'] = len(social_channels) * 10
            
            # Determine community strength
            if total_score >= 80:
                social_analysis['community_strength'] = 'Strong'
            elif total_score >= 50:
                social_analysis['community_strength'] = 'Moderate'
            elif total_score >= 25:
                social_analysis['community_strength'] = 'Weak'
            else:
                social_analysis['community_strength'] = 'Very Weak'
                
        except Exception as e:
            self.logger.error(f"Error analyzing social media presence: {e}")
        
        return social_analysis
    
    def analyze_trading_patterns(self, overview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze enhanced trading patterns from multi-timeframe data.
        
        Args:
            overview_data: Token overview response from Birdeye API
            
        Returns:
            Trading pattern analysis results
        """
        trading_analysis = {
            'volume_acceleration': 0,
            'trade_frequency_score': 0,
            'unique_wallet_growth': 0,
            'volume_consistency': 0,
            'trading_momentum': 'Neutral'
        }
        
        try:
            volume_data = overview_data.get('volume', {})
            trades_data = overview_data.get('trades', {})
            unique_wallets_data = overview_data.get('uniqueWallets', {})
            
            # Calculate volume acceleration (shorter timeframes vs longer)
            vol_1h = volume_data.get('h1', 0)
            vol_4h = volume_data.get('h4', 0)
            vol_24h = volume_data.get('h24', 0)
            
            if vol_24h > 0:
                # Normalized hourly rates
                vol_1h_rate = vol_1h  # Already 1h
                vol_4h_rate = vol_4h / 4  # Convert to hourly rate
                vol_24h_rate = vol_24h / 24  # Convert to hourly rate
                
                # Volume acceleration score
                if vol_1h_rate > vol_4h_rate > vol_24h_rate:
                    trading_analysis['volume_acceleration'] = min(100, (vol_1h_rate / vol_24h_rate) * 20)
                elif vol_1h_rate > vol_24h_rate:
                    trading_analysis['volume_acceleration'] = min(100, (vol_1h_rate / vol_24h_rate) * 10)
                
                # Volume consistency (lower variance is better)
                rates = [vol_1h_rate, vol_4h_rate, vol_24h_rate]
                avg_rate = sum(rates) / len(rates)
                variance = sum((r - avg_rate) ** 2 for r in rates) / len(rates)
                consistency = max(0, 100 - (variance / avg_rate * 100)) if avg_rate > 0 else 0
                trading_analysis['volume_consistency'] = consistency
            
            # Trade frequency analysis
            trades_1h = trades_data.get('h1', 0)
            trades_24h = trades_data.get('h24', 0)
            
            if trades_24h > 0:
                trades_per_hour = trades_24h / 24
                if trades_per_hour >= 10:
                    trading_analysis['trade_frequency_score'] = 100
                elif trades_per_hour >= 5:
                    trading_analysis['trade_frequency_score'] = 75
                elif trades_per_hour >= 1:
                    trading_analysis['trade_frequency_score'] = 50
                else:
                    trading_analysis['trade_frequency_score'] = 25
            
            # Unique wallet growth
            wallets_1h = unique_wallets_data.get('h1', 0)
            wallets_24h = unique_wallets_data.get('h24', 0)
            
            if wallets_24h > 0:
                wallet_hourly_rate = wallets_24h / 24
                if wallets_1h > wallet_hourly_rate * 2:  # 2x expected rate
                    trading_analysis['unique_wallet_growth'] = 100
                elif wallets_1h > wallet_hourly_rate * 1.5:  # 1.5x expected rate
                    trading_analysis['unique_wallet_growth'] = 75
                elif wallets_1h >= wallet_hourly_rate:
                    trading_analysis['unique_wallet_growth'] = 50
                else:
                    trading_analysis['unique_wallet_growth'] = 25
            
            # Overall momentum assessment
            momentum_score = (
                trading_analysis['volume_acceleration'] * 0.4 +
                trading_analysis['trade_frequency_score'] * 0.3 +
                trading_analysis['unique_wallet_growth'] * 0.3
            )
            
            if momentum_score >= 80:
                trading_analysis['trading_momentum'] = 'Very Strong'
            elif momentum_score >= 60:
                trading_analysis['trading_momentum'] = 'Strong'
            elif momentum_score >= 40:
                trading_analysis['trading_momentum'] = 'Moderate'
            elif momentum_score >= 20:
                trading_analysis['trading_momentum'] = 'Weak'
            else:
                trading_analysis['trading_momentum'] = 'Very Weak'
                
        except Exception as e:
            self.logger.error(f"Error analyzing trading patterns: {e}")
        
        return trading_analysis
    
    def analyze_price_dynamics(self, overview_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze price momentum across multiple timeframes.
        
        Args:
            overview_data: Token overview response from Birdeye API
            
        Returns:
            Price dynamics analysis results
        """
        price_analysis = {
            'momentum_score': 0,
            'volatility_score': 0,
            'trend_strength': 'Neutral',
            'price_stability': 0,
            'short_term_trend': 'Sideways',
            'medium_term_trend': 'Sideways'
        }
        
        try:
            # Extract price changes
            price_1h = overview_data.get('priceChange1h', 0)
            price_4h = overview_data.get('priceChange4h', 0)
            price_24h = overview_data.get('priceChange24h', 0)
            price_7d = overview_data.get('priceChange7d', 0)
            
            # Momentum score (consistent upward movement)
            positive_periods = sum(1 for p in [price_1h, price_4h, price_24h] if p > 0)
            if positive_periods == 3 and price_1h > price_4h > 0:
                price_analysis['momentum_score'] = min(100, abs(price_24h) * 2)
            elif positive_periods >= 2:
                price_analysis['momentum_score'] = min(100, abs(price_24h) * 1.5)
            elif positive_periods == 1:
                price_analysis['momentum_score'] = min(100, abs(price_24h))
            
            # Volatility analysis
            price_changes = [price_1h, price_4h, price_24h]
            avg_change = sum(abs(p) for p in price_changes) / len(price_changes)
            if avg_change >= 50:
                price_analysis['volatility_score'] = 100
            elif avg_change >= 20:
                price_analysis['volatility_score'] = 80
            elif avg_change >= 10:
                price_analysis['volatility_score'] = 60
            elif avg_change >= 5:
                price_analysis['volatility_score'] = 40
            else:
                price_analysis['volatility_score'] = 20
            
            # Price stability (lower volatility with consistent direction)
            if avg_change < 5 and positive_periods >= 2:
                price_analysis['price_stability'] = 90
            elif avg_change < 10 and positive_periods >= 2:
                price_analysis['price_stability'] = 70
            elif avg_change < 20:
                price_analysis['price_stability'] = 50
            else:
                price_analysis['price_stability'] = 20
            
            # Trend determination
            if price_1h > 5 and price_4h > 5:
                price_analysis['short_term_trend'] = 'Strong Up'
            elif price_1h > 0 and price_4h > 0:
                price_analysis['short_term_trend'] = 'Up'
            elif price_1h < -5 and price_4h < -5:
                price_analysis['short_term_trend'] = 'Strong Down'
            elif price_1h < 0 and price_4h < 0:
                price_analysis['short_term_trend'] = 'Down'
            
            if price_24h > 10 and price_7d > 10:
                price_analysis['medium_term_trend'] = 'Strong Up'
            elif price_24h > 0 and price_7d > 0:
                price_analysis['medium_term_trend'] = 'Up'
            elif price_24h < -10 and price_7d < -10:
                price_analysis['medium_term_trend'] = 'Strong Down'
            elif price_24h < 0 and price_7d < 0:
                price_analysis['medium_term_trend'] = 'Down'
            
            # Overall trend strength
            momentum = price_analysis['momentum_score']
            if momentum >= 80:
                price_analysis['trend_strength'] = 'Very Strong'
            elif momentum >= 60:
                price_analysis['trend_strength'] = 'Strong'
            elif momentum >= 40:
                price_analysis['trend_strength'] = 'Moderate'
            elif momentum >= 20:
                price_analysis['trend_strength'] = 'Weak'
            else:
                price_analysis['trend_strength'] = 'Very Weak'
                
        except Exception as e:
            self.logger.error(f"Error analyzing price dynamics: {e}")
        
        return price_analysis
    
    def analyze_liquidity_health(self, overview_data: Dict[str, Any], security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze liquidity and market health indicators.
        
        Args:
            overview_data: Token overview response
            security_data: Token security response
            
        Returns:
            Liquidity health analysis results
        """
        liquidity_analysis = {
            'liquidity_health_score': 0,
            'lp_security_score': 0,
            'market_depth_score': 0,
            'liquidity_risk': 'Unknown',
            'provider_diversification': 0
        }
        
        try:
            # Extract liquidity data
            liquidity = overview_data.get('liquidity', 0)
            market_cap = overview_data.get('marketCap', 0)
            
            # Extract security data
            lp_locked = security_data.get('lpLocked', False)
            lp_locked_percentage = security_data.get('lpLockedPercentage', 0)
            liquidity_providers = security_data.get('liquidityProviders', 0)
            
            # Liquidity to market cap ratio
            if market_cap > 0:
                liquidity_ratio = liquidity / market_cap
                if liquidity_ratio >= 0.3:  # 30%+ liquidity
                    liquidity_analysis['market_depth_score'] = 100
                elif liquidity_ratio >= 0.15:  # 15%+ liquidity
                    liquidity_analysis['market_depth_score'] = 80
                elif liquidity_ratio >= 0.05:  # 5%+ liquidity
                    liquidity_analysis['market_depth_score'] = 60
                else:
                    liquidity_analysis['market_depth_score'] = 30
            
            # LP security score
            if lp_locked and lp_locked_percentage >= 80:
                liquidity_analysis['lp_security_score'] = 100
            elif lp_locked and lp_locked_percentage >= 50:
                liquidity_analysis['lp_security_score'] = 75
            elif lp_locked:
                liquidity_analysis['lp_security_score'] = 50
            else:
                liquidity_analysis['lp_security_score'] = 0  # Major risk
            
            # Provider diversification
            if liquidity_providers >= 100:
                liquidity_analysis['provider_diversification'] = 100
            elif liquidity_providers >= 50:
                liquidity_analysis['provider_diversification'] = 80
            elif liquidity_providers >= 20:
                liquidity_analysis['provider_diversification'] = 60
            elif liquidity_providers >= 5:
                liquidity_analysis['provider_diversification'] = 40
            else:
                liquidity_analysis['provider_diversification'] = 20
            
            # Overall liquidity health
            overall_score = (
                liquidity_analysis['market_depth_score'] * 0.4 +
                liquidity_analysis['lp_security_score'] * 0.4 +
                liquidity_analysis['provider_diversification'] * 0.2
            )
            liquidity_analysis['liquidity_health_score'] = overall_score
            
            # Risk assessment
            if overall_score >= 80 and lp_locked:
                liquidity_analysis['liquidity_risk'] = 'Very Low'
            elif overall_score >= 60 and lp_locked:
                liquidity_analysis['liquidity_risk'] = 'Low'
            elif overall_score >= 40:
                liquidity_analysis['liquidity_risk'] = 'Moderate'
            elif lp_locked:
                liquidity_analysis['liquidity_risk'] = 'High'
            else:
                liquidity_analysis['liquidity_risk'] = 'Very High'
                
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity health: {e}")
        
        return liquidity_analysis
    
    def generate_comprehensive_metadata_score(self, 
                                            social_analysis: Dict[str, Any],
                                            trading_analysis: Dict[str, Any], 
                                            price_analysis: Dict[str, Any],
                                            liquidity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive metadata-based score from all analyses.
        
        Returns:
            Comprehensive scoring results
        """
        try:
            # Weight the different components
            weights = {
                'social': 0.15,      # Social media presence
                'trading': 0.35,     # Trading patterns
                'price': 0.25,       # Price dynamics
                'liquidity': 0.25    # Liquidity health
            }
            
            # Extract component scores
            social_score = social_analysis.get('social_score', 0)
            trading_score = (
                trading_analysis.get('volume_acceleration', 0) * 0.4 +
                trading_analysis.get('trade_frequency_score', 0) * 0.3 +
                trading_analysis.get('unique_wallet_growth', 0) * 0.3
            )
            price_score = price_analysis.get('momentum_score', 0)
            liquidity_score = liquidity_analysis.get('liquidity_health_score', 0)
            
            # Calculate composite score
            composite_score = (
                social_score * weights['social'] +
                trading_score * weights['trading'] +
                price_score * weights['price'] +
                liquidity_score * weights['liquidity']
            )
            
            return {
                'metadata_composite_score': composite_score,
                'component_scores': {
                    'social_score': social_score,
                    'trading_score': trading_score,
                    'price_score': price_score,
                    'liquidity_score': liquidity_score
                },
                'score_weights': weights,
                'metadata_grade': self._get_grade(composite_score),
                'key_strengths': self._identify_strengths(social_analysis, trading_analysis, price_analysis, liquidity_analysis),
                'key_risks': self._identify_risks(social_analysis, trading_analysis, price_analysis, liquidity_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive metadata score: {e}")
            return {
                'metadata_composite_score': 0,
                'component_scores': {},
                'score_weights': weights,
                'metadata_grade': 'Unknown',
                'key_strengths': [],
                'key_risks': ['Analysis error']
            }
    
    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        else:
            return 'D'
    
    def _identify_strengths(self, social_analysis, trading_analysis, price_analysis, liquidity_analysis) -> List[str]:
        """Identify key strengths based on analysis results"""
        strengths = []
        
        if social_analysis.get('social_score', 0) >= 70:
            strengths.append(f"Strong community presence ({social_analysis['community_strength']})")
        
        if trading_analysis.get('volume_acceleration', 0) >= 70:
            strengths.append("High volume acceleration")
        
        if price_analysis.get('momentum_score', 0) >= 70:
            strengths.append(f"Strong price momentum ({price_analysis['trend_strength']})")
        
        if liquidity_analysis.get('liquidity_health_score', 0) >= 70:
            strengths.append(f"Healthy liquidity ({liquidity_analysis['liquidity_risk']} risk)")
        
        return strengths[:3]  # Top 3 strengths
    
    def _identify_risks(self, social_analysis, trading_analysis, price_analysis, liquidity_analysis) -> List[str]:
        """Identify key risks based on analysis results"""
        risks = []
        
        if social_analysis.get('social_score', 0) < 30:
            risks.append("Weak community presence")
        
        if trading_analysis.get('trade_frequency_score', 0) < 30:
            risks.append("Low trading activity")
        
        if price_analysis.get('volatility_score', 0) >= 80:
            risks.append("High price volatility")
        
        if liquidity_analysis.get('liquidity_risk') in ['High', 'Very High']:
            risks.append(f"Liquidity risk: {liquidity_analysis['liquidity_risk']}")
        
        return risks[:3]  # Top 3 risks 