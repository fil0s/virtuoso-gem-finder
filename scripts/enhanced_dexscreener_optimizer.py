#!/usr/bin/env python3
"""
Enhanced DexScreener Free API Optimizer
Maximizes free DexScreener usage for token discovery and validation
"""

class EnhancedDexScreenerOptimizer:
    """Leverage all DexScreener free endpoints intelligently"""
    
    def __init__(self, dexscreener_connector):
        self.dexscreener = dexscreener_connector
    
    async def comprehensive_free_discovery(self) -> Dict[str, Any]:
        """Use all free DexScreener endpoints for comprehensive token discovery"""
        
        # 1. Get boosted tokens (marketing signals)
        boosted_tokens = await self.dexscreener.get_boosted_tokens()
        
        # 2. Get top boosted tokens (highest investment)
        top_boosted = await self.dexscreener.get_top_boosted_tokens()
        
        # 3. Get token profiles (fundamental analysis)
        token_profiles = await self.dexscreener.get_token_profiles()
        
        # 4. Narrative-based discovery (trending themes)
        narrative_tokens = await self.dexscreener.discover_narrative_tokens([
            "AI", "agent", "meme", "gaming", "DeFi", "RWA", "pump", 
            "solana", "bitcoin", "ethereum", "trump", "elon"
        ])
        
        # 5. Combine and deduplicate all discovered tokens
        all_discovered_tokens = self._combine_and_deduplicate_tokens(
            boosted_tokens, top_boosted, token_profiles, narrative_tokens
        )
        
        # 6. Analyze liquidity for high-priority tokens
        high_priority_tokens = self._identify_high_priority_tokens(all_discovered_tokens)
        liquidity_analysis = {}
        
        for token in high_priority_tokens[:20]:  # Limit to top 20 to avoid rate limits
            analysis = await self.dexscreener.get_token_liquidity_analysis(token['address'])
            if analysis:
                liquidity_analysis[token['address']] = analysis
        
        return {
            'boosted_tokens': boosted_tokens,
            'top_boosted_tokens': top_boosted,
            'token_profiles': token_profiles,
            'narrative_tokens': narrative_tokens,
            'all_discovered_tokens': all_discovered_tokens,
            'liquidity_analysis': liquidity_analysis,
            'discovery_summary': self._generate_discovery_summary(all_discovered_tokens),
            'cost_optimization': self._calculate_cost_savings(all_discovered_tokens)
        }
    
    def _combine_and_deduplicate_tokens(self, boosted_tokens, top_boosted, token_profiles, narrative_tokens):
        """Combine and deduplicate all discovered tokens"""
        
        all_tokens = {**{token['address']: token for token in boosted_tokens},
                      **{token['address']: token for token in top_boosted},
                      **{token['address']: token for token in token_profiles},
                      **{token['address']: token for token in narrative_tokens}}
        
        return list(all_tokens.values())
    
    def _identify_high_priority_tokens(self, all_tokens):
        """Identify high-priority tokens based on various criteria"""
        
        high_priority_tokens = []
        
        for token in all_tokens:
            priority_score = 0
            
            # High priority: Trending on DexScreener
            if token['priority_score'] >= 40:
                priority_score += 50
            
            # High priority: Passes security checks
            if token.get('is_healthy', False):
                priority_score += 30
            
            # High priority: Recommended for analysis
            if token.get('recommended_for_analysis', False):
                priority_score += 25
            
            # Medium priority: Has legitimate liquidity pools
            if token.get('liquidity_pools_healthy', False):
                priority_score += 15
            
            # Medium priority: Good holder distribution
            if token.get('holder_distribution_healthy', False):
                priority_score += 10
            
            # Low priority: Clean trading patterns
            if token.get('trading_patterns_clean', False):
                priority_score += 5
            
            if priority_score >= 40:
                high_priority_tokens.append({
                    'address': token['address'],
                    'priority_score': priority_score,
                    'reasons': [f"priority_score >= {priority_score}"]
                })
        
        return high_priority_tokens
    
    def _generate_discovery_summary(self, all_tokens):
        """Generate a summary of the discovery process"""
        
        total_tokens = len(all_tokens)
        high_priority_tokens = len([t for t in all_tokens if t['priority_score'] >= 40])
        
        return {
            'total_tokens': total_tokens,
            'high_priority_tokens': high_priority_tokens,
            'low_priority_tokens': total_tokens - high_priority_tokens,
            'discovery_efficiency': f"{(high_priority_tokens/total_tokens)*100:.1f}% tokens discovered"
        }
    
    def _calculate_cost_savings(self, all_tokens):
        """Calculate estimated cost savings from filtering"""
        
        total_tokens = len(all_tokens)
        high_priority_tokens = len([t for t in all_tokens if t['priority_score'] >= 40])
        
        # Estimated costs (adjust based on actual API pricing)
        birdeye_cost_per_token = 0.005  # $0.005 per detailed token analysis
        moralis_cost_per_token = 0.001  # $0.001 per token metadata call
        
        # Without filtering
        total_birdeye_cost = total_tokens * birdeye_cost_per_token
        total_moralis_cost = total_tokens * moralis_cost_per_token
        
        # With filtering
        filtered_birdeye_cost = high_priority_tokens * birdeye_cost_per_token
        filtered_moralis_cost = high_priority_tokens * moralis_cost_per_token
        
        return {
            'total_tokens': total_tokens,
            'high_priority_tokens': high_priority_tokens,
            'low_priority_tokens': total_tokens - high_priority_tokens,
            'birdeye_cost_savings': total_birdeye_cost - filtered_birdeye_cost,
            'moralis_cost_savings': total_moralis_cost - filtered_moralis_cost,
            'total_cost_savings': (total_birdeye_cost + total_moralis_cost) - (filtered_birdeye_cost + filtered_moralis_cost),
            'filtering_efficiency': f"{(high_priority_tokens/total_tokens)*100:.1f}% tokens filtered"
        } 