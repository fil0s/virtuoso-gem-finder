#!/usr/bin/env python3
"""
Improved Normalized Scoring System for High Conviction Token Detector
Normalizes all scoring components to 0-100 scale with proper weighting
"""

import math
from typing import Dict, Any, Optional

class ImprovedTokenScorer:
    """
    Improved scoring system with proper normalization and market condition adaptability
    """
    
    def __init__(self, market_condition: str = "normal"):
        """
        Initialize scorer with market condition adjustments
        
        Args:
            market_condition: "bear", "normal", "bull" - adjusts thresholds accordingly
        """
        self.market_condition = market_condition
        self.thresholds = self._get_market_adjusted_thresholds()
        
    def _get_market_adjusted_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get market-condition adjusted thresholds"""
        
        base_thresholds = {
            "market_cap": {
                "excellent": 10_000_000,  # $10M
                "good": 1_000_000,        # $1M  
                "fair": 100_000,          # $100K
                "poor": 10_000            # $10K
            },
            "liquidity": {
                "excellent": 5_000_000,   # $5M
                "good": 500_000,          # $500K
                "fair": 100_000,          # $100K
                "poor": 10_000            # $10K
            },
            "holders": {
                "excellent": 10_000,
                "good": 1_000,
                "fair": 100,
                "poor": 10
            },
            "volume_24h": {
                "excellent": 1_000_000,   # $1M
                "good": 100_000,          # $100K
                "fair": 10_000,           # $10K
                "poor": 1_000             # $1K
            }
        }
        
        # Adjust thresholds based on market conditions
        if self.market_condition == "bear":
            # Lower thresholds in bear market
            multiplier = 0.3
        elif self.market_condition == "bull":
            # Higher thresholds in bull market
            multiplier = 2.0
        else:  # normal
            multiplier = 1.0
            
        adjusted_thresholds = {}
        for category, thresholds in base_thresholds.items():
            adjusted_thresholds[category] = {
                level: value * multiplier for level, value in thresholds.items()
            }
            
        return adjusted_thresholds
    
    def calculate_normalized_score(self, 
                                 candidate: Dict[str, Any],
                                 overview_data: Dict[str, Any],
                                 whale_analysis: Dict[str, Any],
                                 volume_price_analysis: Dict[str, Any],
                                 community_boost_analysis: Dict[str, Any],
                                 security_analysis: Dict[str, Any],
                                 trading_activity: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate normalized scores (0-100) for all components with equal weighting
        
        Returns:
            Dict with individual component scores and final weighted score
        """
        
        # Calculate individual component scores (all 0-100)
        scores = {
            "cross_platform_score": self._normalize_cross_platform_score(candidate),
            "market_fundamentals_score": self._calculate_market_fundamentals_score(overview_data),
            "whale_distribution_score": self._calculate_whale_distribution_score(whale_analysis),
            "momentum_score": self._calculate_momentum_score(volume_price_analysis, overview_data),
            "community_score": self._calculate_community_score(community_boost_analysis),
            "security_score": self._calculate_security_score(security_analysis),
            "trading_activity_score": self._calculate_trading_activity_score(trading_activity)
        }
        
        # Define component weights (should sum to 1.0)
        weights = {
            "cross_platform_score": 0.20,      # 20% - Multi-platform validation
            "market_fundamentals_score": 0.25,  # 25% - Market cap, liquidity, holders
            "whale_distribution_score": 0.15,   # 15% - Token distribution health
            "momentum_score": 0.20,             # 20% - Price/volume momentum
            "community_score": 0.10,            # 10% - Social presence
            "security_score": 0.05,             # 5% - Safety check
            "trading_activity_score": 0.05      # 5% - Recent trading
        }
        
        # Calculate weighted final score
        final_score = sum(scores[component] * weights[component] for component in scores.keys())
        
        # Add final score to results
        scores["final_score"] = final_score
        scores["market_condition"] = self.market_condition
        
        return scores
    
    def _normalize_cross_platform_score(self, candidate: Dict[str, Any]) -> float:
        """Normalize cross-platform score to 0-100"""
        base_score = candidate.get('cross_platform_score', 0)
        
        # Assume cross-platform scores typically range from 0-60
        # Normalize to 0-100 with sigmoid curve for better distribution
        normalized = (base_score / 60.0) * 100
        return min(100, max(0, normalized))
    
    def _calculate_market_fundamentals_score(self, overview_data: Dict[str, Any]) -> float:
        """Calculate market fundamentals score (0-100)"""
        if not overview_data:
            return 0
        
        # Extract metrics
        market_cap = overview_data.get('market_cap', 0)
        liquidity = overview_data.get('liquidity', 0)
        holders = overview_data.get('holders', 0)
        volume_24h = overview_data.get('volume_24h', 0)
        
        # Calculate individual scores using logarithmic scaling
        market_cap_score = self._log_scale_score(market_cap, self.thresholds['market_cap'])
        liquidity_score = self._log_scale_score(liquidity, self.thresholds['liquidity'])
        holders_score = self._log_scale_score(holders, self.thresholds['holders'])
        volume_score = self._log_scale_score(volume_24h, self.thresholds['volume_24h'])
        
        # Weighted average of fundamentals
        fundamental_score = (
            market_cap_score * 0.30 +    # 30% market cap
            liquidity_score * 0.30 +     # 30% liquidity
            holders_score * 0.25 +       # 25% holders
            volume_score * 0.15          # 15% volume
        )
        
        return fundamental_score
    
    def _calculate_whale_distribution_score(self, whale_analysis: Dict[str, Any]) -> float:
        """Calculate whale distribution health score (0-100)"""
        if not whale_analysis:
            return 50  # Neutral score if no data
        
        whale_concentration = whale_analysis.get('whale_concentration', 0)
        smart_money_detected = whale_analysis.get('smart_money_detected', False)
        total_holders = whale_analysis.get('total_holders', 0)
        
        # Optimal whale concentration is 20-40% (healthy distribution)
        if 20 <= whale_concentration <= 40:
            concentration_score = 100
        elif 10 <= whale_concentration <= 60:
            # Gradually decrease score as we move away from optimal range
            distance_from_optimal = min(abs(whale_concentration - 20), abs(whale_concentration - 40))
            concentration_score = 100 - (distance_from_optimal * 2)
        elif whale_concentration > 80:
            # Too concentrated - risky
            concentration_score = 10
        else:
            concentration_score = 50
        
        # Smart money bonus
        smart_money_bonus = 20 if smart_money_detected else 0
        
        # Holder count factor
        holder_factor = min(20, total_holders / 50)  # Up to 20 points for 1000+ holders
        
        whale_score = min(100, concentration_score + smart_money_bonus + holder_factor)
        return whale_score
    
    def _calculate_momentum_score(self, volume_price_analysis: Dict[str, Any], overview_data: Dict[str, Any]) -> float:
        """Calculate price and volume momentum score (0-100)"""
        momentum_score = 50  # Start neutral
        
        # Volume momentum
        if volume_price_analysis:
            volume_trend = volume_price_analysis.get('volume_trend', 'stable')
            price_momentum = volume_price_analysis.get('price_momentum', 'neutral')
            recent_volume_spike = volume_price_analysis.get('recent_volume_spike', False)
            
            # Volume trend scoring
            if volume_trend == 'increasing':
                momentum_score += 25
            elif volume_trend == 'stable':
                momentum_score += 10
            # decreasing gets no bonus
            
            # Price momentum scoring
            if price_momentum == 'bullish':
                momentum_score += 25
            elif price_momentum == 'neutral':
                momentum_score += 5
            # bearish gets no bonus
            
            # Volume spike bonus
            if recent_volume_spike:
                momentum_score += 10
        
        # Price change momentum from overview
        if overview_data:
            price_change_1h = overview_data.get('price_change_1h', 0)
            price_change_24h = overview_data.get('price_change_24h', 0)
            
            # 1-hour momentum (more weight for recent action)
            if price_change_1h > 20:
                momentum_score += 15
            elif price_change_1h > 10:
                momentum_score += 10
            elif price_change_1h > 5:
                momentum_score += 5
            elif price_change_1h < -10:
                momentum_score -= 10
            
            # 24-hour momentum
            if price_change_24h > 50:
                momentum_score += 10
            elif price_change_24h > 20:
                momentum_score += 5
            elif price_change_24h < -20:
                momentum_score -= 5
        
        return min(100, max(0, momentum_score))
    
    def _calculate_community_score(self, community_boost_analysis: Dict[str, Any]) -> float:
        """Calculate community strength score (0-100)"""
        if not community_boost_analysis:
            return 0
        
        # Social presence scoring
        has_website = community_boost_analysis.get('has_website', False)
        has_twitter = community_boost_analysis.get('has_twitter', False)
        has_telegram = community_boost_analysis.get('has_telegram', False)
        social_score = community_boost_analysis.get('social_score', 0)
        community_strength = community_boost_analysis.get('community_strength', 'unknown')
        
        community_score = 0
        
        # Basic social presence (40 points max)
        if has_website:
            community_score += 15
        if has_twitter:
            community_score += 15
        if has_telegram:
            community_score += 10
        
        # Community strength assessment (40 points max)
        if community_strength == 'strong':
            community_score += 40
        elif community_strength == 'moderate':
            community_score += 25
        elif community_strength == 'weak':
            community_score += 10
        
        # Social score bonus (20 points max)
        social_bonus = min(20, social_score * 3)
        community_score += social_bonus
        
        return min(100, community_score)
    
    def _calculate_security_score(self, security_analysis: Dict[str, Any]) -> float:
        """Calculate security score (0-100)"""
        if not security_analysis:
            return 80  # Assume safe if no data
        
        base_security_score = security_analysis.get('security_score', 100)
        risk_factors = security_analysis.get('risk_factors', [])
        is_scam = security_analysis.get('is_scam', False)
        is_risky = security_analysis.get('is_risky', False)
        
        # Start with base score
        security_score = base_security_score
        
        # Penalize risk factors
        security_score -= len(risk_factors) * 10
        
        # Major penalties
        if is_scam:
            security_score = 0
        elif is_risky:
            security_score *= 0.5
        
        return min(100, max(0, security_score))
    
    def _calculate_trading_activity_score(self, trading_activity: Dict[str, Any]) -> float:
        """Calculate trading activity score (0-100)"""
        if not trading_activity:
            return 30  # Low but not zero for no data
        
        total_transactions = trading_activity.get('total_transactions', 0)
        buy_sell_ratio = trading_activity.get('buy_sell_ratio', 0)
        trading_frequency = trading_activity.get('trading_frequency', 'low')
        recent_activity_score = trading_activity.get('recent_activity_score', 0)
        
        activity_score = 0
        
        # Transaction count scoring (40 points max)
        if total_transactions >= 50:
            activity_score += 40
        elif total_transactions >= 20:
            activity_score += 30
        elif total_transactions >= 10:
            activity_score += 20
        elif total_transactions >= 5:
            activity_score += 10
        
        # Buy/sell ratio scoring (30 points max)
        if buy_sell_ratio > 2.0:  # Strong buy pressure
            activity_score += 30
        elif buy_sell_ratio > 1.5:
            activity_score += 20
        elif buy_sell_ratio > 1.0:
            activity_score += 10
        elif buy_sell_ratio > 0.5:
            activity_score += 5
        # Heavy selling gets no points
        
        # Trading frequency (20 points max)
        if trading_frequency == 'high':
            activity_score += 20
        elif trading_frequency == 'medium':
            activity_score += 15
        elif trading_frequency == 'low':
            activity_score += 5
        
        # Recent activity bonus (10 points max)
        activity_bonus = min(10, recent_activity_score / 10)
        activity_score += activity_bonus
        
        return min(100, activity_score)
    
    def _log_scale_score(self, value: float, thresholds: Dict[str, float]) -> float:
        """Apply logarithmic scaling for better score distribution"""
        if value <= 0:
            return 0
        
        # Use logarithmic scaling to handle wide value ranges
        log_value = math.log10(max(1, value))
        
        # Define log thresholds
        log_thresholds = {
            level: math.log10(max(1, threshold)) 
            for level, threshold in thresholds.items()
        }
        
        if log_value >= log_thresholds['excellent']:
            return 100
        elif log_value >= log_thresholds['good']:
            # Linear interpolation between good and excellent
            ratio = (log_value - log_thresholds['good']) / (log_thresholds['excellent'] - log_thresholds['good'])
            return 80 + (ratio * 20)
        elif log_value >= log_thresholds['fair']:
            # Linear interpolation between fair and good
            ratio = (log_value - log_thresholds['fair']) / (log_thresholds['good'] - log_thresholds['fair'])
            return 50 + (ratio * 30)
        elif log_value >= log_thresholds['poor']:
            # Linear interpolation between poor and fair
            ratio = (log_value - log_thresholds['poor']) / (log_thresholds['fair'] - log_thresholds['poor'])
            return 20 + (ratio * 30)
        else:
            # Below poor threshold
            ratio = log_value / log_thresholds['poor']
            return ratio * 20
    
    def get_conviction_level(self, final_score: float) -> str:
        """Get conviction level based on final score"""
        if final_score >= 80:
            return "VERY HIGH"
        elif final_score >= 60:
            return "HIGH" 
        elif final_score >= 40:
            return "MODERATE"
        elif final_score >= 20:
            return "LOW"
        else:
            return "VERY LOW"
    
    def get_recommended_thresholds(self) -> Dict[str, float]:
        """Get recommended alert thresholds based on market conditions"""
        if self.market_condition == "bear":
            return {
                "high_conviction": 45.0,
                "moderate_conviction": 30.0,
                "low_conviction": 15.0
            }
        elif self.market_condition == "bull":
            return {
                "high_conviction": 70.0,
                "moderate_conviction": 50.0,
                "low_conviction": 30.0
            }
        else:  # normal
            return {
                "high_conviction": 60.0,
                "moderate_conviction": 40.0,
                "low_conviction": 20.0
            }


