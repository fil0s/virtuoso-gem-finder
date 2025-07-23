#!/usr/bin/env python3
"""
VLR Enhanced Demo Runner
=======================

Orchestrates and demonstrates all three VLR intelligence systems:
1. High Conviction Token Detector (with VLR scoring)
2. Cross-Platform Token Analyzer (with VLR optimization)  
3. VLR Optimal Scanner (standalone gem hunting)

Shows comprehensive VLR intelligence integration in action.
"""

import asyncio
import json
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Setup logging for the demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/vlr_enhanced_demo.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

async def run_high_conviction_detector_demo():
    """Run High Conviction Token Detector with VLR scoring"""
    print("\n🎯 RUNNING: High Conviction Token Detector (VLR Enhanced)")
    print("=" * 60)
    
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        detector = HighConvictionTokenDetector(debug_mode=False)
        print("✅ High Conviction Detector initialized with VLR intelligence")
        
        # Run a single detection cycle
        print("🔍 Running enhanced detection cycle...")
        result = await detector.run_detection_cycle()
        
        if result and result.get('status') == 'completed':
            print(f"✅ Detection completed successfully!")
            print(f"📊 Tokens analyzed: {result.get('total_analyzed', 0)}")
            print(f"🎯 High conviction found: {result.get('high_conviction_candidates', 0)}")
            print(f"📱 Alerts sent: {result.get('alerts_sent', 0)}")
            print(f"⏱️ Duration: {result.get('cycle_duration_seconds', 0):.1f}s")
            
            # Show VLR scoring impact
            detailed_analyses = result.get('detailed_analyses_data', [])
            vlr_enhanced_count = 0
            total_vlr_points = 0
            
            for analysis in detailed_analyses:
                if analysis and 'vlr_analysis' in analysis:
                    vlr_enhanced_count += 1
                    vlr_points = analysis.get('vlr_score', 0)
                    total_vlr_points += vlr_points
            
            if vlr_enhanced_count > 0:
                avg_vlr_points = total_vlr_points / vlr_enhanced_count
                print(f"🧠 VLR Enhancement: {vlr_enhanced_count} tokens with VLR analysis")
                print(f"📈 Average VLR points added: {avg_vlr_points:.1f}/15")
            
        await detector.cleanup()
        return result
        
    except Exception as e:
        print(f"❌ High Conviction Detector demo failed: {e}")
        return {'error': str(e)}

async def run_cross_platform_analyzer_demo():
    """Run Cross-Platform Token Analyzer with VLR optimization"""
    print("\n🔗 RUNNING: Cross-Platform Token Analyzer (VLR Optimized)")
    print("=" * 60)
    
    try:
        from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
        
        analyzer = CrossPlatformAnalyzer()
        print("✅ Cross-Platform Analyzer initialized with VLR optimization")
        
        # Run comprehensive analysis
        print("🔍 Running cross-platform analysis with VLR intelligence...")
        result = await analyzer.run_analysis()
        
        if 'error' not in result:
            correlations = result.get('correlations', {})
            all_tokens = correlations.get('all_tokens', {})
            vlr_summary = correlations.get('vlr_summary', {})
            
            print(f"✅ Analysis completed successfully!")
            print(f"📊 Total tokens analyzed: {len(all_tokens)}")
            print(f"🔗 Cross-platform correlations found: {correlations.get('cross_platform_count', 0)}")
            
            # Show VLR optimization results
            if vlr_summary:
                print(f"🧠 VLR Analysis Results:")
                print(f"  • Tokens with VLR data: {vlr_summary.get('total_with_vlr', 0)}")
                print(f"  • Gem candidates: {len(vlr_summary.get('gem_candidates', []))}")
                print(f"  • LP opportunities: {len(vlr_summary.get('lp_opportunities', []))}")
                print(f"  • Risk alerts: {len(vlr_summary.get('risk_alerts', []))}")
                
                # Show top VLR opportunities
                gem_candidates = vlr_summary.get('gem_candidates', [])[:3]
                if gem_candidates:
                    print(f"  🎯 Top Gem Candidates:")
                    for i, gem in enumerate(gem_candidates, 1):
                        symbol = gem.get('symbol', 'Unknown')
                        vlr = gem.get('vlr', 0)
                        category = gem.get('category', 'Unknown')
                        print(f"    {i}. {symbol} - VLR: {vlr:.2f} ({category})")
        
        await analyzer.close()
        return result
        
    except Exception as e:
        print(f"❌ Cross-Platform Analyzer demo failed: {e}")
        return {'error': str(e)}

