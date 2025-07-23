#!/usr/bin/env python3
"""
Comprehensive Strategy Comparison Script (Enhanced Deep Analysis v3.0)

This script now includes deep token analysis capabilities with holder concentration,
price volatility, market context analysis, risk assessment, and quality scoring
for comprehensive strategy evaluation based on token quality, not just quantity.
"""

import asyncio
import sys
import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UPDATED: Import the newly optimized strategy classes
from core.strategies.volume_momentum_strategy import VolumeMomentumStrategy
from core.strategies.recent_listings_strategy import RecentListingsStrategy
from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.strategies.liquidity_growth_strategy import LiquidityGrowthStrategy
from core.strategies.high_trading_activity_strategy import HighTradingActivityStrategy
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import get_config_manager
from services.logger_setup import LoggerSetup


@dataclass
class TokenAnalysis:
    """Deep analysis results for a single token"""
    address: str
    symbol: str
    basic_data: Dict[str, Any]
    holder_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]
    market_analysis: Dict[str, Any]
    quality_score: float
    risk_level: str
    risk_score: float
    grade: str
    alerts: List[str]
    analysis_success: bool = True
    analysis_error: str = None


@dataclass
class EnhancedStrategyResult:
    """Enhanced strategy execution results with deep token analysis"""
    name: str
    description: str
    execution_time: float
    tokens_found: int
    api_calls_made: int
    cache_hits: int
    cache_misses: int
    
    # Basic token metrics
    avg_volume_24h: float
    avg_price_change_24h: float
    avg_market_cap: float
    avg_liquidity: float
    avg_consecutive_appearances: float
    high_quality_tokens: int
    unique_tokens: int
    
    # Enhanced batch metrics
    batch_efficiency_ratio: float
    estimated_cu_saved: float
    cost_optimization_grade: str
    batch_enriched_tokens: int
    api_call_breakdown: Dict[str, Any] = None
    
    # ENHANCED: Deep analysis metrics
    token_analyses: List[TokenAnalysis] = None
    avg_quality_score: float = 0.0
    avg_risk_score: float = 0.0
    quality_distribution: Dict[str, int] = None
    risk_distribution: Dict[str, int] = None
    high_quality_percentage: float = 0.0
    low_risk_percentage: float = 0.0
    strategy_quality_grade: str = "N/A"
    critical_alerts: int = 0
    
    # Top quality tokens
    top_quality_tokens: List[Dict[str, Any]] = None
    error: str = None