def demonstrate_improved_scoring():
    """Demonstrate the improved scoring system"""
    
    print("🎯" * 80)
    print("🎯 IMPROVED NORMALIZED SCORING SYSTEM DEMONSTRATION")
    print("🎯" * 80)
    
    # Create scorers for different market conditions
    bear_scorer = ImprovedTokenScorer("bear")
    normal_scorer = ImprovedTokenScorer("normal")
    bull_scorer = ImprovedTokenScorer("bull")
    
    # Example token data (simulating your discovered tokens)
    example_candidate = {
        'cross_platform_score': 35.0,
        'symbol': 'EXAMPLE',
        'platforms': ['dexscreener', 'birdeye']
    }
    
    example_overview = {
        'market_cap': 75000,      # $75K
        'liquidity': 25000,       # $25K  
        'holders': 150,
        'volume_24h': 15000,      # $15K
        'price_change_1h': 8.5,   # +8.5%
        'price_change_24h': 15.2  # +15.2%
    }
    
    example_whale = {
        'whale_concentration': 35.0,  # 35% - good range
        'smart_money_detected': False,
        'total_holders': 150
    }
    
    example_volume = {
        'volume_trend': 'increasing',
        'price_momentum': 'bullish',
        'recent_volume_spike': True
    }
    
    example_community = {
        'has_website': True,
        'has_twitter': True,
        'has_telegram': False,
        'social_score': 5,
        'community_strength': 'moderate'
    }
    
    example_security = {
        'security_score': 95,
        'risk_factors': [],
        'is_scam': False,
        'is_risky': False
    }
    
    example_trading = {
        'total_transactions': 25,
        'buy_sell_ratio': 1.8,
        'trading_frequency': 'medium',
        'recent_activity_score': 60
    }
    
    print(f"\n📊 EXAMPLE TOKEN ANALYSIS:")
    print(f"Symbol: {example_candidate['symbol']}")
    print(f"Market Cap: ${example_overview['market_cap']:,}")
    print(f"Liquidity: ${example_overview['liquidity']:,}")
    print(f"Holders: {example_overview['holders']:,}")
    print(f"24h Volume: ${example_overview['volume_24h']:,}")
    print(f"Price Change 1h: +{example_overview['price_change_1h']:.1f}%")
    print(f"Price Change 24h: +{example_overview['price_change_24h']:.1f}%")
    
    # Calculate scores for different market conditions
    for market_condition, scorer in [("BEAR", bear_scorer), ("NORMAL", normal_scorer), ("BULL", bull_scorer)]:
        print(f"\n" + "="*60)
        print(f"📈 {market_condition} MARKET SCORING")
        print("="*60)
        
        scores = scorer.calculate_normalized_score(
            example_candidate, example_overview, example_whale,
            example_volume, example_community, example_security, example_trading
        )
        
        print(f"\n🔍 COMPONENT SCORES (0-100):")
        print(f"  📊 Cross-Platform Score: {scores['cross_platform_score']:.1f}")
        print(f"  💰 Market Fundamentals: {scores['market_fundamentals_score']:.1f}")
        print(f"  🐋 Whale Distribution: {scores['whale_distribution_score']:.1f}")
        print(f"  📈 Momentum Score: {scores['momentum_score']:.1f}")
        print(f"  👥 Community Score: {scores['community_score']:.1f}")
        print(f"  🔒 Security Score: {scores['security_score']:.1f}")
        print(f"  💹 Trading Activity: {scores['trading_activity_score']:.1f}")
        
        final_score = scores['final_score']
        conviction_level = scorer.get_conviction_level(final_score)
        
        print(f"\n🎯 FINAL SCORE: {final_score:.1f}/100")
        print(f"🎯 CONVICTION LEVEL: {conviction_level}")
        
        # Show recommended thresholds
        thresholds = scorer.get_recommended_thresholds()
        print(f"\n📋 RECOMMENDED THRESHOLDS:")
        for level, threshold in thresholds.items():
            status = "✅ ALERT" if final_score >= threshold else "❌ NO ALERT"
            print(f"  • {level.replace('_', ' ').title()}: {threshold:.1f} - {status}")
    
    print(f"\n🎯" * 80)
    print(f"🎯 KEY IMPROVEMENTS:")
    print(f"  ✅ All components normalized to 0-100 scale")
    print(f"  ✅ Proper weighting system (totals 100%)")
    print(f"  ✅ Market condition adaptability")
    print(f"  ✅ Logarithmic scaling for wide value ranges")
    print(f"  ✅ More intuitive conviction levels")
    print(f"  ✅ Recommended thresholds per market condition")
    print(f"🎯" * 80)


if __name__ == "__main__":
    demonstrate_improved_scoring() 