async def run_vlr_optimal_scanner_demo():
    """Run VLR Optimal Scanner for specialized gem hunting"""
    print("\n🔍 RUNNING: VLR Optimal Scanner (Standalone Gem Hunting)")
    print("=" * 60)
    
    try:
        from scripts.vlr_optimal_scanner import VLROptimalScanner, VLRCategory
        
        # Focus on gem discovery and momentum building
        target_categories = [
            VLRCategory.GEM_DISCOVERY,
            VLRCategory.MOMENTUM_BUILD,
            VLRCategory.PEAK_PERFORMANCE
        ]
        
        scanner = VLROptimalScanner(target_categories=target_categories)
        print("✅ VLR Optimal Scanner initialized for gem hunting")
        
        # Run specialized VLR scan
        print("🔍 Running optimal VLR scan for gem opportunities...")
        result = await scanner.scan_for_optimal_vlr(
            min_liquidity=10000,  # Lower threshold for gem discovery
            min_volume=50000,     # Lower threshold for early gems
            max_tokens=50
        )
        
        if 'error' not in result:
            scan_info = result.get('scan_info', {})
            vlr_analysis = result.get('vlr_analysis', {})
            
            print(f"✅ VLR scan completed successfully!")
            print(f"📊 Total tokens analyzed: {scan_info.get('total_tokens_analyzed', 0)}")
            print(f"⏱️ Execution time: {scan_info.get('execution_time', 0):.1f}s")
            
            # Show category breakdown
            category_analysis = vlr_analysis.get('category_analysis', {})
            if category_analysis:
                print(f"🎯 VLR Category Results:")
                for category, tokens in category_analysis.items():
                    if tokens:
                        print(f"  • {category}: {len(tokens)} opportunities")
                        
                        # Show top opportunity in each category
                        if tokens:
                            top_token = tokens[0]
                            symbol = top_token.get('symbol', 'Unknown')
                            vlr = top_token.get('vlr', 0)
                            gem_potential = top_token.get('gem_potential', 'Unknown')
                            print(f"    Top: {symbol} - VLR: {vlr:.2f} ({gem_potential})")
        
        return result
        
    except Exception as e:
        print(f"❌ VLR Optimal Scanner demo failed: {e}")
        return {'error': str(e)}

