#!/usr/bin/env python3
"""
Phase 3 Enhanced Deep Token Analysis

Advanced token analysis with holder concentration, price volatility,
and market context analysis capabilities.
"""

import asyncio
import sys
import os
from datetime import datetime
import json
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from utils.logger_setup import LoggerSetup

class Phase3DeepTokenAnalyzer:
    """
    Phase 3 Enhanced Deep Token Analysis with advanced features
    """
    
    def __init__(self):
        logger_setup = LoggerSetup("Phase3DeepAnalysis")
        self.logger = logger_setup.logger
        
        # We'll initialize the API components when we need them
        self.birdeye_api = None
        self._api_initialized = False
    
    async def _ensure_api_initialized(self):
        """Initialize API components if not already done"""
        if self._api_initialized:
            return
            
        try:
            from api.birdeye_connector import BirdeyeAPI
            from core.cache_manager import CacheManager
            from services.rate_limiter_service import RateLimiterService
            
            # Create simple configuration for testing
            config = {
                'birdeye': {
                    'api_key': os.getenv('BIRDEYE_API_KEY'),
                    'base_url': 'https://public-api.birdeye.so',
                    'rate_limit': 100,
                    'request_timeout_seconds': 20,
                    'cache_ttl_default_seconds': 300,
                    'cache_ttl_error_seconds': 60,
                    'max_retries': 3,
                    'backoff_factor': 2
                },
                'cache': {
                    'enabled': True,
                    'default_ttl': 300,
                    'max_size': 1000
                },
                'rate_limiting': {
                    'enabled': True,
                    'default_rate': 100
                }
            }
            
            # Verify API key is available
            if not config['birdeye']['api_key']:
                self.logger.error("❌ BIRDEYE_API_KEY environment variable is not set!")
                self.logger.error("Please set your BirdEye API key in the .env file or as an environment variable")
                raise ValueError("BirdEye API key not configured")
            
            cache_manager = CacheManager(config.get('cache', {}))
            rate_limiter = RateLimiterService(config.get('rate_limiting', {}))
            
            self.birdeye_api = BirdeyeAPI(
                config=config.get('birdeye', {}),
                logger=self.logger,
                cache_manager=cache_manager,
                rate_limiter=rate_limiter
            )
            
            self._api_initialized = True
            self.logger.info("✅ API components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize API components: {e}")
            raise
    
    async def analyze_token_comprehensive(self, token_address: str) -> Dict[str, Any]:
        """
        Comprehensive Phase 3 token analysis
        """
        await self._ensure_api_initialized()
        
        self.logger.info(f"🚀 Starting Phase 3 comprehensive analysis for {token_address[:8]}...")
        
        analysis_result = {
            'token_address': token_address,
            'analysis_timestamp': datetime.now().isoformat(),
            'phase': 'Phase 3',
            'basic_data': {},
            'holder_analysis': {},
            'volatility_analysis': {},
            'market_analysis': {},
            'comprehensive_scoring': {},
            'risk_assessment': {},
            'trading_recommendations': {},
            'alerts': [],
            'errors': []
        }
        
        try:
            # 1. Basic token data
            self.logger.info("📊 Fetching basic token data...")
            basic_data = await self._fetch_basic_token_data(token_address)
            analysis_result['basic_data'] = basic_data
            
            if not basic_data.get('overview'):
                analysis_result['errors'].append("Failed to fetch basic token data")
                return analysis_result
            
            # 2. Holder concentration analysis
            self.logger.info("👥 Analyzing holder concentration...")
            holder_analysis = await self._analyze_holder_concentration(token_address)
            analysis_result['holder_analysis'] = holder_analysis
            
            # 3. Price volatility analysis
            self.logger.info("📊 Analyzing price volatility...")
            volatility_analysis = await self._analyze_price_volatility(token_address)
            analysis_result['volatility_analysis'] = volatility_analysis
            
            # 4. Market context analysis
            self.logger.info("🌍 Analyzing market context...")
            market_analysis = await self._analyze_market_context(token_address, basic_data)
            analysis_result['market_analysis'] = market_analysis
            
            # 5. Comprehensive scoring
            self.logger.info("🎯 Calculating comprehensive scores...")
            scoring = self._calculate_comprehensive_scoring(analysis_result)
            analysis_result['comprehensive_scoring'] = scoring
            
            # 6. Risk assessment
            self.logger.info("⚠️ Performing risk assessment...")
            risk_assessment = self._perform_risk_assessment(analysis_result)
            analysis_result['risk_assessment'] = risk_assessment
            
            # 7. Trading recommendations
            self.logger.info("💡 Generating trading recommendations...")
            recommendations = self._generate_trading_recommendations(analysis_result)
            analysis_result['trading_recommendations'] = recommendations
            
            # 8. Compile alerts
            analysis_result['alerts'] = self._compile_all_alerts(analysis_result)
            
            self.logger.info(f"✅ Phase 3 comprehensive analysis completed for {token_address[:8]}")
            
        except Exception as e:
            self.logger.error(f"❌ Phase 3 analysis failed: {e}")
            analysis_result['errors'].append(f"Analysis failed: {str(e)}")
        
        return analysis_result
    
    async def _fetch_basic_token_data(self, token_address: str) -> Dict[str, Any]:
        """
        Fetch basic token data using available API methods
        """
        try:
            # Get token overview (price, market cap, liquidity, volume)
            overview = await self.birdeye_api.get_token_overview(token_address)
            
            # Get token age
            age_days, age_description = await self.birdeye_api.get_token_age(token_address)
            
            # Get token security info
            security = await self.birdeye_api.get_token_security(token_address)
            
            # Get recent transactions for volume calculation
            transactions = await self.birdeye_api.get_token_transactions(token_address, limit=50, max_pages=2)
            
            return {
                'overview': overview or {},
                'age_days': age_days,
                'age_description': age_description,
                'security': security or {},
                'recent_transactions': transactions or [],
                'data_quality': self._assess_data_quality(overview, age_days, security, transactions)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching basic token data: {e}")
            return {}
    
    def _assess_data_quality(self, overview: Dict, age_days: float, security: Dict, transactions: List) -> Dict[str, Any]:
        """
        Assess quality of basic data
        """
        quality_score = 0
        quality_factors = []
        
        # Overview data quality
        if overview:
            quality_score += 25
            quality_factors.append("Overview data available")
            
            if overview.get('price', 0) > 0:
                quality_score += 15
                quality_factors.append("Price data available")
            
            if overview.get('liquidity', 0) > 0:
                quality_score += 15
                quality_factors.append("Liquidity data available")
        
        # Age data quality
        if age_days > 0:
            quality_score += 15
            quality_factors.append("Token age available")
        
        # Security data quality
        if security:
            quality_score += 15
            quality_factors.append("Security data available")
        
        # Transaction data quality
        if transactions:
            quality_score += 15
            quality_factors.append("Transaction data available")
        
        return {
            'quality_score': quality_score,
            'quality_factors': quality_factors,
            'data_completeness': len(quality_factors) / 6 * 100  # Out of 6 possible factors
        }
    
    async def _analyze_holder_concentration(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze holder concentration using available API methods
        """
        try:
            # Get holder data
            holders_data = await self.birdeye_api.get_token_holders(token_address, limit=100)
            
            if not holders_data or not isinstance(holders_data, dict):
                return {
                    'analysis_available': False,
                    'error': 'No holder data available'
                }
            
            holders = holders_data.get('data', {}).get('items', [])
            
            if not holders:
                return {
                    'analysis_available': False,
                    'error': 'No holder items found'
                }
            
            # Calculate concentration metrics
            total_holders = len(holders)
            
            # Extract balances and percentages
            balances = []
            percentages = []
            
            for holder in holders:
                balance = holder.get('balance', 0)
                percentage = holder.get('percentage', 0)
                
                if isinstance(balance, (int, float)) and balance > 0:
                    balances.append(balance)
                    percentages.append(percentage)
            
            if not percentages:
                return {
                    'analysis_available': False,
                    'error': 'No valid holder percentages found'
                }
            
            # Calculate metrics
            top_1_percentage = percentages[0] if percentages else 0
            top_5_percentage = sum(percentages[:5]) if len(percentages) >= 5 else sum(percentages)
            top_10_percentage = sum(percentages[:10]) if len(percentages) >= 10 else sum(percentages)
            
            # Whale analysis (holders with >5% of supply)
            whales = [h for h in holders if h.get('percentage', 0) >= 5.0]
            whale_count = len(whales)
            whale_total_percentage = sum(h.get('percentage', 0) for h in whales)
            
            # Risk assessment
            concentration_risk = 'Low'
            risk_factors = []
            
            if top_1_percentage >= 50:
                concentration_risk = 'Critical'
                risk_factors.append('Single holder controls >50% of supply')
            elif top_5_percentage >= 80:
                concentration_risk = 'High'
                risk_factors.append('Top 5 holders control >80% of supply')
            elif whale_count >= 3:
                concentration_risk = 'Medium'
                risk_factors.append('Multiple whale holders detected')
            
            return {
                'analysis_available': True,
                'total_holders': total_holders,
                'top_1_percentage': top_1_percentage,
                'top_5_percentage': top_5_percentage,
                'top_10_percentage': top_10_percentage,
                'whale_count': whale_count,
                'whale_total_percentage': whale_total_percentage,
                'concentration_risk': concentration_risk,
                'risk_factors': risk_factors,
                'concentration_score': max(0, 100 - top_10_percentage)  # Lower concentration = higher score
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing holder concentration: {e}")
            return {
                'analysis_available': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    async def _analyze_price_volatility(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze price volatility using transaction data
        """
        try:
            # Get recent transactions for price analysis
            transactions = await self.birdeye_api.get_token_transactions(token_address, limit=50, max_pages=3)
            
            if not transactions:
                return {
                    'analysis_available': False,
                    'error': 'No transaction data available'
                }
            
            # Extract prices from transactions
            prices = []
            for tx in transactions:
                # Try to extract price from different possible fields
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
                return {
                    'analysis_available': False,
                    'error': 'Insufficient price data points'
                }
            
            # Calculate volatility metrics
            import statistics
            
            current_price = prices[0]
            max_price = max(prices)
            min_price = min(prices)
            mean_price = statistics.mean(prices)
            
            # Price range percentage
            price_range_pct = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
            
            # Standard deviation
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
            
            # Volatility score (inverse of volatility - lower volatility = higher score)
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
            self.logger.error(f"Error analyzing price volatility: {e}")
            return {
                'analysis_available': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    async def _analyze_market_context(self, token_address: str, basic_data: Dict) -> Dict[str, Any]:
        """
        Analyze market context using available data
        """
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
            
            # Liquidity efficiency
            liquidity_ratio = liquidity / market_cap if market_cap > 0 else 0
            volume_ratio = volume_24h / liquidity if liquidity > 0 else 0
            
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
                'liquidity_ratio': liquidity_ratio,
                'volume_ratio': volume_ratio,
                'market_quality_score': market_quality_score
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market context: {e}")
            return {
                'analysis_available': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    def _calculate_comprehensive_scoring(self, analysis: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive Phase 3 scoring
        """
        scores = {}
        
        # Data quality score
        data_quality = analysis.get('basic_data', {}).get('data_quality', {}).get('quality_score', 0)
        scores['data_quality_score'] = data_quality
        
        # Holder concentration score
        holder_analysis = analysis.get('holder_analysis', {})
        concentration_score = holder_analysis.get('concentration_score', 0) if holder_analysis.get('analysis_available') else 50
        scores['concentration_score'] = concentration_score
        
        # Volatility score
        volatility_analysis = analysis.get('volatility_analysis', {})
        volatility_score = volatility_analysis.get('volatility_score', 0) if volatility_analysis.get('analysis_available') else 50
        scores['volatility_score'] = volatility_score
        
        # Market quality score
        market_analysis = analysis.get('market_analysis', {})
        market_quality_score = market_analysis.get('market_quality_score', 0) if market_analysis.get('analysis_available') else 50
        scores['market_quality_score'] = market_quality_score
        
        # Calculate weighted overall score
        weights = {
            'data_quality_score': 0.2,
            'concentration_score': 0.3,
            'volatility_score': 0.25,
            'market_quality_score': 0.25
        }
        
        overall_score = sum(scores[key] * weights[key] for key in weights if key in scores)
        
        # Determine grade
        if overall_score >= 85:
            grade = "A+"
        elif overall_score >= 80:
            grade = "A"
        elif overall_score >= 75:
            grade = "A-"
        elif overall_score >= 70:
            grade = "B+"
        elif overall_score >= 65:
            grade = "B"
        elif overall_score >= 60:
            grade = "B-"
        elif overall_score >= 55:
            grade = "C+"
        elif overall_score >= 50:
            grade = "C"
        elif overall_score >= 45:
            grade = "C-"
        elif overall_score >= 40:
            grade = "D+"
        elif overall_score >= 35:
            grade = "D"
        elif overall_score >= 30:
            grade = "D-"
        else:
            grade = "F"
        
        return {
            'individual_scores': scores,
            'weights': weights,
            'overall_score': overall_score,
            'grade': grade,
            'score_interpretation': self._interpret_overall_score(overall_score)
        }
    
    def _interpret_overall_score(self, score: float) -> str:
        """
        Interpret overall score
        """
        if score >= 80:
            return "Excellent token with strong fundamentals"
        elif score >= 70:
            return "Good token with solid characteristics"
        elif score >= 60:
            return "Average token with mixed signals"
        elif score >= 50:
            return "Below average token with concerns"
        elif score >= 40:
            return "Poor token with significant risks"
        else:
            return "Very poor token - high risk"
    
    def _perform_risk_assessment(self, analysis: Dict) -> Dict[str, Any]:
        """
        Comprehensive risk assessment
        """
        risk_factors = []
        risk_score = 0
        
        # Holder concentration risks
        holder_analysis = analysis.get('holder_analysis', {})
        if holder_analysis.get('analysis_available'):
            concentration_risk = holder_analysis.get('concentration_risk', 'Low')
            if concentration_risk == 'Critical':
                risk_score += 30
                risk_factors.append("Critical holder concentration")
            elif concentration_risk == 'High':
                risk_score += 20
                risk_factors.append("High holder concentration")
            elif concentration_risk == 'Medium':
                risk_score += 10
                risk_factors.append("Moderate holder concentration")
        
        # Volatility risks
        volatility_analysis = analysis.get('volatility_analysis', {})
        if volatility_analysis.get('analysis_available'):
            volatility_risk = volatility_analysis.get('volatility_risk', 'Low')
            if volatility_risk == 'Critical':
                risk_score += 25
                risk_factors.append("Extreme price volatility")
            elif volatility_risk == 'High':
                risk_score += 15
                risk_factors.append("High price volatility")
            elif volatility_risk == 'Medium':
                risk_score += 8
                risk_factors.append("Moderate price volatility")
        
        # Market risks
        market_analysis = analysis.get('market_analysis', {})
        if market_analysis.get('analysis_available'):
            liquidity_category = market_analysis.get('liquidity_category', '')
            if 'Insufficient' in liquidity_category:
                risk_score += 25
                risk_factors.append("Insufficient liquidity")
            elif 'Critical' in liquidity_category:
                risk_score += 20
                risk_factors.append("Critical liquidity levels")
            elif 'Low' in liquidity_category:
                risk_score += 10
                risk_factors.append("Low liquidity")
            
            # Age risk
            age_days = market_analysis.get('age_days', 0)
            if age_days < 7:
                risk_score += 15
                risk_factors.append("Very new token (< 1 week)")
            elif age_days < 30:
                risk_score += 10
                risk_factors.append("New token (< 1 month)")
        
        # Overall risk level
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
        
        return {
            'overall_risk_level': risk_level,
            'risk_score': min(100, risk_score),
            'risk_factors': risk_factors
        }
    
    def _generate_trading_recommendations(self, analysis: Dict) -> Dict[str, Any]:
        """
        Generate trading recommendations
        """
        scoring = analysis.get('comprehensive_scoring', {})
        risk_assessment = analysis.get('risk_assessment', {})
        
        overall_score = scoring.get('overall_score', 0)
        risk_level = risk_assessment.get('overall_risk_level', 'High')
        
        # Overall recommendation
        if overall_score >= 80 and risk_level in ['Very Low', 'Low']:
            overall_recommendation = "STRONG BUY - Excellent fundamentals with low risk"
        elif overall_score >= 70 and risk_level in ['Very Low', 'Low', 'Medium']:
            overall_recommendation = "BUY - Good fundamentals with acceptable risk"
        elif overall_score >= 60 and risk_level in ['Low', 'Medium']:
            overall_recommendation = "MODERATE BUY - Average token, suitable for diversified portfolio"
        elif overall_score >= 50:
            overall_recommendation = "HOLD/NEUTRAL - Mixed signals, proceed with caution"
        elif overall_score >= 40:
            overall_recommendation = "WEAK SELL - Below average, consider reducing exposure"
        else:
            overall_recommendation = "STRONG SELL - Poor fundamentals, high risk"
        
        # Position sizing
        if risk_level == 'Extreme':
            position_sizing = "Micro position only (0.5-1% of portfolio)"
        elif risk_level == 'High':
            position_sizing = "Small position (1-3% of portfolio)"
        elif risk_level == 'Medium' and overall_score >= 60:
            position_sizing = "Moderate position (3-7% of portfolio)"
        elif risk_level == 'Low' and overall_score >= 70:
            position_sizing = "Standard position (5-10% of portfolio)"
        elif risk_level == 'Very Low' and overall_score >= 80:
            position_sizing = "Large position acceptable (8-15% of portfolio)"
        else:
            position_sizing = "Small to moderate position (2-5% of portfolio)"
        
        return {
            'overall_recommendation': overall_recommendation,
            'position_sizing': position_sizing,
            'risk_management': self._get_risk_management_advice(risk_level),
            'time_horizon': self._get_time_horizon_advice(analysis)
        }
    
    def _get_risk_management_advice(self, risk_level: str) -> List[str]:
        """
        Get risk management advice based on risk level
        """
        if risk_level in ['Extreme', 'High']:
            return [
                "Use very tight stop losses (3-5%)",
                "Monitor position closely",
                "Consider hedging strategies",
                "Use limit orders only"
            ]
        elif risk_level == 'Medium':
            return [
                "Use moderate stop losses (5-8%)",
                "Regular position monitoring",
                "Use limit orders for entries"
            ]
        else:
            return [
                "Standard stop losses (8-12%)",
                "Regular portfolio review",
                "Standard risk management practices"
            ]
    
    def _get_time_horizon_advice(self, analysis: Dict) -> str:
        """
        Get time horizon advice
        """
        volatility_analysis = analysis.get('volatility_analysis', {})
        market_analysis = analysis.get('market_analysis', {})
        
        if volatility_analysis.get('volatility_risk') in ['Critical', 'High']:
            return "Short-term only (days to weeks)"
        elif market_analysis.get('market_maturity') == 'Mature Market':
            return "Medium to long-term (months to years)"
        else:
            return "Medium-term (weeks to months)"
    
    def _compile_all_alerts(self, analysis: Dict) -> List[str]:
        """
        Compile all alerts from different analysis components
        """
        alerts = []
        
        # Holder concentration alerts
        holder_analysis = analysis.get('holder_analysis', {})
        if holder_analysis.get('analysis_available'):
            concentration_risk = holder_analysis.get('concentration_risk', 'Low')
            if concentration_risk == 'Critical':
                alerts.append("🚨 CRITICAL: Extreme holder concentration detected")
            elif concentration_risk == 'High':
                alerts.append("⚠️ HIGH RISK: Significant holder concentration")
        
        # Volatility alerts
        volatility_analysis = analysis.get('volatility_analysis', {})
        if volatility_analysis.get('analysis_available'):
            volatility_risk = volatility_analysis.get('volatility_risk', 'Low')
            if volatility_risk == 'Critical':
                alerts.append("🚨 EXTREME VOLATILITY: Price movements are extremely volatile")
            elif volatility_risk == 'High':
                alerts.append("⚠️ HIGH VOLATILITY: Significant price swings detected")
        
        # Market alerts
        market_analysis = analysis.get('market_analysis', {})
        if market_analysis.get('analysis_available'):
            liquidity_category = market_analysis.get('liquidity_category', '')
            if 'Insufficient' in liquidity_category:
                alerts.append("🚨 CRITICAL: Insufficient liquidity for safe trading")
            elif 'Critical' in liquidity_category:
                alerts.append("⚠️ LIQUIDITY RISK: Critical liquidity levels")
        
        # Risk level alert
        risk_assessment = analysis.get('risk_assessment', {})
        risk_level = risk_assessment.get('overall_risk_level', '')
        if risk_level == 'Extreme':
            alerts.append("🚨 EXTREME RISK: Multiple high-risk factors detected")
        elif risk_level == 'High':
            alerts.append("⚠️ HIGH RISK: Significant risk factors present")
        
        return alerts

async def analyze_tokens(token_addresses: List[str]):
    """
    Analyze multiple tokens with Phase 3 enhanced analysis
    """
    analyzer = Phase3DeepTokenAnalyzer()
    results = {}
    
    print(f"\n🚀 Phase 3 Enhanced Deep Token Analysis")
    print(f"📊 Analyzing {len(token_addresses)} tokens with advanced features")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    for i, token_address in enumerate(token_addresses, 1):
        print(f"\n[{i}/{len(token_addresses)}] Analyzing {token_address[:8]}...")
        
        try:
            result = await analyzer.analyze_token_comprehensive(token_address)
            results[token_address] = result
            
            # Print summary
            scoring = result.get('comprehensive_scoring', {})
            risk = result.get('risk_assessment', {})
            recommendation = result.get('trading_recommendations', {})
            
            print(f"✅ Analysis completed for {token_address[:8]}")
            print(f"   Score: {scoring.get('overall_score', 0):.1f}/100 ({scoring.get('grade', 'N/A')})")
            print(f"   Risk: {risk.get('overall_risk_level', 'Unknown')}")
            print(f"   Recommendation: {recommendation.get('overall_recommendation', 'N/A')}")
            
            alerts = result.get('alerts', [])
            if alerts:
                print(f"   Alerts: {len(alerts)} alert(s)")
                for alert in alerts[:3]:  # Show first 3 alerts
                    print(f"     • {alert}")
                if len(alerts) > 3:
                    print(f"     • ... and {len(alerts) - 3} more")
            
        except Exception as e:
            print(f"❌ Error analyzing {token_address[:8]}: {e}")
            results[token_address] = {'error': str(e)}
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scripts/results/phase3_deep_analysis_{timestamp}.json"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")
    print("="*80)
    
    return results

async def main():
    """
    Main function for Phase 3 analysis
    """
    # Test tokens
    test_tokens = [
        "9b1BzC1af9gQBtegh5WcuFB6ARBYQk7PgURW1aogpump",  # Token 1
        "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump",  # Token 2
        "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",  # Token 3
        "69G8CpUVZAxbPMiEBrfCCCH445NwFxH6PzVL693Xpump", # Xavier
        "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",  # DATBOI
        "8jFpBJoJwHkYLgNgequJJu6CMt3LkY3P6QndUupLpump"   # SHARKCAT
    ]
    
    print("🚀 Phase 3 Enhanced Deep Token Analysis")
    print("Features: Holder Concentration + Price Volatility + Market Context")
    
    results = await analyze_tokens(test_tokens)
    
    # Print summary statistics
    print(f"\n📈 ANALYSIS SUMMARY")
    print("="*50)
    
    successful_analyses = [r for r in results.values() if 'error' not in r]
    
    if successful_analyses:
        scores = [r.get('comprehensive_scoring', {}).get('overall_score', 0) for r in successful_analyses]
        risk_levels = [r.get('risk_assessment', {}).get('overall_risk_level', 'Unknown') for r in successful_analyses]
        
        print(f"Successful analyses: {len(successful_analyses)}/{len(test_tokens)}")
        print(f"Average score: {sum(scores)/len(scores):.1f}/100")
        print(f"Score range: {min(scores):.1f} - {max(scores):.1f}")
        
        # Risk distribution
        risk_counts = {}
        for risk in risk_levels:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        print("Risk distribution:")
        for risk, count in risk_counts.items():
            print(f"  {risk}: {count}")
    
    print("\n✅ Phase 3 Analysis Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 