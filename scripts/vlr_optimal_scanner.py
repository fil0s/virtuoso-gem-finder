#!/usr/bin/env python3
"""
VLR Optimal Scanner - Find Best VLR Opportunities Across DEXs
============================================================

Scans multiple DEXs to find tokens with optimal VLR scores for:
- Gem hunting (VLR 0.5-3.0)
- Peak performance (VLR 5.0-10.0)
- Liquidity provision opportunities
- Early manipulation detection

Uses VLR intelligence framework for comprehensive analysis.
"""

import asyncio
import json
import time
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from enum import Enum

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
    from api.enhanced_jupiter_connector import EnhancedJupiterConnector
    from services.enhanced_cache_manager import EnhancedPositionCacheManager
    from core.cache_manager import CacheManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class VLRCategory(Enum):
    """VLR optimization categories"""
    GEM_DISCOVERY = "🔍 Gem Discovery"      # VLR 0.5-2.0
    MOMENTUM_BUILD = "🚀 Momentum Building"  # VLR 2.0-5.0
    PEAK_PERFORMANCE = "💰 Peak Performance" # VLR 5.0-10.0
    DANGER_ZONE = "⚠️ Danger Zone"         # VLR 10.0-20.0
    MANIPULATION = "🚨 Manipulation"        # VLR >20.0