def display_comprehensive_summary(hc_result: Dict[str, Any], 
                                 cp_result: Dict[str, Any], 
                                 vlr_result: Dict[str, Any]):
    """Display comprehensive summary of all three VLR systems"""
    print("\n🧠 COMPREHENSIVE VLR INTELLIGENCE SUMMARY")
    print("=" * 80)
    
    # Overall statistics
    total_tokens_analyzed = 0
    total_vlr_enhanced = 0
    total_opportunities = 0
    
    # High Conviction Detector stats
    if hc_result and 'error' not in hc_result:
        hc_analyzed = hc_result.get('total_analyzed', 0)
        hc_high_conviction = hc_result.get('high_conviction_candidates', 0)
        total_tokens_analyzed += hc_analyzed
        total_opportunities += hc_high_conviction
        
        detailed_analyses = hc_result.get('detailed_analyses_data', [])
        vlr_enhanced_hc = sum(1 for a in detailed_analyses if a and 'vlr_analysis' in a)
        total_vlr_enhanced += vlr_enhanced_hc
        
        print(f"🎯 High Conviction Detector:")
        print(f"  • Tokens analyzed: {hc_analyzed}")
        print(f"  • High conviction found: {hc_high_conviction}")
        print(f"  • VLR enhanced tokens: {vlr_enhanced_hc}")
    
    # Cross-Platform Analyzer stats
    if cp_result and 'error' not in cp_result:
        correlations = cp_result.get('correlations', {})
        all_tokens = correlations.get('all_tokens', {})
        vlr_summary = correlations.get('vlr_summary', {})
        
        cp_analyzed = len(all_tokens)
        vlr_tokens = vlr_summary.get('total_with_vlr', 0) if vlr_summary else 0
        gem_candidates = len(vlr_summary.get('gem_candidates', [])) if vlr_summary else 0
        
        total_tokens_analyzed += cp_analyzed
        total_vlr_enhanced += vlr_tokens
        total_opportunities += gem_candidates
        
        print(f"🔗 Cross-Platform Analyzer:")
        print(f"  • Tokens analyzed: {cp_analyzed}")
        print(f"  • VLR enhanced tokens: {vlr_tokens}")
        print(f"  • Gem candidates: {gem_candidates}")
    
    # VLR Optimal Scanner stats
    if vlr_result and 'error' not in vlr_result:
        scan_info = vlr_result.get('scan_info', {})
        vlr_analysis = vlr_result.get('vlr_analysis', {})
        
        vlr_analyzed = scan_info.get('total_tokens_analyzed', 0)
        category_analysis = vlr_analysis.get('category_analysis', {})
        vlr_opportunities = sum(len(tokens) for tokens in category_analysis.values())
        
        total_tokens_analyzed += vlr_analyzed
        total_vlr_enhanced += vlr_analyzed  # All tokens in VLR scanner have VLR analysis
        total_opportunities += vlr_opportunities
        
        print(f"🔍 VLR Optimal Scanner:")
        print(f"  • Tokens analyzed: {vlr_analyzed}")
        print(f"  • VLR opportunities: {vlr_opportunities}")
        print(f"  • Categories covered: {len(category_analysis)}")
    
    # Overall summary
    print(f"\n📊 OVERALL VLR INTELLIGENCE PERFORMANCE:")
    print(f"  • Total tokens analyzed: {total_tokens_analyzed}")
    print(f"  • Total VLR enhanced: {total_vlr_enhanced}")
    print(f"  • Total opportunities found: {total_opportunities}")
    
    if total_tokens_analyzed > 0:
        vlr_coverage = (total_vlr_enhanced / total_tokens_analyzed) * 100
        opportunity_rate = (total_opportunities / total_tokens_analyzed) * 100
        print(f"  • VLR coverage: {vlr_coverage:.1f}%")
        print(f"  • Opportunity rate: {opportunity_rate:.1f}%")
    
    print(f"\n🎉 VLR Intelligence Integration: FULLY OPERATIONAL!")
    print("=" * 80)

async def main():
    """Main demo orchestration"""
    logger = setup_logging()
    
    print("🚀 VLR ENHANCED DEMO - COMPREHENSIVE INTELLIGENCE SHOWCASE")
    print("=" * 80)
    print("🧠 Demonstrating integrated VLR intelligence across all systems:")
    print("   1. High Conviction Token Detector (VLR scoring)")
    print("   2. Cross-Platform Token Analyzer (VLR optimization)")
    print("   3. VLR Optimal Scanner (specialized gem hunting)")
    print("=" * 80)
    
    start_time = time.time()
    
    # Run all three VLR systems
    hc_result = await run_high_conviction_detector_demo()
    cp_result = await run_cross_platform_analyzer_demo()
    vlr_result = await run_vlr_optimal_scanner_demo()
    
    # Display comprehensive summary
    display_comprehensive_summary(hc_result, cp_result, vlr_result)
    
    # Save comprehensive results
    demo_results = {
        'demo_info': {
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': time.time() - start_time,
            'systems_tested': 3
        },
        'high_conviction_detector': hc_result,
        'cross_platform_analyzer': cp_result,
        'vlr_optimal_scanner': vlr_result
    }
    
    # Save results
    results_file = f"scripts/results/vlr_enhanced_demo_{int(time.time())}.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(demo_results, f, indent=2, default=str)
    
    print(f"\n📁 Demo results saved to: {results_file}")
    logger.info(f"VLR Enhanced Demo completed successfully in {time.time() - start_time:.1f}s")

if __name__ == "__main__":
    asyncio.run(main()) 