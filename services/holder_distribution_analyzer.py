#!/usr/bin/env python3
"""
Holder Distribution Analyzer Service

This service analyzes token holder distribution using the Birdeye /defi/v3/token/holder endpoint
to assess concentration risks and provide risk-adjusted scoring.
"""

import asyncio
import time
import logging
import statistics
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager


class HolderDistributionAnalyzer:
    """
    Analyzes token holder distribution and concentration risks.
    
    Uses the Birdeye /defi/v3/token/holder endpoint to analyze holder patterns,
    calculate concentration metrics, and provide risk assessments.
    """
    
    def __init__(self, birdeye_api: BirdeyeAPI, logger: Optional[logging.Logger] = None):
        """
        Initialize the holder distribution analyzer.
        
        Args:
            birdeye_api: Birdeye API instance
            logger: Logger instance
        """
        self.birdeye_api = birdeye_api
        self.logger = logger or logging.getLogger(__name__)
        self.cache_manager = CacheManager()
        
        # Cache settings
        self.holder_cache_ttl = 1800  # 30 minutes cache for holder data
        self.analysis_cache_ttl = 900  # 15 minutes cache for analysis results
        
        # Risk assessment thresholds
        self.risk_thresholds = {
            "high_concentration": 0.7,      # >70% in top 10 holders = high risk
            "moderate_concentration": 0.5,  # >50% in top 10 holders = moderate risk
            "whale_dominance": 0.3,         # >30% in single wallet = whale dominance
            "min_holders": 100,             # Minimum holders for healthy distribution
            "gini_coefficient_threshold": 0.8,  # Gini coefficient threshold for inequality
        }
        
        # Scoring weights for distribution analysis
        self.scoring_weights = {
            "concentration_weight": 0.4,    # Top holder concentration
            "gini_weight": 0.25,           # Gini coefficient (inequality measure)
            "holder_count_weight": 0.2,    # Total number of holders
            "whale_risk_weight": 0.15      # Individual whale risk
        }
        
        # Internal tracking
        self._holder_data_cache = {}
        self._distribution_metrics_cache = {}
        
    async def analyze_holder_distribution(self, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """
        Analyze holder distribution for a specific token.
        
        Args:
            token_address: Token address to analyze
            limit: Maximum number of holders to analyze
            
        Returns:
            Comprehensive holder distribution analysis
        """
        cache_key = f"holder_distribution_{token_address}_{limit}"
        
        # Check cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            self.logger.debug(f"👥 Using cached holder distribution for {token_address}")
            return cached_data
        
        try:
            self.logger.info(f"📊 Analyzing holder distribution for token {token_address}")
            
            # Get holder data from Birdeye API
            result = await self.birdeye_api.get_token_holders(token_address, limit=limit)
            
            # Fix: API returns direct structure with "items", not wrapped in "data"
            if result and isinstance(result, dict) and "items" in result:
                holders_data = result["items"]
                
                # Perform comprehensive distribution analysis
                analysis_result = await self._perform_distribution_analysis(holders_data, token_address)
                
                # Cache the results
                self.cache_manager.set(cache_key, analysis_result, ttl=self.holder_cache_ttl)
                
                self.logger.info(f"✅ Analyzed {len(holders_data)} holders for {token_address}")
                return analysis_result
            else:
                self.logger.warning(f"⚠️ Holder data API call failed for {token_address}: {result}")
                return self._get_empty_analysis(token_address)
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing holder distribution for {token_address}: {e}")
            return self._get_empty_analysis(token_address)
    
    async def _perform_distribution_analysis(self, holders_data: List[Dict[str, Any]], token_address: str) -> Dict[str, Any]:
        """
        Perform comprehensive holder distribution analysis.
        
        Args:
            holders_data: Raw holder data from API
            token_address: Token address being analyzed
            
        Returns:
            Comprehensive distribution analysis results
        """
        current_time = int(time.time())
        
        # Extract holder balances and addresses
        holder_balances = []
        holder_addresses = []
        total_supply = 0
        
        for holder in holders_data:
            try:
                # Fix: API returns "ui_amount" not "balance", "owner" not "address"
                balance = holder.get("ui_amount", 0) or 0
                address = holder.get("owner", "")
                
                if balance > 0 and address:
                    holder_balances.append(balance)
                    holder_addresses.append(address)
                    total_supply += balance
                    
            except Exception as e:
                self.logger.error(f"Error processing holder data: {e}")
                continue
        
        if not holder_balances:
            return self._get_empty_analysis(token_address)
        
        # Calculate distribution metrics
        concentration_metrics = self._calculate_concentration_metrics(holder_balances, total_supply)
        gini_coefficient = self._calculate_gini_coefficient(holder_balances)
        whale_analysis = self._analyze_whale_presence(holder_balances, total_supply)
        distribution_quality = self._assess_distribution_quality(holder_balances, total_supply)
        
        # Determine risk level
        risk_assessment = self._assess_concentration_risk(
            concentration_metrics, gini_coefficient, whale_analysis, len(holder_balances)
        )
        
        # Calculate score adjustment based on distribution
        score_adjustment = self._calculate_distribution_score_adjustment(risk_assessment, concentration_metrics)
        
        return {
            "token_address": token_address,
            "analysis_timestamp": current_time,
            "total_holders": len(holder_balances),
            "total_supply_analyzed": total_supply,
            "concentration_metrics": concentration_metrics,
            "gini_coefficient": gini_coefficient,
            "whale_analysis": whale_analysis,
            "distribution_quality": distribution_quality,
            "risk_assessment": risk_assessment,
            "score_adjustment": score_adjustment,
            "holder_categories": self._categorize_holders(holder_balances, total_supply),
            "distribution_warnings": self._generate_distribution_warnings(risk_assessment, concentration_metrics),
            "validation_passed": self._validate_distribution_analysis(holder_balances, total_supply)
        }
    
    def _calculate_concentration_metrics(self, holder_balances: List[float], total_supply: float) -> Dict[str, Any]:
        """
        Calculate concentration metrics for holder distribution.
        
        Args:
            holder_balances: List of holder balances (sorted descending)
            total_supply: Total token supply analyzed
            
        Returns:
            Concentration metrics dictionary
        """
        try:
            # Sort balances in descending order
            sorted_balances = sorted(holder_balances, reverse=True)
            
            # Calculate top N holder concentrations
            top_1_pct = (sorted_balances[0] / total_supply * 100) if len(sorted_balances) >= 1 else 0
            top_5_pct = (sum(sorted_balances[:5]) / total_supply * 100) if len(sorted_balances) >= 5 else 0
            top_10_pct = (sum(sorted_balances[:10]) / total_supply * 100) if len(sorted_balances) >= 10 else 0
            top_20_pct = (sum(sorted_balances[:20]) / total_supply * 100) if len(sorted_balances) >= 20 else 0
            
            # Calculate Herfindahl-Hirschman Index (HHI)
            hhi = sum((balance / total_supply) ** 2 for balance in sorted_balances) * 10000
            
            return {
                "top_1_holder_pct": round(top_1_pct, 2),
                "top_5_holders_pct": round(top_5_pct, 2),
                "top_10_holders_pct": round(top_10_pct, 2),
                "top_20_holders_pct": round(top_20_pct, 2),
                "herfindahl_index": round(hhi, 2),
                "concentration_level": self._determine_concentration_level(top_10_pct, hhi)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating concentration metrics: {e}")
            return {
                "top_1_holder_pct": 0,
                "top_5_holders_pct": 0,
                "top_10_holders_pct": 0,
                "top_20_holders_pct": 0,
                "herfindahl_index": 0,
                "concentration_level": "unknown"
            }
    
    def _calculate_gini_coefficient(self, holder_balances: List[float]) -> float:
        """
        Calculate Gini coefficient for holder distribution inequality.
        
        Args:
            holder_balances: List of holder balances
            
        Returns:
            Gini coefficient (0 = perfect equality, 1 = perfect inequality)
        """
        try:
            if not holder_balances or len(holder_balances) < 2:
                return 0.0
            
            # Sort balances
            sorted_balances = sorted(holder_balances)
            n = len(sorted_balances)
            
            # Calculate Gini coefficient using the standard formula
            cumulative_sum = sum((2 * i - n - 1) * balance for i, balance in enumerate(sorted_balances, 1))
            gini = cumulative_sum / (n * sum(sorted_balances))
            
            return round(abs(gini), 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating Gini coefficient: {e}")
            return 0.0
    
    def _analyze_whale_presence(self, holder_balances: List[float], total_supply: float) -> Dict[str, Any]:
        """
        Analyze whale presence and dominance patterns.
        
        Args:
            holder_balances: List of holder balances
            total_supply: Total token supply
            
        Returns:
            Whale analysis results
        """
        try:
            sorted_balances = sorted(holder_balances, reverse=True)
            
            # Define whale thresholds (holders with >1% of supply)
            whale_threshold = total_supply * 0.01
            whales = [balance for balance in sorted_balances if balance >= whale_threshold]
            
            # Calculate whale metrics
            whale_count = len(whales)
            whale_dominance_pct = (sum(whales) / total_supply * 100) if whales else 0
            largest_whale_pct = (sorted_balances[0] / total_supply * 100) if sorted_balances else 0
            
            # Assess whale risk level
            whale_risk_level = self._assess_whale_risk(whale_count, whale_dominance_pct, largest_whale_pct)
            
            return {
                "whale_count": whale_count,
                "whale_dominance_pct": round(whale_dominance_pct, 2),
                "largest_whale_pct": round(largest_whale_pct, 2),
                "whale_risk_level": whale_risk_level,
                "whale_threshold_pct": 1.0,  # 1% threshold used
                "average_whale_holding": round(sum(whales) / len(whales), 2) if whales else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing whale presence: {e}")
            return {
                "whale_count": 0,
                "whale_dominance_pct": 0,
                "largest_whale_pct": 0,
                "whale_risk_level": "unknown",
                "whale_threshold_pct": 1.0,
                "average_whale_holding": 0
            }
    
    def _assess_distribution_quality(self, holder_balances: List[float], total_supply: float) -> Dict[str, Any]:
        """
        Assess overall distribution quality and health.
        
        Args:
            holder_balances: List of holder balances
            total_supply: Total token supply
            
        Returns:
            Distribution quality assessment
        """
        try:
            holder_count = len(holder_balances)
            
            # Calculate distribution statistics
            mean_holding = statistics.mean(holder_balances) if holder_balances else 0
            median_holding = statistics.median(holder_balances) if holder_balances else 0
            std_deviation = statistics.stdev(holder_balances) if len(holder_balances) > 1 else 0
            
            # Calculate coefficient of variation (relative dispersion)
            cv = (std_deviation / mean_holding) if mean_holding > 0 else 0
            
            # Assess holder count adequacy
            holder_adequacy = self._assess_holder_adequacy(holder_count)
            
            # Calculate distribution score (0-100)
            distribution_score = self._calculate_distribution_score(
                holder_count, cv, holder_balances, total_supply
            )
            
            return {
                "holder_count": holder_count,
                "mean_holding": round(mean_holding, 2),
                "median_holding": round(median_holding, 2),
                "std_deviation": round(std_deviation, 2),
                "coefficient_of_variation": round(cv, 4),
                "holder_adequacy": holder_adequacy,
                "distribution_score": round(distribution_score, 2),
                "quality_level": self._determine_quality_level(distribution_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing distribution quality: {e}")
            return {
                "holder_count": 0,
                "mean_holding": 0,
                "median_holding": 0,
                "std_deviation": 0,
                "coefficient_of_variation": 0,
                "holder_adequacy": "insufficient",
                "distribution_score": 0,
                "quality_level": "poor"
            }
    
    def _assess_concentration_risk(self, concentration_metrics: Dict[str, Any], gini_coefficient: float,
                                 whale_analysis: Dict[str, Any], holder_count: int) -> Dict[str, Any]:
        """
        Assess overall concentration risk based on multiple factors.
        
        Args:
            concentration_metrics: Concentration metrics
            gini_coefficient: Gini coefficient
            whale_analysis: Whale analysis results
            holder_count: Total number of holders
            
        Returns:
            Risk assessment results
        """
        try:
            # Extract key metrics
            top_10_pct = concentration_metrics.get("top_10_holders_pct", 0)
            whale_dominance = whale_analysis.get("whale_dominance_pct", 0)
            largest_whale = whale_analysis.get("largest_whale_pct", 0)
            
            # Calculate risk scores (0-100, higher = more risky)
            concentration_risk = min(100, top_10_pct * 1.43)  # Scale to 0-100
            inequality_risk = gini_coefficient * 100
            whale_risk = min(100, whale_dominance * 2)  # Scale to 0-100
            holder_risk = max(0, 100 - (holder_count / 10))  # Risk decreases with more holders
            
            # Weighted overall risk score
            overall_risk_score = (
                concentration_risk * 0.4 +
                inequality_risk * 0.25 +
                whale_risk * 0.25 +
                holder_risk * 0.1
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Identify specific risk factors
            risk_factors = self._identify_risk_factors(
                top_10_pct, gini_coefficient, whale_dominance, largest_whale, holder_count
            )
            
            return {
                "overall_risk_score": round(overall_risk_score, 2),
                "risk_level": risk_level,
                "concentration_risk": round(concentration_risk, 2),
                "inequality_risk": round(inequality_risk, 2),
                "whale_risk": round(whale_risk, 2),
                "holder_count_risk": round(holder_risk, 2),
                "risk_factors": risk_factors,
                "is_high_risk": overall_risk_score > 70,
                "recommendation": self._get_risk_recommendation(risk_level, risk_factors)
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing concentration risk: {e}")
            return {
                "overall_risk_score": 100,
                "risk_level": "unknown",
                "concentration_risk": 100,
                "inequality_risk": 100,
                "whale_risk": 100,
                "holder_count_risk": 100,
                "risk_factors": ["analysis_error"],
                "is_high_risk": True,
                "recommendation": "avoid"
            }
    
    def _calculate_distribution_score_adjustment(self, risk_assessment: Dict[str, Any], 
                                               concentration_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate score adjustment based on distribution analysis.
        
        Args:
            risk_assessment: Risk assessment results
            concentration_metrics: Concentration metrics
            
        Returns:
            Score adjustment information
        """
        try:
            risk_level = risk_assessment.get("risk_level", "unknown")
            overall_risk_score = risk_assessment.get("overall_risk_score", 100)
            
            # Base adjustment factors
            adjustment_factors = {
                "excellent": 1.2,   # 20% boost
                "good": 1.1,        # 10% boost
                "fair": 1.0,        # No adjustment
                "poor": 0.9,        # 10% penalty
                "critical": 0.8     # 20% penalty
            }
            
            base_adjustment = adjustment_factors.get(risk_level, 0.8)
            
            # Additional adjustments for specific conditions
            top_10_pct = concentration_metrics.get("top_10_holders_pct", 100)
            
            # Severe concentration penalty
            if top_10_pct > 80:
                base_adjustment *= 0.7  # Additional 30% penalty
            elif top_10_pct > 70:
                base_adjustment *= 0.85  # Additional 15% penalty
            
            # Cap adjustments
            final_adjustment = max(0.5, min(1.3, base_adjustment))
            
            return {
                "score_multiplier": round(final_adjustment, 3),
                "adjustment_reason": self._get_adjustment_reason(risk_level, top_10_pct),
                "base_adjustment": round(base_adjustment, 3),
                "final_adjustment": round(final_adjustment, 3),
                "risk_level": risk_level
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating score adjustment: {e}")
            return {
                "score_multiplier": 0.8,
                "adjustment_reason": "analysis_error",
                "base_adjustment": 0.8,
                "final_adjustment": 0.8,
                "risk_level": "unknown"
            }
    
    def _categorize_holders(self, holder_balances: List[float], total_supply: float) -> Dict[str, Any]:
        """
        Categorize holders into different groups based on their holdings.
        
        Args:
            holder_balances: List of holder balances
            total_supply: Total token supply
            
        Returns:
            Holder categorization results
        """
        try:
            categories = {
                "whales": [],      # >1% of supply
                "large": [],       # 0.1% - 1% of supply
                "medium": [],      # 0.01% - 0.1% of supply
                "small": [],       # <0.01% of supply
            }
            
            for balance in holder_balances:
                percentage = (balance / total_supply) * 100
                
                if percentage > 1.0:
                    categories["whales"].append(balance)
                elif percentage > 0.1:
                    categories["large"].append(balance)
                elif percentage > 0.01:
                    categories["medium"].append(balance)
                else:
                    categories["small"].append(balance)
            
            return {
                "whale_holders": len(categories["whales"]),
                "large_holders": len(categories["large"]),
                "medium_holders": len(categories["medium"]),
                "small_holders": len(categories["small"]),
                "whale_dominance": round(sum(categories["whales"]) / total_supply * 100, 2),
                "large_holder_share": round(sum(categories["large"]) / total_supply * 100, 2),
                "retail_share": round((sum(categories["medium"]) + sum(categories["small"])) / total_supply * 100, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error categorizing holders: {e}")
            return {
                "whale_holders": 0,
                "large_holders": 0,
                "medium_holders": 0,
                "small_holders": 0,
                "whale_dominance": 0,
                "large_holder_share": 0,
                "retail_share": 0
            }
    
    def _determine_concentration_level(self, top_10_pct: float, hhi: float) -> str:
        """Determine concentration level based on metrics."""
        if top_10_pct > 80 or hhi > 2500:
            return "extreme"
        elif top_10_pct > 70 or hhi > 1800:
            return "high"
        elif top_10_pct > 50 or hhi > 1000:
            return "moderate"
        elif top_10_pct > 30 or hhi > 500:
            return "low"
        else:
            return "minimal"
    
    def _assess_whale_risk(self, whale_count: int, whale_dominance: float, largest_whale: float) -> str:
        """Assess whale risk level."""
        if largest_whale > 30 or whale_dominance > 50:
            return "critical"
        elif largest_whale > 20 or whale_dominance > 40:
            return "high"
        elif largest_whale > 10 or whale_dominance > 25:
            return "moderate"
        elif whale_count > 0:
            return "low"
        else:
            return "minimal"
    
    def _assess_holder_adequacy(self, holder_count: int) -> str:
        """Assess if holder count is adequate."""
        if holder_count > 1000:
            return "excellent"
        elif holder_count > 500:
            return "good"
        elif holder_count > 200:
            return "adequate"
        elif holder_count > 100:
            return "marginal"
        else:
            return "insufficient"
    
    def _calculate_distribution_score(self, holder_count: int, cv: float, 
                                    holder_balances: List[float], total_supply: float) -> float:
        """Calculate overall distribution quality score."""
        try:
            score = 0.0
            
            # Holder count component (40% weight)
            if holder_count > 1000:
                score += 40
            elif holder_count > 500:
                score += 35
            elif holder_count > 200:
                score += 25
            elif holder_count > 100:
                score += 15
            else:
                score += max(0, holder_count / 10)
            
            # Distribution evenness component (30% weight)
            # Lower CV is better (less variation)
            evenness_score = max(0, 30 - (cv * 10))
            score += min(30, evenness_score)
            
            # Top holder concentration component (30% weight)
            sorted_balances = sorted(holder_balances, reverse=True)
            top_1_pct = (sorted_balances[0] / total_supply * 100) if sorted_balances else 0
            concentration_score = max(0, 30 - top_1_pct)
            score += concentration_score
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating distribution score: {e}")
            return 0.0
    
    def _determine_quality_level(self, distribution_score: float) -> str:
        """Determine quality level from distribution score."""
        if distribution_score > 80:
            return "excellent"
        elif distribution_score > 65:
            return "good"
        elif distribution_score > 50:
            return "fair"
        elif distribution_score > 30:
            return "poor"
        else:
            return "critical"
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from overall risk score."""
        if risk_score > 80:
            return "critical"
        elif risk_score > 65:
            return "high"
        elif risk_score > 50:
            return "moderate"
        elif risk_score > 30:
            return "low"
        else:
            return "minimal"
    
    def _identify_risk_factors(self, top_10_pct: float, gini: float, whale_dominance: float,
                             largest_whale: float, holder_count: int) -> List[str]:
        """Identify specific risk factors."""
        factors = []
        
        if top_10_pct > 70:
            factors.append("high_concentration")
        if gini > 0.8:
            factors.append("high_inequality")
        if whale_dominance > 40:
            factors.append("whale_dominance")
        if largest_whale > 25:
            factors.append("single_whale_risk")
        if holder_count < 100:
            factors.append("insufficient_holders")
        
        return factors if factors else ["low_risk"]
    
    def _get_risk_recommendation(self, risk_level: str, risk_factors: List[str]) -> str:
        """Get investment recommendation based on risk assessment."""
        if risk_level in ["critical", "high"]:
            return "avoid"
        elif risk_level == "moderate":
            return "caution"
        elif risk_level == "low":
            return "acceptable"
        else:
            return "favorable"
    
    def _get_adjustment_reason(self, risk_level: str, top_10_pct: float) -> str:
        """Get reason for score adjustment."""
        if top_10_pct > 80:
            return "extreme_concentration_penalty"
        elif risk_level == "critical":
            return "critical_risk_penalty"
        elif risk_level == "high":
            return "high_risk_penalty"
        elif risk_level == "excellent":
            return "excellent_distribution_bonus"
        elif risk_level == "good":
            return "good_distribution_bonus"
        else:
            return "standard_adjustment"
    
    def _generate_distribution_warnings(self, risk_assessment: Dict[str, Any], 
                                      concentration_metrics: Dict[str, Any]) -> List[str]:
        """Generate distribution-related warnings."""
        warnings = []
        
        risk_factors = risk_assessment.get("risk_factors", [])
        top_10_pct = concentration_metrics.get("top_10_holders_pct", 0)
        
        if "high_concentration" in risk_factors:
            warnings.append(f"High concentration: {top_10_pct:.1f}% held by top 10 holders")
        if "whale_dominance" in risk_factors:
            warnings.append("Whale dominance detected - high sell pressure risk")
        if "single_whale_risk" in risk_factors:
            warnings.append("Single large holder poses significant risk")
        if "insufficient_holders" in risk_factors:
            warnings.append("Insufficient holder count for healthy distribution")
        
        return warnings
    
    def _validate_distribution_analysis(self, holder_balances: List[float], total_supply: float) -> bool:
        """Validate distribution analysis results."""
        try:
            if not holder_balances or total_supply <= 0:
                return False
            
            # Check if balances sum reasonably close to total supply
            balance_sum = sum(holder_balances)
            if abs(balance_sum - total_supply) / total_supply > 0.1:  # 10% tolerance
                return False
            
            # Check for reasonable holder count
            if len(holder_balances) < 1:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating distribution analysis: {e}")
            return False
    
    def _get_empty_analysis(self, token_address: str) -> Dict[str, Any]:
        """Get empty analysis result for error cases."""
        return {
            "token_address": token_address,
            "analysis_timestamp": int(time.time()),
            "total_holders": 0,
            "total_supply_analyzed": 0,
            "concentration_metrics": {
                "top_1_holder_pct": 0,
                "top_5_holders_pct": 0,
                "top_10_holders_pct": 0,
                "top_20_holders_pct": 0,
                "herfindahl_index": 0,
                "concentration_level": "unknown"
            },
            "gini_coefficient": 0.0,
            "whale_analysis": {
                "whale_count": 0,
                "whale_dominance_pct": 0,
                "largest_whale_pct": 0,
                "whale_risk_level": "unknown",
                "whale_threshold_pct": 1.0,
                "average_whale_holding": 0
            },
            "distribution_quality": {
                "holder_count": 0,
                "mean_holding": 0,
                "median_holding": 0,
                "std_deviation": 0,
                "coefficient_of_variation": 0,
                "holder_adequacy": "insufficient",
                "distribution_score": 0,
                "quality_level": "poor"
            },
            "risk_assessment": {
                "overall_risk_score": 100,
                "risk_level": "unknown",
                "concentration_risk": 100,
                "inequality_risk": 100,
                "whale_risk": 100,
                "holder_count_risk": 100,
                "risk_factors": ["no_data"],
                "is_high_risk": True,
                "recommendation": "avoid"
            },
            "score_adjustment": {
                "score_multiplier": 0.5,
                "adjustment_reason": "no_data",
                "base_adjustment": 0.5,
                "final_adjustment": 0.5,
                "risk_level": "unknown"
            },
            "holder_categories": {
                "whale_holders": 0,
                "large_holders": 0,
                "medium_holders": 0,
                "small_holders": 0,
                "whale_dominance": 0,
                "large_holder_share": 0,
                "retail_share": 0
            },
            "distribution_warnings": ["No holder data available"],
            "validation_passed": False
        }
    
    async def batch_analyze_distributions(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch analyze holder distributions for multiple tokens.
        
        Args:
            token_addresses: List of token addresses to analyze
            
        Returns:
            Dictionary mapping token addresses to distribution analysis results
        """
        results = {}
        
        # Process in smaller batches to avoid overwhelming the API
        batch_size = 3  # Smaller batch size for holder data (more intensive)
        for i in range(0, len(token_addresses), batch_size):
            batch = token_addresses[i:i + batch_size]
            
            # Process batch with some concurrency
            batch_tasks = [
                self.analyze_holder_distribution(token_address)
                for token_address in batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for token_address, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Error analyzing distribution for {token_address}: {result}")
                        results[token_address] = self._get_empty_analysis(token_address)
                    else:
                        results[token_address] = result
                        
            except Exception as e:
                self.logger.error(f"Error in batch distribution analysis: {e}")
                for token_address in batch:
                    results[token_address] = self._get_empty_analysis(token_address)
            
            # Longer delay between batches for holder data
            if i + batch_size < len(token_addresses):
                await asyncio.sleep(2.0)
        
        return results
    
    def get_distribution_summary(self, token_address: str) -> Dict[str, Any]:
        """
        Get a summary of holder distribution analysis for a token.
        
        Args:
            token_address: Token address
            
        Returns:
            Distribution summary
        """
        cache_key = f"holder_distribution_{token_address}_100"
        cached_data = self.cache_manager.get(cache_key)
        
        if not cached_data:
            return {"available": False, "reason": "No cached data"}
        
        risk_assessment = cached_data.get("risk_assessment", {})
        concentration_metrics = cached_data.get("concentration_metrics", {})
        
        return {
            "available": True,
            "risk_level": risk_assessment.get("risk_level", "unknown"),
            "score_multiplier": cached_data.get("score_adjustment", {}).get("score_multiplier", 1.0),
            "top_10_concentration": concentration_metrics.get("top_10_holders_pct", 0),
            "is_high_risk": risk_assessment.get("is_high_risk", True),
            "validation_passed": cached_data.get("validation_passed", False)
        } 