class TokenQualityAnalyzer:
    """Deep token quality analysis similar to Phase3DeepTokenAnalyzer"""
    
    def __init__(self, birdeye_api: BirdeyeAPI, logger):
        self.birdeye_api = birdeye_api
        self.logger = logger
    
    async def analyze_token_comprehensive(self, token_address: str, basic_token_data: Dict = None) -> TokenAnalysis:
        """
        Comprehensive token analysis with holder concentration, volatility, and market context
        """
        try:
            symbol = basic_token_data.get('symbol', 'Unknown') if basic_token_data else 'Unknown'
            
            self.logger.debug(f"🔍 Deep analysis for {symbol} ({token_address[:8]}...)")
            
            # 1. Enhanced basic data (if not provided)
            if not basic_token_data:
                basic_data = await self._fetch_basic_token_data(token_address)
            else:
                basic_data = basic_token_data
                # Enhance with additional data
                overview = await self.birdeye_api.get_token_overview(token_address)
                if overview:
                    basic_data.update(overview)
            
            # 2. Holder concentration analysis
            holder_analysis = await self._analyze_holder_concentration(token_address)
            
            # 3. Price volatility analysis
            volatility_analysis = await self._analyze_price_volatility(token_address)
            
            # 4. Market context analysis
            market_analysis = await self._analyze_market_context(token_address, basic_data)
            
            # 5. Calculate quality metrics
            quality_score, grade = self._calculate_quality_score(
                basic_data, holder_analysis, volatility_analysis, market_analysis
            )
            
            # 6. Risk assessment
            risk_level, risk_score = self._assess_risk_level(
                holder_analysis, volatility_analysis, market_analysis
            )
            
            # 7. Compile alerts
            alerts = self._compile_alerts(holder_analysis, volatility_analysis, market_analysis, risk_level)
            
            return TokenAnalysis(
                address=token_address,
                symbol=symbol,
                basic_data=basic_data,
                holder_analysis=holder_analysis,
                volatility_analysis=volatility_analysis,
                market_analysis=market_analysis,
                quality_score=quality_score,
                risk_level=risk_level,
                risk_score=risk_score,
                grade=grade,
                alerts=alerts,
                analysis_success=True
            )
            
        except Exception as e:
            self.logger.warning(f"Deep analysis failed for {token_address[:8]}: {e}")
            return TokenAnalysis(
                address=token_address,
                symbol=basic_token_data.get('symbol', 'Unknown') if basic_token_data else 'Unknown',
                basic_data=basic_token_data or {},
                holder_analysis={},
                volatility_analysis={},
                market_analysis={},
                quality_score=0.0,
                risk_level="Unknown",
                risk_score=100.0,
                grade="F",
                alerts=[],
                analysis_success=False,
                analysis_error=str(e)
            )
    
    async def _fetch_basic_token_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch basic token data"""
        try:
            overview = await self.birdeye_api.get_token_overview(token_address)
            age_days, age_description = await self.birdeye_api.get_token_age(token_address)
            security = await self.birdeye_api.get_token_security(token_address)
            
            return {
                'overview': overview or {},
                'age_days': age_days,
                'age_description': age_description,
                'security': security or {}
            }
        except Exception as e:
            self.logger.debug(f"Error fetching basic data for {token_address[:8]}: {e}")
            return {}
    
    async def _analyze_holder_concentration(self, token_address: str) -> Dict[str, Any]:
        """Analyze holder concentration"""
        try:
            holders_data = await self.birdeye_api.get_token_holders(token_address, limit=100)
            
            if not holders_data or not isinstance(holders_data, dict):
                return {'analysis_available': False, 'error': 'No holder data available'}
            
            holders = holders_data.get('data', {}).get('items', [])
            if not holders:
                return {'analysis_available': False, 'error': 'No holder items found'}
            
            # Calculate concentration metrics
            total_holders = len(holders)
            percentages = [holder.get('percentage', 0) for holder in holders if holder.get('percentage', 0) > 0]
            
            if not percentages:
                return {'analysis_available': False, 'error': 'No valid holder percentages'}
            
            top_1_percentage = percentages[0] if percentages else 0
            top_5_percentage = sum(percentages[:5]) if len(percentages) >= 5 else sum(percentages)
            top_10_percentage = sum(percentages[:10]) if len(percentages) >= 10 else sum(percentages)
            
            # Whale analysis (holders with >5% of supply)
            whales = [h for h in holders if h.get('percentage', 0) >= 5.0]
            whale_count = len(whales)
            whale_total_percentage = sum(h.get('percentage', 0) for h in whales)
            
            # Risk assessment
            concentration_risk = 'Low'
            if top_1_percentage >= 50:
                concentration_risk = 'Critical'
            elif top_5_percentage >= 80:
                concentration_risk = 'High'
            elif whale_count >= 3:
                concentration_risk = 'Medium'
            
            # Concentration score (lower concentration = higher score)
            concentration_score = max(0, 100 - top_10_percentage)
            
            return {
                'analysis_available': True,
                'total_holders': total_holders,
                'top_1_percentage': top_1_percentage,
                'top_5_percentage': top_5_percentage,
                'top_10_percentage': top_10_percentage,
                'whale_count': whale_count,
                'whale_total_percentage': whale_total_percentage,
                'concentration_risk': concentration_risk,
                'concentration_score': concentration_score
            }
            
        except Exception as e:
            return {'analysis_available': False, 'error': f'Analysis failed: {str(e)}'}
    
    async def _analyze_price_volatility(self, token_address: str) -> Dict[str, Any]:
        """Analyze price volatility using transaction data"""
        try:
            transactions = await self.birdeye_api.get_token_transactions(token_address, limit=50, max_pages=2)
            
            if not transactions:
                return {'analysis_available': False, 'error': 'No transaction data available'}
            
            # Extract prices from transactions
            prices = []
            for tx in transactions:
                price = 0
                if 'price' in tx:
                    price = tx['price']
                elif 'priceInUsd' in tx:
                    price = tx['priceInUsd']
                elif 'from' in tx and isinstance(tx['from'], dict) and 'priceInUsd' in tx['from']:
                    price = tx['from']['priceInUsd']
                elif 'to' in tx and isinstance(tx['to'], dict) and 'priceInUsd' in tx['to']:
                    price = tx['to']['priceInUsd']
                
                if isinstance(price, (int, float)) and price > 0:
                    prices.append(price)
            
            if len(prices) < 5:
                return {'analysis_available': False, 'error': 'Insufficient price data points'}
            
            # Calculate volatility metrics
            current_price = prices[0]
            max_price = max(prices)
            min_price = min(prices)
            mean_price = statistics.mean(prices)
            
            price_range_pct = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
            price_std = statistics.stdev(prices) if len(prices) > 1 else 0
            volatility_coefficient = price_std / mean_price if mean_price > 0 else 0
            
            # Volatility classification
            if volatility_coefficient >= 0.3:
                volatility_class = "Extremely volatile"
                volatility_risk = "Critical"
            elif volatility_coefficient >= 0.15:
                volatility_class = "Highly volatile"
                volatility_risk = "High"
            elif volatility_coefficient >= 0.05:
                volatility_class = "Moderately volatile"
                volatility_risk = "Medium"
            else:
                volatility_class = "Low volatility"
                volatility_risk = "Low"
            
            # Volatility score (inverse of volatility)
            volatility_score = max(0, 100 - (volatility_coefficient * 200))
            
            return {
                'analysis_available': True,
                'price_points_analyzed': len(prices),
                'current_price': current_price,
                'max_price': max_price,
                'min_price': min_price,
                'mean_price': mean_price,
                'price_range_percentage': price_range_pct,
                'standard_deviation': price_std,
                'volatility_coefficient': volatility_coefficient,
                'volatility_classification': volatility_class,
                'volatility_risk': volatility_risk,
                'volatility_score': volatility_score
            }
            
        except Exception as e:
            return {'analysis_available': False, 'error': f'Analysis failed: {str(e)}'}
    
    async def _analyze_market_context(self, token_address: str, basic_data: Dict) -> Dict[str, Any]:
        """Analyze market context"""
        try:
            overview = basic_data.get('overview', {})
            age_days = basic_data.get('age_days', 0)
            
            # Extract key metrics
            market_cap = overview.get('marketCap', 0) or overview.get('market_cap', 0)
            liquidity = overview.get('liquidity', 0)
            volume_24h = overview.get('volume', {}).get('h24', 0) if isinstance(overview.get('volume'), dict) else overview.get('volume_24h', 0)
            price = overview.get('price', 0)
            
            # Market classification
            if market_cap >= 1_000_000_000:
                cap_category = "Large Cap"
            elif market_cap >= 100_000_000:
                cap_category = "Mid Cap"
            elif market_cap >= 10_000_000:
                cap_category = "Small Cap"
            elif market_cap >= 1_000_000:
                cap_category = "Micro Cap"
            else:
                cap_category = "Nano Cap"
            
            # Liquidity classification
            if liquidity >= 10_000_000:
                liquidity_category = "High Liquidity"
            elif liquidity >= 1_000_000:
                liquidity_category = "Medium Liquidity"
            elif liquidity >= 100_000:
                liquidity_category = "Low Liquidity"
            elif liquidity >= 10_000:
                liquidity_category = "Critical Liquidity"
            else:
                liquidity_category = "Insufficient Liquidity"
            
            # Market maturity
            if age_days >= 365:
                maturity = "Mature Market"
            elif age_days >= 90:
                maturity = "Developing Market"
            elif age_days >= 30:
                maturity = "Emerging Market"
            else:
                maturity = "Early Stage Market"
            
            # Market quality score
            market_quality_score = 0
            
            # Market cap score (0-30)
            if market_cap >= 100_000_000:
                market_quality_score += 30
            elif market_cap >= 10_000_000:
                market_quality_score += 20
            elif market_cap >= 1_000_000:
                market_quality_score += 10
            
            # Liquidity score (0-40)
            if liquidity >= 1_000_000:
                market_quality_score += 40
            elif liquidity >= 100_000:
                market_quality_score += 25
            elif liquidity >= 10_000:
                market_quality_score += 10
            
            # Age/maturity score (0-30)
            if age_days >= 365:
                market_quality_score += 30
            elif age_days >= 90:
                market_quality_score += 20
            elif age_days >= 30:
                market_quality_score += 10
            
            return {
                'analysis_available': True,
                'market_cap': market_cap,
                'liquidity': liquidity,
                'volume_24h': volume_24h,
                'price': price,
                'age_days': age_days,
                'cap_category': cap_category,
                'liquidity_category': liquidity_category,
                'market_maturity': maturity,
                'market_quality_score': market_quality_score
            }
            
        except Exception as e:
            return {'analysis_available': False, 'error': f'Analysis failed: {str(e)}'}
    
    def _calculate_quality_score(self, basic_data: Dict, holder_analysis: Dict, 
                                volatility_analysis: Dict, market_analysis: Dict) -> Tuple[float, str]:
        """Calculate overall quality score and grade"""
        
        # Component scores
        holder_score = holder_analysis.get('concentration_score', 50) if holder_analysis.get('analysis_available') else 50
        volatility_score = volatility_analysis.get('volatility_score', 50) if volatility_analysis.get('analysis_available') else 50
        market_score = market_analysis.get('market_quality_score', 50) if market_analysis.get('analysis_available') else 50
        
        # Data quality bonus
        data_quality_bonus = 0
        if basic_data.get('overview'):
            data_quality_bonus += 5
        if basic_data.get('age_days', 0) > 0:
            data_quality_bonus += 5
        
        # Weighted average
        weights = {'holder': 0.35, 'volatility': 0.35, 'market': 0.30}
        quality_score = (
            holder_score * weights['holder'] +
            volatility_score * weights['volatility'] +
            market_score * weights['market'] +
            data_quality_bonus
        )
        
        # Determine grade
        if quality_score >= 85:
            grade = "A+"
        elif quality_score >= 80:
            grade = "A"
        elif quality_score >= 75:
            grade = "A-"
        elif quality_score >= 70:
            grade = "B+"
        elif quality_score >= 65:
            grade = "B"
        elif quality_score >= 60:
            grade = "B-"
        elif quality_score >= 55:
            grade = "C+"
        elif quality_score >= 50:
            grade = "C"
        elif quality_score >= 45:
            grade = "C-"
        elif quality_score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        return quality_score, grade
    
    def _assess_risk_level(self, holder_analysis: Dict, volatility_analysis: Dict, 
                          market_analysis: Dict) -> Tuple[str, float]:
        """Assess overall risk level and score"""
        
        risk_score = 0
        
        # Holder concentration risk
        if holder_analysis.get('analysis_available'):
            concentration_risk = holder_analysis.get('concentration_risk', 'Low')
            if concentration_risk == 'Critical':
                risk_score += 35
            elif concentration_risk == 'High':
                risk_score += 25
            elif concentration_risk == 'Medium':
                risk_score += 15
        
        # Volatility risk
        if volatility_analysis.get('analysis_available'):
            volatility_risk = volatility_analysis.get('volatility_risk', 'Low')
            if volatility_risk == 'Critical':
                risk_score += 30
            elif volatility_risk == 'High':
                risk_score += 20
            elif volatility_risk == 'Medium':
                risk_score += 10
        
        # Market/liquidity risk
        if market_analysis.get('analysis_available'):
            liquidity_category = market_analysis.get('liquidity_category', '')
            if 'Insufficient' in liquidity_category:
                risk_score += 25
            elif 'Critical' in liquidity_category:
                risk_score += 15
            elif 'Low' in liquidity_category:
                risk_score += 8
            
            # Age risk
            age_days = market_analysis.get('age_days', 0)
            if age_days < 7:
                risk_score += 15
            elif age_days < 30:
                risk_score += 8
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "Extreme"
        elif risk_score >= 50:
            risk_level = "High"
        elif risk_score >= 30:
            risk_level = "Medium"
        elif risk_score >= 15:
            risk_level = "Low"
        else:
            risk_level = "Very Low"
        
        return risk_level, min(100, risk_score)
    
    def _compile_alerts(self, holder_analysis: Dict, volatility_analysis: Dict, 
                       market_analysis: Dict, risk_level: str) -> List[str]:
        """Compile alerts based on analysis"""
        alerts = []
        
        # Holder concentration alerts
        if holder_analysis.get('analysis_available'):
            concentration_risk = holder_analysis.get('concentration_risk', 'Low')
            if concentration_risk == 'Critical':
                alerts.append("🚨 CRITICAL: Extreme holder concentration")
            elif concentration_risk == 'High':
                alerts.append("⚠️ HIGH RISK: Significant holder concentration")
        
        # Volatility alerts
        if volatility_analysis.get('analysis_available'):
            volatility_risk = volatility_analysis.get('volatility_risk', 'Low')
            if volatility_risk == 'Critical':
                alerts.append("🚨 EXTREME VOLATILITY: Price movements are extremely volatile")
            elif volatility_risk == 'High':
                alerts.append("⚠️ HIGH VOLATILITY: Significant price swings detected")
        
        # Market alerts
        if market_analysis.get('analysis_available'):
            liquidity_category = market_analysis.get('liquidity_category', '')
            if 'Insufficient' in liquidity_category:
                alerts.append("🚨 CRITICAL: Insufficient liquidity for safe trading")
            elif 'Critical' in liquidity_category:
                alerts.append("⚠️ LIQUIDITY RISK: Critical liquidity levels")
        
        # Overall risk alert
        if risk_level == 'Extreme':
            alerts.append("🚨 EXTREME RISK: Multiple high-risk factors detected")
        elif risk_level == 'High':
            alerts.append("⚠️ HIGH RISK: Significant risk factors present")
        
        return alerts


@dataclass
class ComparisonMetrics:
    """Enhanced metrics for comparing strategies including batch efficiency and token quality"""
    efficiency_score: float  # tokens found per second
    quality_score: float     # average quality score of tokens found
    risk_score: float        # average risk score of tokens found
    diversity_score: float   # uniqueness of token selection
    volume_focus: float      # average volume of discovered tokens
    growth_focus: float      # average price change of discovered tokens
    market_cap_focus: str    # "micro", "small", "mid", "large"
    risk_profile: str        # "conservative", "moderate", "aggressive"
    batch_efficiency: float  # batch optimization effectiveness
    cost_efficiency: float   # cost optimization score
    # ENHANCED: Quality-based metrics
    token_quality_grade: str # average grade of tokens found
    high_quality_percentage: float # percentage of high-quality tokens
    low_risk_percentage: float # percentage of low-risk tokens


class EnhancedDeepAnalysisStrategyComparison:
    """Enhanced strategy comparison with deep token analysis capabilities"""
    
    def __init__(self):
        """Initialize the enhanced deep analysis comparison system"""
        self.logger_setup = LoggerSetup("EnhancedDeepAnalysisComparison")
        self.logger = self.logger_setup.logger
        
        # Initialize configuration and components
        try:
            from core.config_manager import get_config_manager
            from core.cache_manager import CacheManager
            from services.rate_limiter_service import RateLimiterService
            
            # Get configuration
            config_manager = get_config_manager()
            config = config_manager.get_config()  # Use get_config() method
            
            # Initialize cache manager
            cache_config = config.get('cache', {
                'enabled': True,
                'default_ttl': 300,
                'max_size': 1000
            })
            cache_manager = CacheManager(cache_config)
            
            # Initialize rate limiter
            rate_limit_config = config.get('rate_limiting', {
                'enabled': True,
                'default_rate': 100
            })
            rate_limiter = RateLimiterService(rate_limit_config)
            
            # Initialize Birdeye API with proper components
            birdeye_config = config.get('BIRDEYE_API', {})  # Use uppercase key
            self.birdeye_api = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=cache_manager,
                rate_limiter=rate_limiter
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API components: {e}")
            # Fallback initialization for testing
            self.birdeye_api = None
            self.logger.warning("Using fallback initialization - some features may not work")
        
        # Initialize token quality analyzer
        if self.birdeye_api:
            self.token_analyzer = TokenQualityAnalyzer(self.birdeye_api, self.logger)
        else:
            self.token_analyzer = None
        
        # UPDATED: Initialize the newly optimized strategy classes
        self.strategies = [
            VolumeMomentumStrategy(logger=self.logger),
            RecentListingsStrategy(logger=self.logger),
            PriceMomentumStrategy(logger=self.logger),
            LiquidityGrowthStrategy(logger=self.logger),
            HighTradingActivityStrategy(logger=self.logger)
        ]
        
        self.results: List[EnhancedStrategyResult] = []
        self.comparison_data: Dict[str, Any] = {}
        
        self.logger.info("🚀 Enhanced Deep Analysis Strategy Comparison initialized")
        self.logger.info(f"📊 Testing {len(self.strategies)} strategies with deep token analysis")
        self.logger.info("🔍 Features: Holder Concentration + Price Volatility + Market Context + Risk Assessment")

    async def test_enhanced_strategy_with_deep_analysis(self, strategy) -> EnhancedStrategyResult:
        """Test a single strategy with comprehensive deep token analysis"""
        
        print(f"\n{'='*80}")
        print(f"🚀 TESTING STRATEGY WITH DEEP ANALYSIS: {strategy.name}")
        print(f"{'='*80}")
        print(f"Description: {strategy.description}")
        print(f"Deep Analysis: Holder Concentration + Price Volatility + Market Context")
        
        # Check if API is available
        if not self.birdeye_api or not self.token_analyzer:
            error_msg = "BirdEye API or Token Analyzer not properly initialized"
            print(f"❌ ERROR: {error_msg}")
            return EnhancedStrategyResult(
                name=strategy.name,
                description=strategy.description,
                execution_time=0,
                tokens_found=0,
                api_calls_made=0,
                cache_hits=0,
                cache_misses=0,
                avg_volume_24h=0,
                avg_price_change_24h=0,
                avg_market_cap=0,
                avg_liquidity=0,
                avg_consecutive_appearances=0,
                high_quality_tokens=0,
                unique_tokens=0,
                batch_efficiency_ratio=0,
                estimated_cu_saved=0,
                cost_optimization_grade="Failed",
                batch_enriched_tokens=0,
                token_analyses=[],
                avg_quality_score=0.0,
                avg_risk_score=100.0,
                quality_distribution={},
                risk_distribution={},
                high_quality_percentage=0.0,
                low_risk_percentage=0.0,
                strategy_quality_grade="F",
                critical_alerts=0,
                top_quality_tokens=[],
                error=error_msg
            )
        
        try:
            # ENHANCED: Initialize API call tracking
            initial_api_stats = self._capture_initial_api_stats()
            
            # Execute the strategy using the batch-optimized execute method
            start_time = time.time()
            
            tokens = await strategy.execute(
                self.birdeye_api, 
                scan_id=f"deep_analysis_{strategy.name.replace(' ', '_')}"
            )
            
            execution_time = time.time() - start_time
            
            # ENHANCED: Capture final API call statistics
            final_api_stats = self._capture_final_api_stats()
            api_call_breakdown = self._calculate_api_call_breakdown(initial_api_stats, final_api_stats)
            
            # Get cost optimization report from the strategy method
            cost_report = strategy.get_cost_optimization_report()
            
            # Calculate basic metrics
            tokens_found = len(tokens) if tokens else 0
            
            # Count batch enriched tokens
            batch_enriched_count = sum(1 for token in tokens if token.get('batch_enriched', False)) if tokens else 0
            
            # ENHANCED: Perform deep analysis on each token
            print(f"\n🔍 PERFORMING DEEP ANALYSIS ON {tokens_found} TOKENS...")
            token_analyses = []
            
            if tokens:
                # Limit deep analysis to top tokens to manage API costs
                max_deep_analysis = min(10, len(tokens))
                analysis_tokens = tokens[:max_deep_analysis]
                
                for i, token in enumerate(analysis_tokens, 1):
                    token_address = token.get('address')
                    if token_address:
                        print(f"   [{i}/{max_deep_analysis}] Analyzing {token.get('symbol', 'Unknown')} ({token_address[:8]}...)")
                        
                        # Perform comprehensive analysis
                        analysis = await self.token_analyzer.analyze_token_comprehensive(
                            token_address, 
                            basic_token_data=token
                        )
                        token_analyses.append(analysis)
                        
                        # Brief delay to respect rate limits
                        await asyncio.sleep(0.5)
            
            # Calculate enhanced metrics from token analyses
            enhanced_metrics = self._calculate_enhanced_metrics(tokens, token_analyses)
            
            # Calculate averages from discovered tokens (legacy metrics)
            if tokens:
                avg_volume_24h = statistics.mean([t.get('volume24h', 0) or t.get('volume_24h_usd', 0) for t in tokens])
                avg_price_change_24h = statistics.mean([t.get('priceChange24h', 0) or t.get('price_change_24h_percent', 0) for t in tokens])
                avg_market_cap = statistics.mean([t.get('marketCap', 0) or t.get('market_cap', 0) for t in tokens])
                avg_liquidity = statistics.mean([t.get('liquidity', 0) for t in tokens])
                avg_consecutive_appearances = statistics.mean([t.get('consecutive_appearances', 1) for t in tokens])
                high_quality_tokens = len([t for t in tokens if t.get('consecutive_appearances', 1) >= 3])
            else:
                avg_volume_24h = avg_price_change_24h = avg_market_cap = avg_liquidity = 0
                avg_consecutive_appearances = high_quality_tokens = 0
            
            # ENHANCED: Get cache performance from strategy or API client
            cache_stats = self._get_cache_stats()
            
            # Create enhanced result object with deep analysis metrics
            result = EnhancedStrategyResult(
                name=strategy.name,
                description=strategy.description,
                execution_time=execution_time,
                tokens_found=tokens_found,
                api_calls_made=api_call_breakdown['total_calls'],
                cache_hits=cache_stats.get('hits', 0),
                cache_misses=cache_stats.get('misses', 0),
                avg_volume_24h=avg_volume_24h,
                avg_price_change_24h=avg_price_change_24h,
                avg_market_cap=avg_market_cap,
                avg_liquidity=avg_liquidity,
                avg_consecutive_appearances=avg_consecutive_appearances,
                high_quality_tokens=high_quality_tokens,
                unique_tokens=tokens_found,
                # Enhanced batch metrics
                batch_efficiency_ratio=cost_report['cost_metrics']['batch_efficiency_ratio'],
                estimated_cu_saved=cost_report['cost_metrics']['estimated_cu_saved'],
                cost_optimization_grade=cost_report['efficiency_grade'],
                batch_enriched_tokens=batch_enriched_count,
                api_call_breakdown=api_call_breakdown,
                # ENHANCED: Deep analysis metrics
                token_analyses=token_analyses,
                avg_quality_score=enhanced_metrics['avg_quality_score'],
                avg_risk_score=enhanced_metrics['avg_risk_score'],
                quality_distribution=enhanced_metrics['quality_distribution'],
                risk_distribution=enhanced_metrics['risk_distribution'],
                high_quality_percentage=enhanced_metrics['high_quality_percentage'],
                low_risk_percentage=enhanced_metrics['low_risk_percentage'],
                strategy_quality_grade=enhanced_metrics['strategy_quality_grade'],
                critical_alerts=enhanced_metrics['critical_alerts'],
                top_quality_tokens=enhanced_metrics['top_quality_tokens']
            )
            
            # Print enhanced results with deep analysis
            self.print_enhanced_deep_analysis_results(result, cost_report, api_call_breakdown)
            
            return result
            
        except Exception as e:
            error_msg = f"Enhanced strategy execution failed: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            self.logger.error(error_msg)
            
            return EnhancedStrategyResult(
                name=strategy.name,
                description=strategy.description,
                execution_time=0,
                tokens_found=0,
                api_calls_made=0,
                cache_hits=0,
                cache_misses=0,
                avg_volume_24h=0,
                avg_price_change_24h=0,
                avg_market_cap=0,
                avg_liquidity=0,
                avg_consecutive_appearances=0,
                high_quality_tokens=0,
                unique_tokens=0,
                batch_efficiency_ratio=0,
                estimated_cu_saved=0,
                cost_optimization_grade="Failed",
                batch_enriched_tokens=0,
                token_analyses=[],
                avg_quality_score=0.0,
                avg_risk_score=100.0,
                quality_distribution={},
                risk_distribution={},
                high_quality_percentage=0.0,
                low_risk_percentage=0.0,
                strategy_quality_grade="F",
                critical_alerts=0,
                top_quality_tokens=[],
                error=error_msg
            )

    def _calculate_enhanced_metrics(self, tokens: List[Dict], token_analyses: List[TokenAnalysis]) -> Dict[str, Any]:
        """Calculate enhanced metrics from deep token analysis"""
        
        if not token_analyses:
            return {
                'avg_quality_score': 0.0,
                'avg_risk_score': 100.0,
                'quality_distribution': {},
                'risk_distribution': {},
                'high_quality_percentage': 0.0,
                'low_risk_percentage': 0.0,
                'strategy_quality_grade': "N/A",
                'critical_alerts': 0,
                'top_quality_tokens': []
            }
        
        # Calculate averages
        successful_analyses = [a for a in token_analyses if a.analysis_success]
        
        if not successful_analyses:
            return {
                'avg_quality_score': 0.0,
                'avg_risk_score': 100.0,
                'quality_distribution': {},
                'risk_distribution': {},
                'high_quality_percentage': 0.0,
                'low_risk_percentage': 0.0,
                'strategy_quality_grade': "F",
                'critical_alerts': 0,
                'top_quality_tokens': []
            }
        
        # Quality metrics
        quality_scores = [a.quality_score for a in successful_analyses]
        avg_quality_score = statistics.mean(quality_scores)
        
        # Risk metrics
        risk_scores = [a.risk_score for a in successful_analyses]
        avg_risk_score = statistics.mean(risk_scores)
        
        # Grade distribution
        grades = [a.grade for a in successful_analyses]
        quality_distribution = {}
        for grade in grades:
            quality_distribution[grade] = quality_distribution.get(grade, 0) + 1
        
        # Risk level distribution
        risk_levels = [a.risk_level for a in successful_analyses]
        risk_distribution = {}
        for risk_level in risk_levels:
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Quality percentages
        high_quality_count = len([a for a in successful_analyses if a.quality_score >= 70])
        high_quality_percentage = (high_quality_count / len(successful_analyses)) * 100
        
        low_risk_count = len([a for a in successful_analyses if a.risk_level in ['Very Low', 'Low']])
        low_risk_percentage = (low_risk_count / len(successful_analyses)) * 100
        
        # Strategy quality grade
        if avg_quality_score >= 80:
            strategy_quality_grade = "A"
        elif avg_quality_score >= 70:
            strategy_quality_grade = "B"
        elif avg_quality_score >= 60:
            strategy_quality_grade = "C"
        elif avg_quality_score >= 50:
            strategy_quality_grade = "D"
        else:
            strategy_quality_grade = "F"
        
        # Critical alerts
        critical_alerts = sum(len([alert for alert in a.alerts if "🚨" in alert]) for a in successful_analyses)
        
        # Top quality tokens
        sorted_analyses = sorted(successful_analyses, key=lambda x: x.quality_score, reverse=True)
        top_quality_tokens = []
        
        for analysis in sorted_analyses[:5]:
            top_quality_tokens.append({
                'symbol': analysis.symbol,
                'address': analysis.address,
                'quality_score': analysis.quality_score,
                'grade': analysis.grade,
                'risk_level': analysis.risk_level,
                'alerts': len(analysis.alerts)
            })
        
        return {
            'avg_quality_score': avg_quality_score,
            'avg_risk_score': avg_risk_score,
            'quality_distribution': quality_distribution,
            'risk_distribution': risk_distribution,
            'high_quality_percentage': high_quality_percentage,
            'low_risk_percentage': low_risk_percentage,
            'strategy_quality_grade': strategy_quality_grade,
            'critical_alerts': critical_alerts,
            'top_quality_tokens': top_quality_tokens
        }

    def _capture_initial_api_stats(self) -> Dict[str, Any]:
        """Capture initial API call statistics before strategy execution"""
        try:
            # Get stats from BirdeyeAPI's built-in tracking system
            api_stats = self.birdeye_api.get_api_call_statistics()
            
            # Also get performance stats
            performance_stats = self.birdeye_api.get_performance_stats()
            
            return {
                'total_calls': api_stats.get('total_api_calls', 0),
                'successful_calls': api_stats.get('successful_api_calls', 0),
                'failed_calls': api_stats.get('failed_api_calls', 0),
                'cache_hits': api_stats.get('cache_hits', 0),
                'cache_misses': api_stats.get('cache_misses', 0),
                'calls_by_endpoint': api_stats.get('calls_by_endpoint', {}).copy(),
                'performance_total_requests': performance_stats.get('total_requests', 0),
                'performance_successful_requests': performance_stats.get('successful_requests', 0),
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.warning(f"Could not capture initial API stats: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'calls_by_endpoint': {},
                'performance_total_requests': 0,
                'performance_successful_requests': 0,
                'timestamp': time.time()
            }
    
    def _capture_final_api_stats(self) -> Dict[str, Any]:
        """Capture final API call statistics after strategy execution"""
        try:
            # Get stats from BirdeyeAPI's built-in tracking system
            api_stats = self.birdeye_api.get_api_call_statistics()
            
            # Also get performance stats
            performance_stats = self.birdeye_api.get_performance_stats()
            
            return {
                'total_calls': api_stats.get('total_api_calls', 0),
                'successful_calls': api_stats.get('successful_api_calls', 0),
                'failed_calls': api_stats.get('failed_api_calls', 0),
                'cache_hits': api_stats.get('cache_hits', 0),
                'cache_misses': api_stats.get('cache_misses', 0),
                'calls_by_endpoint': api_stats.get('calls_by_endpoint', {}).copy(),
                'performance_total_requests': performance_stats.get('total_requests', 0),
                'performance_successful_requests': performance_stats.get('successful_requests', 0),
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.warning(f"Could not capture final API stats: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'calls_by_endpoint': {},
                'performance_total_requests': 0,
                'performance_successful_requests': 0,
                'timestamp': time.time()
            }
    
    def _calculate_api_call_breakdown(self, initial_stats: Dict[str, Any], final_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the breakdown of API calls made during strategy execution"""
        try:
            # Calculate differences using BirdeyeAPI's tracking data
            total_calls = final_stats['total_calls'] - initial_stats['total_calls']
            successful_calls = final_stats['successful_calls'] - initial_stats['successful_calls']
            failed_calls = final_stats['failed_calls'] - initial_stats['failed_calls']
            cache_hits = final_stats['cache_hits'] - initial_stats['cache_hits']
            cache_misses = final_stats['cache_misses'] - initial_stats['cache_misses']
            
            # Calculate endpoint breakdown
            endpoint_breakdown = {}
            for endpoint, final_data in final_stats['calls_by_endpoint'].items():
                initial_data = initial_stats['calls_by_endpoint'].get(endpoint, {'total': 0})
                
                # Handle both dict and int formats
                if isinstance(final_data, dict):
                    final_count = final_data.get('total', 0)
                else:
                    final_count = final_data
                    
                if isinstance(initial_data, dict):
                    initial_count = initial_data.get('total', 0)
                else:
                    initial_count = initial_data
                
                calls_made = final_count - initial_count
                if calls_made > 0:
                    endpoint_breakdown[endpoint] = calls_made
            
            # Categorize endpoints into batch vs individual
            batch_endpoints = {}
            individual_endpoints = {}
            batch_calls = 0
            individual_calls = 0
            
            for endpoint, count in endpoint_breakdown.items():
                # Identify batch endpoints by common patterns
                if any(batch_pattern in endpoint.lower() for batch_pattern in ['multi', 'multiple', 'batch']):
                    batch_endpoints[endpoint] = count
                    batch_calls += count
                else:
                    individual_endpoints[endpoint] = count
                    individual_calls += count
            
            # Calculate efficiency metrics
            batch_efficiency = (batch_calls / max(1, total_calls)) * 100 if total_calls > 0 else 0
            success_rate = (successful_calls / max(1, total_calls)) * 100 if total_calls > 0 else 0
            cache_hit_rate = (cache_hits / max(1, cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
            
            breakdown = {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'batch_calls': batch_calls,
                'individual_calls': individual_calls,
                'cache_hits': cache_hits,
                'cache_misses': cache_misses,
                'batch_efficiency_pct': batch_efficiency,
                'success_rate_pct': success_rate,
                'cache_hit_rate_pct': cache_hit_rate,
                'endpoint_breakdown': endpoint_breakdown,
                'batch_endpoints': batch_endpoints,
                'individual_endpoints': individual_endpoints,
                'execution_duration': final_stats['timestamp'] - initial_stats['timestamp']
            }
            
            return breakdown
            
        except Exception as e:
            self.logger.warning(f"Could not calculate API call breakdown: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'batch_calls': 0,
                'individual_calls': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'batch_efficiency_pct': 0,
                'success_rate_pct': 0,
                'cache_hit_rate_pct': 0,
                'endpoint_breakdown': {},
                'batch_endpoints': {},
                'individual_endpoints': {},
                'execution_duration': 0
            }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics from BirdeyeAPI"""
        try:
            # Get the latest API call statistics which include cache data
            api_stats = self.birdeye_api.get_api_call_statistics()
            
            cache_hits = api_stats.get('cache_hits', 0)
            cache_misses = api_stats.get('cache_misses', 0)
            total_cache_requests = cache_hits + cache_misses
            hit_rate = (cache_hits / max(1, total_cache_requests)) * 100
            
            return {
                'hits': cache_hits,
                'misses': cache_misses,
                'hit_rate': hit_rate,
                'total_requests': total_cache_requests
            }
        except Exception as e:
            self.logger.warning(f"Could not get cache stats: {e}")
            return {'hits': 0, 'misses': 0, 'hit_rate': 0, 'total_requests': 0}
    
    def print_enhanced_deep_analysis_results(self, result: EnhancedStrategyResult, cost_report: Dict[str, Any], api_call_breakdown: Dict[str, Any]):
        """Print detailed results with deep analysis metrics and API call tracking"""
        
        print(f"\n📊 ENHANCED DEEP ANALYSIS RESULTS FOR {result.name.upper()}")
        print(f"{'-'*70}")
        
        if result.error:
            print(f"❌ ERROR: {result.error}")
            return
        
        # Performance metrics
        print(f"⏱️  Execution Time: {result.execution_time:.2f} seconds")
        print(f"🔍 Tokens Found: {result.tokens_found}")
        print(f"🚀 Batch Enriched Tokens: {result.batch_enriched_tokens}/{result.tokens_found}")
        
        # ENHANCED: Deep Analysis Results
        if result.token_analyses:
            successful_analyses = len([a for a in result.token_analyses if a.analysis_success])
            print(f"\n🔬 DEEP ANALYSIS RESULTS:")
            print(f"   📊 Tokens Analyzed: {len(result.token_analyses)}")
            print(f"   ✅ Successful Analyses: {successful_analyses}")
            print(f"   📈 Average Quality Score: {result.avg_quality_score:.1f}/100")
            print(f"   ⚠️ Average Risk Score: {result.avg_risk_score:.1f}/100")
            print(f"   🏆 Strategy Quality Grade: {result.strategy_quality_grade}")
            print(f"   💎 High Quality Tokens: {result.high_quality_percentage:.1f}%")
            print(f"   🛡️ Low Risk Tokens: {result.low_risk_percentage:.1f}%")
            print(f"   🚨 Critical Alerts: {result.critical_alerts}")
            
            # Quality distribution
            if result.quality_distribution:
                print(f"\n📊 QUALITY GRADE DISTRIBUTION:")
                for grade, count in sorted(result.quality_distribution.items()):
                    print(f"   {grade}: {count} tokens")
            
            # Risk distribution
            if result.risk_distribution:
                print(f"\n⚠️ RISK LEVEL DISTRIBUTION:")
                for risk_level, count in sorted(result.risk_distribution.items()):
                    print(f"   {risk_level}: {count} tokens")
        
        # ENHANCED: Detailed API call tracking
        print(f"\n🌐 API CALL BREAKDOWN:")
        print(f"   📊 Total API Calls: {api_call_breakdown['total_calls']}")
        print(f"   ✅ Successful Calls: {api_call_breakdown['successful_calls']}")
        print(f"   ❌ Failed Calls: {api_call_breakdown['failed_calls']}")
        print(f"   🚀 Batch API Calls: {api_call_breakdown['batch_calls']}")
        print(f"   🔄 Individual API Calls: {api_call_breakdown['individual_calls']}")
        print(f"   📈 Batch Efficiency: {api_call_breakdown['batch_efficiency_pct']:.1f}%")
        print(f"   🎯 Success Rate: {api_call_breakdown['success_rate_pct']:.1f}%")
        
        # Endpoint breakdown
        if api_call_breakdown['batch_endpoints']:
            print(f"\n🚀 BATCH ENDPOINTS USED:")
            for endpoint, count in api_call_breakdown['batch_endpoints'].items():
                print(f"   • {endpoint}: {count} calls")
        
        if api_call_breakdown['individual_endpoints']:
            print(f"\n🔄 INDIVIDUAL ENDPOINTS USED:")
            for endpoint, count in api_call_breakdown['individual_endpoints'].items():
                print(f"   • {endpoint}: {count} calls")
        
        # Cache performance with enhanced metrics
        if api_call_breakdown['cache_hits'] > 0 or api_call_breakdown['cache_misses'] > 0:
            print(f"\n💾 CACHE PERFORMANCE:")
            print(f"   📈 Cache Hits: {api_call_breakdown['cache_hits']}")
            print(f"   📉 Cache Misses: {api_call_breakdown['cache_misses']}")
            print(f"   🎯 Cache Hit Rate: {api_call_breakdown['cache_hit_rate_pct']:.1f}%")
        
        # Enhanced batch optimization metrics
        print(f"\n🚀 ENHANCED BATCH OPTIMIZATION METRICS:")
        print(f"   💰 Cost Efficiency Grade: {result.cost_optimization_grade}")
        print(f"   📈 Batch Efficiency Ratio: {result.batch_efficiency_ratio:.1%}")
        print(f"   💾 Estimated CU Saved: {result.estimated_cu_saved:.0f}")
        print(f"   🔄 Total API Calls: {cost_report['cost_metrics']['total_api_calls']}")
        print(f"   📊 Batch API Calls: {cost_report['cost_metrics']['batch_api_calls']}")
        
        # Rate limiting compliance
        rate_config = cost_report.get('rate_limit_config', {})
        print(f"\n⚡ RATE LIMITING COMPLIANCE:")
        print(f"   🔢 Max Concurrent Batches: {rate_config.get('max_concurrent_batches', 'N/A')}")
        print(f"   ⏱️  Batch Delay: {rate_config.get('batch_delay_seconds', 'N/A')}s")
        print(f"   ✅ Batch APIs Enabled: {rate_config.get('prefer_batch_apis', 'N/A')}")
        
        if result.tokens_found > 0:
            # Quality metrics
            quality_percentage = (result.high_quality_tokens / result.tokens_found) * 100
            efficiency = result.tokens_found / result.execution_time if result.execution_time > 0 else 0
            batch_enrichment_rate = (result.batch_enriched_tokens / result.tokens_found) * 100
            
            print(f"\n⭐ QUALITY METRICS:")
            print(f"   High Quality Tokens: {result.high_quality_tokens} ({quality_percentage:.1f}%)")
            print(f"   Unique Tokens: {result.unique_tokens}")
            print(f"   Discovery Efficiency: {efficiency:.1f} tokens/second")
            print(f"   Batch Enrichment Rate: {batch_enrichment_rate:.1f}%")
            
            # Market metrics
            print(f"\n💰 MARKET CHARACTERISTICS:")
            print(f"   Average 24h Volume: ${result.avg_volume_24h:,.0f}")
            print(f"   Average Price Change: {result.avg_price_change_24h:.2f}%")
            print(f"   Average Market Cap: ${result.avg_market_cap:,.0f}")
            print(f"   Average Liquidity: ${result.avg_liquidity:,.0f}")
            print(f"   Average Consecutive Appearances: {result.avg_consecutive_appearances:.1f}")
            
            # Top quality tokens with deep analysis results
            if result.top_quality_tokens:
                print(f"\n🏆 TOP {len(result.top_quality_tokens)} QUALITY TOKENS (DEEP ANALYSIS):")
                for i, token in enumerate(result.top_quality_tokens, 1):
                    print(f"   {i}. {token['symbol']} ({token['address'][:12]}...) - Grade: {token['grade']}")
                    print(f"      Quality Score: {token['quality_score']:.1f}/100")
                    print(f"      Risk Level: {token['risk_level']}")
                    if token['alerts'] > 0:
                        print(f"      Alerts: {token['alerts']} alert(s)")
        else:
            print("   No tokens found with current parameters")
            print("   💡 This may indicate:")
            print("      • Very strict filtering criteria")
            print("      • Current market conditions")
            print("      • Need for parameter adjustment")

    def calculate_enhanced_comparison_metrics(self, result: EnhancedStrategyResult) -> ComparisonMetrics:
        """Calculate enhanced comparison metrics including deep analysis and batch efficiency"""
        
        if result.error or result.tokens_found == 0:
            return ComparisonMetrics(0, 0, 100, 0, 0, 0, "unknown", "unknown", 0, 0, "F", 0, 0)
        
        # Efficiency: tokens found per second
        efficiency_score = result.tokens_found / result.execution_time if result.execution_time > 0 else 0
        
        # ENHANCED: Quality score from deep analysis
        quality_score = result.avg_quality_score
        
        # ENHANCED: Risk score from deep analysis
        risk_score = result.avg_risk_score
        
        # Diversity: ratio of unique tokens
        diversity_score = (result.unique_tokens / result.tokens_found) * 100 if result.tokens_found > 0 else 0
        
        # Volume focus: normalized volume score
        volume_focus = min(result.avg_volume_24h / 1000000, 100)  # Cap at 100M for scoring
        
        # Growth focus: absolute price change
        growth_focus = abs(result.avg_price_change_24h)
        
        # Market cap focus classification
        if result.avg_market_cap < 1000000:
            market_cap_focus = "micro"
        elif result.avg_market_cap < 10000000:
            market_cap_focus = "small"
        elif result.avg_market_cap < 100000000:
            market_cap_focus = "mid"
        else:
            market_cap_focus = "large"
        
        # Risk profile classification based on deep analysis
        if result.avg_risk_score <= 20:
            risk_profile = "conservative"
        elif result.avg_risk_score <= 40:
            risk_profile = "moderate"
        else:
            risk_profile = "aggressive"
        
        # Enhanced batch efficiency score
        batch_efficiency = result.batch_efficiency_ratio * 100
        
        # Cost efficiency score (based on CU saved and API calls)
        cost_efficiency = min(100, result.estimated_cu_saved / max(1, result.api_calls_made * 10))
        
        return ComparisonMetrics(
            efficiency_score=efficiency_score,
            quality_score=quality_score,
            risk_score=risk_score,
            diversity_score=diversity_score,
            volume_focus=volume_focus,
            growth_focus=growth_focus,
            market_cap_focus=market_cap_focus,
            risk_profile=risk_profile,
            batch_efficiency=batch_efficiency,
            cost_efficiency=cost_efficiency,
            token_quality_grade=result.strategy_quality_grade,
            high_quality_percentage=result.high_quality_percentage,
            low_risk_percentage=result.low_risk_percentage
        )

    async def run_enhanced_comprehensive_comparison(self):
        """Run enhanced comprehensive comparison with deep token analysis"""
        
        print("🚀 STARTING ENHANCED DEEP ANALYSIS STRATEGY COMPARISON v3.0")
        print("="*80)
        print(f"Using newly optimized strategy classes with deep token analysis")
        print(f"Features: Holder Concentration + Price Volatility + Market Context + Risk Assessment")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test each strategy with deep analysis
        for strategy in self.strategies:
            result = await self.test_enhanced_strategy_with_deep_analysis(strategy)
            self.results.append(result)
            
            # Brief delay between strategies to respect rate limits and API costs
            await asyncio.sleep(5)
        
        # Generate enhanced comparative analysis
        self.generate_enhanced_comparative_analysis()
        
        # Save enhanced results
        self.save_enhanced_results()
        
        print(f"\n✅ Enhanced Deep Analysis Strategy Comparison completed!")
        print(f"Results saved to: {self.get_results_filename()}")

    def generate_enhanced_comparative_analysis(self):
        """Generate enhanced comparative analysis with deep token analysis insights"""
        
        print(f"\n{'='*80}")
        print("📊 ENHANCED DEEP ANALYSIS COMPARATIVE ANALYSIS v3.0")
        print(f"{'='*80}")
        
        # Filter out error results for analysis
        valid_results = [r for r in self.results if not r.error and r.tokens_found > 0]
        
        if not valid_results:
            print("❌ No valid results to analyze")
            print("💡 Suggestions:")
            print("   • Check API connectivity")
            print("   • Verify strategy parameters")
            print("   • Try during different market conditions")
            return
        
        # Calculate enhanced comparison metrics
        metrics = {}
        for result in valid_results:
            metrics[result.name] = self.calculate_enhanced_comparison_metrics(result)
        
        # Enhanced Deep Analysis Summary
        print(f"\n🔬 ENHANCED DEEP ANALYSIS SUMMARY v3.0")
        print(f"{'-'*50}")
        
        total_cu_saved = sum(r.estimated_cu_saved for r in valid_results)
        avg_batch_efficiency = statistics.mean([r.batch_efficiency_ratio for r in valid_results])
        total_batch_enriched = sum(r.batch_enriched_tokens for r in valid_results)
        total_tokens = sum(r.tokens_found for r in valid_results)
        
        # ENHANCED: Deep analysis summary metrics
        avg_quality_score = statistics.mean([r.avg_quality_score for r in valid_results])
        avg_risk_score = statistics.mean([r.avg_risk_score for r in valid_results])
        total_analyses = sum(len(r.token_analyses) for r in valid_results)
        successful_analyses = sum(len([a for a in r.token_analyses if a.analysis_success]) for r in valid_results)
        total_critical_alerts = sum(r.critical_alerts for r in valid_results)
        
        # ENHANCED: API call summary
        total_api_calls = sum(r.api_calls_made for r in valid_results)
        total_batch_calls = sum(getattr(r, 'api_call_breakdown', {}).get('batch_calls', 0) for r in valid_results)
        total_individual_calls = sum(getattr(r, 'api_call_breakdown', {}).get('individual_calls', 0) for r in valid_results)
        overall_batch_efficiency = (total_batch_calls / max(1, total_api_calls)) * 100
        
        print(f"   💰 Total CU Saved: {total_cu_saved:.0f}")
        print(f"   📈 Average Batch Efficiency: {avg_batch_efficiency:.1%}")
        print(f"   🚀 Batch Enriched Tokens: {total_batch_enriched}/{total_tokens} ({total_batch_enriched/max(1,total_tokens)*100:.1f}%)")
        print(f"   ⭐ Cost Optimization Grades: {[r.cost_optimization_grade for r in valid_results]}")
        
        # ENHANCED: Deep analysis summary
        print(f"\n🔬 DEEP ANALYSIS SUMMARY:")
        print(f"   📊 Total Token Analyses: {total_analyses}")
        print(f"   ✅ Successful Analyses: {successful_analyses} ({successful_analyses/max(1,total_analyses)*100:.1f}%)")
        print(f"   📈 Average Quality Score: {avg_quality_score:.1f}/100")
        print(f"   ⚠️ Average Risk Score: {avg_risk_score:.1f}/100")
        print(f"   🚨 Total Critical Alerts: {total_critical_alerts}")
        
        # ENHANCED: API call summary
        print(f"\n🌐 API CALL SUMMARY ACROSS ALL STRATEGIES:")
        print(f"   📊 Total API Calls: {total_api_calls}")
        print(f"   🚀 Batch API Calls: {total_batch_calls}")
        print(f"   🔄 Individual API Calls: {total_individual_calls}")
        print(f"   📈 Overall Batch Efficiency: {overall_batch_efficiency:.1f}%")
        
        # Endpoint usage analysis
        self._analyze_endpoint_usage(valid_results)
        
        # Enhanced Performance Rankings with Deep Analysis
        print(f"\n🏆 ENHANCED PERFORMANCE RANKINGS WITH DEEP ANALYSIS")
        print(f"{'-'*60}")
        
        # Quality-based ranking (NEW)
        quality_ranking = sorted(valid_results, key=lambda x: x.avg_quality_score, reverse=True)
        print(f"\n💎 TOKEN QUALITY RANKING:")
        for i, result in enumerate(quality_ranking, 1):
            print(f"   {i}. {result.name}: {result.avg_quality_score:.1f}/100 (Grade: {result.strategy_quality_grade})")
            print(f"      High Quality: {result.high_quality_percentage:.1f}% | Low Risk: {result.low_risk_percentage:.1f}%")
        
        # Risk-adjusted ranking (NEW)
        risk_adjusted_ranking = sorted(valid_results, key=lambda x: x.avg_risk_score)
        print(f"\n🛡️ RISK-ADJUSTED RANKING (Lower is Better):")
        for i, result in enumerate(risk_adjusted_ranking, 1):
            print(f"   {i}. {result.name}: {result.avg_risk_score:.1f}/100 risk score")
            print(f"      Critical Alerts: {result.critical_alerts} | Low Risk Tokens: {result.low_risk_percentage:.1f}%")
        
        # API efficiency ranking
        api_efficiency_ranking = sorted(valid_results, 
                                       key=lambda x: getattr(x, 'api_call_breakdown', {}).get('batch_efficiency_pct', 0), 
                                       reverse=True)
        print(f"\n🌐 API EFFICIENCY RANKING (Batch %):")
        for i, result in enumerate(api_efficiency_ranking, 1):
            api_breakdown = getattr(result, 'api_call_breakdown', {})
            batch_pct = api_breakdown.get('batch_efficiency_pct', 0)
            total_calls = api_breakdown.get('total_calls', 0)
            print(f"   {i}. {result.name}: {batch_pct:.1f}% batch efficiency")
            print(f"      Total Calls: {total_calls} | Batch: {api_breakdown.get('batch_calls', 0)} | Individual: {api_breakdown.get('individual_calls', 0)}")
        
        # Traditional rankings with enhanced context
        efficiency_ranking = sorted(valid_results, key=lambda x: x.tokens_found / x.execution_time, reverse=True)
        print(f"\n⚡ DISCOVERY EFFICIENCY (Tokens/Second):")
        for i, result in enumerate(efficiency_ranking, 1):
            efficiency = result.tokens_found / result.execution_time
            print(f"   {i}. {result.name}: {efficiency:.2f} tokens/sec")
            print(f"      Quality: {result.avg_quality_score:.1f}/100 | Risk: {result.avg_risk_score:.1f}/100")
        
        # Enhanced Strategy Characteristics with Deep Analysis
        print(f"\n🎯 ENHANCED STRATEGY CHARACTERISTICS WITH DEEP ANALYSIS")
        print(f"{'-'*60}")
        
        for result in valid_results:
            metric = metrics[result.name]
            api_breakdown = getattr(result, 'api_call_breakdown', {})
            print(f"\n{result.name}:")
            print(f"   🎯 Risk Profile: {metric.risk_profile.title()}")
            print(f"   💰 Market Cap Focus: {metric.market_cap_focus.title()}")
            print(f"   🚀 Batch Efficiency: {metric.batch_efficiency:.1f}%")
            print(f"   💾 Cost Efficiency: {metric.cost_efficiency:.1f}")
            print(f"   💎 Average Quality Score: {metric.quality_score:.1f}/100")
            print(f"   🛡️ Average Risk Score: {metric.risk_score:.1f}/100")
            print(f"   📊 Token Quality Grade: {metric.token_quality_grade}")
            print(f"   ⚡ Discovery Efficiency: {metric.efficiency_score:.2f} tokens/sec")
            print(f"   🔍 High Quality Tokens: {metric.high_quality_percentage:.1f}%")
            print(f"   🛡️ Low Risk Tokens: {metric.low_risk_percentage:.1f}%")
            print(f"   🌐 API Calls: {api_breakdown.get('total_calls', result.api_calls_made)} (Batch: {api_breakdown.get('batch_calls', 0)}, Individual: {api_breakdown.get('individual_calls', 0)})")
        
        # Enhanced Recommendations with Deep Analysis Insights
        self.generate_enhanced_recommendations(valid_results)
        
        # Store enhanced comparison data
        self.comparison_data = {
            'enhanced_deep_analysis_summary': {
                'total_cu_saved': total_cu_saved,
                'avg_batch_efficiency': avg_batch_efficiency,
                'total_batch_enriched': total_batch_enriched,
                'batch_enrichment_rate': total_batch_enriched/max(1,total_tokens)*100,
                'total_api_calls': total_api_calls,
                'total_batch_calls': total_batch_calls,
                'total_individual_calls': total_individual_calls,
                'overall_batch_efficiency': overall_batch_efficiency,
                # Deep analysis metrics
                'avg_quality_score': avg_quality_score,
                'avg_risk_score': avg_risk_score,
                'total_analyses': total_analyses,
                'successful_analyses': successful_analyses,
                'analysis_success_rate': successful_analyses/max(1,total_analyses)*100,
                'total_critical_alerts': total_critical_alerts
            },
            'quality_ranking': [(r.name, r.avg_quality_score) for r in quality_ranking],
            'risk_adjusted_ranking': [(r.name, r.avg_risk_score) for r in risk_adjusted_ranking],
            'api_efficiency_ranking': [(r.name, getattr(r, 'api_call_breakdown', {}).get('batch_efficiency_pct', 0)) for r in api_efficiency_ranking],
            'efficiency_ranking': [(r.name, r.tokens_found / r.execution_time) for r in efficiency_ranking],
            'enhanced_metrics': {name: asdict(metric) for name, metric in metrics.items()}
        }

    def _analyze_endpoint_usage(self, valid_results: List[EnhancedStrategyResult]):
        """Analyze endpoint usage patterns across all strategies"""
        
        print(f"\n🔍 ENDPOINT USAGE ANALYSIS:")
        print(f"{'-'*30}")
        
        # Collect all endpoint usage
        all_batch_endpoints = {}
        all_individual_endpoints = {}
        
        for result in valid_results:
            api_breakdown = getattr(result, 'api_call_breakdown', {})
            
            # Aggregate batch endpoints
            for endpoint, count in api_breakdown.get('batch_endpoints', {}).items():
                all_batch_endpoints[endpoint] = all_batch_endpoints.get(endpoint, 0) + count
            
            # Aggregate individual endpoints
            for endpoint, count in api_breakdown.get('individual_endpoints', {}).items():
                all_individual_endpoints[endpoint] = all_individual_endpoints.get(endpoint, 0) + count
        
        # Display batch endpoints
        if all_batch_endpoints:
            print(f"\n🚀 BATCH ENDPOINTS USED ACROSS ALL STRATEGIES:")
            sorted_batch = sorted(all_batch_endpoints.items(), key=lambda x: x[1], reverse=True)
            for endpoint, total_calls in sorted_batch:
                print(f"   • {endpoint}: {total_calls} calls")
        
        # Display individual endpoints
        if all_individual_endpoints:
            print(f"\n🔄 INDIVIDUAL ENDPOINTS USED ACROSS ALL STRATEGIES:")
            sorted_individual = sorted(all_individual_endpoints.items(), key=lambda x: x[1], reverse=True)
            for endpoint, total_calls in sorted_individual:
                print(f"   • {endpoint}: {total_calls} calls")
        
        # Optimization opportunities
        if all_individual_endpoints:
            print(f"\n💡 OPTIMIZATION OPPORTUNITIES:")
            for endpoint, count in sorted_individual:
                if count > 5:  # Suggest batch optimization for frequently used endpoints
                    print(f"   🔄 Consider batch optimization for {endpoint} ({count} calls)")
    
    def generate_enhanced_recommendations(self, valid_results: List[EnhancedStrategyResult]):
        """Generate enhanced strategy recommendations with deep token analysis insights"""
        
        print(f"\n💡 ENHANCED STRATEGY RECOMMENDATIONS v3.0")
        print(f"{'-'*50}")
        
        # Find best performers across different dimensions
        best_quality = max(valid_results, key=lambda x: x.avg_quality_score)
        best_risk_adjusted = min(valid_results, key=lambda x: x.avg_risk_score)
        best_batch_efficiency = max(valid_results, key=lambda x: x.batch_efficiency_ratio)
        best_cost_savings = max(valid_results, key=lambda x: x.estimated_cu_saved)
        best_overall_efficiency = max(valid_results, key=lambda x: x.tokens_found / x.execution_time)
        
        print(f"   💎 Best Token Quality: {best_quality.name}")
        print(f"      Average Quality Score: {best_quality.avg_quality_score:.1f}/100")
        print(f"      Strategy Grade: {best_quality.strategy_quality_grade}")
        print(f"      High Quality Tokens: {best_quality.high_quality_percentage:.1f}%")
        
        print(f"   🛡️ Best Risk Profile: {best_risk_adjusted.name}")
        print(f"      Average Risk Score: {best_risk_adjusted.avg_risk_score:.1f}/100")
        print(f"      Low Risk Tokens: {best_risk_adjusted.low_risk_percentage:.1f}%")
        print(f"      Critical Alerts: {best_risk_adjusted.critical_alerts}")
        
        print(f"   🚀 Best Batch Efficiency: {best_batch_efficiency.name}")
        print(f"      Batch Efficiency: {best_batch_efficiency.batch_efficiency_ratio:.1%}")
        print(f"      Grade: {best_batch_efficiency.cost_optimization_grade}")
        
        print(f"   💰 Best Cost Optimization: {best_cost_savings.name}")
        print(f"      CU Saved: {best_cost_savings.estimated_cu_saved:.0f}")
        print(f"      Batch Enriched: {best_cost_savings.batch_enriched_tokens}/{best_cost_savings.tokens_found}")
        
        print(f"   ⚡ Best Overall Efficiency: {best_overall_efficiency.name}")
        efficiency = best_overall_efficiency.tokens_found / best_overall_efficiency.execution_time
        print(f"      Discovery Rate: {efficiency:.2f} tokens/second")
        
        # Usage recommendations with deep token analysis context
        print(f"\n🎯 ENHANCED USAGE RECOMMENDATIONS:")
        print(f"   💎 For Highest Quality Tokens: Use {best_quality.name}")
        print(f"      • Finds tokens with highest quality scores and grades")
        print(f"      • Best for conservative investment strategies")
        print(f"      • Recommended for long-term holdings")
        
        print(f"   🛡️ For Lowest Risk Exposure: Use {best_risk_adjusted.name}")
        print(f"      • Identifies tokens with lowest risk profiles")
        print(f"      • Minimal critical alerts and risk factors")
        print(f"      • Ideal for risk-averse investors")
        
        print(f"   🚀 For Maximum Cost Efficiency: Use {best_cost_savings.name}")
        print(f"      • Achieves highest CU savings with batch optimization")
        print(f"      • Best for production environments with cost constraints")
        print(f"      • Optimal for high-frequency scanning")
        
        print(f"   ⚡ For Maximum Speed: Use {best_overall_efficiency.name}")
        print(f"      • Fastest token discovery with deep analysis")
        print(f"      • Ideal for real-time monitoring and alerts")
        print(f"      • Best for time-sensitive opportunities")
        
        print(f"   🔧 For Development/Testing: Use {best_batch_efficiency.name}")
        print(f"      • Most efficient batch API utilization")
        print(f"      • Excellent for learning deep analysis patterns")
        print(f"      • Good balance of features and performance")
        
        # Strategy combination recommendations
        print(f"\n🔄 STRATEGY COMBINATION RECOMMENDATIONS:")
        
        # Find complementary strategies
        high_quality_strategies = [r for r in valid_results if r.avg_quality_score >= 70]
        low_risk_strategies = [r for r in valid_results if r.avg_risk_score <= 30]
        
        if high_quality_strategies:
            print(f"   💎 High Quality Strategy Pool: {', '.join([s.name for s in high_quality_strategies])}")
            print(f"      • Use for core portfolio positions")
            print(f"      • Combine for diversified quality exposure")
        
        if low_risk_strategies:
            print(f"   🛡️ Low Risk Strategy Pool: {', '.join([s.name for s in low_risk_strategies])}")
            print(f"      • Use for conservative allocations")
            print(f"      • Suitable for larger position sizes")
        
        # Market condition recommendations
        print(f"\n🌍 MARKET CONDITION RECOMMENDATIONS:")
        print(f"   📈 Bull Market: Focus on {best_overall_efficiency.name} for maximum discovery")
        print(f"   📉 Bear Market: Focus on {best_risk_adjusted.name} for risk management")
        print(f"   🌊 Volatile Market: Use {best_quality.name} for stable fundamentals")
        print(f"   💰 Cost-Conscious: Always use {best_cost_savings.name} for efficiency")

    def save_enhanced_results(self):
        """Save enhanced results with deep token analysis metrics"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"data/enhanced_deep_analysis_strategy_comparison_{timestamp}.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare enhanced data for JSON serialization
        results_data = {
            'test_metadata': {
                'timestamp': timestamp,
                'test_date': datetime.now().isoformat(),
                'version': 'Enhanced Deep Analysis v3.0',
                'strategies_tested': len(self.strategies),
                'total_execution_time': sum(r.execution_time for r in self.results),
                'enhanced_deep_analysis': True,
                'using_new_strategy_classes': True,
                'batch_api_integration': True,
                'rate_limiting_optimized': True,
                'api_call_tracking_enabled': True,
                'deep_token_analysis_enabled': True,
                'holder_concentration_analysis': True,
                'price_volatility_analysis': True,
                'market_context_analysis': True,
                'risk_assessment_enabled': True,
                'quality_scoring_enabled': True
            },
            'individual_results': [asdict(result) for result in self.results],
            'enhanced_comparative_analysis': self.comparison_data,
            'enhanced_summary': {
                'total_unique_tokens': sum(r.unique_tokens for r in self.results if not r.error),
                'total_api_calls': sum(r.api_calls_made for r in self.results if not r.error),
                'total_batch_api_calls': sum(getattr(r, 'api_call_breakdown', {}).get('batch_calls', 0) for r in self.results if not r.error),
                'total_individual_api_calls': sum(getattr(r, 'api_call_breakdown', {}).get('individual_calls', 0) for r in self.results if not r.error),
                'total_cu_saved': sum(r.estimated_cu_saved for r in self.results if not r.error),
                'average_batch_efficiency': statistics.mean([r.batch_efficiency_ratio for r in self.results if not r.error]) if [r for r in self.results if not r.error] else 0,
                'total_batch_enriched_tokens': sum(r.batch_enriched_tokens for r in self.results if not r.error),
                'cost_optimization_grades': [r.cost_optimization_grade for r in self.results if not r.error],
                'overall_api_batch_efficiency': (sum(getattr(r, 'api_call_breakdown', {}).get('batch_calls', 0) for r in self.results if not r.error) / max(1, sum(r.api_calls_made for r in self.results if not r.error))) * 100,
                # Deep analysis summary
                'total_token_analyses': sum(len(r.token_analyses) for r in self.results if not r.error),
                'successful_analyses': sum(len([a for a in r.token_analyses if a.analysis_success]) for r in self.results if not r.error),
                'average_quality_score': statistics.mean([r.avg_quality_score for r in self.results if not r.error and r.avg_quality_score > 0]) if [r for r in self.results if not r.error and r.avg_quality_score > 0] else 0,
                'average_risk_score': statistics.mean([r.avg_risk_score for r in self.results if not r.error and r.avg_risk_score > 0]) if [r for r in self.results if not r.error and r.avg_risk_score > 0] else 0,
                'total_critical_alerts': sum(r.critical_alerts for r in self.results if not r.error),
                'strategy_quality_grades': [r.strategy_quality_grade for r in self.results if not r.error]
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        self.results_file = results_file

    def print_enhanced_summary_table(self):
        """Print an enhanced summary table with deep token analysis metrics"""
        
        print(f"\n📋 ENHANCED DEEP ANALYSIS SUMMARY TABLE v3.0")
        print(f"{'='*200}")
        
        # Enhanced header with deep analysis metrics
        headers = ["Strategy", "Tokens", "Time(s)", "Quality", "Risk", "Grade", "API Calls", "Batch%", "CU Saved", "Alerts", "High Qual%", "Low Risk%"]
        print(f"{headers[0]:<30} {headers[1]:<8} {headers[2]:<8} {headers[3]:<8} {headers[4]:<6} {headers[5]:<6} {headers[6]:<10} {headers[7]:<8} {headers[8]:<9} {headers[9]:<7} {headers[10]:<10} {headers[11]:<10}")
        print("-" * 200)
        
        # Enhanced data rows with deep analysis metrics
        for result in self.results:
            if result.error:
                print(f"{result.name:<30} {'ERROR':<8} {'N/A':<8} {'N/A':<8} {'N/A':<6} {'F':<6} {'N/A':<10} {'N/A':<8} {'N/A':<9} {'N/A':<7} {'N/A':<10} {'N/A':<10}")
            else:
                # Get API call breakdown
                api_breakdown = getattr(result, 'api_call_breakdown', {})
                total_api_calls = api_breakdown.get('total_calls', result.api_calls_made)
                batch_efficiency_pct = api_breakdown.get('batch_efficiency_pct', 0)
                
                print(f"{result.name:<30} {result.tokens_found:<8} {result.execution_time:<8.2f} {result.avg_quality_score:<8.1f} {result.avg_risk_score:<6.1f} {result.strategy_quality_grade:<6} {total_api_calls:<10} {batch_efficiency_pct:<8.1f} {result.estimated_cu_saved:<9.0f} {result.critical_alerts:<7} {result.high_quality_percentage:<10.1f} {result.low_risk_percentage:<10.1f}")
        
        print("-" * 200)
        print("Legend:")
        print("Quality: Average quality score (0-100, higher is better)")
        print("Risk: Average risk score (0-100, lower is better)")
        print("Grade: Strategy quality grade (A+ to F)")
        print("Batch%: Percentage of API calls using batch endpoints")
        print("Alerts: Number of critical alerts detected")
        print("High Qual%: Percentage of high-quality tokens found")
        print("Low Risk%: Percentage of low-risk tokens found")
    
    def get_results_filename(self) -> str:
        """Get the results filename"""
        return str(getattr(self, 'results_file', 'results not saved'))


async def main():
    """Main function to run enhanced deep analysis strategy comparison"""
    
    print("🚀 ENHANCED DEEP ANALYSIS STRATEGY COMPARISON v3.0")
    print("="*80)
    print("Using newly optimized strategy classes with comprehensive deep token analysis")
    print("Features: Holder Concentration + Price Volatility + Market Context + Risk Assessment")
    print("Enhanced with batch API optimization and quality-based strategy evaluation")
    
    # Initialize enhanced comparison system
    comparison = EnhancedDeepAnalysisStrategyComparison()
    
    try:
        # Run enhanced comprehensive comparison with deep analysis
        await comparison.run_enhanced_comprehensive_comparison()
        
        # Print enhanced summary table
        comparison.print_enhanced_summary_table()
        
        print(f"\n🎉 Enhanced Deep Analysis Strategy Comparison Complete!")
        print(f"📊 Detailed results saved to: {comparison.get_results_filename()}")
        print(f"\n💡 KEY ENHANCEMENTS IN v3.0:")
        print(f"   • ✅ Using newly optimized strategy classes")
        print(f"   • ✅ Comprehensive deep token analysis capabilities")
        print(f"   • ✅ Holder concentration analysis (whale detection)")
        print(f"   • ✅ Price volatility analysis (risk assessment)")
        print(f"   • ✅ Market context analysis (maturity & liquidity)")
        print(f"   • ✅ Quality scoring and grading system")
        print(f"   • ✅ Risk-adjusted strategy rankings")
        print(f"   • ✅ Enhanced batch API optimization")
        print(f"   • ✅ Real-time cost optimization tracking")
        print(f"   • ✅ Critical alert detection and monitoring")
        print(f"   • ✅ Strategy quality grades (A+ to F)")
        print(f"   • ✅ Comprehensive risk and quality metrics")
        
        print(f"\n🔍 DEEP ANALYSIS FEATURES:")
        print(f"   📊 Holder Concentration: Detects whale dominance and distribution risks")
        print(f"   📈 Price Volatility: Analyzes price stability and trading risks")
        print(f"   🌍 Market Context: Evaluates liquidity, market cap, and token maturity")
        print(f"   🛡️ Risk Assessment: Comprehensive risk scoring and alerts")
        print(f"   💎 Quality Scoring: Multi-factor quality assessment with grades")
        print(f"   🎯 Strategy Ranking: Quality-based and risk-adjusted rankings")
        
    except Exception as e:
        print(f"❌ Error during enhanced deep analysis strategy comparison: {e}")
        comparison.logger.error(f"Enhanced deep analysis strategy comparison error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())