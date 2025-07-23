#!/usr/bin/env python3
"""
DEX Enhancement Demo Test
Demonstrates how Orca and Raydium integration enhances existing token analysis
WITHOUT modifying production files
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector
from api.cache_manager import EnhancedAPICacheManager
from utils.logger_setup import LoggerSetup

class DEXEnhancementDemo:
    """Demonstrates DEX integration benefits without modifying production code"""
    
    def __init__(self):
        logger_setup = LoggerSetup("dex_enhancement_demo")
        self.logger = logger_setup.logger
        self.cache_manager = EnhancedAPICacheManager()
        
        # Initialize DEX connectors
        self.orca = OrcaConnector(enhanced_cache=self.cache_manager)
        self.raydium = RaydiumConnector(enhanced_cache=self.cache_manager)
        
        # Sample tokens from your system
        self.test_tokens = {
            "TRUMP": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",
            "USELESS": "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",
            "aura": "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
        }
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'enhancement_benefits': {},
            'summary': {}
        }

    async def run_enhancement_demo(self):
        """Run the complete enhancement demonstration"""
        print("🚀 DEX Enhancement Demo - Testing Integration Benefits")
        print(f"📅 {self.results['timestamp']}")
        print("="*70)
        
        async with self.orca, self.raydium:
            print("\n📊 PHASE 1: Current Analysis (Simulated)")
            current_analysis = await self.simulate_current_analysis()
            
            print("\n🔗 PHASE 2: Enhanced Analysis with DEX Data")
            enhanced_analysis = await self.perform_dex_enhanced_analysis()
            
            print("\n📈 PHASE 3: Benefits Analysis")
            benefits = self.analyze_benefits(current_analysis, enhanced_analysis)
            
            self.results['current_analysis'] = current_analysis
            self.results['enhanced_analysis'] = enhanced_analysis
            self.results['enhancement_benefits'] = benefits
            
            self.display_summary()
            
            return self.results

    async def simulate_current_analysis(self):
        """Simulate current token analysis approach"""
        print("  🔍 Simulating current analysis...")
        
        current_scores = {}
        for name, address in self.test_tokens.items():
            score = 75.0 + (hash(address) % 20)  # 75-95 range
            current_scores[name] = {
                'address': address,
                'current_score': score,
                'risk_level': "MEDIUM",
                'data_sources': ['aggregated_apis']
            }
            print(f"    {name}: Score {score:.1f} | Risk: MEDIUM")
        
        return current_scores

    async def perform_dex_enhanced_analysis(self):
        """Perform enhanced analysis using DEX data"""
        print("  🔗 Enhancing with DEX data...")
        
        enhanced_scores = {}
        
        for name, address in self.test_tokens.items():
            print(f"    🔍 Analyzing {name}...")
            
            # Get DEX data
            orca_data = await self.get_orca_data(address)
            raydium_data = await self.get_raydium_data(address)
            
            # Calculate scores
            dex_score = self.calculate_dex_score(orca_data, raydium_data)
            risk_level = self.assess_risk(orca_data, raydium_data)
            
            base_score = 75.0 + (hash(address) % 20)
            enhanced_score = base_score + (dex_score * 0.3)
            
            enhanced_scores[name] = {
                'address': address,
                'base_score': base_score,
                'enhanced_score': enhanced_score,
                'dex_score': dex_score,
                'enhanced_risk_level': risk_level,
                'orca_found': orca_data['found'],
                'raydium_found': raydium_data['found'],
                'data_sources': ['orca_dex', 'raydium_dex']
            }
            
            print(f"      📈 Enhanced Score: {enhanced_score:.1f} (+{enhanced_score - base_score:.1f})")
            print(f"      ⚠️  Risk Level: {risk_level}")
            
        return enhanced_scores

    async def get_orca_data(self, token_address: str) -> Dict[str, Any]:
        """Get Orca DEX data"""
        try:
            pools = await self.orca.get_token_pools(token_address)
            return {
                'found': len(pools) > 0,
                'pool_count': len(pools),
                'pools': pools[:2]
            }
        except Exception as e:
            return {'found': False, 'error': str(e)}

    async def get_raydium_data(self, token_address: str) -> Dict[str, Any]:
        """Get Raydium DEX data"""
        try:
            pairs = await self.raydium.get_token_pairs(token_address)
            return {
                'found': len(pairs) > 0,
                'pair_count': len(pairs),
                'pairs': pairs[:2]
            }
        except Exception as e:
            return {'found': False, 'error': str(e)}

    def calculate_dex_score(self, orca_data: Dict, raydium_data: Dict) -> float:
        """Calculate DEX presence score"""
        score = 0.0
        
        if orca_data.get('found', False):
            score += 30.0
            score += min(20.0, orca_data.get('pool_count', 0) * 5)
        
        if raydium_data.get('found', False):
            score += 30.0
            score += min(20.0, raydium_data.get('pair_count', 0) * 5)
        
        return min(100.0, score)

    def assess_risk(self, orca_data: Dict, raydium_data: Dict) -> str:
        """Assess risk level with DEX data"""
        orca_found = orca_data.get('found', False)
        raydium_found = raydium_data.get('found', False)
        
        if not orca_found and not raydium_found:
            return "VERY HIGH"
        elif orca_found and raydium_found:
            return "LOW"
        else:
            return "MEDIUM"

    def analyze_benefits(self, current_analysis: Dict, enhanced_analysis: Dict) -> Dict[str, Any]:
        """Analyze enhancement benefits"""
        print("  📊 Calculating benefits...")
        
        score_improvements = []
        validation_successes = 0
        
        for token_name in current_analysis.keys():
            current = current_analysis[token_name]
            enhanced = enhanced_analysis[token_name]
            
            score_diff = enhanced['enhanced_score'] - current['current_score']
            score_improvements.append(score_diff)
            
            if enhanced['orca_found'] or enhanced['raydium_found']:
                validation_successes += 1
            
            print(f"    {token_name}: Score {score_diff:+.1f} | DEX Found: {enhanced['orca_found'] or enhanced['raydium_found']}")
        
        return {
            'total_tokens': len(current_analysis),
            'avg_score_improvement': sum(score_improvements) / len(score_improvements),
            'tokens_validated': validation_successes,
            'validation_rate': (validation_successes / len(current_analysis)) * 100
        }

    def display_summary(self):
        """Display summary"""
        print("\n" + "="*70)
        print("🎯 DEX ENHANCEMENT DEMO SUMMARY")
        print("="*70)
        
        benefits = self.results['enhancement_benefits']
        
        print(f"\n📊 RESULTS:")
        print(f"  • Tokens Analyzed: {benefits['total_tokens']}")
        print(f"  • DEX Validation Rate: {benefits['validation_rate']:.1f}%")
        print(f"  • Average Score Improvement: {benefits['avg_score_improvement']:+.1f} points")
        print(f"  • Tokens Validated on DEX: {benefits['tokens_validated']}")
        
        print(f"\n💡 RECOMMENDATION:")
        if benefits['validation_rate'] > 40:
            print("  ✅ STRONG RECOMMENDATION: Integrate DEX data immediately")
        else:
            print("  ⚠️  MODERATE RECOMMENDATION: Consider broader token testing")
        
        print("\n" + "="*70)

async def main():
    """Run the demo"""
    demo = DEXEnhancementDemo()
    
    try:
        await demo.run_enhancement_demo()
        print("\n🎉 Demo completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
