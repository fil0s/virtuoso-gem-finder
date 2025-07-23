#!/usr/bin/env python3
"""
🧠 INTERACTION-BASED SCORING SYSTEM

Addresses the fundamental mathematical flaw of linear additivity in token analysis.
Implements sophisticated factor interactions, danger detection, and signal amplification.

Key Features:
- DANGER AMPLIFICATION: Bad factors making each other worse (e.g., high VLR + low liquidity = manipulation)
- SIGNAL AMPLIFICATION: Good factors reinforcing each other (e.g., smart money + volume = conviction multiplier)
- CONTRADICTION DETECTION: Conflicting signals requiring careful analysis
- EMERGENT PATTERN RECOGNITION: Complex multi-factor interactions

Mathematical Foundation:
- Replaces: final_score = sum(factors) [LINEAR - WRONG]
- With: final_score = f(factor_interactions, amplifications, contradictions) [NON-LINEAR - CORRECT]
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path
import json
from datetime import datetime

class InteractionType(Enum):
    """Types of factor interactions"""
    DANGER_AMPLIFICATION = "danger_amplification"
    SIGNAL_AMPLIFICATION = "signal_amplification" 
    CONTRADICTION = "contradiction"
    NEUTRAL = "neutral"

class RiskLevel(Enum):
    """Risk assessment levels"""
    CRITICAL = "CRITICAL"  # Immediate avoidance required
    HIGH = "HIGH"         # Extreme caution
    MEDIUM = "MEDIUM"     # Careful analysis needed
    LOW = "LOW"           # Standard due diligence

@dataclass
class FactorValues:
    """Normalized factor values (0-1 scale for calculations)"""
    vlr_ratio: float = 0.0           # Volume-to-Liquidity Ratio (normalized)
    liquidity: float = 0.0           # Liquidity depth (normalized)
    smart_money_score: float = 0.0   # Smart money detection (0-1)
    volume_momentum: float = 0.0     # Volume trend momentum (0-1)
    security_score: float = 0.0      # Security assessment (0-1)
    whale_concentration: float = 0.0  # Whale concentration (0-1)
    price_momentum: float = 0.0      # Price momentum (0-1)
    cross_platform_validation: float = 0.0  # Multi-platform validation (0-1)
    age_factor: float = 0.0          # Token age appropriateness (0-1)
    
    # Raw values for detailed analysis
    raw_vlr: float = 0.0
    raw_liquidity: float = 0.0
    raw_volume_24h: float = 0.0
    platforms_count: int = 0

@dataclass
class InteractionResult:
    """Result of factor interaction analysis"""
    interaction_type: InteractionType
    risk_level: RiskLevel
    score_modifier: float  # Multiplier or override value
    confidence: float     # Confidence in the interaction (0-1)
    explanation: str      # Human-readable explanation
    factors_involved: List[str]  # Which factors triggered this interaction
    override_linear: bool = False  # Whether to completely override linear scoring

class InteractionBasedScorer:
    """
    Advanced token scoring system using factor interactions instead of linear additivity.
    
    This addresses the fundamental mathematical flaw where traditional systems assume:
    Score = Factor1 + Factor2 + Factor3 + ... (WRONG)
    
    Instead implements:
    Score = f(factor_interactions, amplifications, contradictions, emergent_patterns)
    """
    
    def __init__(self, debug_mode: bool = False):
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        
        # Thresholds for interaction detection
        self.interaction_thresholds = {
            'manipulation_vlr_threshold': 10.0,      # VLR above this = manipulation risk
            'low_liquidity_threshold': 50000,       # Below this = liquidity risk
            'smart_money_threshold': 0.3,           # Above this = smart money detected
            'volume_surge_threshold': 0.7,          # Above this = volume surge
            'whale_dominance_threshold': 0.8,       # Above this = whale dominance
            'security_risk_threshold': 0.3,         # Below this = security risk
            'platform_validation_threshold': 0.5    # Above this = well validated
        }
        
        # Interaction weights for different scenarios
        self.interaction_weights = {
            'danger_override_weight': 0.05,    # Danger interactions get very low scores
            'amplification_multiplier': 1.8,   # Amplification multiplies by this factor
            'contradiction_dampener': 0.7,     # Contradictions reduce scores
            'neutral_baseline': 1.0            # Neutral interactions use baseline
        }
        
        # Store interaction history for analysis
        self.interaction_history: List[Dict[str, Any]] = []
    
    def calculate_interaction_based_score(self, factors: FactorValues, 
                                        traditional_components: Dict[str, float]) -> Tuple[float, Dict[str, Any]]:
        """
        Main entry point: Calculate score using factor interactions instead of linear addition.
        
        Args:
            factors: Normalized factor values (0-1 scale)
            traditional_components: Traditional component scores for comparison
            
        Returns:
            Tuple of (final_score, detailed_analysis)
        """
        try:
            # Step 1: Detect all factor interactions
            interactions = self._detect_factor_interactions(factors)
            
            # Step 2: Calculate base score from traditional components (as starting point)
            base_score = self._calculate_traditional_baseline(traditional_components)
            
            # Step 3: Apply interaction-based modifications
            final_score, interaction_analysis = self._apply_interaction_modifications(
                base_score, interactions, factors
            )
            
            # Step 4: Generate detailed analysis
            detailed_analysis = self._generate_interaction_analysis(
                factors, interactions, base_score, final_score, traditional_components
            )
            
            # Step 5: Record for historical analysis
            self._record_interaction_event(factors, interactions, final_score)
            
            return final_score, detailed_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in interaction-based scoring: {e}")
            # Fallback to traditional scoring
            fallback_score = sum(traditional_components.values())
            return fallback_score, {'error': str(e), 'fallback_used': True}
    
    def _detect_factor_interactions(self, factors: FactorValues) -> List[InteractionResult]:
        """
        Detect all types of factor interactions.
        
        This is the core innovation - instead of treating factors as independent,
        we analyze how they interact with each other.
        """
        interactions = []
        
        # CRITICAL DANGER INTERACTIONS (Override everything else)
        danger_interactions = self._detect_danger_interactions(factors)
        interactions.extend(danger_interactions)
        
        # If critical dangers detected, skip other analysis
        if any(i.risk_level == RiskLevel.CRITICAL for i in danger_interactions):
            return interactions
        
        # SIGNAL AMPLIFICATION INTERACTIONS
        amplification_interactions = self._detect_signal_amplifications(factors)
        interactions.extend(amplification_interactions)
        
        # CONTRADICTION INTERACTIONS
        contradiction_interactions = self._detect_contradictions(factors)
        interactions.extend(contradiction_interactions)
        
        # EMERGENT PATTERN INTERACTIONS
        emergent_interactions = self._detect_emergent_patterns(factors)
        interactions.extend(emergent_interactions)
        
        return interactions
    
    def _detect_danger_interactions(self, factors: FactorValues) -> List[InteractionResult]:
        """
        Detect dangerous factor combinations that should override linear scoring.
        
        These are the "false positive" scenarios where linear scoring fails.
        """
        dangers = []
        
        # DANGER 1: High VLR + Low Liquidity = MANIPULATION DETECTED
        if (factors.raw_vlr > self.interaction_thresholds['manipulation_vlr_threshold'] and 
            factors.raw_liquidity < self.interaction_thresholds['low_liquidity_threshold']):
            
            dangers.append(InteractionResult(
                interaction_type=InteractionType.DANGER_AMPLIFICATION,
                risk_level=RiskLevel.CRITICAL,
                score_modifier=0.05,  # Override to 5% of calculated score
                confidence=0.95,
                explanation=f"🚨 PUMP & DUMP DETECTED: VLR {factors.raw_vlr:.1f} with liquidity ${factors.raw_liquidity:,.0f} indicates manipulation",
                factors_involved=['vlr_ratio', 'liquidity'],
                override_linear=True
            ))
        
        # DANGER 2: Poor Security + High Whale Concentration = RUG PULL SETUP
        if (factors.security_score < self.interaction_thresholds['security_risk_threshold'] and 
            factors.whale_concentration > self.interaction_thresholds['whale_dominance_threshold']):
            
            dangers.append(InteractionResult(
                interaction_type=InteractionType.DANGER_AMPLIFICATION,
                risk_level=RiskLevel.CRITICAL,
                score_modifier=0.03,  # Override to 3% of calculated score
                confidence=0.90,
                explanation=f"🚨 RUG PULL SETUP: Poor security ({factors.security_score:.1f}) + whale dominance ({factors.whale_concentration:.1f}) = high rug risk",
                factors_involved=['security_score', 'whale_concentration'],
                override_linear=True
            ))
        
        # DANGER 3: High Volume + No Smart Money + Low Platform Validation = BOT TRADING
        if (factors.volume_momentum > 0.8 and 
            factors.smart_money_score < 0.1 and 
            factors.cross_platform_validation < 0.3):
            
            dangers.append(InteractionResult(
                interaction_type=InteractionType.DANGER_AMPLIFICATION,
                risk_level=RiskLevel.HIGH,
                score_modifier=0.15,  # Heavily penalize
                confidence=0.80,
                explanation=f"⚠️ BOT TRADING DETECTED: High volume without smart money or platform validation suggests artificial activity",
                factors_involved=['volume_momentum', 'smart_money_score', 'cross_platform_validation'],
                override_linear=False
            ))
        
        # DANGER 4: Extreme VLR = Pure Manipulation
        if factors.raw_vlr > 20.0:
            dangers.append(InteractionResult(
                interaction_type=InteractionType.DANGER_AMPLIFICATION,
                risk_level=RiskLevel.CRITICAL,
                score_modifier=0.02,  # Nearly zero score
                confidence=0.98,
                explanation=f"🚨 EXTREME MANIPULATION: VLR {factors.raw_vlr:.1f} indicates active pump & dump",
                factors_involved=['vlr_ratio'],
                override_linear=True
            ))
        
        return dangers
    
    def _detect_signal_amplifications(self, factors: FactorValues) -> List[InteractionResult]:
        """
        Detect positive factor combinations that should amplify scores.
        
        These are the "true positive" scenarios where good factors reinforce each other.
        """
        amplifications = []
        
        # AMPLIFICATION 1: Smart Money + Volume Surge = CONVICTION MULTIPLIER
        if (factors.smart_money_score > self.interaction_thresholds['smart_money_threshold'] and 
            factors.volume_momentum > self.interaction_thresholds['volume_surge_threshold']):
            
            # Calculate amplification strength
            amplification_strength = min(2.0, 1.2 + (factors.smart_money_score * factors.volume_momentum))
            
            amplifications.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=amplification_strength,
                confidence=0.85,
                explanation=f"🚀 CONVICTION AMPLIFIER: Smart money ({factors.smart_money_score:.1f}) + volume surge ({factors.volume_momentum:.1f}) = {amplification_strength:.1f}x multiplier",
                factors_involved=['smart_money_score', 'volume_momentum'],
                override_linear=False
            ))
        
        # AMPLIFICATION 2: Optimal VLR + High Liquidity = LP GOLDMINE
        if (5.0 <= factors.raw_vlr <= 10.0 and factors.raw_liquidity > 500000):
            amplification_strength = 1.4 + (factors.liquidity * 0.3)
            
            amplifications.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=amplification_strength,
                confidence=0.80,
                explanation=f"💰 LP OPPORTUNITY: VLR {factors.raw_vlr:.1f} + liquidity ${factors.raw_liquidity:,.0f} = excellent LP target",
                factors_involved=['vlr_ratio', 'liquidity'],
                override_linear=False
            ))
        
        # AMPLIFICATION 3: Multi-Platform + Security + Healthy Distribution = TRIPLE VALIDATION
        if (factors.cross_platform_validation > 0.7 and 
            factors.security_score > 0.8 and 
            factors.whale_concentration < 0.6):
            
            amplifications.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=1.6,
                confidence=0.90,
                explanation=f"✅ TRIPLE VALIDATION: Platform validation + security + healthy distribution = high confidence",
                factors_involved=['cross_platform_validation', 'security_score', 'whale_concentration'],
                override_linear=False
            ))
        
        # AMPLIFICATION 4: Price Momentum + Volume + Smart Money = MOMENTUM SURGE
        if (factors.price_momentum > 0.6 and 
            factors.volume_momentum > 0.6 and 
            factors.smart_money_score > 0.4):
            
            surge_strength = 1.3 + (factors.price_momentum * factors.volume_momentum * 0.5)
            
            amplifications.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=surge_strength,
                confidence=0.75,
                explanation=f"📈 MOMENTUM SURGE: Price + volume + smart money alignment = {surge_strength:.1f}x multiplier",
                factors_involved=['price_momentum', 'volume_momentum', 'smart_money_score'],
                override_linear=False
            ))
        
        return amplifications
    
    def _detect_contradictions(self, factors: FactorValues) -> List[InteractionResult]:
        """
        Detect conflicting signals that require careful analysis.
        
        These are scenarios where factors send mixed messages.
        """
        contradictions = []
        
        # CONTRADICTION 1: Good Security + Terrible Whale Distribution
        if (factors.security_score > 0.8 and factors.whale_concentration > 0.9):
            contradictions.append(InteractionResult(
                interaction_type=InteractionType.CONTRADICTION,
                risk_level=RiskLevel.MEDIUM,
                score_modifier=0.7,  # Dampen the score
                confidence=0.70,
                explanation=f"⚖️ MIXED SIGNALS: Excellent security ({factors.security_score:.1f}) conflicts with whale dominance ({factors.whale_concentration:.1f})",
                factors_involved=['security_score', 'whale_concentration'],
                override_linear=False
            ))
        
        # CONTRADICTION 2: High Volume + Low Cross-Platform Validation
        if (factors.volume_momentum > 0.8 and factors.cross_platform_validation < 0.3):
            contradictions.append(InteractionResult(
                interaction_type=InteractionType.CONTRADICTION,
                risk_level=RiskLevel.MEDIUM,
                score_modifier=0.65,
                confidence=0.75,
                explanation=f"⚖️ VALIDATION CONFLICT: High volume ({factors.volume_momentum:.1f}) without platform validation ({factors.cross_platform_validation:.1f})",
                factors_involved=['volume_momentum', 'cross_platform_validation'],
                override_linear=False
            ))
        
        # CONTRADICTION 3: Smart Money + High Risk Factors
        if (factors.smart_money_score > 0.6 and factors.security_score < 0.4):
            contradictions.append(InteractionResult(
                interaction_type=InteractionType.CONTRADICTION,
                risk_level=RiskLevel.MEDIUM,
                score_modifier=0.8,
                confidence=0.65,
                explanation=f"⚖️ RISK PARADOX: Smart money interest ({factors.smart_money_score:.1f}) despite security concerns ({factors.security_score:.1f})",
                factors_involved=['smart_money_score', 'security_score'],
                override_linear=False
            ))
        
        return contradictions
    
    def _detect_emergent_patterns(self, factors: FactorValues) -> List[InteractionResult]:
        """
        Detect complex multi-factor patterns that emerge from combinations.
        
        These are sophisticated patterns that only appear when multiple factors align.
        """
        emergent = []
        
        # EMERGENT 1: The "Stealth Gem" Pattern
        # (Good fundamentals + Low attention + Organic growth)
        if (factors.security_score > 0.7 and 
            factors.cross_platform_validation < 0.4 and 
            1.0 <= factors.raw_vlr <= 3.0 and
            factors.whale_concentration < 0.5):
            
            emergent.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=1.5,
                confidence=0.70,
                explanation=f"💎 STEALTH GEM: Strong fundamentals with low attention = early discovery opportunity",
                factors_involved=['security_score', 'cross_platform_validation', 'vlr_ratio', 'whale_concentration'],
                override_linear=False
            ))
        
        # EMERGENT 2: The "Institutional Accumulation" Pattern
        # (Smart money + Rising volume + Stable VLR + Good security)
        if (factors.smart_money_score > 0.5 and 
            factors.volume_momentum > 0.4 and 
            2.0 <= factors.raw_vlr <= 8.0 and
            factors.security_score > 0.6):
            
            emergent.append(InteractionResult(
                interaction_type=InteractionType.SIGNAL_AMPLIFICATION,
                risk_level=RiskLevel.LOW,
                score_modifier=1.7,
                confidence=0.80,
                explanation=f"🏛️ INSTITUTIONAL PATTERN: Smart money accumulation with stable metrics = institutional interest",
                factors_involved=['smart_money_score', 'volume_momentum', 'vlr_ratio', 'security_score'],
                override_linear=False
            ))
        
        return emergent
    
    def _apply_interaction_modifications(self, base_score: float, 
                                       interactions: List[InteractionResult], 
                                       factors: FactorValues) -> Tuple[float, Dict[str, Any]]:
        """
        Apply interaction-based modifications to the base score.
        
        This is where the non-linear magic happens!
        """
        modified_score = base_score
        applied_interactions = []
        
        # Sort interactions by priority (CRITICAL dangers first)
        interactions.sort(key=lambda x: (
            x.risk_level == RiskLevel.CRITICAL,
            x.override_linear,
            x.confidence
        ), reverse=True)
        
        for interaction in interactions:
            if interaction.override_linear and interaction.risk_level == RiskLevel.CRITICAL:
                # CRITICAL OVERRIDE: Ignore all other factors
                modified_score = base_score * interaction.score_modifier
                applied_interactions.append({
                    'type': interaction.interaction_type.value,
                    'modifier': interaction.score_modifier,
                    'explanation': interaction.explanation,
                    'override': True
                })
                break  # Stop processing - this overrides everything
            
            elif interaction.interaction_type == InteractionType.SIGNAL_AMPLIFICATION:
                # AMPLIFICATION: Multiply score
                modified_score *= interaction.score_modifier
                applied_interactions.append({
                    'type': 'amplification',
                    'multiplier': interaction.score_modifier,
                    'explanation': interaction.explanation
                })
            
            elif interaction.interaction_type == InteractionType.CONTRADICTION:
                # CONTRADICTION: Dampen score
                modified_score *= interaction.score_modifier
                applied_interactions.append({
                    'type': 'contradiction',
                    'dampener': interaction.score_modifier,
                    'explanation': interaction.explanation
                })
        
        # Ensure score stays within bounds
        modified_score = max(0, min(100, modified_score))
        
        interaction_analysis = {
            'base_score': base_score,
            'final_score': modified_score,
            'total_interactions': len(interactions),
            'applied_interactions': applied_interactions,
            'interaction_summary': self._summarize_interactions(interactions)
        }
        
        return modified_score, interaction_analysis
    
    def _calculate_traditional_baseline(self, components: Dict[str, float]) -> float:
        """Calculate baseline score from traditional components (for comparison)"""
        return min(100, sum(components.values()))
    
    def _generate_interaction_analysis(self, factors: FactorValues, 
                                     interactions: List[InteractionResult],
                                     base_score: float, final_score: float,
                                     traditional_components: Dict[str, float]) -> Dict[str, Any]:
        """Generate comprehensive analysis of the interaction-based scoring"""
        
        analysis = {
            'scoring_methodology': 'INTERACTION-BASED (Non-Linear)',
            'linear_vs_interaction': {
                'traditional_linear_score': self._calculate_traditional_baseline(traditional_components),
                'interaction_based_score': final_score,
                'improvement_factor': final_score / max(1, self._calculate_traditional_baseline(traditional_components)),
                'methodology_comparison': 'Interaction-based scoring captures factor synergies and contradictions'
            },
            'factor_values': {
                'vlr_analysis': {
                    'raw_vlr': factors.raw_vlr,
                    'normalized_vlr': factors.vlr_ratio,
                    'interpretation': self._interpret_vlr(factors.raw_vlr)
                },
                'liquidity_analysis': {
                    'raw_liquidity': factors.raw_liquidity,
                    'normalized_liquidity': factors.liquidity,
                    'adequacy': 'HIGH' if factors.raw_liquidity > 500000 else 'MEDIUM' if factors.raw_liquidity > 100000 else 'LOW'
                },
                'smart_money': {
                    'score': factors.smart_money_score,
                    'detection': 'DETECTED' if factors.smart_money_score > 0.3 else 'NOT_DETECTED'
                },
                'validation_strength': {
                    'platform_count': factors.platforms_count,
                    'validation_score': factors.cross_platform_validation,
                    'strength': 'STRONG' if factors.cross_platform_validation > 0.7 else 'MODERATE' if factors.cross_platform_validation > 0.4 else 'WEAK'
                }
            },
            'interaction_analysis': {
                'total_interactions_detected': len(interactions),
                'danger_interactions': len([i for i in interactions if i.interaction_type == InteractionType.DANGER_AMPLIFICATION]),
                'amplification_interactions': len([i for i in interactions if i.interaction_type == InteractionType.SIGNAL_AMPLIFICATION]),
                'contradiction_interactions': len([i for i in interactions if i.interaction_type == InteractionType.CONTRADICTION]),
                'interactions_detail': [
                    {
                        'type': i.interaction_type.value,
                        'risk_level': i.risk_level.value,
                        'confidence': i.confidence,
                        'explanation': i.explanation,
                        'factors': i.factors_involved
                    }
                    for i in interactions
                ]
            },
            'risk_assessment': {
                'overall_risk': self._calculate_overall_risk(interactions),
                'confidence_level': self._calculate_confidence_level(interactions),
                'recommendation': self._generate_recommendation(final_score, interactions)
            },
            'mathematical_foundation': {
                'linear_assumption_flaw': 'Traditional scoring assumes factor independence (Score = A + B + C)',
                'interaction_reality': 'Factors interact non-linearly (Score = f(interactions, amplifications, contradictions))',
                'key_insight': 'In financial markets, 2+2 ≠ 4 (can equal 0, 10, or 3 depending on interactions)'
            }
        }
        
        return analysis
    
    def _interpret_vlr(self, vlr: float) -> str:
        """Interpret VLR value"""
        if vlr > 20:
            return "EXTREME MANIPULATION - Avoid immediately"
        elif vlr > 10:
            return "HIGH MANIPULATION RISK - Proceed with extreme caution"
        elif vlr > 5:
            return "PEAK PERFORMANCE - Optimal profit extraction zone"
        elif vlr > 2:
            return "MOMENTUM BUILDING - Strong growth confirmed"
        elif vlr > 0.5:
            return "GEM DISCOVERY - Early-stage opportunity"
        else:
            return "LOW ACTIVITY - Limited trading interest"
    
    def _calculate_overall_risk(self, interactions: List[InteractionResult]) -> str:
        """Calculate overall risk level from interactions"""
        if any(i.risk_level == RiskLevel.CRITICAL for i in interactions):
            return "CRITICAL"
        elif any(i.risk_level == RiskLevel.HIGH for i in interactions):
            return "HIGH"
        elif any(i.risk_level == RiskLevel.MEDIUM for i in interactions):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_confidence_level(self, interactions: List[InteractionResult]) -> float:
        """Calculate overall confidence level"""
        if not interactions:
            return 0.5
        
        # Weight confidence by interaction importance
        total_weighted_confidence = 0
        total_weight = 0
        
        for interaction in interactions:
            weight = 1.0
            if interaction.risk_level == RiskLevel.CRITICAL:
                weight = 3.0
            elif interaction.risk_level == RiskLevel.HIGH:
                weight = 2.0
            elif interaction.risk_level == RiskLevel.MEDIUM:
                weight = 1.5
            
            total_weighted_confidence += interaction.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.5
    
    def _generate_recommendation(self, score: float, interactions: List[InteractionResult]) -> str:
        """Generate trading recommendation based on score and interactions"""
        
        # Check for critical dangers first
        critical_dangers = [i for i in interactions if i.risk_level == RiskLevel.CRITICAL]
        if critical_dangers:
            return "🚨 AVOID IMMEDIATELY - Critical risks detected"
        
        # Check for high-confidence amplifications
        strong_amplifications = [i for i in interactions 
                               if i.interaction_type == InteractionType.SIGNAL_AMPLIFICATION 
                               and i.confidence > 0.8]
        
        if strong_amplifications and score > 75:
            return "🚀 STRONG BUY - High-confidence amplification detected"
        elif score > 85:
            return "🔥 BUY - High conviction opportunity"
        elif score > 70:
            return "📈 CONSIDER - Promising opportunity with due diligence"
        elif score > 50:
            return "🔍 MONITOR - Meets threshold but requires careful analysis"
        else:
            return "❌ PASS - Below conviction threshold"
    
    def _summarize_interactions(self, interactions: List[InteractionResult]) -> Dict[str, Any]:
        """Summarize all interactions for reporting"""
        return {
            'danger_count': len([i for i in interactions if i.interaction_type == InteractionType.DANGER_AMPLIFICATION]),
            'amplification_count': len([i for i in interactions if i.interaction_type == InteractionType.SIGNAL_AMPLIFICATION]),
            'contradiction_count': len([i for i in interactions if i.interaction_type == InteractionType.CONTRADICTION]),
            'average_confidence': np.mean([i.confidence for i in interactions]) if interactions else 0,
            'highest_risk': max([i.risk_level.value for i in interactions]) if interactions else 'LOW'
        }
    
    def _record_interaction_event(self, factors: FactorValues, 
                                interactions: List[InteractionResult], 
                                final_score: float):
        """Record interaction event for historical analysis"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'factors': {
                'vlr': factors.raw_vlr,
                'liquidity': factors.raw_liquidity,
                'smart_money': factors.smart_money_score,
                'platforms': factors.platforms_count
            },
            'interactions_detected': len(interactions),
            'final_score': final_score,
            'interaction_types': [i.interaction_type.value for i in interactions]
        }
        
        self.interaction_history.append(event)
        
        # Keep only last 1000 events
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-1000:]
    
    def get_interaction_statistics(self) -> Dict[str, Any]:
        """Get statistics about interaction patterns"""
        if not self.interaction_history:
            return {'message': 'No interaction history available'}
        
        return {
            'total_events': len(self.interaction_history),
            'danger_detection_rate': len([e for e in self.interaction_history 
                                        if 'danger_amplification' in e['interaction_types']]) / len(self.interaction_history),
            'amplification_rate': len([e for e in self.interaction_history 
                                     if 'signal_amplification' in e['interaction_types']]) / len(self.interaction_history),
            'average_interactions_per_token': np.mean([e['interactions_detected'] for e in self.interaction_history]),
            'score_distribution': {
                'high_confidence': len([e for e in self.interaction_history if e['final_score'] > 80]),
                'medium_confidence': len([e for e in self.interaction_history if 50 <= e['final_score'] <= 80]),
                'low_confidence': len([e for e in self.interaction_history if e['final_score'] < 50])
            }
        }

