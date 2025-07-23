#!/usr/bin/env python3
"""
VLR Intelligence Module - Shared VLR Analysis for Token Discovery Systems
========================================================================

Provides comprehensive VLR (Volume-to-Liquidity Ratio) analysis capabilities
for integration into token discovery and analysis systems.

Features:
- VLR calculation and categorization
- Gem hunting analysis
- Pump & dump detection
- LP attractiveness scoring
- Position sizing recommendations
- Risk assessment and alerts
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class VLRCategory(Enum):
    """VLR optimization categories"""
    GEM_DISCOVERY = "🔍 Gem Discovery"      # VLR 0.5-2.0
    MOMENTUM_BUILD = "🚀 Momentum Building"  # VLR 2.0-5.0
    PEAK_PERFORMANCE = "💰 Peak Performance" # VLR 5.0-10.0
    DANGER_ZONE = "⚠️ Danger Zone"         # VLR 10.0-20.0
    MANIPULATION = "🚨 Manipulation"        # VLR >20.0

class GemStage(Enum):
    """Gem classification stages based on VLR"""
    EMBRYO = "🥚 Embryo"          # VLR 0.1-0.5
    SEEDLING = "🌱 Seedling"      # VLR 0.5-1.0
    ROCKET = "🚀 Rocket"          # VLR 1.0-3.0
    DIAMOND = "💎 Diamond"        # VLR 3.0-7.0
    SUPERNOVA = "🔥 Supernova"    # VLR 7.0-15.0
    COLLAPSE = "💥 Collapse"      # VLR 15.0+

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class VLRAnalysis:
    """Complete VLR analysis result"""
    address: str
    symbol: str
    vlr: float
    category: VLRCategory
    gem_stage: GemStage
    risk_level: RiskLevel
    gem_potential: str
    lp_attractiveness: float
    expected_apy: float
    position_recommendation: str
    risk_warnings: List[str]
    investment_strategy: str
    monitoring_frequency: str
    entry_trigger: str
    exit_trigger: str
    
class VLRIntelligence:
    """Comprehensive VLR intelligence analysis system"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # VLR thresholds for categories
        self.vlr_thresholds = {
            VLRCategory.GEM_DISCOVERY: (0.5, 2.0),
            VLRCategory.MOMENTUM_BUILD: (2.0, 5.0),
            VLRCategory.PEAK_PERFORMANCE: (5.0, 10.0),
            VLRCategory.DANGER_ZONE: (10.0, 20.0),
            VLRCategory.MANIPULATION: (20.0, float('inf'))
        }
        
        # Gem stage thresholds
        self.gem_thresholds = {
            GemStage.EMBRYO: (0.1, 0.5),
            GemStage.SEEDLING: (0.5, 1.0),
            GemStage.ROCKET: (1.0, 3.0),
            GemStage.DIAMOND: (3.0, 7.0),
            GemStage.SUPERNOVA: (7.0, 15.0),
            GemStage.COLLAPSE: (15.0, float('inf'))
        }
        
        self.logger.info("🧠 VLR Intelligence module initialized")
    
    def calculate_vlr(self, volume_24h: float, liquidity: float) -> float:
        """Calculate Volume-to-Liquidity Ratio"""
        if liquidity <= 0:
            return 0.0
        return volume_24h / liquidity
    
    def classify_vlr_category(self, vlr: float) -> VLRCategory:
        """Classify VLR into optimization category"""
        if vlr >= 20.0:
            return VLRCategory.MANIPULATION
        elif vlr >= 10.0:
            return VLRCategory.DANGER_ZONE
        elif vlr >= 5.0:
            return VLRCategory.PEAK_PERFORMANCE
        elif vlr >= 2.0:
            return VLRCategory.MOMENTUM_BUILD
        else:
            return VLRCategory.GEM_DISCOVERY
    
    def classify_gem_stage(self, vlr: float) -> GemStage:
        """Classify gem stage based on VLR"""
        if vlr >= 15.0:
            return GemStage.COLLAPSE
        elif vlr >= 7.0:
            return GemStage.SUPERNOVA
        elif vlr >= 3.0:
            return GemStage.DIAMOND
        elif vlr >= 1.0:
            return GemStage.ROCKET
        elif vlr >= 0.5:
            return GemStage.SEEDLING
        else:
            return GemStage.EMBRYO
    
    def assess_risk_level(self, vlr: float, liquidity: float, volume: float) -> RiskLevel:
        """Assess risk level based on VLR and other factors"""
        if vlr >= 20.0:
            return RiskLevel.CRITICAL
        elif vlr >= 10.0:
            return RiskLevel.HIGH
        elif vlr >= 5.0 and liquidity < 100_000:
            return RiskLevel.HIGH  # High VLR with low liquidity is risky
        elif vlr >= 5.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def assess_gem_potential(self, vlr: float, liquidity: float, volume: float, 
                           market_cap: float = 0) -> str:
        """Assess gem potential based on multiple factors"""
        # Ideal gem criteria: good VLR, decent liquidity, reasonable market cap
        if (0.5 <= vlr <= 3.0 and 
            100_000 <= liquidity <= 5_000_000 and
            volume > 50_000 and
            (market_cap == 0 or market_cap < 50_000_000)):
            return 'HIGH'
        elif (0.3 <= vlr <= 5.0 and 
              liquidity > 50_000 and
              volume > 25_000):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def calculate_lp_attractiveness(self, vlr: float, liquidity: float, 
                                  volume: float) -> float:
        """Calculate liquidity provision attractiveness score (0-100)"""
        base_score = min(vlr * 15, 100)  # Base score from VLR
        
        # Liquidity bonus (prefer pools with good liquidity)
        if liquidity >= 1_000_000:
            liquidity_bonus = 10
        elif liquidity >= 500_000:
            liquidity_bonus = 5
        elif liquidity >= 100_000:
            liquidity_bonus = 0
        else:
            liquidity_bonus = -10  # Penalty for low liquidity
        
        # Volume consistency bonus
        if volume >= 1_000_000:
            volume_bonus = 5
        elif volume >= 500_000:
            volume_bonus = 2
        else:
            volume_bonus = 0
        
        # Risk adjustment
        if vlr > 15.0:
            risk_penalty = -30  # High manipulation risk
        elif vlr > 10.0:
            risk_penalty = -15  # High volatility risk
        else:
            risk_penalty = 0
        
        final_score = base_score + liquidity_bonus + volume_bonus + risk_penalty
        return max(0, min(100, final_score))
    
    def calculate_expected_apy(self, vlr: float, fee_rate: float = 0.003) -> float:
        """Calculate expected APY from fee generation"""
        # Simplified APY calculation: VLR * 365 * fee_rate * 100
        return vlr * 365 * fee_rate * 100
    
    def get_position_recommendation(self, category: VLRCategory, 
                                  risk_level: RiskLevel) -> str:
        """Get position sizing recommendation"""
        if category == VLRCategory.PEAK_PERFORMANCE and risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            return "20-40% of LP allocation"
        elif category == VLRCategory.MOMENTUM_BUILD and risk_level == RiskLevel.LOW:
            return "10-25% of allocation"
        elif category == VLRCategory.MOMENTUM_BUILD:
            return "5-15% of allocation"
        elif category == VLRCategory.GEM_DISCOVERY:
            return "2-10% of allocation"
        elif category in [VLRCategory.DANGER_ZONE, VLRCategory.MANIPULATION]:
            return "AVOID - High risk"
        else:
            return "1-5% of allocation"
    
    def get_investment_strategy(self, category: VLRCategory, gem_stage: GemStage) -> str:
        """Get investment strategy recommendation"""
        if category == VLRCategory.PEAK_PERFORMANCE:
            return "STRONG BUY - LP Position for optimal fee generation"
        elif category == VLRCategory.MOMENTUM_BUILD:
            return "BUY - Growth position with momentum confirmation"
        elif category == VLRCategory.GEM_DISCOVERY:
            if gem_stage in [GemStage.SEEDLING, GemStage.ROCKET]:
                return "ACCUMULATE - Early entry with potential upside"
            else:
                return "RESEARCH - Monitor for breakout signals"
        elif category == VLRCategory.DANGER_ZONE:
            return "CAUTION - High volatility, consider exit"
        else:  # MANIPULATION
            return "AVOID - Manipulation risk detected"
    
    def get_monitoring_frequency(self, category: VLRCategory, risk_level: RiskLevel) -> str:
        """Get recommended monitoring frequency"""
        if category == VLRCategory.MANIPULATION or risk_level == RiskLevel.CRITICAL:
            return "Every 5-15 minutes"
        elif category == VLRCategory.DANGER_ZONE or risk_level == RiskLevel.HIGH:
            return "Every 30-60 minutes"
        elif category == VLRCategory.PEAK_PERFORMANCE:
            return "Every 2-4 hours"
        elif category == VLRCategory.MOMENTUM_BUILD:
            return "Every 4-8 hours"
        else:  # GEM_DISCOVERY
            return "Daily"
    
    def get_entry_trigger(self, category: VLRCategory, vlr: float) -> str:
        """Get entry trigger recommendation"""
        if category == VLRCategory.GEM_DISCOVERY:
            return f"VLR breakout above 2.0 (current: {vlr:.2f})"
        elif category == VLRCategory.MOMENTUM_BUILD:
            return f"VLR confirmation above 3.0 (current: {vlr:.2f})"
        elif category == VLRCategory.PEAK_PERFORMANCE:
            return f"Immediate entry - optimal range (current: {vlr:.2f})"
        else:
            return "DO NOT ENTER"
    
    def get_exit_trigger(self, category: VLRCategory, vlr: float) -> str:
        """Get exit trigger recommendation"""
        if category == VLRCategory.PEAK_PERFORMANCE:
            return f"VLR decline below 4.0 or above 12.0"
        elif category == VLRCategory.MOMENTUM_BUILD:
            return f"VLR decline below 1.5 or above 8.0"
        elif category == VLRCategory.GEM_DISCOVERY:
            return f"VLR decline below 0.3 or above 5.0"
        else:
            return "EXIT IMMEDIATELY"
    
    def generate_risk_warnings(self, vlr: float, category: VLRCategory, 
                             liquidity: float, volume: float) -> List[str]:
        """Generate specific risk warnings"""
        warnings = []
        
        if category == VLRCategory.MANIPULATION:
            warnings.append("🚨 CRITICAL: Manipulation pattern detected")
            warnings.append("💀 Extreme pump & dump risk")
            warnings.append("🚫 DO NOT ENTER - Exit any existing positions")
        
        elif category == VLRCategory.DANGER_ZONE:
            warnings.append("⚠️ HIGH RISK: Extreme volatility detected")
            warnings.append("📉 Potential for rapid price swings")
            warnings.append("🔍 Monitor closely for exit signals")
        
        elif vlr > 8.0 and category == VLRCategory.PEAK_PERFORMANCE:
            warnings.append("⚠️ VLR approaching danger zone")
            warnings.append("📊 Consider partial profit taking")
        
        if liquidity < 100_000:
            warnings.append("💧 Low liquidity - High slippage risk")
        
        if volume > liquidity * 50:  # Extreme volume spike
            warnings.append("📈 Extreme volume spike - Monitor for manipulation")
        
        return warnings
    
    def analyze_token_vlr(self, token_data: Dict[str, Any]) -> VLRAnalysis:
        """Perform comprehensive VLR analysis on a token"""
        # Extract data
        address = token_data.get('address', '')
        symbol = token_data.get('symbol', 'Unknown')
        volume_24h = float(token_data.get('volume_24h', 0))
        liquidity = float(token_data.get('liquidity', 0))
        market_cap = float(token_data.get('market_cap', 0))
        
        # Calculate VLR
        vlr = self.calculate_vlr(volume_24h, liquidity)
        
        # Classify
        category = self.classify_vlr_category(vlr)
        gem_stage = self.classify_gem_stage(vlr)
        risk_level = self.assess_risk_level(vlr, liquidity, volume_24h)
        
        # Assess potential
        gem_potential = self.assess_gem_potential(vlr, liquidity, volume_24h, market_cap)
        lp_attractiveness = self.calculate_lp_attractiveness(vlr, liquidity, volume_24h)
        expected_apy = self.calculate_expected_apy(vlr)
        
        # Generate recommendations
        position_recommendation = self.get_position_recommendation(category, risk_level)
        investment_strategy = self.get_investment_strategy(category, gem_stage)
        monitoring_frequency = self.get_monitoring_frequency(category, risk_level)
        entry_trigger = self.get_entry_trigger(category, vlr)
        exit_trigger = self.get_exit_trigger(category, vlr)
        risk_warnings = self.generate_risk_warnings(vlr, category, liquidity, volume_24h)
        
        return VLRAnalysis(
            address=address,
            symbol=symbol,
            vlr=vlr,
            category=category,
            gem_stage=gem_stage,
            risk_level=risk_level,
            gem_potential=gem_potential,
            lp_attractiveness=lp_attractiveness,
            expected_apy=expected_apy,
            position_recommendation=position_recommendation,
            risk_warnings=risk_warnings,
            investment_strategy=investment_strategy,
            monitoring_frequency=monitoring_frequency,
            entry_trigger=entry_trigger,
            exit_trigger=exit_trigger
        )
    
    def batch_analyze_vlr(self, tokens_data: List[Dict[str, Any]]) -> List[VLRAnalysis]:
        """Perform VLR analysis on multiple tokens"""
        analyses = []
        
        for token_data in tokens_data:
            try:
                analysis = self.analyze_token_vlr(token_data)
                analyses.append(analysis)
            except Exception as e:
                self.logger.warning(f"⚠️ VLR analysis failed for {token_data.get('symbol', 'Unknown')}: {e}")
                continue
        
        # Sort by VLR score
        analyses.sort(key=lambda x: x.vlr, reverse=True)
        return analyses
    
    def categorize_opportunities(self, analyses: List[VLRAnalysis]) -> Dict[VLRCategory, List[VLRAnalysis]]:
        """Categorize VLR analyses by opportunity type"""
        categorized = {category: [] for category in VLRCategory}
        
        for analysis in analyses:
            categorized[analysis.category].append(analysis)
        
        return categorized
    
    def get_top_opportunities(self, analyses: List[VLRAnalysis], 
                            target_categories: List[VLRCategory] = None,
                            limit: int = 5) -> List[VLRAnalysis]:
        """Get top VLR opportunities from specific categories"""
        if target_categories is None:
            target_categories = [VLRCategory.PEAK_PERFORMANCE, VLRCategory.MOMENTUM_BUILD]
        
        opportunities = [a for a in analyses if a.category in target_categories]
        opportunities.sort(key=lambda x: x.vlr, reverse=True)
        
        return opportunities[:limit]
    
    def generate_vlr_summary(self, analyses: List[VLRAnalysis]) -> Dict[str, Any]:
        """Generate comprehensive VLR analysis summary"""
        if not analyses:
            return {'error': 'No analyses provided'}
        
        categorized = self.categorize_opportunities(analyses)
        
        summary = {
            'total_tokens': len(analyses),
            'category_breakdown': {},
            'top_opportunities': self.get_top_opportunities(analyses),
            'gem_candidates': [a for a in analyses if a.gem_potential == 'HIGH'],
            'risk_alerts': [a for a in analyses if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]],
            'average_vlr': sum(a.vlr for a in analyses) / len(analyses),
            'vlr_range': (min(a.vlr for a in analyses), max(a.vlr for a in analyses))
        }
        
        # Category breakdown
        for category, tokens in categorized.items():
            if tokens:
                summary['category_breakdown'][category.value] = {
                    'count': len(tokens),
                    'avg_vlr': sum(t.vlr for t in tokens) / len(tokens),
                    'top_tokens': tokens[:3]
                }
        
        return summary
    
    def format_vlr_alert(self, analysis: VLRAnalysis) -> str:
        """Format VLR analysis for alert/notification"""
        alert = f"🎯 VLR OPPORTUNITY: {analysis.symbol}\n"
        alert += f"📊 VLR: {analysis.vlr:.2f} | {analysis.category.value}\n"
        alert += f"💎 Stage: {analysis.gem_stage.value}\n"
        alert += f"💰 Expected APY: {analysis.expected_apy:.0f}%\n"
        alert += f"📋 Strategy: {analysis.investment_strategy}\n"
        alert += f"💸 Position: {analysis.position_recommendation}\n"
        
        if analysis.risk_warnings:
            alert += f"\n⚠️ WARNINGS:\n"
            for warning in analysis.risk_warnings:
                alert += f"   • {warning}\n"
        
        return alert

# Convenience functions for easy integration
def analyze_token_vlr_simple(token_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple VLR analysis function for easy integration"""
    vlr_intel = VLRIntelligence()
    analysis = vlr_intel.analyze_token_vlr(token_data)
    
    return {
        'vlr': analysis.vlr,
        'category': analysis.category.value,
        'gem_stage': analysis.gem_stage.value,
        'risk_level': analysis.risk_level.value,
        'gem_potential': analysis.gem_potential,
        'lp_attractiveness': analysis.lp_attractiveness,
        'expected_apy': analysis.expected_apy,
        'position_recommendation': analysis.position_recommendation,
        'investment_strategy': analysis.investment_strategy,
        'risk_warnings': analysis.risk_warnings
    }

def get_vlr_category(vlr: float) -> str:
    """Quick VLR category classification"""
    vlr_intel = VLRIntelligence()
    category = vlr_intel.classify_vlr_category(vlr)
    return category.value

def calculate_vlr_score(volume_24h: float, liquidity: float) -> float:
    """Quick VLR calculation"""
    vlr_intel = VLRIntelligence()
    return vlr_intel.calculate_vlr(volume_24h, liquidity) 