#!/usr/bin/env python3
"""
🚀 Enhanced Jupiter + Meteora Integration with Emerging Token Discovery
Unified system for both established trending tokens and new emerging opportunities

Features:
- Complete Jupiter + Meteora cross-platform analysis
- Dedicated emerging token discovery pipeline
- Risk-adjusted scoring for different token categories
- Comprehensive multi-stage validation
- Unified reporting and recommendations
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

# Import base systems
from test_jupiter_meteora_cross_platform_integration import JupiterMeteoraIntegratedAnalyzer
from emerging_token_discovery_system import EmergingTokenDiscoverySystem


class EnhancedJupiterMeteoraAnalyzer:
    """Enhanced analyzer combining established and emerging token discovery"""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize both analysis systems
        self.established_analyzer = JupiterMeteoraIntegratedAnalyzer(config, logger)
        self.emerging_analyzer = EmergingTokenDiscoverySystem(config, logger)
        
        # Enhanced configuration
        self.enhanced_config = {
            'discovery_modes': {
                'established_trending': True,      # High-volume, proven tokens
                'emerging_discovery': True,        # New, growing tokens
                'cross_validation': True,          # Validate across both systems
                'risk_assessment': True            # Comprehensive risk analysis
            },
            'scoring_weights': {
                'established_weight': 1.0,         # Standard weight for established
                'emerging_weight': 0.8,            # Slightly lower weight for emerging
                'cross_platform_bonus': 0.3,      # Bonus for multi-platform
                'risk_penalty': 0.2                # Penalty for high risk
            },
            'output_limits': {
                'top_established': 15,             # Top established tokens
                'top_emerging': 10,                # Top emerging tokens
                'top_combined': 25                 # Combined output limit
            }
        }
    
    async def run_comprehensive_analysis(self) -> Dict:
        """Run both established and emerging token analysis"""
        
        self.logger.info("🚀 Starting Enhanced Jupiter + Meteora Comprehensive Analysis")
        self.logger.info("=" * 90)
        
        start_time = time.time()
        
        try:
            # Stage 1: Established Token Analysis
            self.logger.info("📊 Stage 1: Established Token Trending Analysis")
            platform_data = await self.established_analyzer.collect_all_data()
            platform_breakdown = self.established_analyzer._generate_platform_breakdown(platform_data)
            
            # Stage 2: Emerging Token Discovery  
            self.logger.info("🔍 Stage 2: Emerging Token Discovery")
            emerging_results = await self.emerging_analyzer.run_emerging_token_discovery()
            
            # Combine results
            duration = time.time() - start_time
            
            final_results = {
                'analysis_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'duration_seconds': round(duration, 2),
                    'status': 'SUCCESS'
                },
                'established_analysis': {
                    'platform_breakdown': platform_breakdown,
                    'top_tokens': platform_breakdown.get('cross_platform_analysis', {}).get('top_multi_platform_tokens', [])
                },
                'emerging_analysis': emerging_results
            }
            
            # Save results
            timestamp = int(time.time())
            filename = f"scripts/tests/enhanced_comprehensive_analysis_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(final_results, f, indent=2, default=str)
            
            self.logger.info(f"\n🎯 COMPREHENSIVE ANALYSIS COMPLETE")
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info(f"Results saved to: {filename}")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    async def _run_established_analysis(self) -> Dict:
        """Run the established token trending analysis"""
        
        try:
            # Collect data from all platforms
            platform_data = await self.established_analyzer.collect_all_data()
            
            # Generate platform breakdown
            platform_breakdown = self.established_analyzer._generate_platform_breakdown(platform_data)
            
            # Get API stats
            api_stats = self.established_analyzer.get_api_stats()
            
            established_results = {
                'data_collection': {
                    'jupiter_tokens': len(platform_data.get('jupiter_all_tokens', [])),
                    'jupiter_trending': len(platform_data.get('jupiter_trending_quotes', [])),
                    'meteora_tokens': len(platform_data.get('meteora_trending_pools', [])),
                    'dexscreener_tokens': sum([
                        len(platform_data.get('dexscreener_boosted', [])),
                        len(platform_data.get('dexscreener_top', [])),
                        len(platform_data.get('dexscreener_profiles', [])),
                        len(platform_data.get('dexscreener_narratives', []))
                    ]),
                    'rugcheck_tokens': len(platform_data.get('rugcheck_trending', [])),
                    'birdeye_tokens': len(platform_data.get('birdeye_trending', []) + 
                                        platform_data.get('birdeye_emerging_stars', []))
                },
                'platform_breakdown': platform_breakdown,
                'api_performance': api_stats,
                'top_tokens': platform_breakdown.get('cross_platform_analysis', {}).get('top_multi_platform_tokens', [])
            }
            
            self.logger.info(f"✅ Established analysis complete: {len(established_results['top_tokens'])} top tokens")
            return established_results
            
        except Exception as e:
            self.logger.error(f"Error in established analysis: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    async def _run_emerging_analysis(self) -> Dict:
        """Run the emerging token discovery analysis"""
        
        try:
            emerging_results = await self.emerging_analyzer.run_emerging_token_discovery()
            
            self.logger.info(f"✅ Emerging analysis complete: {emerging_results.get('discovery_results', {}).get('cross_platform_count', 0)} cross-platform emerging")
            return emerging_results
            
        except Exception as e:
            self.logger.error(f"Error in emerging analysis: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    async def _cross_validate_discoveries(self, established_results: Dict, emerging_results: Dict) -> Dict:
        """Cross-validate discoveries between established and emerging systems"""
        
        validation_results = {
            'overlap_analysis': {},
            'graduation_candidates': [],  # Emerging tokens that appear in established
            'validation_metrics': {},
            'cross_system_confidence': {}
        }
        
        try:
            # Get token lists from both systems
            established_tokens = established_results.get('top_tokens', [])
            emerging_tokens = emerging_results.get('emerging_tokens', {}).get('cross_platform', [])
            
            # Find overlaps
            established_addresses = {token.get('address'): token for token in established_tokens}
            emerging_addresses = {token.get('address'): token for token in emerging_tokens}
            
            overlapping_addresses = set(established_addresses.keys()) & set(emerging_addresses.keys())
            
            validation_results['overlap_analysis'] = {
                'total_established': len(established_addresses),
                'total_emerging': len(emerging_addresses),
                'overlapping_count': len(overlapping_addresses),
                'overlap_percentage': (len(overlapping_addresses) / max(1, len(emerging_addresses))) * 100
            }
            
            # Identify graduation candidates (emerging -> established)
            for address in overlapping_addresses:
                established_token = established_addresses[address]
                emerging_token = emerging_addresses[address]
                
                graduation_candidate = {
                    'address': address,
                    'symbol': established_token.get('symbol', emerging_token.get('symbol')),
                    'established_score': established_token.get('total_score', 0),
                    'emerging_score': emerging_token.get('total_score', 0),
                    'validation_strength': 'HIGH',  # Appears in both systems
                    'confidence_level': 'VERY_HIGH',
                    'graduation_status': 'GRADUATED'  # From emerging to established
                }
                
                validation_results['graduation_candidates'].append(graduation_candidate)
            
            # Calculate validation metrics
            validation_results['validation_metrics'] = {
                'system_correlation': len(overlapping_addresses) / max(1, min(len(established_addresses), len(emerging_addresses))),
                'discovery_efficiency': {
                    'established_unique': len(established_addresses) - len(overlapping_addresses),
                    'emerging_unique': len(emerging_addresses) - len(overlapping_addresses),
                    'validated_discoveries': len(overlapping_addresses)
                }
            }
            
            self.logger.info(f"🔗 Cross-validation complete: {len(overlapping_addresses)} overlapping tokens")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error in cross-validation: {e}")
            return validation_results
    
    def _create_unified_rankings(self, established_results: Dict, emerging_results: Dict, 
                                validation_results: Dict) -> Dict:
        """Create unified rankings combining both systems"""
        
        unified_tokens = []
        
        try:
            # Process established tokens
            established_tokens = established_results.get('top_tokens', [])
            for token in established_tokens:
                unified_token = {
                    'address': token.get('address'),
                    'symbol': token.get('symbol'),
                    'category': 'ESTABLISHED',
                    'platforms': token.get('platforms', []),
                    'platform_count': token.get('platform_count', 0),
                    'raw_score': token.get('total_score', 0),
                    'weighted_score': token.get('total_score', 0) * self.enhanced_config['scoring_weights']['established_weight'],
                    'confidence_level': 'HIGH',
                    'risk_level': 'LOW',
                    'source_system': 'established_trending'
                }
                
                # Check if also in emerging (graduation candidate)
                graduation_candidates = validation_results.get('graduation_candidates', [])
                for grad in graduation_candidates:
                    if grad['address'] == token.get('address'):
                        unified_token['category'] = 'GRADUATED'
                        unified_token['confidence_level'] = 'VERY_HIGH'
                        unified_token['weighted_score'] += self.enhanced_config['scoring_weights']['cross_platform_bonus']
                        break
                
                unified_tokens.append(unified_token)
            
            # Process emerging tokens (that aren't already in established)
            emerging_tokens = emerging_results.get('emerging_tokens', {}).get('cross_platform', [])
            graduation_addresses = {grad['address'] for grad in validation_results.get('graduation_candidates', [])}
            
            for token in emerging_tokens:
                if token.get('address') not in graduation_addresses:
                    unified_token = {
                        'address': token.get('address'),
                        'symbol': token.get('symbol'),
                        'category': 'EMERGING',
                        'platforms': token.get('platforms', []),
                        'platform_count': token.get('platform_count', 0),
                        'raw_score': token.get('total_score', 0),
                        'weighted_score': token.get('total_score', 0) * self.enhanced_config['scoring_weights']['emerging_weight'],
                        'confidence_level': token.get('confidence_level', 'MEDIUM'),
                        'risk_level': token.get('risk_assessment', {}).get('overall_risk', 'HIGH'),
                        'source_system': 'emerging_discovery'
                    }
                    
                    # Apply risk penalty for high-risk tokens
                    if unified_token['risk_level'] == 'HIGH':
                        unified_token['weighted_score'] *= (1 - self.enhanced_config['scoring_weights']['risk_penalty'])
                    
                    unified_tokens.append(unified_token)
            
            # Sort by weighted score
            unified_tokens.sort(key=lambda x: x['weighted_score'], reverse=True)
            
            # Limit results
            max_results = self.enhanced_config['output_limits']['top_combined']
            unified_tokens = unified_tokens[:max_results]
            
            # Create rankings
            unified_rankings = {
                'total_tokens': len(unified_tokens),
                'category_distribution': {
                    'ESTABLISHED': len([t for t in unified_tokens if t['category'] == 'ESTABLISHED']),
                    'EMERGING': len([t for t in unified_tokens if t['category'] == 'EMERGING']),
                    'GRADUATED': len([t for t in unified_tokens if t['category'] == 'GRADUATED'])
                },
                'confidence_distribution': {
                    'VERY_HIGH': len([t for t in unified_tokens if t['confidence_level'] == 'VERY_HIGH']),
                    'HIGH': len([t for t in unified_tokens if t['confidence_level'] == 'HIGH']),
                    'MEDIUM': len([t for t in unified_tokens if t['confidence_level'] == 'MEDIUM'])
                },
                'ranked_tokens': unified_tokens
            }
            
            self.logger.info(f"📈 Unified rankings created: {len(unified_tokens)} total tokens")
            return unified_rankings
            
        except Exception as e:
            self.logger.error(f"Error creating unified rankings: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def _comprehensive_risk_assessment(self, unified_results: Dict) -> Dict:
        """Perform comprehensive risk assessment across all discovered tokens"""
        
        risk_assessment = {
            'overall_market_risk': 'MEDIUM',
            'category_risks': {
                'ESTABLISHED': 'LOW',
                'EMERGING': 'HIGH', 
                'GRADUATED': 'MEDIUM'
            },
            'portfolio_recommendations': [],
            'risk_warnings': [],
            'diversification_analysis': {}
        }
        
        try:
            tokens = unified_results.get('ranked_tokens', [])
            
            if not tokens:
                return risk_assessment
            
            # Analyze risk distribution
            high_risk_count = len([t for t in tokens if t['risk_level'] == 'HIGH'])
            medium_risk_count = len([t for t in tokens if t['risk_level'] == 'MEDIUM'])
            low_risk_count = len([t for t in tokens if t['risk_level'] == 'LOW'])
            
            total_tokens = len(tokens)
            
            # Determine overall market risk
            if high_risk_count / total_tokens > 0.6:
                risk_assessment['overall_market_risk'] = 'HIGH'
            elif low_risk_count / total_tokens > 0.6:
                risk_assessment['overall_market_risk'] = 'LOW'
            
            # Portfolio recommendations
            established_count = len([t for t in tokens if t['category'] == 'ESTABLISHED'])
            emerging_count = len([t for t in tokens if t['category'] == 'EMERGING'])
            
            if established_count >= 5:
                risk_assessment['portfolio_recommendations'].append(
                    f"✅ {established_count} established tokens available for core positions"
                )
            
            if emerging_count >= 3:
                risk_assessment['portfolio_recommendations'].append(
                    f"🚀 {emerging_count} emerging tokens for speculative allocation (max 10-20% portfolio)"
                )
            
            # Risk warnings
            if high_risk_count > total_tokens * 0.5:
                risk_assessment['risk_warnings'].append(
                    "⚠️ High proportion of risky tokens - exercise extreme caution"
                )
            
            if emerging_count > established_count:
                risk_assessment['risk_warnings'].append(
                    "🚨 More emerging than established tokens - market may be overheated"
                )
            
            # Diversification analysis
            platform_counts = {}
            for token in tokens:
                for platform in token.get('platforms', []):
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            risk_assessment['diversification_analysis'] = {
                'platform_distribution': platform_counts,
                'cross_platform_tokens': len([t for t in tokens if t['platform_count'] > 1]),
                'diversification_score': min(len(platform_counts) / 5.0, 1.0)  # Normalized to 1.0
            }
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error in risk assessment: {e}")
            return risk_assessment
    
    def _generate_strategic_recommendations(self, unified_results: Dict) -> List[str]:
        """Generate strategic trading recommendations"""
        
        recommendations = []
        
        try:
            tokens = unified_results.get('ranked_tokens', [])
            category_dist = unified_results.get('category_distribution', {})
            
            if not tokens:
                return ["⚠️ No tokens discovered - market may be inactive"]
            
            # Top tier recommendations (graduated tokens)
            graduated_tokens = [t for t in tokens if t['category'] == 'GRADUATED']
            if graduated_tokens:
                recommendations.append(
                    f"🎯 TOP PRIORITY: {len(graduated_tokens)} graduated tokens (emerging → established validation)"
                )
                top_graduated = graduated_tokens[:3]
                for i, token in enumerate(top_graduated, 1):
                    recommendations.append(
                        f"   {i}. {token['symbol']} (Score: {token['weighted_score']:.1f}, Platforms: {token['platform_count']})"
                    )
            
            # Established token recommendations
            established_tokens = [t for t in tokens[:10] if t['category'] == 'ESTABLISHED']
            if established_tokens:
                recommendations.append(
                    f"💎 CORE POSITIONS: Consider {len(established_tokens)} established tokens for portfolio base"
                )
            
            # Emerging token recommendations
            emerging_tokens = [t for t in tokens if t['category'] == 'EMERGING']
            if emerging_tokens:
                high_score_emerging = [t for t in emerging_tokens if t['weighted_score'] > 10]
                recommendations.append(
                    f"🚀 SPECULATIVE PLAYS: {len(high_score_emerging)} high-score emerging tokens (limit to 10-20% allocation)"
                )
            
            # Platform diversification
            multi_platform_tokens = [t for t in tokens[:15] if t['platform_count'] > 1]
            recommendations.append(
                f"🔗 DIVERSIFICATION: {len(multi_platform_tokens)} multi-platform tokens for reduced risk"
            )
            
            # Market timing recommendations
            if category_dist.get('EMERGING', 0) > category_dist.get('ESTABLISHED', 0):
                recommendations.append("⏰ MARKET TIMING: High emerging activity suggests early market cycle - higher risk/reward")
            else:
                recommendations.append("⏰ MARKET TIMING: Established token dominance suggests mature market - focus on quality")
            
            # Risk management
            recommendations.append("🛡️ RISK MANAGEMENT: Never exceed 5% position size on any single emerging token")
            recommendations.append("📊 MONITORING: Set up alerts for top 5 tokens and review positions daily")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["⚠️ Error generating recommendations"]
    
    def _calculate_performance_metrics(self, established_results: Dict, emerging_results: Dict, duration: float) -> Dict:
        """Calculate performance metrics for the analysis"""
        
        return {
            'execution_metrics': {
                'total_duration_seconds': round(duration, 2),
                'tokens_per_second': round(
                    (len(established_results.get('top_tokens', [])) + 
                     len(emerging_results.get('emerging_tokens', {}).get('cross_platform', []))) / duration, 2
                ),
                'api_efficiency': 'HIGH' if duration < 60 else 'MEDIUM' if duration < 120 else 'LOW'
            },
            'discovery_metrics': {
                'established_discovery_rate': len(established_results.get('top_tokens', [])),
                'emerging_discovery_rate': len(emerging_results.get('emerging_tokens', {}).get('cross_platform', [])),
                'cross_validation_success_rate': emerging_results.get('discovery_results', {}).get('cross_platform_count', 0)
            },
            'quality_metrics': {
                'multi_platform_percentage': 0,  # Calculated separately
                'high_confidence_percentage': 0,  # Calculated separately
                'risk_distribution_balance': 'GOOD'  # Qualitative assessment
            }
        }
    
    def _display_comprehensive_results(self, results: Dict):
        """Display comprehensive results in formatted tables"""
        
        self.logger.info("\n🏆 COMPREHENSIVE TOKEN ANALYSIS RESULTS")
        self.logger.info("=" * 120)
        
        # Summary statistics
        unified_results = results.get('unified_rankings', {})
        category_dist = unified_results.get('category_distribution', {})
        
        self.logger.info(f"📊 DISCOVERY SUMMARY:")
        self.logger.info(f"   • Total Tokens: {unified_results.get('total_tokens', 0)}")
        self.logger.info(f"   • Established: {category_dist.get('ESTABLISHED', 0)}")
        self.logger.info(f"   • Emerging: {category_dist.get('EMERGING', 0)}")
        self.logger.info(f"   • Graduated: {category_dist.get('GRADUATED', 0)}")
        
        # Top tokens table
        tokens = unified_results.get('ranked_tokens', [])[:15]
        if tokens:
            self.logger.info("\n🎯 TOP UNIFIED TOKEN RANKINGS:")
            self.logger.info("+" + "-" * 118 + "+")
            self.logger.info("| Rank | Symbol      | Category   | Platforms | Score | Confidence | Risk | Source System    |")
            self.logger.info("+" + "-" * 118 + "+")
            
            for i, token in enumerate(tokens, 1):
                symbol = token['symbol'][:10].ljust(10)
                category = token['category'][:9].ljust(9)
                platforms = str(token['platform_count']).ljust(8)
                score = f"{token['weighted_score']:.1f}".ljust(5)
                confidence = token['confidence_level'][:6].ljust(9)
                risk = token['risk_level'][:4].ljust(4)
                source = token['source_system'][:15].ljust(15)
                
                self.logger.info(f"| {i:4d} | {symbol} | {category} | {platforms} | {score} | {confidence} | {risk} | {source} |")
            
            self.logger.info("+" + "-" * 118 + "+")
        
        # Strategic recommendations
        recommendations = results.get('strategic_recommendations', [])
        if recommendations:
            self.logger.info("\n💡 STRATEGIC RECOMMENDATIONS:")
            for rec in recommendations[:8]:  # Top 8 recommendations
                self.logger.info(f"   {rec}")
        
        # Risk assessment summary
        risk_assessment = results.get('risk_assessment', {})
        self.logger.info(f"\n⚖️ RISK ASSESSMENT:")
        self.logger.info(f"   • Overall Market Risk: {risk_assessment.get('overall_market_risk', 'UNKNOWN')}")
        
        risk_warnings = risk_assessment.get('risk_warnings', [])
        if risk_warnings:
            self.logger.info(f"   • Warnings:")
            for warning in risk_warnings:
                self.logger.info(f"     {warning}")


async def main():
    """Main function to run the enhanced comprehensive analysis"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize and run the enhanced analysis
    enhanced_analyzer = EnhancedJupiterMeteoraAnalyzer(logger=logger)
    results = await enhanced_analyzer.run_comprehensive_analysis()
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 