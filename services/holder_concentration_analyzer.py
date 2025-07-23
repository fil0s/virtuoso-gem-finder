"""
Holder Concentration Analyzer

Analyzes token holder distribution to assess concentration risk,
whale presence, and distribution equality using advanced metrics.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import statistics
import math
from datetime import datetime

class HolderConcentrationAnalyzer:
    """
    Advanced holder concentration analysis with multiple metrics
    """
    
    def __init__(self, birdeye_api, logger, config: Dict = None):
        self.birdeye_api = birdeye_api
        self.logger = logger
        self.config = config or {}
        
        # Configuration defaults
        self.whale_threshold = self.config.get('whale_threshold_percentage', 5.0)  # 5% of supply
        self.large_holder_threshold = self.config.get('large_holder_threshold_percentage', 1.0)  # 1% of supply
        self.concentration_risk_threshold = self.config.get('concentration_risk_threshold', 0.7)  # Gini > 0.7 is high risk
        
    async def analyze_holder_concentration(self, token_address: str) -> Dict[str, Any]:
        """
        Comprehensive holder concentration analysis
        """
        self.logger.info(f"🔍 Starting holder concentration analysis for {token_address[:8]}...")
        
        analysis = {
            'token_address': token_address,
            'analysis_timestamp': datetime.now().isoformat(),
            'holder_data_available': False,
            'total_holders': 0,
            'holder_distribution': {},
            'concentration_metrics': {},
            'whale_analysis': {},
            'risk_assessment': {},
            'distribution_quality': 'unknown',
            'concentration_score': 0,
            'alerts': [],
            'errors': []
        }
        
        try:
            # Get holder data
            holder_data = await self._fetch_holder_data(token_address)
            
            if not holder_data:
                analysis['errors'].append("No holder data available")
                return analysis
            
            analysis['holder_data_available'] = True
            analysis['total_holders'] = len(holder_data)
            
            # Calculate distribution metrics
            analysis['holder_distribution'] = self._calculate_distribution_metrics(holder_data)
            
            # Calculate concentration metrics (Gini coefficient, etc.)
            analysis['concentration_metrics'] = self._calculate_concentration_metrics(holder_data)
            
            # Whale analysis
            analysis['whale_analysis'] = self._analyze_whales(holder_data)
            
            # Risk assessment
            analysis['risk_assessment'] = self._assess_concentration_risk(analysis)
            
            # Overall quality and scoring
            analysis['distribution_quality'] = self._determine_distribution_quality(analysis)
            analysis['concentration_score'] = self._calculate_concentration_score(analysis)
            
            # Generate alerts
            analysis['alerts'] = self._generate_concentration_alerts(analysis)
            
            self.logger.info(f"✅ Holder concentration analysis completed for {token_address[:8]}")
            
        except Exception as e:
            self.logger.error(f"❌ Holder concentration analysis failed: {e}")
            analysis['errors'].append(f"Analysis failed: {str(e)}")
            
        return analysis
    
    async def _fetch_holder_data(self, token_address: str) -> Optional[List[Dict]]:
        """
        Fetch holder data from available endpoints
        """
        try:
            # Try to get holder data from token holder endpoint
            holder_response = await self.birdeye_api.get_token_holder_data(token_address)
            
            if holder_response and isinstance(holder_response, dict):
                holders = holder_response.get('data', {}).get('items', [])
                if holders:
                    return holders
            
            # Alternative: Try to extract holder info from top traders
            top_traders = await self.birdeye_api.get_top_traders(token_address)
            
            if top_traders and isinstance(top_traders, list):
                # Convert trader data to holder-like format
                holder_data = []
                for trader in top_traders[:100]:  # Top 100 traders as proxy
                    if isinstance(trader, dict):
                        holder_data.append({
                            'address': trader.get('address', ''),
                            'balance': trader.get('volumeUsd', 0),  # Use volume as proxy for holdings
                            'percentage': 0  # Will calculate later
                        })
                return holder_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error fetching holder data: {e}")
            return None
    
    def _calculate_distribution_metrics(self, holder_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate basic distribution metrics
        """
        if not holder_data:
            return {}
        
        # Extract balances
        balances = []
        for holder in holder_data:
            balance = holder.get('balance', 0)
            if isinstance(balance, (int, float)) and balance > 0:
                balances.append(balance)
        
        if not balances:
            return {}
        
        total_supply = sum(balances)
        sorted_balances = sorted(balances, reverse=True)
        
        # Calculate percentages
        percentages = [(balance / total_supply) * 100 for balance in sorted_balances]
        
        # Distribution metrics
        metrics = {
            'total_supply_tracked': total_supply,
            'top_1_percentage': percentages[0] if len(percentages) > 0 else 0,
            'top_5_percentage': sum(percentages[:5]) if len(percentages) >= 5 else sum(percentages),
            'top_10_percentage': sum(percentages[:10]) if len(percentages) >= 10 else sum(percentages),
            'top_50_percentage': sum(percentages[:50]) if len(percentages) >= 50 else sum(percentages),
            'median_holding_percentage': statistics.median(percentages) if percentages else 0,
            'mean_holding_percentage': statistics.mean(percentages) if percentages else 0,
            'holder_count_by_size': self._categorize_holders_by_size(percentages)
        }
        
        return metrics
    
    def _categorize_holders_by_size(self, percentages: List[float]) -> Dict[str, int]:
        """
        Categorize holders by their holding size
        """
        categories = {
            'whales': 0,        # >5%
            'large_holders': 0, # 1-5%
            'medium_holders': 0,# 0.1-1%
            'small_holders': 0, # 0.01-0.1%
            'dust_holders': 0   # <0.01%
        }
        
        for percentage in percentages:
            if percentage >= 5.0:
                categories['whales'] += 1
            elif percentage >= 1.0:
                categories['large_holders'] += 1
            elif percentage >= 0.1:
                categories['medium_holders'] += 1
            elif percentage >= 0.01:
                categories['small_holders'] += 1
            else:
                categories['dust_holders'] += 1
        
        return categories
    
    def _calculate_concentration_metrics(self, holder_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate advanced concentration metrics including Gini coefficient
        """
        if not holder_data:
            return {}
        
        # Extract and sort balances
        balances = []
        for holder in holder_data:
            balance = holder.get('balance', 0)
            if isinstance(balance, (int, float)) and balance > 0:
                balances.append(balance)
        
        if not balances:
            return {}
        
        sorted_balances = sorted(balances)
        n = len(sorted_balances)
        
        # Calculate Gini coefficient
        gini_coefficient = self._calculate_gini_coefficient(sorted_balances)
        
        # Calculate Herfindahl-Hirschman Index (HHI)
        total_supply = sum(sorted_balances)
        market_shares = [(balance / total_supply) for balance in sorted_balances]
        hhi = sum(share ** 2 for share in market_shares)
        
        # Calculate concentration ratio (CR4 - top 4 holders)
        sorted_desc = sorted(balances, reverse=True)
        cr4 = sum(sorted_desc[:4]) / total_supply if len(sorted_desc) >= 4 else 1.0
        
        # Calculate Theil index (another inequality measure)
        mean_balance = statistics.mean(sorted_balances)
        theil_index = sum((balance / mean_balance) * math.log(balance / mean_balance) 
                         for balance in sorted_balances if balance > 0) / n
        
        metrics = {
            'gini_coefficient': gini_coefficient,
            'herfindahl_hirschman_index': hhi,
            'concentration_ratio_4': cr4,
            'theil_index': theil_index,
            'inequality_interpretation': self._interpret_gini_coefficient(gini_coefficient),
            'concentration_level': self._determine_concentration_level(gini_coefficient, hhi, cr4)
        }
        
        return metrics
    
    def _calculate_gini_coefficient(self, sorted_balances: List[float]) -> float:
        """
        Calculate Gini coefficient for wealth inequality
        """
        if not sorted_balances:
            return 0.0
        
        n = len(sorted_balances)
        cumsum = 0
        
        for i, balance in enumerate(sorted_balances):
            cumsum += balance * (2 * (i + 1) - n - 1)
        
        return cumsum / (n * sum(sorted_balances))
    
    def _interpret_gini_coefficient(self, gini: float) -> str:
        """
        Interpret Gini coefficient value
        """
        if gini < 0.3:
            return "Low inequality (well distributed)"
        elif gini < 0.5:
            return "Moderate inequality"
        elif gini < 0.7:
            return "High inequality"
        else:
            return "Very high inequality (concentrated)"
    
    def _determine_concentration_level(self, gini: float, hhi: float, cr4: float) -> str:
        """
        Determine overall concentration level
        """
        concentration_score = 0
        
        # Gini contribution (0-40 points)
        if gini > 0.8:
            concentration_score += 40
        elif gini > 0.6:
            concentration_score += 30
        elif gini > 0.4:
            concentration_score += 20
        else:
            concentration_score += 10
        
        # HHI contribution (0-30 points)
        if hhi > 0.25:  # Very concentrated
            concentration_score += 30
        elif hhi > 0.15:  # Moderately concentrated
            concentration_score += 20
        elif hhi > 0.1:  # Somewhat concentrated
            concentration_score += 10
        
        # CR4 contribution (0-30 points)
        if cr4 > 0.8:  # Top 4 hold >80%
            concentration_score += 30
        elif cr4 > 0.6:  # Top 4 hold >60%
            concentration_score += 20
        elif cr4 > 0.4:  # Top 4 hold >40%
            concentration_score += 10
        
        if concentration_score >= 80:
            return "Extremely concentrated"
        elif concentration_score >= 60:
            return "Highly concentrated"
        elif concentration_score >= 40:
            return "Moderately concentrated"
        else:
            return "Well distributed"
    
    def _analyze_whales(self, holder_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze whale holders (>5% of supply)
        """
        if not holder_data:
            return {}
        
        # Extract balances and calculate total
        balances = []
        addresses = []
        for holder in holder_data:
            balance = holder.get('balance', 0)
            address = holder.get('address', '')
            if isinstance(balance, (int, float)) and balance > 0:
                balances.append(balance)
                addresses.append(address)
        
        if not balances:
            return {}
        
        total_supply = sum(balances)
        
        # Identify whales
        whales = []
        whale_total = 0
        
        for i, balance in enumerate(balances):
            percentage = (balance / total_supply) * 100
            if percentage >= self.whale_threshold:
                whales.append({
                    'address': addresses[i] if i < len(addresses) else f"whale_{i+1}",
                    'balance': balance,
                    'percentage': percentage,
                    'whale_category': self._categorize_whale(percentage)
                })
                whale_total += balance
        
        # Sort whales by percentage
        whales.sort(key=lambda x: x['percentage'], reverse=True)
        
        analysis = {
            'whale_count': len(whales),
            'whale_total_percentage': (whale_total / total_supply) * 100 if total_supply > 0 else 0,
            'largest_whale_percentage': whales[0]['percentage'] if whales else 0,
            'whales': whales[:10],  # Top 10 whales
            'whale_risk_level': self._assess_whale_risk(len(whales), whale_total / total_supply if total_supply > 0 else 0)
        }
        
        return analysis
    
    def _categorize_whale(self, percentage: float) -> str:
        """
        Categorize whale by size
        """
        if percentage >= 25:
            return "Mega whale"
        elif percentage >= 15:
            return "Large whale"
        elif percentage >= 10:
            return "Medium whale"
        else:
            return "Small whale"
    
    def _assess_whale_risk(self, whale_count: int, whale_percentage: float) -> str:
        """
        Assess risk level from whale concentration
        """
        risk_score = 0
        
        # Whale count risk
        if whale_count >= 5:
            risk_score += 30
        elif whale_count >= 3:
            risk_score += 20
        elif whale_count >= 1:
            risk_score += 10
        
        # Whale percentage risk
        if whale_percentage >= 0.7:  # >70%
            risk_score += 40
        elif whale_percentage >= 0.5:  # >50%
            risk_score += 30
        elif whale_percentage >= 0.3:  # >30%
            risk_score += 20
        elif whale_percentage >= 0.1:  # >10%
            risk_score += 10
        
        if risk_score >= 60:
            return "Critical"
        elif risk_score >= 40:
            return "High"
        elif risk_score >= 20:
            return "Medium"
        else:
            return "Low"
    
    def _assess_concentration_risk(self, analysis: Dict) -> Dict[str, Any]:
        """
        Comprehensive concentration risk assessment
        """
        concentration_metrics = analysis.get('concentration_metrics', {})
        whale_analysis = analysis.get('whale_analysis', {})
        distribution = analysis.get('holder_distribution', {})
        
        risk_factors = []
        risk_score = 0
        
        # Gini coefficient risk
        gini = concentration_metrics.get('gini_coefficient', 0)
        if gini > 0.8:
            risk_factors.append("Extremely high wealth inequality")
            risk_score += 30
        elif gini > 0.6:
            risk_factors.append("High wealth inequality")
            risk_score += 20
        elif gini > 0.4:
            risk_factors.append("Moderate wealth inequality")
            risk_score += 10
        
        # Whale risk
        whale_count = whale_analysis.get('whale_count', 0)
        whale_percentage = whale_analysis.get('whale_total_percentage', 0)
        
        if whale_count >= 3 and whale_percentage >= 50:
            risk_factors.append("Multiple whales control majority")
            risk_score += 25
        elif whale_percentage >= 70:
            risk_factors.append("Whales control >70% of supply")
            risk_score += 30
        elif whale_percentage >= 50:
            risk_factors.append("Whales control >50% of supply")
            risk_score += 20
        
        # Top holder concentration
        top_10_percentage = distribution.get('top_10_percentage', 0)
        if top_10_percentage >= 90:
            risk_factors.append("Top 10 holders control >90%")
            risk_score += 20
        elif top_10_percentage >= 80:
            risk_factors.append("Top 10 holders control >80%")
            risk_score += 15
        
        # Determine overall risk level
        if risk_score >= 60:
            risk_level = "Critical"
        elif risk_score >= 40:
            risk_level = "High"
        elif risk_score >= 20:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'concentration_concerns': len(risk_factors) > 0
        }
    
    def _determine_distribution_quality(self, analysis: Dict) -> str:
        """
        Determine overall distribution quality
        """
        concentration_metrics = analysis.get('concentration_metrics', {})
        risk_assessment = analysis.get('risk_assessment', {})
        
        gini = concentration_metrics.get('gini_coefficient', 0)
        risk_level = risk_assessment.get('risk_level', 'Unknown')
        
        if gini < 0.3 and risk_level == 'Low':
            return "Excellent"
        elif gini < 0.5 and risk_level in ['Low', 'Medium']:
            return "Good"
        elif gini < 0.7 and risk_level in ['Low', 'Medium', 'High']:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_concentration_score(self, analysis: Dict) -> float:
        """
        Calculate overall concentration score (0-100, higher is better distribution)
        """
        concentration_metrics = analysis.get('concentration_metrics', {})
        risk_assessment = analysis.get('risk_assessment', {})
        
        # Start with base score
        score = 100
        
        # Subtract for high concentration
        gini = concentration_metrics.get('gini_coefficient', 0)
        score -= gini * 50  # Gini penalty (0-50 points)
        
        # Subtract for risk factors
        risk_score = risk_assessment.get('risk_score', 0)
        score -= risk_score  # Risk penalty (0-75+ points)
        
        # Ensure score is between 0-100
        return max(0, min(100, score))
    
    def _generate_concentration_alerts(self, analysis: Dict) -> List[str]:
        """
        Generate alerts based on concentration analysis
        """
        alerts = []
        
        concentration_metrics = analysis.get('concentration_metrics', {})
        whale_analysis = analysis.get('whale_analysis', {})
        risk_assessment = analysis.get('risk_assessment', {})
        
        # Gini coefficient alerts
        gini = concentration_metrics.get('gini_coefficient', 0)
        if gini > 0.8:
            alerts.append("🚨 CRITICAL: Extremely concentrated token distribution")
        elif gini > 0.7:
            alerts.append("⚠️ HIGH RISK: Very concentrated token distribution")
        
        # Whale alerts
        whale_percentage = whale_analysis.get('whale_total_percentage', 0)
        whale_count = whale_analysis.get('whale_count', 0)
        
        if whale_percentage > 70:
            alerts.append(f"🚨 WHALE RISK: {whale_count} whales control {whale_percentage:.1f}% of supply")
        elif whale_percentage > 50:
            alerts.append(f"⚠️ WHALE WARNING: {whale_count} whales control {whale_percentage:.1f}% of supply")
        
        # Risk level alerts
        risk_level = risk_assessment.get('risk_level', '')
        if risk_level == 'Critical':
            alerts.append("🚨 CRITICAL: Extreme concentration risk detected")
        elif risk_level == 'High':
            alerts.append("⚠️ HIGH RISK: Significant concentration concerns")
        
        return alerts 