"""
Market Context Analyzer

Provides enhanced market context through comparative analysis,
liquidity depth scoring, and market positioning assessment.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import statistics
from datetime import datetime

class MarketContextAnalyzer:
    """
    Advanced market context and comparative analysis
    """
    
    def __init__(self, birdeye_api, logger, config: Dict = None):
        self.birdeye_api = birdeye_api
        self.logger = logger
        self.config = config or {}
        
        # Market categorization thresholds
        self.market_cap_thresholds = {
            'nano': 1_000_000,      # $1M
            'micro': 10_000_000,    # $10M
            'small': 100_000_000,   # $100M
            'mid': 1_000_000_000,   # $1B
            'large': 10_000_000_000 # $10B
        }
        
        self.liquidity_thresholds = {
            'critical': 10_000,     # $10k
            'low': 100_000,         # $100k
            'medium': 1_000_000,    # $1M
            'high': 10_000_000      # $10M
        }
    
    async def analyze_market_context(self, token_address: str, basic_data: Dict) -> Dict[str, Any]:
        """
        Comprehensive market context analysis
        """
        self.logger.info(f"🌍 Starting market context analysis for {token_address[:8]}...")
        
        analysis = {
            'token_address': token_address,
            'analysis_timestamp': datetime.now().isoformat(),
            'market_classification': {},
            'liquidity_analysis': {},
            'comparative_metrics': {},
            'market_positioning': {},
            'trading_environment': {},
            'market_quality_score': 0,
            'context_alerts': [],
            'errors': []
        }
        
        try:
            metadata = basic_data.get('metadata', {})
            
            # Market classification
            analysis['market_classification'] = self._classify_market_position(metadata)
            
            # Liquidity analysis
            analysis['liquidity_analysis'] = await self._analyze_liquidity_depth(token_address, metadata)
            
            # Comparative metrics
            analysis['comparative_metrics'] = await self._calculate_comparative_metrics(token_address, metadata)
            
            # Market positioning
            analysis['market_positioning'] = self._assess_market_positioning(analysis)
            
            # Trading environment assessment
            analysis['trading_environment'] = self._assess_trading_environment(analysis)
            
            # Market quality score
            analysis['market_quality_score'] = self._calculate_market_quality_score(analysis)
            
            # Generate context alerts
            analysis['context_alerts'] = self._generate_context_alerts(analysis)
            
            self.logger.info(f"✅ Market context analysis completed for {token_address[:8]}")
            
        except Exception as e:
            self.logger.error(f"❌ Market context analysis failed: {e}")
            analysis['errors'].append(f"Analysis failed: {str(e)}")
            
        return analysis
    
    def _classify_market_position(self, metadata: Dict) -> Dict[str, Any]:
        """
        Classify token's market position
        """
        market_cap = metadata.get('market_cap', 0)
        liquidity = metadata.get('liquidity', 0)
        price = metadata.get('price', 0)
        
        # Market cap classification
        if market_cap >= self.market_cap_thresholds['large']:
            cap_category = "Large Cap"
        elif market_cap >= self.market_cap_thresholds['mid']:
            cap_category = "Mid Cap"
        elif market_cap >= self.market_cap_thresholds['small']:
            cap_category = "Small Cap"
        elif market_cap >= self.market_cap_thresholds['micro']:
            cap_category = "Micro Cap"
        elif market_cap >= self.market_cap_thresholds['nano']:
            cap_category = "Nano Cap"
        else:
            cap_category = "Sub-Nano Cap"
        
        # Liquidity classification
        if liquidity >= self.liquidity_thresholds['high']:
            liquidity_category = "High Liquidity"
        elif liquidity >= self.liquidity_thresholds['medium']:
            liquidity_category = "Medium Liquidity"
        elif liquidity >= self.liquidity_thresholds['low']:
            liquidity_category = "Low Liquidity"
        elif liquidity >= self.liquidity_thresholds['critical']:
            liquidity_category = "Critical Liquidity"
        else:
            liquidity_category = "Insufficient Liquidity"
        
        # Price tier classification
        if price >= 1000:
            price_tier = "High Price"
        elif price >= 1:
            price_tier = "Medium Price"
        elif price >= 0.01:
            price_tier = "Low Price"
        elif price >= 0.000001:
            price_tier = "Micro Price"
        else:
            price_tier = "Nano Price"
        
        # Market maturity assessment
        maturity = self._assess_market_maturity(market_cap, liquidity)
        
        return {
            'market_cap_category': cap_category,
            'liquidity_category': liquidity_category,
            'price_tier': price_tier,
            'market_maturity': maturity,
            'market_cap_usd': market_cap,
            'liquidity_usd': liquidity,
            'price_usd': price
        }
    
    def _assess_market_maturity(self, market_cap: float, liquidity: float) -> str:
        """
        Assess market maturity based on cap and liquidity
        """
        if market_cap >= 100_000_000 and liquidity >= 1_000_000:
            return "Mature Market"
        elif market_cap >= 10_000_000 and liquidity >= 100_000:
            return "Developing Market"
        elif market_cap >= 1_000_000 and liquidity >= 10_000:
            return "Emerging Market"
        else:
            return "Early Stage Market"
    
    async def _analyze_liquidity_depth(self, token_address: str, metadata: Dict) -> Dict[str, Any]:
        """
        Analyze liquidity depth and quality
        """
        liquidity = metadata.get('liquidity', 0)
        market_cap = metadata.get('market_cap', 0)
        volume_24h = metadata.get('volume_24h', 0)
        
        # Basic liquidity metrics
        liquidity_ratio = liquidity / market_cap if market_cap > 0 else 0
        volume_liquidity_ratio = volume_24h / liquidity if liquidity > 0 else 0
        
        # Liquidity quality assessment
        quality_score = self._calculate_liquidity_quality_score(liquidity, liquidity_ratio, volume_liquidity_ratio)
        
        # Liquidity risk assessment
        risk_assessment = self._assess_liquidity_risk(liquidity, liquidity_ratio)
        
        # Trading impact estimation
        trading_impact = self._estimate_trading_impact(liquidity, market_cap)
        
        analysis = {
            'total_liquidity': liquidity,
            'liquidity_to_mcap_ratio': liquidity_ratio,
            'volume_to_liquidity_ratio': volume_liquidity_ratio,
            'liquidity_quality_score': quality_score,
            'liquidity_risk': risk_assessment,
            'trading_impact': trading_impact,
            'liquidity_adequacy': self._assess_liquidity_adequacy(liquidity, market_cap),
            'slippage_estimate': self._estimate_slippage(liquidity)
        }
        
        return analysis
    
    def _calculate_liquidity_quality_score(self, liquidity: float, liquidity_ratio: float, volume_ratio: float) -> float:
        """
        Calculate liquidity quality score (0-100)
        """
        score = 0
        
        # Base liquidity score (0-40 points)
        if liquidity >= 10_000_000:
            score += 40
        elif liquidity >= 1_000_000:
            score += 30
        elif liquidity >= 100_000:
            score += 20
        elif liquidity >= 10_000:
            score += 10
        
        # Liquidity ratio score (0-30 points)
        if liquidity_ratio >= 0.1:  # 10%+ of market cap
            score += 30
        elif liquidity_ratio >= 0.05:  # 5%+ of market cap
            score += 20
        elif liquidity_ratio >= 0.02:  # 2%+ of market cap
            score += 10
        
        # Volume/liquidity ratio score (0-30 points)
        if 0.1 <= volume_ratio <= 2.0:  # Healthy range
            score += 30
        elif 0.05 <= volume_ratio <= 5.0:  # Acceptable range
            score += 20
        elif volume_ratio > 0:
            score += 10
        
        return min(100, score)
    
    def _assess_liquidity_risk(self, liquidity: float, liquidity_ratio: float) -> Dict[str, Any]:
        """
        Assess liquidity-related risks
        """
        risk_factors = []
        risk_score = 0
        
        # Absolute liquidity risk
        if liquidity < 10_000:
            risk_factors.append("Extremely low absolute liquidity")
            risk_score += 40
        elif liquidity < 100_000:
            risk_factors.append("Low absolute liquidity")
            risk_score += 25
        
        # Relative liquidity risk
        if liquidity_ratio < 0.01:  # <1% of market cap
            risk_factors.append("Very low liquidity relative to market cap")
            risk_score += 30
        elif liquidity_ratio < 0.02:  # <2% of market cap
            risk_factors.append("Low liquidity relative to market cap")
            risk_score += 15
        
        # Risk level determination
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
            'risk_factors': risk_factors
        }
    
    def _estimate_trading_impact(self, liquidity: float, market_cap: float) -> Dict[str, Any]:
        """
        Estimate trading impact for different trade sizes
        """
        # Trade size scenarios as % of liquidity
        scenarios = {
            'small': 0.01,    # 1% of liquidity
            'medium': 0.05,   # 5% of liquidity
            'large': 0.1,     # 10% of liquidity
            'whale': 0.2      # 20% of liquidity
        }
        
        impact_estimates = {}
        for scenario, pct in scenarios.items():
            trade_size = liquidity * pct
            
            # Simplified impact estimation (square root model)
            if liquidity > 0:
                impact_pct = (trade_size / liquidity) * 100
                impact_estimates[scenario] = {
                    'trade_size_usd': trade_size,
                    'estimated_impact_pct': impact_pct,
                    'impact_category': self._categorize_impact(impact_pct)
                }
        
        return {
            'impact_scenarios': impact_estimates,
            'liquidity_depth_rating': self._rate_liquidity_depth(liquidity),
            'suitable_for_large_trades': liquidity >= 1_000_000
        }
    
    def _categorize_impact(self, impact_pct: float) -> str:
        """
        Categorize trading impact
        """
        if impact_pct >= 10:
            return "Very High Impact"
        elif impact_pct >= 5:
            return "High Impact"
        elif impact_pct >= 2:
            return "Medium Impact"
        elif impact_pct >= 1:
            return "Low Impact"
        else:
            return "Minimal Impact"
    
    def _rate_liquidity_depth(self, liquidity: float) -> str:
        """
        Rate overall liquidity depth
        """
        if liquidity >= 10_000_000:
            return "Excellent"
        elif liquidity >= 1_000_000:
            return "Good"
        elif liquidity >= 100_000:
            return "Fair"
        elif liquidity >= 10_000:
            return "Poor"
        else:
            return "Critical"
    
    def _assess_liquidity_adequacy(self, liquidity: float, market_cap: float) -> str:
        """
        Assess if liquidity is adequate for market cap
        """
        if market_cap <= 0:
            return "Cannot assess"
        
        ratio = liquidity / market_cap
        
        if ratio >= 0.1:
            return "Excellent liquidity for market cap"
        elif ratio >= 0.05:
            return "Good liquidity for market cap"
        elif ratio >= 0.02:
            return "Adequate liquidity for market cap"
        elif ratio >= 0.01:
            return "Low liquidity for market cap"
        else:
            return "Insufficient liquidity for market cap"
    
    def _estimate_slippage(self, liquidity: float) -> Dict[str, float]:
        """
        Estimate slippage for different trade sizes
        """
        # Simplified slippage estimation
        trade_sizes = [1000, 5000, 10000, 50000, 100000]  # USD amounts
        
        slippage_estimates = {}
        for size in trade_sizes:
            if liquidity > 0:
                # Simplified model: slippage increases with trade size
                slippage_pct = (size / liquidity) * 100 * 0.5  # Rough approximation
                slippage_estimates[f"${size:,}"] = min(50, slippage_pct)  # Cap at 50%
            else:
                slippage_estimates[f"${size:,}"] = 50  # Max slippage for no liquidity
        
        return slippage_estimates
    
    async def _calculate_comparative_metrics(self, token_address: str, metadata: Dict) -> Dict[str, Any]:
        """
        Calculate comparative metrics against market benchmarks
        """
        # This would ideally compare against similar tokens
        # For now, we'll use statistical benchmarks
        
        market_cap = metadata.get('market_cap', 0)
        liquidity = metadata.get('liquidity', 0)
        volume_24h = metadata.get('volume_24h', 0)
        
        # Market cap percentiles (rough estimates for crypto market)
        market_cap_percentiles = {
            '99th': 10_000_000_000,   # $10B
            '95th': 1_000_000_000,    # $1B
            '90th': 100_000_000,      # $100M
            '75th': 10_000_000,       # $10M
            '50th': 1_000_000,        # $1M
            '25th': 100_000,          # $100k
            '10th': 10_000,           # $10k
        }
        
        # Find market cap percentile
        market_cap_percentile = self._find_percentile(market_cap, market_cap_percentiles)
        
        # Liquidity efficiency (liquidity relative to market cap)
        liquidity_efficiency = liquidity / market_cap if market_cap > 0 else 0
        
        # Volume efficiency (volume relative to market cap)
        volume_efficiency = volume_24h / market_cap if market_cap > 0 else 0
        
        return {
            'market_cap_percentile': market_cap_percentile,
            'liquidity_efficiency': liquidity_efficiency,
            'volume_efficiency': volume_efficiency,
            'relative_performance': self._assess_relative_performance(market_cap_percentile, liquidity_efficiency),
            'market_position_summary': self._summarize_market_position(market_cap_percentile, liquidity_efficiency, volume_efficiency)
        }
    
    def _find_percentile(self, value: float, percentiles: Dict[str, float]) -> str:
        """
        Find which percentile a value falls into
        """
        for percentile, threshold in percentiles.items():
            if value >= threshold:
                return f"Above {percentile} percentile"
        return "Below 10th percentile"
    
    def _assess_relative_performance(self, cap_percentile: str, liquidity_efficiency: float) -> str:
        """
        Assess relative performance vs peers
        """
        # Simplified assessment
        if "99th" in cap_percentile or "95th" in cap_percentile:
            if liquidity_efficiency >= 0.05:
                return "Top tier with excellent liquidity"
            else:
                return "Top tier but liquidity concerns"
        elif "90th" in cap_percentile or "75th" in cap_percentile:
            if liquidity_efficiency >= 0.03:
                return "Upper tier with good liquidity"
            else:
                return "Upper tier but liquidity issues"
        elif "50th" in cap_percentile:
            if liquidity_efficiency >= 0.02:
                return "Mid-tier with adequate liquidity"
            else:
                return "Mid-tier with liquidity concerns"
        else:
            if liquidity_efficiency >= 0.01:
                return "Lower tier but decent liquidity"
            else:
                return "Lower tier with poor liquidity"
    
    def _summarize_market_position(self, cap_percentile: str, liquidity_eff: float, volume_eff: float) -> str:
        """
        Summarize overall market position
        """
        position_score = 0
        
        # Market cap score
        if "99th" in cap_percentile:
            position_score += 40
        elif "95th" in cap_percentile:
            position_score += 35
        elif "90th" in cap_percentile:
            position_score += 30
        elif "75th" in cap_percentile:
            position_score += 25
        elif "50th" in cap_percentile:
            position_score += 15
        else:
            position_score += 5
        
        # Liquidity efficiency score
        if liquidity_eff >= 0.1:
            position_score += 30
        elif liquidity_eff >= 0.05:
            position_score += 25
        elif liquidity_eff >= 0.02:
            position_score += 15
        elif liquidity_eff >= 0.01:
            position_score += 10
        else:
            position_score += 0
        
        # Volume efficiency score
        if volume_eff >= 0.5:
            position_score += 30
        elif volume_eff >= 0.2:
            position_score += 25
        elif volume_eff >= 0.1:
            position_score += 15
        elif volume_eff >= 0.05:
            position_score += 10
        else:
            position_score += 0
        
        if position_score >= 80:
            return "Excellent market position"
        elif position_score >= 60:
            return "Strong market position"
        elif position_score >= 40:
            return "Good market position"
        elif position_score >= 20:
            return "Weak market position"
        else:
            return "Poor market position"
    
    def _assess_market_positioning(self, analysis: Dict) -> Dict[str, Any]:
        """
        Assess overall market positioning
        """
        classification = analysis.get('market_classification', {})
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        comparative_metrics = analysis.get('comparative_metrics', {})
        
        # Competitive advantages
        advantages = []
        disadvantages = []
        
        # Market cap advantages
        cap_category = classification.get('market_cap_category', '')
        if cap_category in ['Large Cap', 'Mid Cap']:
            advantages.append("Established market presence")
        elif cap_category in ['Small Cap', 'Micro Cap']:
            advantages.append("Growth potential")
        else:
            disadvantages.append("Very small market presence")
        
        # Liquidity advantages/disadvantages
        liquidity_quality = liquidity_analysis.get('liquidity_quality_score', 0)
        if liquidity_quality >= 70:
            advantages.append("Excellent liquidity")
        elif liquidity_quality >= 50:
            advantages.append("Good liquidity")
        elif liquidity_quality >= 30:
            disadvantages.append("Limited liquidity")
        else:
            disadvantages.append("Poor liquidity")
        
        # Market maturity
        maturity = classification.get('market_maturity', '')
        if maturity == 'Mature Market':
            advantages.append("Mature market dynamics")
        elif maturity == 'Developing Market':
            advantages.append("Developing market with potential")
        else:
            disadvantages.append("Early stage market risks")
        
        return {
            'competitive_advantages': advantages,
            'competitive_disadvantages': disadvantages,
            'market_opportunity': self._assess_market_opportunity(classification, liquidity_analysis),
            'investment_suitability': self._assess_investment_suitability(analysis),
            'trading_suitability': self._assess_trading_suitability(liquidity_analysis)
        }
    
    def _assess_market_opportunity(self, classification: Dict, liquidity_analysis: Dict) -> str:
        """
        Assess market opportunity
        """
        cap_category = classification.get('market_cap_category', '')
        maturity = classification.get('market_maturity', '')
        liquidity_quality = liquidity_analysis.get('liquidity_quality_score', 0)
        
        if cap_category in ['Small Cap', 'Micro Cap'] and maturity in ['Developing Market', 'Emerging Market'] and liquidity_quality >= 50:
            return "High growth opportunity with adequate infrastructure"
        elif cap_category in ['Large Cap', 'Mid Cap'] and liquidity_quality >= 70:
            return "Stable opportunity with excellent infrastructure"
        elif cap_category in ['Nano Cap', 'Sub-Nano Cap'] and liquidity_quality >= 30:
            return "Speculative opportunity with limited infrastructure"
        else:
            return "Limited opportunity due to poor market conditions"
    
    def _assess_investment_suitability(self, analysis: Dict) -> Dict[str, str]:
        """
        Assess suitability for different investment types
        """
        classification = analysis.get('market_classification', {})
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        
        cap_category = classification.get('market_cap_category', '')
        liquidity_risk = liquidity_analysis.get('liquidity_risk', {}).get('risk_level', 'High')
        
        suitability = {}
        
        # Conservative investors
        if cap_category in ['Large Cap', 'Mid Cap'] and liquidity_risk in ['Low', 'Medium']:
            suitability['conservative'] = "Suitable with proper risk management"
        else:
            suitability['conservative'] = "Not suitable"
        
        # Moderate investors
        if cap_category in ['Large Cap', 'Mid Cap', 'Small Cap'] and liquidity_risk != 'Critical':
            suitability['moderate'] = "Suitable with diversification"
        else:
            suitability['moderate'] = "High risk - limited allocation only"
        
        # Aggressive investors
        if liquidity_risk != 'Critical':
            suitability['aggressive'] = "Suitable for speculative allocation"
        else:
            suitability['aggressive'] = "Extreme risk - micro allocation only"
        
        return suitability
    
    def _assess_trading_suitability(self, liquidity_analysis: Dict) -> Dict[str, str]:
        """
        Assess suitability for different trading styles
        """
        liquidity_quality = liquidity_analysis.get('liquidity_quality_score', 0)
        liquidity_risk = liquidity_analysis.get('liquidity_risk', {}).get('risk_level', 'High')
        
        suitability = {}
        
        # Scalping
        if liquidity_quality >= 80 and liquidity_risk == 'Low':
            suitability['scalping'] = "Excellent for scalping"
        elif liquidity_quality >= 60:
            suitability['scalping'] = "Suitable for scalping with caution"
        else:
            suitability['scalping'] = "Not suitable for scalping"
        
        # Day trading
        if liquidity_quality >= 60 and liquidity_risk in ['Low', 'Medium']:
            suitability['day_trading'] = "Good for day trading"
        elif liquidity_quality >= 40:
            suitability['day_trading'] = "Possible but with higher risk"
        else:
            suitability['day_trading'] = "Poor for day trading"
        
        # Swing trading
        if liquidity_quality >= 40:
            suitability['swing_trading'] = "Suitable for swing trading"
        elif liquidity_quality >= 20:
            suitability['swing_trading'] = "Marginal for swing trading"
        else:
            suitability['swing_trading'] = "Poor for swing trading"
        
        return suitability
    
    def _assess_trading_environment(self, analysis: Dict) -> Dict[str, Any]:
        """
        Assess overall trading environment
        """
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        classification = analysis.get('market_classification', {})
        
        liquidity_quality = liquidity_analysis.get('liquidity_quality_score', 0)
        trading_impact = liquidity_analysis.get('trading_impact', {})
        
        # Trading environment factors
        environment_factors = []
        environment_score = 0
        
        # Liquidity factor
        if liquidity_quality >= 70:
            environment_factors.append("Excellent liquidity environment")
            environment_score += 30
        elif liquidity_quality >= 50:
            environment_factors.append("Good liquidity environment")
            environment_score += 20
        elif liquidity_quality >= 30:
            environment_factors.append("Moderate liquidity environment")
            environment_score += 10
        else:
            environment_factors.append("Poor liquidity environment")
        
        # Market maturity factor
        maturity = classification.get('market_maturity', '')
        if maturity == 'Mature Market':
            environment_factors.append("Mature trading environment")
            environment_score += 25
        elif maturity == 'Developing Market':
            environment_factors.append("Developing trading environment")
            environment_score += 15
        else:
            environment_factors.append("Early stage trading environment")
            environment_score += 5
        
        # Trading impact factor
        suitable_for_large = trading_impact.get('suitable_for_large_trades', False)
        if suitable_for_large:
            environment_factors.append("Suitable for institutional trading")
            environment_score += 20
        else:
            environment_factors.append("Limited to retail trading")
            environment_score += 5
        
        # Overall assessment
        if environment_score >= 60:
            overall_assessment = "Excellent trading environment"
        elif environment_score >= 40:
            overall_assessment = "Good trading environment"
        elif environment_score >= 20:
            overall_assessment = "Moderate trading environment"
        else:
            overall_assessment = "Poor trading environment"
        
        return {
            'environment_score': environment_score,
            'overall_assessment': overall_assessment,
            'environment_factors': environment_factors,
            'institutional_suitable': suitable_for_large,
            'retail_suitable': liquidity_quality >= 20
        }
    
    def _calculate_market_quality_score(self, analysis: Dict) -> float:
        """
        Calculate overall market quality score (0-100)
        """
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        comparative_metrics = analysis.get('comparative_metrics', {})
        trading_environment = analysis.get('trading_environment', {})
        
        # Component scores
        liquidity_score = liquidity_analysis.get('liquidity_quality_score', 0) * 0.4  # 40% weight
        
        # Market position score (based on percentile)
        position_score = 0
        cap_percentile = comparative_metrics.get('market_cap_percentile', '')
        if "99th" in cap_percentile:
            position_score = 100
        elif "95th" in cap_percentile:
            position_score = 90
        elif "90th" in cap_percentile:
            position_score = 80
        elif "75th" in cap_percentile:
            position_score = 70
        elif "50th" in cap_percentile:
            position_score = 50
        else:
            position_score = 20
        
        position_score *= 0.3  # 30% weight
        
        # Trading environment score
        environment_score = trading_environment.get('environment_score', 0) * 0.3  # 30% weight
        
        total_score = liquidity_score + position_score + environment_score
        
        return min(100, max(0, total_score))
    
    def _generate_context_alerts(self, analysis: Dict) -> List[str]:
        """
        Generate market context alerts
        """
        alerts = []
        
        liquidity_analysis = analysis.get('liquidity_analysis', {})
        classification = analysis.get('market_classification', {})
        market_quality = analysis.get('market_quality_score', 0)
        
        # Liquidity alerts
        liquidity_risk = liquidity_analysis.get('liquidity_risk', {})
        if liquidity_risk.get('risk_level') == 'Critical':
            alerts.append("🚨 CRITICAL: Extremely poor liquidity conditions")
        elif liquidity_risk.get('risk_level') == 'High':
            alerts.append("⚠️ HIGH RISK: Poor liquidity conditions")
        
        # Market cap alerts
        cap_category = classification.get('market_cap_category', '')
        if cap_category in ['Sub-Nano Cap', 'Nano Cap']:
            alerts.append("⚠️ MICRO CAP: Very small market capitalization")
        
        # Market quality alerts
        if market_quality < 30:
            alerts.append("🚨 POOR MARKET: Low overall market quality")
        elif market_quality < 50:
            alerts.append("⚠️ MARKET CONCERNS: Below average market quality")
        
        # Trading environment alerts
        trading_env = analysis.get('trading_environment', {})
        if not trading_env.get('retail_suitable', True):
            alerts.append("⚠️ TRADING RISK: Poor conditions for retail trading")
        
        return alerts 