class VLROptimalScanner:
    """Scanner for optimal VLR scores across DEXs"""
    
    def __init__(self, target_categories: List[VLRCategory] = None):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Target categories to scan for
        self.target_categories = target_categories or [
            VLRCategory.GEM_DISCOVERY,
            VLRCategory.MOMENTUM_BUILD, 
            VLRCategory.PEAK_PERFORMANCE
        ]
        
        # Initialize cache and connectors
        self.base_cache = CacheManager()
        self.enhanced_cache = EnhancedPositionCacheManager(
            base_cache_manager=self.base_cache,
            logger=self.logger
        )
        
        self.analyzer = None
        
        # VLR thresholds for categories
        self.vlr_thresholds = {
            VLRCategory.GEM_DISCOVERY: (0.5, 2.0),
            VLRCategory.MOMENTUM_BUILD: (2.0, 5.0),
            VLRCategory.PEAK_PERFORMANCE: (5.0, 10.0),
            VLRCategory.DANGER_ZONE: (10.0, 20.0),
            VLRCategory.MANIPULATION: (20.0, float('inf'))
        }
        
        self.logger.info("🔍 VLR Optimal Scanner initialized")
        self.logger.info(f"🎯 Target categories: {[cat.value for cat in self.target_categories]}")
    
    async def scan_for_optimal_vlr(self, min_liquidity: float = 50000, 
                                  min_volume: float = 100000,
                                  max_tokens: int = 100) -> Dict[str, Any]:
        """Main scanning function for optimal VLR scores"""
        
        start_time = time.time()
        self.logger.info("🚀 Starting VLR Optimal Scanner")
        self.logger.info(f"📊 Filters: Min Liquidity ${min_liquidity:,.0f}, Min Volume ${min_volume:,.0f}")
        
        try:
            # Step 1: Gather token data
            self.logger.info("🔍 Gathering comprehensive token data...")
            all_tokens = await self._gather_token_data(max_tokens)
            
            # Step 2: Calculate VLR scores
            self.logger.info("📊 Calculating VLR scores...")
            vlr_tokens = self._calculate_vlr_scores(all_tokens, min_liquidity, min_volume)
            
            # Step 3: Categorize by VLR targets
            self.logger.info("🎯 Categorizing by VLR targets...")
            categorized_tokens = self._categorize_tokens(vlr_tokens)
            
            # Step 4: Analyze opportunities
            self.logger.info("💡 Analyzing opportunities...")
            analysis = self._analyze_opportunities(categorized_tokens)
            
            # Step 5: Generate recommendations
            self.logger.info("📋 Generating recommendations...")
            recommendations = self._generate_recommendations(analysis)
            
            # Compile results
            execution_time = time.time() - start_time
            results = self._compile_results(analysis, recommendations, execution_time)
            
            # Display and save
            self._display_results(results)
            await self._save_results(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ VLR scan failed: {e}")
            return {'error': str(e)}
        
        finally:
            await self.cleanup()
    
    async def _gather_token_data(self, max_tokens: int) -> Dict[str, Any]:
        """Gather comprehensive token data"""
        self.analyzer = CrossPlatformAnalyzer()
        analysis_results = await self.analyzer.run_analysis()
        
        if 'error' in analysis_results:
            raise Exception(f"Failed to gather token data: {analysis_results['error']}")
        
        correlations = analysis_results.get('correlations', {})
        all_tokens = correlations.get('all_tokens', {})
        
        self.logger.info(f"📊 Gathered data for {len(all_tokens)} tokens")
        return all_tokens
    
    def _calculate_vlr_scores(self, all_tokens: Dict[str, Any], 
                             min_liquidity: float, min_volume: float) -> List[Dict[str, Any]]:
        """Calculate VLR scores and filter tokens"""
        
        vlr_tokens = []
        
        for address, token_data in all_tokens.items():
            try:
                liquidity = token_data.get('liquidity', 0)
                volume_24h = token_data.get('volume_24h', 0)
                
                # Apply filters
                if liquidity < min_liquidity or volume_24h < min_volume:
                    continue
                
                # Calculate VLR
                vlr = volume_24h / liquidity if liquidity > 0 else 0
                
                if vlr <= 0:
                    continue
                
                # Create token record
                vlr_token = {
                    'address': address,
                    'symbol': token_data.get('symbol', 'Unknown'),
                    'name': token_data.get('name', ''),
                    'price': token_data.get('price', 0),
                    'liquidity': liquidity,
                    'volume_24h': volume_24h,
                    'vlr': vlr,
                    'platforms': token_data.get('platforms', []),
                    'market_cap': token_data.get('market_cap', 0),
                    'vlr_category': self._classify_vlr_category(vlr),
                    'gem_potential': self._assess_gem_potential(vlr, liquidity, volume_24h),
                    'risk_level': self._assess_risk_level(vlr)
                }
                
                vlr_tokens.append(vlr_token)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error calculating VLR for {address}: {e}")
                continue
        
        # Sort by VLR score
        vlr_tokens.sort(key=lambda x: x['vlr'], reverse=True)
        
        self.logger.info(f"📊 Calculated VLR for {len(vlr_tokens)} qualifying tokens")
        return vlr_tokens
    
    def _categorize_tokens(self, vlr_tokens: List[Dict[str, Any]]) -> Dict[VLRCategory, List[Dict[str, Any]]]:
        """Categorize tokens by VLR optimization targets"""
        
        categorized = defaultdict(list)
        
        for token in vlr_tokens:
            category = token['vlr_category']
            
            # Only include tokens in target categories
            if category in self.target_categories:
                categorized[category].append(token)
        
        # Sort each category by VLR
        for category in categorized:
            categorized[category].sort(key=lambda x: x['vlr'], reverse=True)
        
        return dict(categorized)
    
    def _analyze_opportunities(self, categorized_tokens: Dict[VLRCategory, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze VLR opportunities"""
        
        analysis = {
            'category_analysis': {},
            'top_performers': [],
            'gem_candidates': [],
            'risk_alerts': [],
            'optimal_ranges': {}
        }
        
        all_top_performers = []
        
        # Analyze each category
        for category, tokens in categorized_tokens.items():
            if not tokens:
                continue
            
            # Category statistics
            vlrs = [t['vlr'] for t in tokens]
            category_data = {
                'category': category.value,
                'token_count': len(tokens),
                'avg_vlr': sum(vlrs) / len(vlrs),
                'median_vlr': sorted(vlrs)[len(vlrs)//2],
                'vlr_range': (min(vlrs), max(vlrs)),
                'top_tokens': tokens[:5],
                'optimization_score': self._calculate_optimization_score(category, tokens)
            }
            
            analysis['category_analysis'][category] = category_data
            
            # Add to top performers
            all_top_performers.extend(tokens[:3])
            
            # Identify specific opportunities
            if category == VLRCategory.GEM_DISCOVERY:
                gems = [t for t in tokens if t['gem_potential'] == 'HIGH']
                analysis['gem_candidates'].extend(gems)
            
            elif category in [VLRCategory.DANGER_ZONE, VLRCategory.MANIPULATION]:
                risks = [t for t in tokens if t['risk_level'] == 'CRITICAL']
                analysis['risk_alerts'].extend(risks)
        
        # Sort and limit top performers
        all_top_performers.sort(key=lambda x: x['vlr'], reverse=True)
        analysis['top_performers'] = all_top_performers[:10]
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        
        recommendations = {
            'immediate_actions': [],
            'watch_list': [],
            'risk_warnings': [],
            'position_sizing': {},
            'action_plan': []
        }
        
        # Process top performers
        for token in analysis['top_performers'][:5]:
            vlr = token['vlr']
            category = token['vlr_category']
            
            if category == VLRCategory.PEAK_PERFORMANCE:
                recommendations['immediate_actions'].append({
                    'token': token,
                    'action': 'STRONG BUY - LP Position',
                    'reason': f"Optimal VLR ({vlr:.2f}) for fee generation",
                    'position_size': '20-40% of LP allocation',
                    'expected_apy': f"{vlr * 365 * 0.003 * 100:.0f}%",  # Rough APY estimate
                    'urgency': 'HIGH'
                })
            
            elif category == VLRCategory.MOMENTUM_BUILD:
                recommendations['immediate_actions'].append({
                    'token': token,
                    'action': 'BUY - Growth Position',
                    'reason': f"Building momentum VLR ({vlr:.2f})",
                    'position_size': '10-25% of allocation',
                    'expected_apy': f"{vlr * 365 * 0.003 * 100:.0f}%",
                    'urgency': 'MEDIUM'
                })
            
            elif category == VLRCategory.GEM_DISCOVERY:
                recommendations['watch_list'].append({
                    'token': token,
                    'action': 'ACCUMULATE - Early Entry',
                    'reason': f"Early discovery VLR ({vlr:.2f})",
                    'position_size': '5-15% of allocation',
                    'watch_trigger': 'VLR > 2.0',
                    'urgency': 'LOW'
                })
        
        # Risk warnings
        for risk_token in analysis['risk_alerts']:
            recommendations['risk_warnings'].append({
                'token': risk_token,
                'warning': 'EXTREME RISK - Avoid',
                'reason': f"VLR {risk_token['vlr']:.2f} indicates manipulation",
                'action': 'DO NOT ENTER or EXIT IMMEDIATELY'
            })
        
        # Create action plan
        recommendations['action_plan'] = self._create_action_plan(analysis, recommendations)
        
        return recommendations
    
    def _compile_results(self, analysis: Dict[str, Any], 
                        recommendations: Dict[str, Any], 
                        execution_time: float) -> Dict[str, Any]:
        """Compile final results"""
        
        return {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'execution_time': execution_time,
                'target_categories': [cat.value for cat in self.target_categories],
                'total_tokens_analyzed': sum(
                    data['token_count'] for data in analysis['category_analysis'].values()
                )
            },
            'vlr_analysis': analysis,
            'recommendations': recommendations,
            'summary': {
                'immediate_opportunities': len(recommendations['immediate_actions']),
                'watch_list_items': len(recommendations['watch_list']),
                'risk_alerts': len(recommendations['risk_warnings']),
                'gem_candidates': len(analysis['gem_candidates']),
                'categories_analyzed': len(analysis['category_analysis'])
            }
        }
    
    def _display_results(self, results: Dict[str, Any]):
        """Display comprehensive results"""
        
        print("\n" + "="*80)
        print("🔍 VLR OPTIMAL SCANNER RESULTS")
        print("="*80)
        
        # Summary
        scan_info = results['scan_info']
        summary = results['summary']
        
        print(f"\n📊 SCAN SUMMARY:")
        print(f"   • Execution Time: {scan_info['execution_time']:.1f} seconds")
        print(f"   • Tokens Analyzed: {scan_info['total_tokens_analyzed']}")
        print(f"   • Immediate Opportunities: {summary['immediate_opportunities']}")
        print(f"   • Watch List Items: {summary['watch_list_items']}")
        print(f"   • Risk Alerts: {summary['risk_alerts']}")
        print(f"   • Gem Candidates: {summary['gem_candidates']}")
        
        # Immediate opportunities
        immediate = results['recommendations']['immediate_actions']
        if immediate:
            print(f"\n🚀 IMMEDIATE VLR OPPORTUNITIES:")
            for i, opp in enumerate(immediate, 1):
                token = opp['token']
                print(f"\n   {i}. {token['symbol']} - {opp['action']}")
                print(f"      VLR: {token['vlr']:.2f} | Category: {token['vlr_category'].value}")
                print(f"      Reason: {opp['reason']}")
                print(f"      Position Size: {opp['position_size']}")
                print(f"      Expected APY: {opp.get('expected_apy', 'N/A')}")
                print(f"      Liquidity: ${token['liquidity']:,.0f}")
                print(f"      Volume 24h: ${token['volume_24h']:,.0f}")
                print(f"      Platforms: {len(token['platforms'])}")
        
        # Category breakdown
        categories = results['vlr_analysis']['category_analysis']
        if categories:
            print(f"\n📈 VLR CATEGORY BREAKDOWN:")
            for category, data in categories.items():
                print(f"\n   {data['category']} ({data['token_count']} tokens):")
                print(f"      Average VLR: {data['avg_vlr']:.2f}")
                print(f"      Median VLR: {data['median_vlr']:.2f}")
                print(f"      Range: {data['vlr_range'][0]:.2f} - {data['vlr_range'][1]:.2f}")
                print(f"      Optimization Score: {data['optimization_score']:.1f}/100")
                
                # Top tokens in category
                print(f"      Top Tokens:")
                for token in data['top_tokens'][:3]:
                    print(f"         • {token['symbol']}: VLR {token['vlr']:.2f}")
        
        # Watch list
        watch_list = results['recommendations']['watch_list']
        if watch_list:
            print(f"\n👀 WATCH LIST ({len(watch_list)} items):")
            for item in watch_list[:5]:
                token = item['token']
                print(f"   • {token['symbol']}: VLR {token['vlr']:.2f}")
                print(f"     {item['reason']} | Trigger: {item.get('watch_trigger', 'N/A')}")
        
        # Risk alerts
        risk_warnings = results['recommendations']['risk_warnings']
        if risk_warnings:
            print(f"\n🚨 RISK ALERTS:")
            for warning in risk_warnings[:3]:
                token = warning['token']
                print(f"   ⚠️ {token['symbol']}: VLR {token['vlr']:.2f}")
                print(f"      {warning['warning']} - {warning['reason']}")
        
        # Action plan
        action_plan = results['recommendations']['action_plan']
        if action_plan:
            print(f"\n📋 RECOMMENDED ACTION PLAN:")
            for i, action in enumerate(action_plan, 1):
                print(f"   {i}. {action}")
        
        print("\n" + "="*80)
        print("✅ VLR Optimal Scan Complete!")
        print("💡 Use these results for optimal DEX positioning")
        print("="*80)
    
    async def _save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        timestamp = int(time.time())
        filename = f"scripts/results/vlr_optimal_scan_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"💾 Results saved to: {filename}")
    
    # Helper methods
    def _classify_vlr_category(self, vlr: float) -> VLRCategory:
        """Classify VLR into category"""
        if vlr >= 20.0:
            return VLRCategory.MANIPULATION
        elif vlr >= 10.0:
            return VLRCategory.DANGER_ZONE
        elif vlr >= 5.0:
            return VLRCategory.PEAK_PERFORMANCE
        elif vlr >= 2.0:
            return VLRCategory.MOMENTUM_BUILD
        else:
            return VLRCategory.GEM_DISCOVERY
    
    def _assess_gem_potential(self, vlr: float, liquidity: float, volume: float) -> str:
        """Assess gem potential"""
        if (0.5 <= vlr <= 2.0 and 
            100_000 <= liquidity <= 2_000_000 and
            volume > 50_000):
            return 'HIGH'
        elif 0.3 <= vlr <= 3.0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _assess_risk_level(self, vlr: float) -> str:
        """Assess risk level"""
        if vlr >= 20.0:
            return 'CRITICAL'
        elif vlr >= 10.0:
            return 'HIGH'
        elif vlr >= 5.0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_optimization_score(self, category: VLRCategory, tokens: List[Dict[str, Any]]) -> float:
        """Calculate optimization score"""
        if not tokens:
            return 0.0
        
        vlrs = [t['vlr'] for t in tokens]
        avg_vlr = sum(vlrs) / len(vlrs)
        
        if category == VLRCategory.PEAK_PERFORMANCE:
            # Optimal range is 6-8 VLR
            optimal_tokens = sum(1 for vlr in vlrs if 6.0 <= vlr <= 8.0)
            return (optimal_tokens / len(tokens)) * 100
        elif category == VLRCategory.MOMENTUM_BUILD:
            # Good range is 3-4 VLR
            return min(70.0 + (avg_vlr - 2.0) * 10, 90.0)
        elif category == VLRCategory.GEM_DISCOVERY:
            # Potential range is 1-2 VLR
            return min(50.0 + avg_vlr * 15, 75.0)
        else:
            return max(30.0 - (avg_vlr - 10.0), 0.0)
    
    def _create_action_plan(self, analysis: Dict[str, Any], recommendations: Dict[str, Any]) -> List[str]:
        """Create action plan"""
        plan = []
        
        immediate = recommendations['immediate_actions']
        if immediate:
            plan.append(f"🚀 Review {len(immediate)} immediate VLR opportunities")
            plan.append("📊 Verify current liquidity depth before entering")
            plan.append("💰 Allocate positions based on VLR-optimized sizing")
        
        watch_list = recommendations['watch_list']
        if watch_list:
            plan.append(f"👀 Monitor {len(watch_list)} potential gems for VLR breakouts")
            plan.append("📈 Set VLR alerts for momentum confirmation")
        
        risks = recommendations['risk_warnings']
        if risks:
            plan.append(f"⚠️ Avoid {len(risks)} high-risk manipulation candidates")
        
        plan.append("🔄 Re-scan every 4-6 hours for VLR changes")
        plan.append("🎯 Focus on VLR 6-8 range for optimal returns")
        plan.append("💎 Watch for VLR breakouts above 2.0 in gems")
        
        return plan
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.analyzer:
                await self.analyzer.close()
            self.logger.info("🧹 Cleanup completed")
        except Exception as e:
            self.logger.warning(f"⚠️ Cleanup warning: {e}")

# Convenience functions
async def scan_gems() -> Dict[str, Any]:
    """Scan for gem opportunities"""
    scanner = VLROptimalScanner([VLRCategory.GEM_DISCOVERY])
    return await scanner.scan_for_optimal_vlr(min_liquidity=50000, min_volume=50000)

async def scan_peak_performance() -> Dict[str, Any]:
    """Scan for peak performance opportunities"""
    scanner = VLROptimalScanner([VLRCategory.PEAK_PERFORMANCE])
    return await scanner.scan_for_optimal_vlr(min_liquidity=500000, min_volume=500000)

async def scan_comprehensive() -> Dict[str, Any]:
    """Comprehensive VLR scan"""
    scanner = VLROptimalScanner(list(VLRCategory))
    return await scanner.scan_for_optimal_vlr(min_liquidity=100000, min_volume=100000)

if __name__ == "__main__":
    print("🔍 VLR Optimal Scanner")
    print("1. Gem Discovery Scan")
    print("2. Peak Performance Scan")
    print("3. Comprehensive Scan")
    
    choice = input("Choose scan type (1-3): ").strip()
    
    async def run_scan():
        if choice == "1":
            return await scan_gems()
        elif choice == "2":
            return await scan_peak_performance()
        else:
            return await scan_comprehensive()
    
    asyncio.run(run_scan()) 