# Usage example and testing
if __name__ == "__main__":
    # Example usage of the interaction-based scoring system
    scorer = InteractionBasedScorer(debug_mode=True)
    
    # Example 1: Dangerous scenario (High VLR + Low Liquidity)
    dangerous_factors = FactorValues(
        vlr_ratio=0.8, liquidity=0.2, smart_money_score=0.1,
        volume_momentum=0.9, security_score=0.3, whale_concentration=0.9,
        raw_vlr=15.2, raw_liquidity=80000, platforms_count=2
    )
    
    traditional_components = {
        'base_score': 25, 'overview_score': 18, 'whale_score': 12,
        'volume_score': 10, 'security_score': 8, 'vlr_score': 8
    }
    
    score, analysis = scorer.calculate_interaction_based_score(dangerous_factors, traditional_components)
    print(f"🚨 DANGEROUS TOKEN: Linear would give ~81, Interaction-based gives {score:.1f}")
    print(f"Key insight: {analysis['interaction_analysis']['interactions_detail'][0]['explanation']}\n")
    
    # Example 2: High-conviction scenario (Smart Money + Volume + Security)
    high_conviction_factors = FactorValues(
        vlr_ratio=0.6, liquidity=0.8, smart_money_score=0.7,
        volume_momentum=0.8, security_score=0.9, whale_concentration=0.4,
        raw_vlr=6.5, raw_liquidity=750000, platforms_count=5
    )
    
    score2, analysis2 = scorer.calculate_interaction_based_score(high_conviction_factors, traditional_components)
    print(f"🚀 HIGH CONVICTION: Linear would give ~81, Interaction-based gives {score2:.1f}")
    print(f"Amplification: {analysis2['interaction_analysis']['interactions_detail'][0]['explanation']}")