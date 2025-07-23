"""
RugCheck API Connector

This module provides integration with the RugCheck API (https://api.rugcheck.xyz)
for token security analysis and risk assessment. Used to filter out potentially
risky tokens during the initial discovery phase.

RugCheck API endpoints implemented:
- /v1/tokens/{token_address}/report - Get comprehensive token security report
- /v1/tokens/{token_address}/summary - Get basic security summary
"""

import aiohttp
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from utils.structured_logger import get_structured_logger


class RugRiskLevel(Enum):
    """Risk levels for token security assessment"""
    SAFE = "safe"
    LOW_RISK = "low_risk" 
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL_RISK = "critical_risk"
    UNKNOWN = "unknown"


@dataclass
class RugCheckResult:
    """Result from RugCheck API analysis"""
    token_address: str
    risk_level: RugRiskLevel
    score: Optional[float]  # 0-100 score (higher is safer)
    issues: List[str]
    warnings: List[str]
    is_healthy: bool
    report_data: Dict[str, Any]
    api_success: bool
    error_message: Optional[str] = None


class RugCheckConnector:
    """
    Connector for RugCheck API to analyze token security and detect potential rug pulls.
    
    This connector provides methods to check token security and filter out risky tokens
    during the initial discovery phase.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize RugCheck connector.
        
        Args:
            logger: Optional logger instance
        """
        self.base_url = "https://api.rugcheck.xyz"
        self.api_version = "v1"
        
        # Setup logger
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
        
        self.structured_logger = get_structured_logger('RugCheckConnector')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        
        # Cache for results (10 minute TTL)
        self.result_cache = {}
        self.cache_ttl = 600
        
        # API call tracking
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "last_reset": time.time()
        }
        
        # Risk assessment configuration
        self.risk_thresholds = {
            "min_safe_score": 80.0,      # Scores >= 80 are considered safe
            "min_low_risk_score": 60.0,  # Scores >= 60 are low risk
            "min_medium_risk_score": 40.0, # Scores >= 40 are medium risk
            "critical_issues": [
                "honeypot",
                "proxy_contract", 
                "ownership_not_renounced",
                "pausable_contract",
                "blacklist_function",
                "whitelist_function",
                "anti_whale_function",
                "fee_modification_function"
            ]
        }
        
        self.logger.info("🛡️ RugCheck connector initialized for token security analysis")
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics for reporting"""
        stats = self.api_stats.copy()
        stats["endpoints_used"] = list(stats["endpoints_used"])
        stats["average_response_time_ms"] = (
            stats["total_response_time_ms"] / stats["total_calls"] 
            if stats["total_calls"] > 0 else 0
        )
        return stats
    
    def reset_api_statistics(self):
        """Reset API call statistics"""
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
            "last_reset": time.time()
        }
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to RugCheck API with rate limiting and tracking.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response data or None if failed
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        url = f"{self.base_url}/{self.api_version}/{endpoint}"
        start_time = time.time()
        
        # Track API call
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.last_request_time = time.time()
                    response_time_ms = int((time.time() - start_time) * 1000)
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        data = await response.json()
                        self.api_stats["successful_calls"] += 1
                        
                        self.structured_logger.info({
                            "event": "rugcheck_api_call",
                            "endpoint": endpoint,
                            "status": "success",
                            "status_code": response.status,
                            "response_time_ms": response_time_ms,
                            "timestamp": int(time.time())
                        })
                        return data
                    elif response.status == 429:
                        # Rate limited - wait and retry once
                        self.logger.warning(f"RugCheck API rate limited, waiting...")
                        await asyncio.sleep(2.0)
                        
                        retry_start = time.time()
                        async with session.get(url, params=params) as retry_response:
                            retry_time_ms = int((time.time() - retry_start) * 1000)
                            self.api_stats["total_response_time_ms"] += retry_time_ms
                            
                            if retry_response.status == 200:
                                self.api_stats["successful_calls"] += 1
                                return await retry_response.json()
                            else:
                                self.api_stats["failed_calls"] += 1
                    else:
                        self.api_stats["failed_calls"] += 1
                    
                    self.structured_logger.warning({
                        "event": "rugcheck_api_call",
                        "endpoint": endpoint,
                        "status": "error",
                        "status_code": response.status,
                        "response_time_ms": response_time_ms,
                        "timestamp": int(time.time())
                    })
                    self.logger.warning(f"RugCheck API call failed: {response.status}")
                    return None
                    
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            
            self.structured_logger.error({
                "event": "rugcheck_api_call",
                "endpoint": endpoint,
                "status": "exception",
                "error": str(e),
                "response_time_ms": response_time_ms,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error calling RugCheck API: {e}")
            return None
    
    async def get_token_report(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive security report for a token.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Full security report data
        """
        endpoint = f"tokens/{token_address}/report"
        return await self._make_request(endpoint)
    
    async def get_token_summary(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get basic security summary for a token.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Basic security summary data
        """
        endpoint = f"tokens/{token_address}/summary"
        return await self._make_request(endpoint)
    
    async def analyze_token_security(self, token_address: str) -> RugCheckResult:
        """
        Analyze token security and return structured result.
        
        Args:
            token_address: Token contract address
            
        Returns:
            RugCheckResult with security analysis
        """
        # Check cache first
        cache_key = f"rugcheck_{token_address}"
        if cache_key in self.result_cache:
            cached_result, timestamp = self.result_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.structured_logger.info({
                    "event": "rugcheck_cache_hit",
                    "token_address": token_address,
                    "timestamp": int(time.time())
                })
                return cached_result
        
        # Try to get comprehensive report first
        report_data = await self.get_token_report(token_address)
        
        # Fallback to summary if report fails
        if not report_data:
            report_data = await self.get_token_summary(token_address)
        
        # Process the results
        if report_data:
            result = self._process_rugcheck_data(token_address, report_data)
        else:
            # Create failed result
            result = RugCheckResult(
                token_address=token_address,
                risk_level=RugRiskLevel.UNKNOWN,
                score=None,
                issues=[],
                warnings=["API call failed"],
                is_healthy=False,  # Conservative approach - assume unhealthy if we can't check
                report_data={},
                api_success=False,
                error_message="Failed to fetch security data"
            )
        
        # Cache the result
        self.result_cache[cache_key] = (result, time.time())
        
        self.structured_logger.info({
            "event": "rugcheck_analysis_complete",
            "token_address": token_address,
            "risk_level": result.risk_level.value,
            "score": result.score,
            "is_healthy": result.is_healthy,
            "api_success": result.api_success,
            "timestamp": int(time.time())
        })
        
        return result
    
    def _process_rugcheck_data(self, token_address: str, data: Dict[str, Any]) -> RugCheckResult:
        """
        Process raw RugCheck API data into structured result.
        
        Args:
            token_address: Token contract address
            data: Raw API response data
            
        Returns:
            Processed RugCheckResult
        """
        issues = []
        warnings = []
        score = None
        
        # Extract score if available
        if "score" in data:
            score = float(data["score"])
        elif "risk_score" in data:
            score = 100.0 - float(data["risk_score"])  # Convert risk score to safety score
        
        # Extract issues and warnings
        if "issues" in data and data["issues"] is not None:
            issues.extend(data["issues"])
        if "warnings" in data and data["warnings"] is not None:
            warnings.extend(data["warnings"])
        if "risks" in data and data["risks"] is not None:
            for risk in data["risks"]:
                if risk.get("severity", "").lower() in ["high", "critical"]:
                    issues.append(risk.get("description", "Unknown high risk"))
                else:
                    warnings.append(risk.get("description", "Unknown warning"))
        
        # Determine risk level
        risk_level = self._calculate_risk_level(score, issues, warnings)
        
        # Determine if token is healthy (safe for trading)
        is_healthy = self._is_token_healthy(risk_level, issues, score)
        
        return RugCheckResult(
            token_address=token_address,
            risk_level=risk_level,
            score=score,
            issues=issues,
            warnings=warnings,
            is_healthy=is_healthy,
            report_data=data,
            api_success=True
        )
    
    def _calculate_risk_level(self, score: Optional[float], issues: List[str], warnings: List[str]) -> RugRiskLevel:
        """
        Calculate risk level based on score and identified issues.
        
        Args:
            score: Safety score (0-100, higher is safer)
            issues: List of critical issues
            warnings: List of warnings
            
        Returns:
            Calculated risk level
        """
        # Check for critical issues first
        critical_issues = [issue for issue in issues if any(critical in issue.lower() 
                          for critical in self.risk_thresholds["critical_issues"])]
        
        if critical_issues:
            return RugRiskLevel.CRITICAL_RISK
        
        # Use score-based classification if available
        if score is not None:
            if score >= self.risk_thresholds["min_safe_score"]:
                return RugRiskLevel.SAFE
            elif score >= self.risk_thresholds["min_low_risk_score"]:
                return RugRiskLevel.LOW_RISK
            elif score >= self.risk_thresholds["min_medium_risk_score"]:
                return RugRiskLevel.MEDIUM_RISK
            else:
                return RugRiskLevel.HIGH_RISK
        
        # Fallback to issue count if no score
        if len(issues) >= 3:
            return RugRiskLevel.HIGH_RISK
        elif len(issues) >= 1:
            return RugRiskLevel.MEDIUM_RISK
        elif len(warnings) >= 3:
            return RugRiskLevel.LOW_RISK
        else:
            return RugRiskLevel.SAFE
    
    def _is_token_healthy(self, risk_level: RugRiskLevel, issues: List[str], score: Optional[float]) -> bool:
        """
        Determine if a token is healthy enough for trading consideration.
        
        Args:
            risk_level: Calculated risk level
            issues: List of critical issues
            score: Safety score
            
        Returns:
            True if token is considered healthy for trading
        """
        # Critical and high risk tokens are not healthy
        if risk_level in [RugRiskLevel.CRITICAL_RISK, RugRiskLevel.HIGH_RISK]:
            return False
        
        # Check for specific deal-breaker issues
        deal_breakers = ["honeypot", "proxy_contract", "blacklist_function"]
        if any(any(deal_breaker in issue.lower() for deal_breaker in deal_breakers) 
               for issue in issues):
            return False
        
        # Score-based check
        if score is not None and score < 50.0:
            return False
        
        # Medium risk and below are considered healthy
        return risk_level in [RugRiskLevel.SAFE, RugRiskLevel.LOW_RISK, RugRiskLevel.MEDIUM_RISK]
    
    async def batch_analyze_tokens(self, token_addresses: List[str]) -> Dict[str, RugCheckResult]:
        """
        Analyze multiple tokens in batch with rate limiting.
        
        Args:
            token_addresses: List of token contract addresses
            
        Returns:
            Dictionary mapping token addresses to RugCheckResults
        """
        results = {}
        
        self.logger.info(f"🛡️ Starting batch security analysis for {len(token_addresses)} tokens")
        
        # Process tokens with rate limiting
        for i, token_address in enumerate(token_addresses):
            try:
                result = await self.analyze_token_security(token_address)
                results[token_address] = result
                
                self.logger.info(f"Analyzed {i+1}/{len(token_addresses)}: {token_address} - "
                               f"Risk: {result.risk_level.value}, Healthy: {result.is_healthy}")
                
                # Rate limiting between requests
                if i < len(token_addresses) - 1:
                    await asyncio.sleep(0.6)  # 600ms between requests
                    
            except Exception as e:
                self.logger.error(f"Error analyzing token {token_address}: {e}")
                results[token_address] = RugCheckResult(
                    token_address=token_address,
                    risk_level=RugRiskLevel.UNKNOWN,
                    score=None,
                    issues=[],
                    warnings=[f"Analysis failed: {str(e)}"],
                    is_healthy=False,
                    report_data={},
                    api_success=False,
                    error_message=str(e)
                )
        
        healthy_count = sum(1 for result in results.values() if result.is_healthy)
        self.logger.info(f"🛡️ Batch analysis complete: {healthy_count}/{len(results)} tokens passed security checks")
        
        return results
    
    def filter_healthy_tokens(self, tokens: List[Dict[str, Any]], 
                            rugcheck_results: Dict[str, RugCheckResult]) -> List[Dict[str, Any]]:
        """
        Filter token list to only include healthy tokens based on RugCheck analysis.
        
        Args:
            tokens: List of token data dictionaries
            rugcheck_results: Results from batch analysis
            
        Returns:
            Filtered list containing only healthy tokens
        """
        healthy_tokens = []
        filtered_count = 0
        
        for token in tokens:
            token_address = token.get("address")
            if not token_address:
                continue
            
            rugcheck_result = rugcheck_results.get(token_address)
            if rugcheck_result and rugcheck_result.is_healthy:
                # Add security data to token
                token["security_analysis"] = {
                    "rugcheck_score": rugcheck_result.score,
                    "risk_level": rugcheck_result.risk_level.value,
                    "issues_count": len(rugcheck_result.issues),
                    "warnings_count": len(rugcheck_result.warnings),
                    "analysis_timestamp": int(time.time())
                }
                healthy_tokens.append(token)
            else:
                filtered_count += 1
                if rugcheck_result:
                    self.logger.info(f"🚫 Filtered out {token_address}: Risk={rugcheck_result.risk_level.value}, "
                                   f"Issues={len(rugcheck_result.issues)}")
                else:
                    self.logger.info(f"🚫 Filtered out {token_address}: No security analysis available")
        
        self.logger.info(f"🛡️ Security filtering complete: {len(healthy_tokens)} healthy tokens, {filtered_count} filtered out")
        
        return healthy_tokens
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_results": len(self.result_cache),
            "cache_ttl": self.cache_ttl
        }
    
    def clear_cache(self):
        """Clear the result cache"""
        self.result_cache.clear()
        self.logger.info("RugCheck cache cleared")

    async def get_token_age_info(self, token_address: str) -> Dict[str, Any]:
        """
        Get token creation date and age information from RugCheck.
        Useful for optimizing Birdeye timeframe selection.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with age information
        """
        report_data = await self.get_token_report(token_address)
        
        if not report_data:
            return {'age_days': None, 'created_at': None, 'age_category': 'unknown'}
        
        created_at = report_data.get('created_at') or report_data.get('creation_time')
        if not created_at:
            return {'age_days': None, 'created_at': None, 'age_category': 'unknown'}
        
        # Convert to timestamp if needed
        if isinstance(created_at, str):
            try:
                import dateutil.parser
                created_at = dateutil.parser.parse(created_at).timestamp()
            except:
                return {'age_days': None, 'created_at': None, 'age_category': 'unknown'}
        
        current_time = time.time()
        age_seconds = current_time - created_at
        age_days = age_seconds / 86400
        
        # Categorize age
        if age_days < 1:
            age_category = 'very_new'
        elif age_days < 7:
            age_category = 'new'
        elif age_days < 30:
            age_category = 'young'
        elif age_days < 90:
            age_category = 'established'
        else:
            age_category = 'mature'
        
        return {
            'age_days': age_days,
            'created_at': created_at,
            'age_category': age_category
        }

    async def pre_validate_for_birdeye_analysis(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Pre-validate tokens before expensive Birdeye analysis.
        Checks liquidity pools, holder distribution, and trading patterns.
        
        Args:
            token_addresses: List of token addresses to validate
            
        Returns:
            Dictionary mapping addresses to validation results
        """
        validation_results = {}
        
        self.logger.info(f"🔍 Pre-validating {len(token_addresses)} tokens for Birdeye analysis")
        
        for token_address in token_addresses:
            try:
                report_data = await self.get_token_report(token_address)
                
                validation_result = {
                    'recommended_for_analysis': False,
                    'analysis_priority': 'low',
                    'liquidity_pools_healthy': False,
                    'holder_distribution_healthy': False,
                    'trading_patterns_clean': False,
                    'contract_verified': False,
                    'reasons': []
                }
                
                if not report_data:
                    validation_result['reasons'].append('No RugCheck data available')
                    validation_results[token_address] = validation_result
                    continue
                
                # Check liquidity pools
                liquidity_pools = report_data.get('liquidity_pools', [])
                legitimate_pools = [pool for pool in liquidity_pools 
                                  if pool.get('dex', '').lower() in ['raydium', 'orca', 'jupiter', 'serum']]
                
                if len(legitimate_pools) >= 1:
                    validation_result['liquidity_pools_healthy'] = True
                else:
                    validation_result['reasons'].append('No legitimate DEX pools found')
                
                # Check holder distribution
                holder_data = report_data.get('holder_analysis', {})
                top_10_percentage = holder_data.get('top_10_holders_percentage', 100)
                total_holders = holder_data.get('total_holders', 0)
                
                if top_10_percentage < 80 and total_holders > 50:
                    validation_result['holder_distribution_healthy'] = True
                else:
                    validation_result['reasons'].append(f'Poor holder distribution: {top_10_percentage}% in top 10, {total_holders} total holders')
                
                # Check trading patterns
                trading_patterns = report_data.get('trading_patterns', {})
                suspicious_flags = [
                    trading_patterns.get('wash_trading_detected', False),
                    trading_patterns.get('pump_dump_pattern', False),
                    trading_patterns.get('bot_trading_percentage', 0) > 90
                ]
                
                if not any(suspicious_flags):
                    validation_result['trading_patterns_clean'] = True
                else:
                    validation_result['reasons'].append('Suspicious trading patterns detected')
                
                # Check contract verification
                if report_data.get('contract_verified', False):
                    validation_result['contract_verified'] = True
                else:
                    validation_result['reasons'].append('Contract not verified')
                
                # Determine overall recommendation
                healthy_checks = sum([
                    validation_result['liquidity_pools_healthy'],
                    validation_result['holder_distribution_healthy'],
                    validation_result['trading_patterns_clean'],
                    validation_result['contract_verified']
                ])
                
                if healthy_checks >= 3:
                    validation_result['recommended_for_analysis'] = True
                    validation_result['analysis_priority'] = 'high'
                elif healthy_checks >= 2:
                    validation_result['recommended_for_analysis'] = True
                    validation_result['analysis_priority'] = 'medium'
                else:
                    validation_result['analysis_priority'] = 'low'
                    validation_result['reasons'].append('Failed multiple validation checks')
                
                validation_results[token_address] = validation_result
                
            except Exception as e:
                self.logger.error(f"Error validating token {token_address}: {e}")
                validation_results[token_address] = {
                    'recommended_for_analysis': False,
                    'analysis_priority': 'low',
                    'reasons': [f'Validation error: {str(e)}']
                }
        
        recommended_count = sum(1 for result in validation_results.values() 
                               if result['recommended_for_analysis'])
        
        self.logger.info(f"🔍 Pre-validation complete: {recommended_count}/{len(token_addresses)} tokens recommended for Birdeye analysis")
        
        return validation_results

    async def get_optimal_birdeye_timeframe(self, token_address: str) -> str:
        """
        Get optimal timeframe for Birdeye analysis based on token age.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optimal timeframe string ('1m', '5m', '15m', '1h', '4h', '1d')
        """
        age_info = await self.get_token_age_info(token_address)
        age_days = age_info.get('age_days')
        
        if age_days is None:
            return '1h'  # Default timeframe
        
        # Age-based timeframe optimization
        if age_days < 1:
            return '5m'   # Very fresh - high resolution
        elif age_days < 7:
            return '15m'  # Recent - medium resolution
        elif age_days < 30:
            return '1h'   # Established - standard resolution
        else:
            return '4h'   # Mature - lower resolution
    
    async def get_trending_tokens(self) -> List[Dict[str, Any]]:
        """
        Get trending tokens from RugCheck API with proper API call tracking.
        
        According to the RugCheck API documentation, /stats/trending returns exactly 10 tokens.
        This provides a curated list of trending tokens with inherent quality filtering.
        
        Returns:
            List of trending token dictionaries with addresses and metadata
        """
        try:
            # Use the tracked API call method
            data = await self._make_request("stats/trending")
            
            if not data:
                return []
            
            # Normalize the response format
            if isinstance(data, list):
                # Direct list of tokens
                trending_tokens = data
            elif isinstance(data, dict) and 'tokens' in data:
                # Wrapped in tokens field
                trending_tokens = data['tokens']
            elif isinstance(data, dict) and 'data' in data:
                # Wrapped in data field
                trending_tokens = data['data']
            else:
                # Fallback - treat as single item
                trending_tokens = [data] if data else []
            
            # Ensure proper format for each token
            # RugCheck trending API returns: {"mint": "address", "vote_count": 1, "up_count": 1}
            normalized_tokens = []
            for token in trending_tokens:
                if isinstance(token, dict) and ('mint' in token or 'address' in token):
                    address = token.get('mint', token.get('address', ''))
                    if address:
                        normalized_token = {
                            'address': address,
                            'symbol': token.get('symbol', 'UNKNOWN'),
                            'name': token.get('name', 'Trending Token'),
                            'vote_count': token.get('vote_count', 0),
                            'up_count': token.get('up_count', 0),
                            'score': token.get('score', token.get('up_count', 0)),  # Use up_count as score if no score
                            'risk_level': token.get('risk_level', 'unknown'),
                            'source': 'rugcheck_trending'
                        }
                        normalized_tokens.append(normalized_token)
            
            self.logger.info(f"✅ Retrieved {len(normalized_tokens)} trending tokens from RugCheck")
            return normalized_tokens
            
        except Exception as e:
            self.logger.error(f"Error fetching trending tokens from RugCheck: {e}")
            return []

    def route_tokens_by_quality(self, tokens: List[Dict[str, Any]], 
                               rugcheck_results: Dict[str, RugCheckResult],
                               validation_results: Dict[str, Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Route tokens to different analysis depths based on RugCheck quality assessment.
        This helps optimize Birdeye API usage by focusing resources on high-quality tokens.
        
        Args:
            tokens: List of token data dictionaries
            rugcheck_results: Results from RugCheck security analysis
            validation_results: Optional pre-validation results
            
        Returns:
            Dictionary with tokens routed by analysis priority
        """
        routing = {
            'premium_analysis': [],    # High-quality tokens - full Birdeye analysis
            'standard_analysis': [],   # Medium-quality tokens - basic analysis
            'minimal_analysis': [],    # Low-quality tokens - minimal analysis
            'skip_analysis': []        # Poor-quality tokens - skip expensive calls
        }
        
        for token in tokens:
            token_address = token.get('address')
            if not token_address:
                continue
            
            rugcheck_result = rugcheck_results.get(token_address)
            validation_result = validation_results.get(token_address) if validation_results else None
            
            # Default to skip if no security analysis
            if not rugcheck_result:
                routing['skip_analysis'].append(token)
                continue
            
            # Route based on security risk level
            if rugcheck_result.risk_level == RugRiskLevel.SAFE:
                if validation_result and validation_result.get('analysis_priority') == 'high':
                    routing['premium_analysis'].append(token)
                else:
                    routing['standard_analysis'].append(token)
                    
            elif rugcheck_result.risk_level == RugRiskLevel.LOW_RISK:
                if validation_result and validation_result.get('recommended_for_analysis'):
                    routing['standard_analysis'].append(token)
                else:
                    routing['minimal_analysis'].append(token)
                    
            elif rugcheck_result.risk_level == RugRiskLevel.MEDIUM_RISK:
                routing['minimal_analysis'].append(token)
                
            else:  # HIGH_RISK, CRITICAL_RISK, UNKNOWN
                routing['skip_analysis'].append(token)
        
        # Log routing summary
        self.logger.info(f"🎯 Token routing complete:")
        self.logger.info(f"   Premium analysis: {len(routing['premium_analysis'])} tokens")
        self.logger.info(f"   Standard analysis: {len(routing['standard_analysis'])} tokens")
        self.logger.info(f"   Minimal analysis: {len(routing['minimal_analysis'])} tokens")
        self.logger.info(f"   Skipped: {len(routing['skip_analysis'])} tokens")
        
        return routing

    async def get_detailed_security_report(self, token_address: str) -> Dict[str, Any]:
        """
        Get comprehensive security report for cost-optimized pipeline Stage 2.
        
        This method provides detailed security analysis including:
        - Risk factors breakdown
        - Holder concentration analysis
        - Contract security assessment
        - Liquidity analysis
        
        Args:
            token_address: Token contract address
            
        Returns:
            Detailed security report with cross-validation data
        """
        try:
            # Check cache first
            cache_key = f"detailed_report_{token_address}"
            if cache_key in self.result_cache:
                cache_entry = self.result_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                    return cache_entry['data']
            
            # Get detailed report from RugCheck
            report_data = await self._make_request(f"tokens/{token_address}/report")
            
            if not report_data:
                return self._create_empty_detailed_report(token_address)
            
            # Process detailed report
            detailed_analysis = self._process_detailed_security_report(token_address, report_data)
            
            # Cache the result
            self.result_cache[cache_key] = {
                'data': detailed_analysis,
                'timestamp': time.time()
            }
            
            self.logger.debug(f"✅ Detailed security report retrieved for {token_address}")
            return detailed_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error getting detailed security report for {token_address}: {e}")
            return self._create_empty_detailed_report(token_address)
    
    def _process_detailed_security_report(self, token_address: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process detailed security report data for cost-optimized analysis"""
        try:
            # Extract key security metrics
            security_analysis = {
                'token_address': token_address,
                'overall_risk_score': data.get('riskScore', 0),
                'is_verified': data.get('verified', False),
                'is_scam': data.get('isScam', False),
                'creation_time': data.get('creationTime'),
                'total_holders': data.get('totalHolders', 0),
                'total_supply': data.get('totalSupply', 0),
                'circulating_supply': data.get('circulatingSupply', 0),
                
                # Liquidity analysis
                'liquidity_analysis': {
                    'total_liquidity_usd': data.get('totalMarketLiquidity', 0),
                    'liquidity_locked': data.get('liquidityLocked', False),
                    'liquidity_lock_time': data.get('liquidityLockTime'),
                    'dex_liquidity': data.get('dexLiquidity', {})
                },
                
                # Holder concentration
                'holder_analysis': {
                    'total_holders': data.get('totalHolders', 0),
                    'top_holder_percentage': data.get('topHolderPercentage', 0),
                    'top_10_holder_percentage': data.get('top10HolderPercentage', 0),
                    'creator_percentage': data.get('creatorPercentage', 0),
                    'concentration_risk': self._assess_concentration_risk(data)
                },
                
                # Contract security
                'contract_security': {
                    'is_proxy': data.get('isProxy', False),
                    'is_mintable': data.get('isMintable', False),
                    'is_pausable': data.get('isPausable', False),
                    'ownership_renounced': data.get('ownershipRenounced', False),
                    'has_blacklist': data.get('hasBlacklist', False),
                    'has_whitelist': data.get('hasWhitelist', False),
                    'has_fee_modification': data.get('hasFeeModification', False),
                    'security_issues': data.get('securityIssues', [])
                },
                
                # Risk factors
                'risk_factors': self._extract_risk_factors(data),
                'warnings': data.get('warnings', []),
                'recommendations': data.get('recommendations', []),
                
                # Cross-validation data for Stage 2
                'cross_validation_ready': True,
                'analysis_timestamp': time.time()
            }
            
            return security_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error processing detailed security report: {e}")
            return self._create_empty_detailed_report(token_address)
    
    def _assess_concentration_risk(self, data: Dict[str, Any]) -> str:
        """Assess holder concentration risk level"""
        top_holder_pct = data.get('topHolderPercentage', 0)
        top_10_pct = data.get('top10HolderPercentage', 0)
        
        if top_holder_pct > 50:
            return 'critical'
        elif top_holder_pct > 30:
            return 'high'
        elif top_10_pct > 80:
            return 'high'
        elif top_10_pct > 60:
            return 'medium'
        else:
            return 'low'
    
    def _extract_risk_factors(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and categorize risk factors"""
        risk_factors = []
        
        # Contract risks
        if data.get('isProxy'):
            risk_factors.append({
                'type': 'contract',
                'severity': 'high',
                'factor': 'proxy_contract',
                'description': 'Contract uses proxy pattern, implementation can be changed'
            })
        
        if not data.get('ownershipRenounced'):
            risk_factors.append({
                'type': 'contract',
                'severity': 'medium',
                'factor': 'ownership_not_renounced',
                'description': 'Contract ownership has not been renounced'
            })
        
        if data.get('isMintable'):
            risk_factors.append({
                'type': 'tokenomics',
                'severity': 'high',
                'factor': 'mintable_token',
                'description': 'Token supply can be increased by minting'
            })
        
        # Liquidity risks
        if not data.get('liquidityLocked'):
            risk_factors.append({
                'type': 'liquidity',
                'severity': 'high',
                'factor': 'liquidity_not_locked',
                'description': 'Liquidity is not locked, can be withdrawn'
            })
        
        # Concentration risks
        top_holder_pct = data.get('topHolderPercentage', 0)
        if top_holder_pct > 30:
            risk_factors.append({
                'type': 'concentration',
                'severity': 'high' if top_holder_pct > 50 else 'medium',
                'factor': 'high_concentration',
                'description': f'Top holder owns {top_holder_pct:.1f}% of supply'
            })
        
        return risk_factors
    
    def _create_empty_detailed_report(self, token_address: str) -> Dict[str, Any]:
        """Create empty detailed report structure for failed requests"""
        return {
            'token_address': token_address,
            'overall_risk_score': 0,
            'is_verified': False,
            'is_scam': False,
            'creation_time': None,
            'total_holders': 0,
            'total_supply': 0,
            'circulating_supply': 0,
            'liquidity_analysis': {},
            'holder_analysis': {},
            'contract_security': {},
            'risk_factors': [],
            'warnings': [],
            'recommendations': [],
            'cross_validation_ready': False,
            'analysis_timestamp': time.time(),
            'error': 'Failed to retrieve detailed report'
        }
    
    async def cross_validate_with_external_data(self, token_address: str, external_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-validate RugCheck data with external sources (Birdeye, DexScreener).
        Used in Stage 2 of cost-optimized pipeline.
        
        Args:
            token_address: Token contract address
            external_data: Data from other sources (Birdeye, DexScreener)
            
        Returns:
            Cross-validation results with consistency scores
        """
        try:
            # Get our detailed report
            rugcheck_data = await self.get_detailed_security_report(token_address)
            
            if not rugcheck_data.get('cross_validation_ready'):
                return {'validation_status': 'failed', 'reason': 'RugCheck data unavailable'}
            
            validation_results = {
                'token_address': token_address,
                'validation_status': 'completed',
                'consistency_score': 0.0,
                'validation_checks': {},
                'discrepancies': [],
                'confidence_level': 'low'
            }
            
            checks_passed = 0
            total_checks = 0
            
            # Validate holder count consistency
            if 'holder_count' in external_data:
                total_checks += 1
                rugcheck_holders = rugcheck_data.get('total_holders', 0)
                external_holders = external_data['holder_count']
                
                # Allow 10% variance
                if abs(rugcheck_holders - external_holders) / max(rugcheck_holders, external_holders, 1) <= 0.1:
                    checks_passed += 1
                    validation_results['validation_checks']['holder_count'] = 'consistent'
                else:
                    validation_results['validation_checks']['holder_count'] = 'inconsistent'
                    validation_results['discrepancies'].append({
                        'field': 'holder_count',
                        'rugcheck_value': rugcheck_holders,
                        'external_value': external_holders,
                        'variance_percent': abs(rugcheck_holders - external_holders) / max(rugcheck_holders, external_holders, 1) * 100
                    })
            
            # Validate liquidity consistency
            if 'liquidity_usd' in external_data:
                total_checks += 1
                rugcheck_liquidity = rugcheck_data.get('liquidity_analysis', {}).get('total_liquidity_usd', 0)
                external_liquidity = external_data['liquidity_usd']
                
                # Allow 20% variance for liquidity (more volatile)
                if abs(rugcheck_liquidity - external_liquidity) / max(rugcheck_liquidity, external_liquidity, 1) <= 0.2:
                    checks_passed += 1
                    validation_results['validation_checks']['liquidity'] = 'consistent'
                else:
                    validation_results['validation_checks']['liquidity'] = 'inconsistent'
                    validation_results['discrepancies'].append({
                        'field': 'liquidity_usd',
                        'rugcheck_value': rugcheck_liquidity,
                        'external_value': external_liquidity,
                        'variance_percent': abs(rugcheck_liquidity - external_liquidity) / max(rugcheck_liquidity, external_liquidity, 1) * 100
                    })
            
            # Validate market cap consistency
            if 'market_cap' in external_data:
                total_checks += 1
                rugcheck_supply = rugcheck_data.get('circulating_supply', 0)
                external_mc = external_data['market_cap']
                
                # Calculate implied price and compare with external data if available
                if 'price' in external_data and rugcheck_supply > 0:
                    implied_mc = external_data['price'] * rugcheck_supply
                    if abs(implied_mc - external_mc) / max(implied_mc, external_mc, 1) <= 0.15:
                        checks_passed += 1
                        validation_results['validation_checks']['market_cap'] = 'consistent'
                    else:
                        validation_results['validation_checks']['market_cap'] = 'inconsistent'
                        validation_results['discrepancies'].append({
                            'field': 'market_cap',
                            'rugcheck_implied': implied_mc,
                            'external_value': external_mc,
                            'variance_percent': abs(implied_mc - external_mc) / max(implied_mc, external_mc, 1) * 100
                        })
                else:
                    validation_results['validation_checks']['market_cap'] = 'insufficient_data'
            
            # Calculate overall consistency score
            if total_checks > 0:
                validation_results['consistency_score'] = checks_passed / total_checks
                
                if validation_results['consistency_score'] >= 0.8:
                    validation_results['confidence_level'] = 'high'
                elif validation_results['consistency_score'] >= 0.6:
                    validation_results['confidence_level'] = 'medium'
                else:
                    validation_results['confidence_level'] = 'low'
            
            self.logger.debug(f"✅ Cross-validation completed for {token_address}: {validation_results['consistency_score']:.2f} consistency")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in cross-validation for {token_address}: {e}")
            return {
                'validation_status': 'error',
                'reason': str(e),
                'consistency_score': 0.0,
                'confidence_level': 'none'
            }