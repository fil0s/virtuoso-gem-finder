#!/usr/bin/env python3
"""
Enhanced RugCheck API Optimizer
Maximizes free RugCheck API usage to minimize expensive API calls
"""

class EnhancedRugCheckOptimizer:
    """Leverage all RugCheck free endpoints for intelligent filtering"""
    
    def __init__(self, rugcheck_connector):
        self.rugcheck = rugcheck_connector
        
    async def comprehensive_free_analysis(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Use all free RugCheck endpoints before expensive API calls"""
        
        # 1. Get trending tokens (already implemented)
        trending_tokens = await self.rugcheck.get_trending_tokens()
        trending_addresses = {token['address'] for token in trending_tokens}
        
        # 2. Batch security analysis for all tokens
        security_results = await self.rugcheck.batch_analyze_tokens(token_addresses)
        
        # 3. Pre-validation for expensive APIs (already implemented)
        validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(token_addresses)
        
        # 4. Quality-based routing (already implemented)
        routing_results = self.rugcheck.route_tokens_by_quality(
            [{'address': addr} for addr in token_addresses],
            security_results,
            validation_results
        )
        
        # 5. Prioritize tokens by multiple criteria
        prioritized_tokens = self._prioritize_tokens_for_expensive_apis(
            token_addresses, 
            trending_addresses,
            security_results,
            validation_results,
            routing_results
        )
        
        return {
            'trending_tokens': trending_tokens,
            'security_results': security_results,
            'validation_results': validation_results,
            'routing_results': routing_results,
            'prioritized_for_expensive_apis': prioritized_tokens,
            'cost_optimization': self._calculate_cost_savings(prioritized_tokens, token_addresses)
        }
    
    def _prioritize_tokens_for_expensive_apis(self, all_tokens, trending_addresses, 
                                            security_results, validation_results, routing_results):
        """Smart prioritization to minimize expensive API calls"""
        
        priority_tokens = []
        
        for token_addr in all_tokens:
            priority_score = 0
            reasons = []
            
            # High priority: Trending on RugCheck
            if token_addr in trending_addresses:
                priority_score += 50
                reasons.append("trending_on_rugcheck")
            
            # High priority: Passes security checks
            security_result = security_results.get(token_addr, {})
            if security_result.get('is_healthy', False):
                priority_score += 30
                reasons.append("security_validated")
            
            # High priority: Recommended for analysis
            validation_result = validation_results.get(token_addr, {})
            if validation_result.get('recommended_for_analysis', False):
                priority_score += 25
                reasons.append("analysis_recommended")
            
            # Medium priority: Has legitimate liquidity pools
            if validation_result.get('liquidity_pools_healthy', False):
                priority_score += 15
                reasons.append("healthy_liquidity")
            
            # Medium priority: Good holder distribution
            if validation_result.get('holder_distribution_healthy', False):
                priority_score += 10
                reasons.append("healthy_holders")
            
            # Low priority: Clean trading patterns
            if validation_result.get('trading_patterns_clean', False):
                priority_score += 5
                reasons.append("clean_trading")
            
            priority_tokens.append({
                'address': token_addr,
                'priority_score': priority_score,
                'reasons': reasons,
                'recommended_for_birdeye': priority_score >= 40,
                'recommended_for_moralis': priority_score >= 30
            })
        
        # Sort by priority score
        priority_tokens.sort(key=lambda x: x['priority_score'], reverse=True)
        return priority_tokens
    
    def _calculate_cost_savings(self, prioritized_tokens, all_tokens):
        """Calculate estimated cost savings from filtering"""
        
        total_tokens = len(all_tokens)
        recommended_for_birdeye = len([t for t in prioritized_tokens if t['recommended_for_birdeye']])
        recommended_for_moralis = len([t for t in prioritized_tokens if t['recommended_for_moralis']])
        
        # Estimated costs (adjust based on actual API pricing)
        birdeye_cost_per_token = 0.005  # $0.005 per detailed token analysis
        moralis_cost_per_token = 0.001  # $0.001 per token metadata call
        
        # Without filtering
        total_birdeye_cost = total_tokens * birdeye_cost_per_token
        total_moralis_cost = total_tokens * moralis_cost_per_token
        
        # With filtering
        filtered_birdeye_cost = recommended_for_birdeye * birdeye_cost_per_token
        filtered_moralis_cost = recommended_for_moralis * moralis_cost_per_token
        
        return {
            'total_tokens': total_tokens,
            'recommended_for_birdeye': recommended_for_birdeye,
            'recommended_for_moralis': recommended_for_moralis,
            'birdeye_cost_savings': total_birdeye_cost - filtered_birdeye_cost,
            'moralis_cost_savings': total_moralis_cost - filtered_moralis_cost,
            'total_cost_savings': (total_birdeye_cost + total_moralis_cost) - (filtered_birdeye_cost + filtered_moralis_cost),
            'filtering_efficiency': {
                'birdeye': f"{(1 - recommended_for_birdeye/total_tokens)*100:.1f}% tokens filtered",
                'moralis': f"{(1 - recommended_for_moralis/total_tokens)*100:.1f}% tokens filtered"
            }
        } 