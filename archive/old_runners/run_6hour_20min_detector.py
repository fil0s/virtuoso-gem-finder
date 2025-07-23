#!/usr/bin/env python3
"""
6-Hour High Conviction Token Detector - Pure Scoring System
Runs scans every 20 minutes for 6 hours (18 total cycles)
Uses pure numerical scoring without category classifications
"""

import asyncio
import sys
import os
import time
import logging
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging to reduce detector console output duplication
# This will be applied after detector initialization

def _display_detailed_scan_summary(detector, result, cycle_number):
    """Display detailed scan summary with tables if available"""
    try:
        # Try to import prettytable for enhanced display
        try:
            from prettytable import PrettyTable
            has_prettytable = True
        except ImportError:
            has_prettytable = False
        
        print(f"\n📊 SCAN #{cycle_number} COMPREHENSIVE SUMMARY:")
        print("-" * 50)
        
        # Display comprehensive token breakdown with all metrics included
        _display_cycle_token_breakdown(detector, result, cycle_number, has_prettytable)
        
        # Get token discovery data from detector for historical view
        tokens_discovered = detector.session_stats.get('tokens_discovered', {})
        if tokens_discovered:
            # Create tokens table
            if has_prettytable:
                token_table = PrettyTable()
                token_table.field_names = ["Rank", "Symbol", "Score", "Platforms", "Full Address"]
                token_table.align = "l"
                
                # Sort tokens by best conviction score
                sorted_tokens = sorted(
                    tokens_discovered.items(),
                    key=lambda x: x[1].get('best_conviction_score', 0),
                    reverse=True
                )[:5]  # Top 5
                
                for i, (address, token_data) in enumerate(sorted_tokens, 1):
                    symbol = token_data.get('symbol', 'Unknown')
                    score = token_data.get('best_conviction_score', 0)
                    platforms = ', '.join(token_data.get('platforms', []))
                    if len(platforms) > 15:
                        platforms = platforms[:12] + "..."
                    
                    token_table.add_row([
                        f"{i}.",
                        symbol[:10],
                        f"{score:.1f}",
                        platforms,
                        address
                    ])
                
                # Removed "TOP TOKENS THIS CYCLE" section to avoid redundancy with "TOKENS DISCOVERED" table
                pass
            else:
                # Fallback section also removed
                pass
        
        # Display API usage for this cycle
        if has_prettytable:
            api_table = PrettyTable()
            api_table.field_names = ["Platform", "Calls", "Success Rate", "Avg Response"]
            api_table.align = "l"
            
            api_usage = detector.session_stats.get('api_usage_by_service', {})
            for platform, stats in api_usage.items():
                calls = stats.get('total_calls', 0)
                successes = stats.get('successful_calls', 0)
                success_rate = (successes / max(1, calls)) * 100
                avg_response = stats.get('avg_response_time_ms', 0)
                
                api_table.add_row([
                    platform.title(),
                    str(calls),
                    f"{success_rate:.1f}%",
                    f"{avg_response:.0f}ms"
                ])
            
            print(f"\n📡 API PERFORMANCE THIS CYCLE:")
            print(api_table)
        
        print("-" * 50)
        
    except Exception as e:
        print(f"⚠️ Error in detailed scan summary: {e}")

def _display_session_summary_tables(detector):
    """Display comprehensive session summary with tables"""
    try:
        # Try to import prettytable
        try:
            from prettytable import PrettyTable
            has_prettytable = True
        except ImportError:
            has_prettytable = False
            
        if not has_prettytable:
            print("📊 Enhanced tables require 'prettytable' package")
            return
            
        print(f"\n📊 COMPREHENSIVE SESSION SUMMARY:")
        print("=" * 80)
        
        # Get session token registry if available
        if hasattr(detector, 'session_token_registry'):
            registry = detector.session_token_registry
            summary = registry.get('session_summary', {})
            
            # Overall statistics table
            overview_table = PrettyTable()
            overview_table.field_names = ["Metric", "Count", "Percentage"]
            overview_table.align = "l"
            
            total_tokens = summary.get('total_unique_tokens', 0)
            multi_platform = summary.get('multi_platform_tokens', 0)
            
            overview_table.add_row([
                "🎯 Total Unique Tokens", 
                str(total_tokens), 
                "100.0%"
            ])
            
            if multi_platform > 0:
                overview_table.add_row([
                    "🔗 Cross-Platform Validated", 
                    str(multi_platform), 
                    f"{(multi_platform/max(total_tokens, 1)*100):.1f}%"
                ])
            
            print(f"\n{overview_table}")
            
            # High conviction tokens table
            high_conviction_tokens = registry.get('high_conviction_tokens', {})
            if high_conviction_tokens:
                hc_table = PrettyTable()
                hc_table.field_names = ["Rank", "Symbol", "Score", "Platforms", "Full Address"]
                hc_table.align = "l"
                
                sorted_hc = sorted(
                    high_conviction_tokens.items(),
                    key=lambda x: x[1].get('score', 0),
                    reverse=True
                )[:10]  # Top 10
                
                for i, (address, token) in enumerate(sorted_hc, 1):
                    platforms_str = ', '.join(token.get('platforms', []))
                    if len(platforms_str) > 15:
                        platforms_str = platforms_str[:12] + "..."
                    
                    hc_table.add_row([
                        f"{i}.",
                        token.get('symbol', 'Unknown')[:10],
                        f"{token.get('score', 0):.1f}",
                        platforms_str,
                        address
                    ])
                
                print(f"\n🎯 HIGH CONVICTION TOKENS ({len(high_conviction_tokens)}):")
                print(hc_table)
        
        # Enhanced API usage summary table (including Jupiter & Meteora)
        api_usage = detector.session_stats.get('api_usage_by_service', {})
        if api_usage:
            api_summary_table = PrettyTable()
            api_summary_table.field_names = ["Platform", "Total Calls", "Success Rate", "Cost (USD)", "Type"]
            api_summary_table.align = "l"
            
            # Platform categorization for better display
            platform_types = {
                'birdeye': 'Traditional',
                'dexscreener': 'Traditional', 
                'rugcheck': 'Traditional',
                'jupiter': 'Emerging',
                'meteora': 'Emerging'
            }
            
            for platform, stats in api_usage.items():
                calls = stats.get('total_calls', 0)
                successes = stats.get('successful_calls', 0)
                success_rate = (successes / max(1, calls)) * 100
                cost = stats.get('estimated_cost_usd', 0.0)
                platform_type = platform_types.get(platform, 'Unknown')
                
                api_summary_table.add_row([
                    platform.title(),
                    str(calls),
                    f"{success_rate:.1f}%",
                    f"${cost:.4f}",
                    platform_type
                ])
            
            print(f"\n📡 ENHANCED API USAGE SUMMARY (Phase 3):")
            print(api_summary_table)
        
        print("=" * 80)
        
    except Exception as e:
        print(f"⚠️ Error in session summary tables: {e}")

def _display_scoring_analysis(detector, result, cycle_number):
    """Display pure scoring analysis without categories"""
    try:
        print(f"\n🎯 SCORING ANALYSIS (Pure Scoring System):")
        print("-" * 50)
        
        # Get scoring data from result or detector
        session_stats = getattr(detector, 'session_stats', {})
        
        # Score distribution analysis
        tokens_discovered = session_stats.get('tokens_discovered', {})
        if tokens_discovered:
            scores = [token.get('best_conviction_score', 0) for token in tokens_discovered.values()]
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                
                print(f"📊 Score Statistics:")
                print(f"  • Average Score: {avg_score:.1f}")
                print(f"  • Highest Score: {max_score:.1f}")
                print(f"  • Lowest Score: {min_score:.1f}")
                print(f"  • Total Tokens: {len(scores)}")
                
                # Score distribution ranges
                high_score = sum(1 for s in scores if s >= 70)
                medium_score = sum(1 for s in scores if 50 <= s < 70)
                low_score = sum(1 for s in scores if s < 50)
                
                print(f"\n📈 Score Distribution:")
                print(f"  • High (70+): {high_score} tokens ({(high_score/len(scores)*100):.1f}%)")
                print(f"  • Medium (50-69): {medium_score} tokens ({(medium_score/len(scores)*100):.1f}%)")
                print(f"  • Low (<50): {low_score} tokens ({(low_score/len(scores)*100):.1f}%)")
        else:
            print("  📊 No scoring data available for this cycle")
        
        # Platform coverage analysis (simplified)
        if hasattr(detector, 'session_stats'):
            api_usage = session_stats.get('api_usage_by_service', {})
            if api_usage:
                print(f"\n🌐 Platform Coverage:")
                for platform, stats in api_usage.items():
                    calls = stats.get('total_calls', 0)
                    success_rate = (stats.get('successful_calls', 0) / max(1, calls)) * 100
                    print(f"  • {platform.title()}: {calls} calls ({success_rate:.1f}% success)")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"⚠️ Error in scoring analysis: {e}")

def _display_pipeline_performance_analysis(detector, cycle_number):
    """Display enhanced pipeline performance analysis with per-scan metrics"""
    try:
        from prettytable import PrettyTable
        
        performance_summary = detector.get_pipeline_performance_summary()
        
        print(f"\n⚡ PIPELINE PERFORMANCE ANALYSIS - Cycle #{cycle_number}:")
        
        # ===== CYCLE-LEVEL PERFORMANCE =====
        print(f"\n🔄 CYCLE-LEVEL PERFORMANCE:")
        
        if performance_summary.get('stage_averages'):
            # Pipeline stages table
            pipeline_table = PrettyTable()
            pipeline_table.field_names = ["Pipeline Stage", "Avg Duration (ms)", "Samples", "Bottleneck Risk"]
            pipeline_table.align = "l"
            
            stage_names = {
                'cross_platform_analysis_ms': 'Cross-Platform Analysis',
                'detailed_analysis_ms': 'Detailed Analysis',
                'whale_analysis_ms': 'Whale Analysis',
                'volume_analysis_ms': 'Volume Analysis',
                'security_analysis_ms': 'Security Analysis',
                'community_analysis_ms': 'Community Analysis',
                'scoring_calculation_ms': 'Scoring Calculation',
                'alert_generation_ms': 'Alert Generation'
            }
            
            for stage_key, stage_data in performance_summary['stage_averages'].items():
                stage_name = stage_names.get(stage_key, stage_key.replace('_', ' ').title())
                duration = stage_data['avg_duration_ms']
                samples = stage_data['sample_count']
                risk = stage_data['bottleneck_risk']
                
                # Color code risk levels
                risk_display = f"🔴 {risk}" if risk == 'High' else f"🟡 {risk}" if risk == 'Medium' else f"🟢 {risk}"
                
                pipeline_table.add_row([
                    stage_name,
                    f"{duration:.0f}",
                    str(samples),
                    risk_display
                ])
            
            print(pipeline_table)
        
        # ===== SCAN-LEVEL PERFORMANCE (Individual API Calls) =====
        print(f"\n🔍 SCAN-LEVEL PERFORMANCE (Individual API Calls):")
        
        # Get API usage stats for detailed scan analysis
        api_stats = {}
        try:
            if hasattr(detector, 'session_stats') and detector.session_stats:
                api_usage = detector.session_stats.get('api_usage_by_service', {})
                api_stats = api_usage
                
                # Validate API stats accuracy
                total_recorded_calls = sum(stats.get('total_calls', 0) for stats in api_stats.values())
                if total_recorded_calls == 0:
                    print(f"⚠️ WARNING: No API calls recorded in session stats")
                    
        except Exception:
            api_stats = {}
        
        if api_stats:
            # Validate data before displaying
            valid_services = {}
            for service, stats in api_stats.items():
                total_calls = stats.get('total_calls', 0)
                successful_calls = stats.get('successful_calls', 0)
                
                # Data validation
                if successful_calls > total_calls:
                    print(f"⚠️ WARNING: {service} has more successful calls ({successful_calls}) than total calls ({total_calls})")
                    stats['successful_calls'] = total_calls  # Fix the data
                    
                if total_calls > 0:
                    valid_services[service] = stats
                    
            api_stats = valid_services
            scan_table = PrettyTable()
            scan_table.field_names = ["API Endpoint", "Total Calls", "Success Rate", "Avg Response (ms)", "Cost/Call", "Performance"]
            scan_table.align = "l"
            
            for service, stats in api_stats.items():
                total_calls = stats.get('total_calls', 0)
                successful_calls = stats.get('successful_calls', 0)
                avg_response_time = stats.get('avg_response_time_ms', 0)
                total_cost = stats.get('estimated_cost_usd', 0.0)
                
                if total_calls > 0:
                    success_rate = (successful_calls / total_calls) * 100
                    cost_per_call = total_cost / total_calls if total_calls > 0 else 0
                    
                    # Performance rating based on success rate and response time
                    if success_rate > 95 and avg_response_time < 500:
                        performance = "🟢 Excellent"
                    elif success_rate > 90 and avg_response_time < 1000:
                        performance = "🟡 Good"
                    elif success_rate > 80:
                        performance = "🟠 Fair"
                    else:
                        performance = "🔴 Poor"
                    
                    scan_table.add_row([
                        service.title(),
                        str(total_calls),
                        f"{success_rate:.1f}%",
                        f"{avg_response_time:.0f}",
                        f"${cost_per_call:.4f}",
                        performance
                    ])
            
            print(scan_table)
        else:
            print("  📊 No API usage data available yet")
        
        # ===== SCAN TYPE BREAKDOWN =====
        print(f"\n📊 SCAN TYPE ANALYSIS:")
        if api_stats:
            scan_types_table = PrettyTable()
            scan_types_table.field_names = ["Scan Type", "Purpose", "Calls/Cycle", "Success Rate", "Avg Response", "Impact"]
            scan_types_table.align = "l"
            
            # Define scan types and their characteristics
            scan_types = [
                {
                    'name': 'Cross-Platform Discovery',
                    'purpose': 'Multi-platform token discovery',
                    'service': 'dexscreener',
                    'impact': '🔴 Critical'
                },
                {
                    'name': 'Token Validation',
                    'purpose': 'Security & legitimacy checks',
                    'service': 'rugcheck',
                    'impact': '🟡 High'
                },
                {
                    'name': 'Detailed Analysis',
                    'purpose': 'Deep token metrics & scoring',
                    'service': 'birdeye',
                    'impact': '🔴 Critical'
                }
            ]
            
            total_cycles = detector.session_stats.get('performance_metrics', {}).get('total_cycles', 1)
            
            for scan_type in scan_types:
                service = scan_type['service']
                if service in api_stats:
                    stats = api_stats[service]
                    total_calls = stats.get('total_calls', 0)
                    successful_calls = stats.get('successful_calls', 0)
                    avg_response_time = stats.get('avg_response_time_ms', 0)
                    success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
                    
                    # Calculate calls per cycle
                    calls_per_cycle = total_calls / max(total_cycles, 1)
                    
                    scan_types_table.add_row([
                        scan_type['name'],
                        scan_type['purpose'],
                        f"{calls_per_cycle:.1f}",
                        f"{success_rate:.1f}%",
                        f"{avg_response_time:.0f}ms",
                        scan_type['impact']
                    ])
            
            print(scan_types_table)
        
        # ===== CYCLE vs SCAN CORRELATION =====
        print(f"\n🔗 CYCLE vs SCAN CORRELATION ANALYSIS:")
        
        if api_stats:
            # Identify scan-level bottlenecks
            bottlenecks = []
            performance_issues = []
            
            for service, stats in api_stats.items():
                total_calls = stats.get('total_calls', 0)
                if total_calls > 0:
                    avg_response_time = stats.get('avg_response_time_ms', 0)
                    success_rate = (stats.get('successful_calls', 0) / total_calls) * 100
                    
                    if avg_response_time > 2000:  # Slow response time
                        bottlenecks.append(f"🐌 {service.title()}: Slow response ({avg_response_time:.0f}ms)")
                    if success_rate < 90:  # Low success rate
                        performance_issues.append(f"⚠️ {service.title()}: Low reliability ({success_rate:.1f}%)")
            
            if bottlenecks or performance_issues:
                print(f"  🚨 Scan-Level Issues Detected:")
                for issue in (bottlenecks + performance_issues):
                    print(f"    • {issue}")
            else:
                print(f"  ✅ No significant scan-level bottlenecks detected")
            
            # Performance consistency analysis
            response_times = [stats.get('avg_response_time_ms', 0) for stats in api_stats.values() if stats.get('total_calls', 0) > 0 and stats.get('avg_response_time_ms', 0) > 0]
            if response_times and len(response_times) > 1:
                min_time = min(response_times)
                max_time = max(response_times)
                if max_time > 0:
                    consistency_score = max(0, 100 - ((max_time - min_time) / max_time * 100))
                else:
                    consistency_score = 100.0
                consistency_rating = "🟢 Excellent" if consistency_score > 80 else "🟡 Good" if consistency_score > 60 else "🔴 Inconsistent"
                print(f"  📊 Response Time Consistency: {consistency_rating} ({consistency_score:.1f}/100)")
            elif response_times and len(response_times) == 1:
                print(f"  📊 Response Time Consistency: 🟢 Single API (100.0/100)")
            else:
                print(f"  📊 Response Time Consistency: ⚪ No Data (0.0/100)")
            
            # Scan efficiency ranking
            scan_efficiency = {}
            for service, stats in api_stats.items():
                if stats.get('total_calls', 0) > 0:
                    success_rate = (stats.get('successful_calls', 0) / stats.get('total_calls', 1)) * 100
                    response_time_score = max(0, (2000 - stats.get('avg_response_time_ms', 1000)) / 2000 * 100)
                    efficiency = (success_rate * 0.7 + response_time_score * 0.3)
                    scan_efficiency[service] = efficiency
            
            if scan_efficiency:
                best_scan = max(scan_efficiency, key=scan_efficiency.get)
                worst_scan = min(scan_efficiency, key=scan_efficiency.get)
                
                print(f"  🏆 Best Performing Scan: {best_scan.title()} ({scan_efficiency[best_scan]:.1f}/100)")
                print(f"  📉 Needs Optimization: {worst_scan.title()} ({scan_efficiency[worst_scan]:.1f}/100)")
        
        # ===== OVERALL EFFICIENCY & RECOMMENDATIONS =====
        efficiency = performance_summary.get('efficiency_score', 0)
        efficiency_color = "🟢" if efficiency > 80 else "🟡" if efficiency > 60 else "🔴"
        print(f"\n🎯 Overall Pipeline Efficiency: {efficiency_color} {efficiency:.1f}/100")
        
        # Performance improvement recommendations
        print(f"\n💡 SCAN-LEVEL OPTIMIZATION RECOMMENDATIONS:")
        recommendations = []
        
        if api_stats:
            for service, stats in api_stats.items():
                if stats.get('total_calls', 0) > 0:
                    success_rate = (stats.get('successful_calls', 0) / stats.get('total_calls', 1)) * 100
                    avg_response_time = stats.get('avg_response_time_ms', 0)
                    
                    if success_rate < 95:
                        recommendations.append(f"Improve {service.title()} reliability (current: {success_rate:.1f}%)")
                    if avg_response_time > 1500:
                        recommendations.append(f"Optimize {service.title()} response time (current: {avg_response_time:.0f}ms)")
        
        if not recommendations:
            recommendations.append("All scans performing optimally - no immediate optimizations needed")
        
        for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
            print(f"  {i}. {rec}")
        
        # Show recent bottlenecks from cycle level
        bottlenecks = performance_summary.get('bottlenecks', [])
        if bottlenecks:
            print(f"\n⚠️ Recent Cycle-Level Bottlenecks: {len(bottlenecks)}")
            for bottleneck in bottlenecks[-3:]:  # Show last 3
                cycle_num = bottleneck.get('cycle_number', 'Unknown')
                duration = bottleneck.get('duration_seconds', 0)
                print(f"  • Cycle #{cycle_num}: {duration:.1f}s duration")
                
    except ImportError:
        print("📊 Pipeline performance analysis requires 'prettytable' package")
    except Exception as e:
        print(f"⚠️ Error in pipeline performance analysis: {e}")

def _display_cost_analysis_summary(detector, cycle_number):
    """Display detailed cost analysis with optimization recommendations"""
    try:
        from prettytable import PrettyTable
        
        cost_summary = detector.get_cost_analysis_summary()
        
        print(f"\n💰 COST ANALYSIS - Cycle #{cycle_number}:")
        
        # Cost breakdown table
        cost_table = PrettyTable()
        cost_table.field_names = ["Service Type", "Cost (USD)", "% of Total", "Optimization"]
        cost_table.align = "l"
        
        total_cost = cost_summary.get('total_cost', 0.0)
        cost_breakdown = cost_summary.get('cost_breakdown', {})
        
        service_names = {
            'rugcheck': 'RugCheck API',
            'dexscreener': 'DexScreener API',
            'birdeye_cross_platform': 'Birdeye Cross-Platform',
            'birdeye_detailed_analysis': 'Birdeye Detailed Analysis',
            'birdeye_whale_analysis': 'Birdeye Whale Analysis',
            'birdeye_volume_analysis': 'Birdeye Volume Analysis',
            'birdeye_security_analysis': 'Birdeye Security',
            'birdeye_community_analysis': 'Birdeye Community'
        }
        
        for service_key, cost_data in cost_breakdown.items():
            if isinstance(cost_data, dict):
                cost_usd = cost_data.get('cost_usd', 0.0)
                percentage = cost_data.get('percentage', 0.0)
            else:
                cost_usd = cost_data
                percentage = (cost_usd / max(total_cost, 0.001)) * 100
            
            service_name = service_names.get(service_key, service_key.replace('_', ' ').title())
            
            # Optimization potential
            if percentage > 50:
                optimization = "🔴 High Priority"
            elif percentage > 25:
                optimization = "🟡 Monitor"
            else:
                optimization = "🟢 Optimal"
            
            if cost_usd > 0:
                cost_table.add_row([
                    service_name,
                    f"${cost_usd:.4f}",
                    f"{percentage:.1f}%",
                    optimization
                ])
        
        print(cost_table)
        
        # Cost efficiency metrics
        cost_metrics = cost_summary.get('cost_per_metrics', {})
        print(f"\n💡 Cost Efficiency Metrics:")
        print(f"  • Cost per Cycle: ${cost_metrics.get('cost_per_cycle', 0.0):.4f}")
        print(f"  • Cost per Token: ${cost_metrics.get('cost_per_token', 0.0):.4f}")
        print(f"  • Cost per High Conviction: ${cost_metrics.get('cost_per_high_conviction', 0.0):.4f}")
        
        # Optimization recommendations
        recommendations = cost_summary.get('optimization_recommendations', [])
        if recommendations:
            print(f"\n🎯 Optimization Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
                print(f"  {i}. {rec}")
                
    except ImportError:
        print("💰 Cost analysis requires 'prettytable' package")
    except Exception as e:
        print(f"⚠️ Error in cost analysis: {e}")

def _display_token_quality_analysis(detector, cycle_number):
    """Display token discovery quality analysis"""
    try:
        from prettytable import PrettyTable
        
        quality_analysis = detector.get_token_quality_analysis()
        
        print(f"\n🎯 TOKEN QUALITY ANALYSIS - Cycle #{cycle_number}:")
        
        # Score distribution table
        score_dist = quality_analysis.get('score_distribution', {})
        if score_dist:
            dist_table = PrettyTable()
            dist_table.field_names = ["Score Range", "Token Count", "Quality Level"]
            dist_table.align = "l"
            
            quality_levels = {
                '0-20': '🔴 Poor',
                '20-40': '🟡 Fair', 
                '40-60': '🟠 Good',
                '60-80': '🟢 Excellent',
                '80-100': '🟣 Outstanding'
            }
            
            for score_range, count in score_dist.items():
                if count > 0:
                    quality = quality_levels.get(score_range, '⚪ Unknown')
                    dist_table.add_row([score_range, str(count), quality])
            
            print(f"\n📊 Score Distribution:")
            print(dist_table)
        
        # Platform effectiveness table
        platform_stats = quality_analysis.get('platform_effectiveness', {})
        if platform_stats:
            platform_table = PrettyTable()
            platform_table.field_names = ["Platform", "Tokens", "Avg Score", "High Conv Rate"]
            platform_table.align = "l"
            
            for platform, stats in platform_stats.items():
                count = stats.get('count', 0)
                avg_score = stats.get('avg_score', 0)
                hc_rate = stats.get('high_conviction_rate', 0)
                
                # Effectiveness rating
                effectiveness = "🟢" if avg_score > 6 else "🟡" if avg_score > 4 else "🔴"
                
                platform_table.add_row([
                    f"{effectiveness} {platform.title()}",
                    str(count),
                    f"{avg_score:.1f}",
                    f"{hc_rate:.1f}%"
                ])
            
            print(f"\n🔗 Platform Effectiveness:")
            print(platform_table)
        
        # Enhanced progression analysis
        progression = quality_analysis.get('progression_analysis', {})
        if progression:
            print(f"\n📈 DETAILED TOKEN SCORE PROGRESSION:")
            
            # Overall progression statistics
            improving_count = progression.get('improving_count', 0)
            declining_count = progression.get('declining_count', 0)
            stable_count = progression.get('stable_count', 0)
            total_tracked = improving_count + declining_count + stable_count
            
            if total_tracked > 0:
                # Create progression summary table
                progression_table = PrettyTable()
                progression_table.field_names = ["Category", "Count", "Percentage", "Trend"]
                progression_table.align = "l"
                
                progression_table.add_row([
                    "🟢 Improving", 
                    str(improving_count), 
                    f"{(improving_count/total_tracked*100):.1f}%",
                    "📈 Bullish"
                ])
                progression_table.add_row([
                    "🔴 Declining", 
                    str(declining_count), 
                    f"{(declining_count/total_tracked*100):.1f}%",
                    "📉 Bearish"
                ])
                progression_table.add_row([
                    "➡️ Stable", 
                    str(stable_count), 
                    f"{(stable_count/total_tracked*100):.1f}%",
                    "🔄 Neutral"
                ])
                
                print(progression_table)
            
            # Performance metrics
            best_improvement = progression.get('best_improvement', 0)
            worst_decline = progression.get('worst_decline', 0)
            avg_change = progression.get('average_change', 0)
            
            print(f"\n🎯 Performance Metrics:")
            print(f"  🏆 Best Improvement: +{best_improvement:.1f} points")
            print(f"  📉 Worst Decline: -{abs(worst_decline):.1f} points")
            print(f"  📊 Average Change: {avg_change:+.1f} points")
            
            # Volatility analysis
            volatility = progression.get('volatility_score', 0)
            volatility_level = "🔴 High" if volatility > 7 else "🟡 Medium" if volatility > 3 else "🟢 Low"
            print(f"  📊 Market Volatility: {volatility_level} ({volatility:.1f})")
            
            # Top movers (if available)
            top_gainers = progression.get('top_gainers', [])
            top_losers = progression.get('top_losers', [])
            
            if top_gainers:
                print(f"\n🚀 TOP GAINERS:")
                gainers_table = PrettyTable()
                gainers_table.field_names = ["Symbol", "Score Change", "Current Score", "Platforms"]
                gainers_table.align = "l"
                
                for gainer in top_gainers[:5]:  # Top 5
                    symbol = gainer.get('symbol', 'Unknown')
                    change = gainer.get('score_change', 0)
                    current = gainer.get('current_score', 0)
                    platforms = len(gainer.get('platforms', []))
                    
                    gainers_table.add_row([
                        symbol,
                        f"+{change:.1f}",
                        f"{current:.1f}",
                        str(platforms)
                    ])
                
                print(gainers_table)
            
            if top_losers:
                print(f"\n📉 TOP DECLINERS:")
                losers_table = PrettyTable()
                losers_table.field_names = ["Symbol", "Score Change", "Current Score", "Platforms"]
                losers_table.align = "l"
                
                for loser in top_losers[:5]:  # Top 5
                    symbol = loser.get('symbol', 'Unknown')
                    change = loser.get('score_change', 0)
                    current = loser.get('current_score', 0)
                    platforms = len(loser.get('platforms', []))
                    
                    losers_table.add_row([
                        symbol,
                        f"{change:.1f}",
                        f"{current:.1f}",
                        str(platforms)
                    ])
                
                print(losers_table)
            
            # Momentum analysis
            momentum_stats = progression.get('momentum_analysis', {})
            if momentum_stats:
                print(f"\n⚡ MOMENTUM ANALYSIS:")
                print(f"  🔥 Strong Momentum: {momentum_stats.get('strong_momentum_count', 0)} tokens")
                print(f"  📈 Positive Momentum: {momentum_stats.get('positive_momentum_count', 0)} tokens")
                print(f"  📉 Negative Momentum: {momentum_stats.get('negative_momentum_count', 0)} tokens")
                print(f"  💤 No Momentum: {momentum_stats.get('no_momentum_count', 0)} tokens")
                
                # Momentum strength
                avg_momentum = momentum_stats.get('average_momentum_strength', 0)
                momentum_strength = "🚀 Very Strong" if avg_momentum > 8 else "🔥 Strong" if avg_momentum > 5 else "📈 Moderate" if avg_momentum > 2 else "📉 Weak"
                print(f"  📊 Average Momentum Strength: {momentum_strength} ({avg_momentum:.1f})")
            
            # Time-based analysis
            time_analysis = progression.get('time_analysis', {})
            if time_analysis:
                print(f"\n⏰ TIME-BASED TRENDS:")
                print(f"  📅 Best Performing Hour: {time_analysis.get('best_hour', 'N/A')}")
                print(f"  📉 Worst Performing Hour: {time_analysis.get('worst_hour', 'N/A')}")
                print(f"  🔄 Cycle Consistency: {time_analysis.get('consistency_score', 0):.1f}/10")
        else:
            print(f"\n📈 Token Score Progression: No progression data available yet")
                
    except ImportError:
        print("🎯 Token quality analysis requires 'prettytable' package")
    except Exception as e:
        print(f"⚠️ Error in token quality analysis: {e}")

def _display_error_health_analysis(detector, cycle_number):
    """Display error analysis and system health monitoring"""
    try:
        from prettytable import PrettyTable
        
        error_summary = detector.get_error_analysis_summary()
        health_summary = detector.get_system_health_summary()
        
        print(f"\n🏥 SYSTEM HEALTH & ERROR ANALYSIS - Cycle #{cycle_number}:")
        
        # System health overview
        health_score = health_summary.get('overall_health_score', 0)
        health_color = "🟢" if health_score > 80 else "🟡" if health_score > 60 else "🔴"
        
        print(f"\n{health_color} Overall System Health: {health_score:.1f}/100")
        
        # Key health metrics
        print(f"📊 Key Metrics:")
        print(f"  • API Efficiency: {health_summary.get('api_efficiency_score', 0):.1f}/100")
        print(f"  • Cycle Success Rate: {health_summary.get('cycle_success_rate', 0):.1f}%")
        print(f"  • Total Errors: {error_summary.get('total_errors', 0)}")
        print(f"  • Recovery Rate: {error_summary.get('recovery_success_rate', 0):.1f}%")
        
        # Error breakdown table
        errors_by_service = error_summary.get('errors_by_service', {})
        if errors_by_service and any(count > 0 for count in errors_by_service.values()):
            error_table = PrettyTable()
            error_table.field_names = ["Service", "Error Count", "Error Rate", "Status"]
            error_table.align = "l"
            
            for service, error_count in errors_by_service.items():
                if error_count > 0:
                    # Calculate error rate (simplified)
                    total_cycles = detector.session_stats['performance_metrics']['total_cycles']
                    error_rate = (error_count / max(total_cycles, 1)) * 100
                    
                    status = "🔴 Critical" if error_rate > 20 else "🟡 Warning" if error_rate > 10 else "🟢 Stable"
                    
                    error_table.add_row([
                        service.title(),
                        str(error_count),
                        f"{error_rate:.1f}%",
                        status
                    ])
            
            print(f"\n🚨 Error Breakdown:")
            print(error_table)
        
        # System resources
        resources = health_summary.get('system_resources', {})
        if resources:
            print(f"\n💻 System Resources:")
            print(f"  • Peak Memory: {resources.get('peak_memory_mb', 0):.1f} MB")
            print(f"  • Avg CPU: {resources.get('avg_cpu_percent', 0):.1f}%")
        
        # Recent errors
        recent_errors = error_summary.get('recent_errors', [])
        if recent_errors:
            print(f"\n⚠️ Recent Errors ({len(recent_errors)}):")
            for error in recent_errors[-3:]:  # Show last 3
                error_type = error.get('type', 'unknown')
                provider = error.get('provider', 'unknown')
                print(f"  • {error_type} in {provider}")
                
    except ImportError:
        print("🏥 Health analysis requires 'prettytable' package")
    except Exception as e:
        print(f"⚠️ Error in health analysis: {e}")

def _display_cycle_token_breakdown(detector, result, cycle_number, has_prettytable):
    """Display comprehensive breakdown including scan metrics and tokens found in this cycle"""
    try:
        # Display basic scan metrics first
        total_analyzed = result.get('total_analyzed', 0)
        high_conviction_found = result.get('high_conviction_candidates', 0)
        new_candidates = result.get('new_candidates', 0)
        alerts_sent = result.get('alerts_sent', 0)
        duration = result.get('cycle_duration_seconds', 0)
        
        print(f"🔍 Analyzed: {total_analyzed} tokens | 🎯 High Conviction: {high_conviction_found} | 🆕 New: {new_candidates} | 📱 Alerts: {alerts_sent} | ⏱️ Duration: {duration:.1f}s")
        
        # Get detailed analysis data from the result
        detailed_analyses = result.get('detailed_analyses_data', [])
        high_conviction_candidates = result.get('high_conviction_candidates_data', [])
        
        # Combine all tokens found in this cycle
        cycle_tokens = []
        
        # Add detailed analysis tokens (these are the ones that went through full analysis)
        for analysis in detailed_analyses:
            if analysis and 'candidate' in analysis:
                candidate = analysis['candidate']
                cycle_tokens.append({
                    'address': candidate.get('address', 'Unknown'),
                    'symbol': candidate.get('symbol', 'Unknown'),
                    'score': analysis.get('final_score', 0),
                    'cross_platform_score': candidate.get('cross_platform_score', 0),
                    'platforms': candidate.get('platforms', []),
                    'status': 'Detailed Analysis',
                    'alert_sent': analysis.get('final_score', 0) >= detector.high_conviction_threshold,
                    'is_new': True  # All detailed analyses are new candidates
                })
        
        # Add high conviction candidates that didn't get detailed analysis
        detailed_addresses = {token['address'] for token in cycle_tokens}
        for candidate in high_conviction_candidates:
            if isinstance(candidate, dict) and candidate.get('address') not in detailed_addresses:
                cycle_tokens.append({
                    'address': candidate.get('address', 'Unknown'),
                    'symbol': candidate.get('symbol', 'Unknown'),
                    'score': candidate.get('cross_platform_score', 0),
                    'cross_platform_score': candidate.get('cross_platform_score', 0),
                    'platforms': candidate.get('platforms', []),
                    'status': 'Cross-Platform Only',
                    'alert_sent': False,
                    'is_new': True
                })
        
        if not cycle_tokens:
            print(f"\n📊 No tokens discovered in Cycle #{cycle_number}")
            return
        
        # Sort by score (highest first)
        cycle_tokens.sort(key=lambda x: x['score'], reverse=True)
        
        if has_prettytable:
            from prettytable import PrettyTable
            
            # Create detailed tokens table
            tokens_table = PrettyTable()
            tokens_table.field_names = ["Rank", "Symbol", "Final Score", "Cross-Platform", "Platform Count", "Platforms", "Status", "Alert", "Full Address"]
            tokens_table.align = "l"
            
            for i, token in enumerate(cycle_tokens, 1):
                symbol = token['symbol'][:12]  # Truncate long symbols
                final_score = token['score']
                cp_score = token['cross_platform_score']
                # Use unique platform count to avoid duplicates
                unique_platforms = list(set(token['platforms']))
                platform_count = len(unique_platforms)
                
                # Enhanced platform display logic with icons and better grouping
                platform_display = _format_platform_display(unique_platforms)
                
                status = token['status']
                
                # Alert status with icon
                alert_status = "🟢 Sent" if token['alert_sent'] else "⚪ None"
                
                tokens_table.add_row([
                    f"{i}.",
                    symbol,
                    f"{final_score:.1f}",
                    f"{cp_score:.1f}",
                    str(platform_count),
                    platform_display,
                    status,
                    alert_status,
                    token['address']
                ])
            
            print(f"\n🎯 TOKENS DISCOVERED IN CYCLE #{cycle_number} ({len(cycle_tokens)}):")
            print(tokens_table)
            
            # Show score distribution only (other metrics already shown at top)
            high_score = sum(1 for token in cycle_tokens if token['score'] >= 70)
            medium_score = sum(1 for token in cycle_tokens if 50 <= token['score'] < 70)
            low_score = sum(1 for token in cycle_tokens if token['score'] < 50)
            
            print(f"\n📊 Score Distribution: 🟢 High ({high_score}) | 🟡 Medium ({medium_score}) | ⚪ Low ({low_score})")
            
        else:
            # Fallback without prettytable
            print(f"\n🎯 TOKENS DISCOVERED IN CYCLE #{cycle_number} ({len(cycle_tokens)}):")
            
            for i, token in enumerate(cycle_tokens, 1):
                symbol = token['symbol']
                final_score = token['score']
                platforms = ', '.join(token['platforms'])
                status = token['status']
                alert_icon = "🟢" if token['alert_sent'] else "⚪"
                address = token['address']
                
                print(f"  {i}. {symbol} - Score: {final_score:.1f} - Platforms: {platforms} - {status} {alert_icon} - Address: {address}")
            
            # Summary
            new_count = sum(1 for token in cycle_tokens if token['is_new'])
            alerted_count = sum(1 for token in cycle_tokens if token['alert_sent'])
            print(f"\n  📋 Summary: {len(cycle_tokens)} total | {new_count} new | {alerted_count} alerted")
        
    except Exception as e:
        print(f"⚠️ Error displaying cycle token breakdown: {e}")

def _format_platform_display(platforms):
    """
    Enhanced platform display formatting with icons, grouping, and smart abbreviations
    
    Args:
        platforms: List of platform names
        
    Returns:
        Formatted string for display in table
    """
    if not platforms:
        return "None"
    
    # Platform mapping with clean abbreviations
    platform_mapping = {
        # Birdeye platforms
        'birdeye': 'BE',
        'birdeye_trending': 'BE',
        'birdeye_emerging_stars': 'BE*',
        'birdeye_cross_platform': 'BE+',
        'birdeye_detailed_analysis': 'BE-D',
        'birdeye_whale_analysis': 'BE-W',
        'birdeye_volume_analysis': 'BE-V',
        'birdeye_security_analysis': 'BE-S',
        'birdeye_community_analysis': 'BE-C',
        
        # DexScreener platforms
        'dexscreener': 'DX',
        'dexscreener_boosted': 'DX-B',
        'dexscreener_top': 'DX-T',
        'dexscreener_profiles': 'DX-P',
        'dexscreener_narratives': 'DX-N',
        
        # Jupiter platforms
        'jupiter': 'JUP',
        'jupiter_trending_quotes': 'JUP-Q',
        'jupiter_quote': 'JUP-Q',
        'jupiter_tokens': 'JUP-T',
        'jupiter_liquidity': 'JUP-L',
        
        # Meteora platforms
        'meteora': 'MET',
        'meteora_trending_pools': 'MET-P',
        'meteora_volume': 'MET-V',
        
        # RugCheck platforms
        'rugcheck': 'RUG',
        'rugcheck_trending': 'RUG-T',
        'rugcheck_security': 'RUG-S',
        
        # Orca platforms
        'orca': 'ORCA',
        'orca_whirlpool': 'ORCA-W',
        'orca_pools': 'ORCA-P',
        
        # Raydium platforms
        'raydium': 'RAY',
        'raydium_amm': 'RAY-AMM',
        'raydium_clmm': 'RAY-CLMM',
        'raydium_farms': 'RAY-F',
    }
    
    # Group platforms by provider
    platform_groups = {
        'birdeye': [],
        'dexscreener': [],
        'jupiter': [],
        'meteora': [],
        'rugcheck': [],
        'orca': [],
        'raydium': [],
        'other': []
    }
    
    # Categorize platforms
    for platform in platforms:
        if platform.startswith('birdeye'):
            platform_groups['birdeye'].append(platform)
        elif platform.startswith('dexscreener') or platform == 'dex':
            platform_groups['dexscreener'].append(platform)
        elif platform.startswith('jupiter'):
            platform_groups['jupiter'].append(platform)
        elif platform.startswith('meteora'):
            platform_groups['meteora'].append(platform)
        elif platform.startswith('rugcheck') or platform == 'rug':
            platform_groups['rugcheck'].append(platform)
        elif platform.startswith('orca'):
            platform_groups['orca'].append(platform)
        elif platform.startswith('raydium'):
            platform_groups['raydium'].append(platform)
        else:
            platform_groups['other'].append(platform)
    
    # Build display string
    display_parts = []
    
    # Birdeye group
    if platform_groups['birdeye']:
        birdeye_platforms = platform_groups['birdeye']
        if len(birdeye_platforms) == 1:
            display_parts.append(platform_mapping.get(birdeye_platforms[0], 'BE'))
        else:
            # Multiple birdeye endpoints - show count
            has_stars = any('stars' in p for p in birdeye_platforms)
            base_abbrev = 'BE*' if has_stars else 'BE'
            if len(birdeye_platforms) > 1:
                display_parts.append(f"{base_abbrev}({len(birdeye_platforms)})")
            else:
                display_parts.append(base_abbrev)
    
    # DexScreener group
    if platform_groups['dexscreener']:
        dex_platforms = platform_groups['dexscreener']
        if len(dex_platforms) == 1:
            platform_name = dex_platforms[0]
            if platform_name == 'dex':
                platform_name = 'dexscreener'
            display_parts.append(platform_mapping.get(platform_name, 'DX'))
        else:
            display_parts.append(f"DX({len(dex_platforms)})")
    
    # Jupiter group
    if platform_groups['jupiter']:
        jupiter_platforms = platform_groups['jupiter']
        if len(jupiter_platforms) == 1:
            display_parts.append(platform_mapping.get(jupiter_platforms[0], 'JUP'))
        else:
            # Multiple jupiter endpoints - show count instead of "jupiter_..."
            display_parts.append(f"JUP({len(jupiter_platforms)})")
    
    # Meteora group
    if platform_groups['meteora']:
        meteora_platforms = platform_groups['meteora']
        if len(meteora_platforms) == 1:
            display_parts.append(platform_mapping.get(meteora_platforms[0], 'MET'))
        else:
            display_parts.append(f"MET({len(meteora_platforms)})")
    
    # RugCheck group
    if platform_groups['rugcheck']:
        rug_platforms = platform_groups['rugcheck']
        if len(rug_platforms) == 1:
            platform_name = rug_platforms[0]
            if platform_name == 'rug':
                platform_name = 'rugcheck'
            display_parts.append(platform_mapping.get(platform_name, 'RUG'))
        else:
            display_parts.append(f"RUG({len(rug_platforms)})")
    
    # Orca group
    if platform_groups['orca']:
        orca_platforms = platform_groups['orca']
        if len(orca_platforms) == 1:
            display_parts.append(platform_mapping.get(orca_platforms[0], 'ORCA'))
        else:
            display_parts.append(f"ORCA({len(orca_platforms)})")
    
    # Raydium group
    if platform_groups['raydium']:
        raydium_platforms = platform_groups['raydium']
        if len(raydium_platforms) == 1:
            display_parts.append(platform_mapping.get(raydium_platforms[0], 'RAY'))
        else:
            display_parts.append(f"RAY({len(raydium_platforms)})")
    
    # Other platforms
    for platform in platform_groups['other']:
        if len(platform) > 8:
            display_parts.append(platform[:6] + '..')
        else:
            display_parts.append(platform)
    
    # Join with commas, but keep it concise
    result = ', '.join(display_parts)
    
    # If result is too long, use summary format
    if len(result) > 30:
        total_platforms = len(platforms)
        unique_providers = sum(1 for group in platform_groups.values() if group)
        result = f"{unique_providers} providers ({total_platforms} endpoints)"
    
    return result

def _validate_detector_data_accuracy(detector, result, cycle_number):
    """Validate and fix data accuracy issues in detector metrics"""
    try:
        print(f"🔍 Validating data accuracy for cycle #{cycle_number}...")
        
        # Get current session stats
        session_stats = detector.session_stats
        performance_metrics = session_stats.get('performance_metrics', {})
        api_usage = session_stats.get('api_usage_by_service', {})
        
        # Validation 1: API Usage vs Performance Metrics Consistency
        total_api_calls = sum(stats.get('total_calls', 0) for stats in api_usage.values())
        if total_api_calls == 0 and cycle_number > 1:
            print(f"⚠️ WARNING: No API calls recorded but cycle {cycle_number} completed")
            
        # Validation 2: High Conviction Token Count Accuracy
        high_conviction_count = performance_metrics.get('high_conviction_tokens', 0)
        total_tokens_found = performance_metrics.get('total_tokens_found', 0)
        
        if high_conviction_count > total_tokens_found:
            print(f"⚠️ WARNING: High conviction count ({high_conviction_count}) > total tokens ({total_tokens_found})")
            
        # Validation 3: Cost Calculation Accuracy
        total_cost = session_stats.get('cost_analysis', {}).get('total_estimated_cost_usd', 0.0)
        cost_per_high_conviction = session_stats.get('cost_analysis', {}).get('cost_per_high_conviction_token', 0.0)
        
        if high_conviction_count > 0 and cost_per_high_conviction == 0.0 and total_cost > 0:
            # Recalculate cost per high conviction
            corrected_cost = total_cost / high_conviction_count
            session_stats['cost_analysis']['cost_per_high_conviction_token'] = corrected_cost
            print(f"✅ Fixed cost per high conviction: ${corrected_cost:.4f}")
            
        # Validation 4: Success Rate Accuracy
        successful_cycles = performance_metrics.get('successful_cycles', 0)
        total_cycles = performance_metrics.get('total_cycles', 0)
        
        if total_cycles > 0:
            calculated_success_rate = (successful_cycles / total_cycles) * 100
            recorded_success_rate = performance_metrics.get('cycle_success_rate', 0)
            
            if abs(calculated_success_rate - recorded_success_rate) > 1.0:  # More than 1% difference
                performance_metrics['cycle_success_rate'] = calculated_success_rate
                print(f"✅ Fixed success rate: {calculated_success_rate:.1f}%")
                
        # Validation 5: API Efficiency Score Accuracy
        api_efficiency = performance_metrics.get('api_efficiency_score', 0)
        if api_efficiency == 0 and total_api_calls > 0:
            # Recalculate API efficiency
            detector._calculate_api_efficiency_score()
            new_efficiency = performance_metrics.get('api_efficiency_score', 0)
            if new_efficiency > 0:
                print(f"✅ Fixed API efficiency score: {new_efficiency:.1f}/100")
                
        # Validation 6: Pipeline Stage Duration Accuracy
        pipeline_summary = detector.get_pipeline_performance_summary()
        stage_averages = pipeline_summary.get('stage_averages', {})
        
        for stage_key, stage_data in stage_averages.items():
            duration_ms = stage_data.get('avg_duration_ms', 0)
            if duration_ms > 60000:  # More than 60 seconds seems unrealistic
                print(f"⚠️ WARNING: {stage_key} shows {duration_ms:.0f}ms ({duration_ms/1000:.1f}s) - check for timing issues")
                
        # Validation 7: Token Discovery Consistency
        tokens_discovered = session_stats.get('tokens_discovered', {})
        unique_token_count = len(tokens_discovered)
        recorded_unique_count = performance_metrics.get('unique_tokens', 0)
        
        if unique_token_count != recorded_unique_count:
            performance_metrics['unique_tokens'] = unique_token_count
            print(f"✅ Fixed unique token count: {unique_token_count}")
            
        print(f"✅ Data validation completed for cycle #{cycle_number}")
        
    except Exception as e:
        print(f"⚠️ Error during data validation: {e}")

def _display_accuracy_report(detector, cycle_number):
    """Display comprehensive accuracy report"""
    try:
        print(f"\n🎯 DATA ACCURACY REPORT - Cycle #{cycle_number}:")
        
        session_stats = detector.session_stats
        performance_metrics = session_stats.get('performance_metrics', {})
        api_usage = session_stats.get('api_usage_by_service', {})
        
        # Calculate accuracy metrics
        accuracy_issues = []
        accuracy_score = 100.0
        
        # Check 1: API Call Consistency
        total_api_calls = sum(stats.get('total_calls', 0) for stats in api_usage.values())
        if total_api_calls == 0 and cycle_number > 1:
            accuracy_issues.append("No API calls recorded despite cycle completion")
            accuracy_score -= 20
            
        # Check 2: Token Count Consistency
        high_conviction_count = performance_metrics.get('high_conviction_tokens', 0)
        total_tokens_found = performance_metrics.get('total_tokens_found', 0)
        
        if high_conviction_count > total_tokens_found:
            accuracy_issues.append(f"High conviction count ({high_conviction_count}) exceeds total tokens ({total_tokens_found})")
            accuracy_score -= 15
            
        # Check 3: Cost Calculation Consistency
        total_cost = session_stats.get('cost_analysis', {}).get('total_estimated_cost_usd', 0.0)
        cost_per_token = session_stats.get('cost_analysis', {}).get('cost_per_token_discovered', 0.0)
        
        if total_tokens_found > 0 and cost_per_token == 0.0 and total_cost > 0:
            accuracy_issues.append("Cost per token calculation appears incorrect")
            accuracy_score -= 10
            
        # Check 4: Success Rate Logic
        successful_cycles = performance_metrics.get('successful_cycles', 0)
        total_cycles = performance_metrics.get('total_cycles', 0)
        
        if total_cycles > 0:
            calculated_success_rate = (successful_cycles / total_cycles) * 100
            recorded_success_rate = performance_metrics.get('cycle_success_rate', 0)
            
            if abs(calculated_success_rate - recorded_success_rate) > 5.0:
                accuracy_issues.append(f"Success rate mismatch: calculated {calculated_success_rate:.1f}% vs recorded {recorded_success_rate:.1f}%")
                accuracy_score -= 15
                
        # Display accuracy score
        accuracy_color = "🟢" if accuracy_score > 90 else "🟡" if accuracy_score > 70 else "🔴"
        print(f"  {accuracy_color} Data Accuracy Score: {accuracy_score:.1f}/100")
        
        # Display issues if any
        if accuracy_issues:
            print(f"\n  ⚠️ Accuracy Issues Detected ({len(accuracy_issues)}):")
            for i, issue in enumerate(accuracy_issues, 1):
                print(f"    {i}. {issue}")
        else:
            print(f"  ✅ No accuracy issues detected")
            
        # Display data consistency metrics
        print(f"\n  📊 Data Consistency Metrics:")
        print(f"    • API Calls Recorded: {total_api_calls}")
        print(f"    • Total Cycles: {total_cycles}")
        print(f"    • Successful Cycles: {successful_cycles}")
        print(f"    • Tokens Discovered: {total_tokens_found}")
        print(f"    • High Conviction: {high_conviction_count}")
        print(f"    • Total Cost: ${total_cost:.4f}")
        
    except Exception as e:
        print(f"⚠️ Error generating accuracy report: {e}")

def _display_condensed_cycle_summary(detector, result, cycle_number):
    """Display condensed cycle summary with key metrics only"""
    try:
        # Basic cycle metrics
        total_analyzed = result.get('total_analyzed', 0)
        high_conviction_found = result.get('high_conviction_candidates', 0)
        new_candidates = result.get('new_candidates', 0)
        alerts_sent = result.get('alerts_sent', 0)
        duration = result.get('cycle_duration_seconds', 0)
        
        print(f"\n📊 CYCLE #{cycle_number} SUMMARY:")
        print(f"🔍 Analyzed: {total_analyzed} | 🎯 High Conviction: {high_conviction_found} | 🆕 New: {new_candidates} | 📱 Alerts: {alerts_sent} | ⏱️ {duration:.1f}s")
        
        # Key scoring metrics
        session_stats = getattr(detector, 'session_stats', {})
        tokens_discovered = session_stats.get('tokens_discovered', {})
        
        if tokens_discovered:
            scores = [token.get('best_conviction_score', 0) for token in tokens_discovered.values()]
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                high_score_count = sum(1 for s in scores if s >= 70)
                
                print(f"📈 Scoring: Avg {avg_score:.1f} | Max {max_score:.1f} | High (70+): {high_score_count}")
        
        # API efficiency summary
        api_usage = session_stats.get('api_usage_by_service', {})
        if api_usage:
            total_calls = sum(stats.get('total_calls', 0) for stats in api_usage.values())
            total_successes = sum(stats.get('successful_calls', 0) for stats in api_usage.values())
            success_rate = (total_successes / max(total_calls, 1)) * 100
            
            print(f"📡 API: {total_calls} calls | {success_rate:.1f}% success")
            
            # Show platform breakdown in one line
            platform_summary = []
            for platform, stats in api_usage.items():
                calls = stats.get('total_calls', 0)
                if calls > 0:
                    platform_summary.append(f"{platform.title()}({calls})")
            
            if platform_summary:
                print(f"🔗 Platforms: {' | '.join(platform_summary)}")
        
        # Show top 3 tokens if any found
        if high_conviction_found > 0:
            detailed_analyses = result.get('detailed_analyses_data', [])
            high_conviction_candidates = result.get('high_conviction_candidates_data', [])
            
            # Get top tokens by score
            all_tokens = []
            for analysis in detailed_analyses:
                if analysis and 'candidate' in analysis:
                    candidate = analysis['candidate']
                    all_tokens.append({
                        'symbol': candidate.get('symbol', 'Unknown'),
                        'score': analysis.get('final_score', 0),
                        'platforms': len(candidate.get('platforms', []))
                    })
            
            for candidate in high_conviction_candidates:
                if isinstance(candidate, dict):
                    all_tokens.append({
                        'symbol': candidate.get('symbol', 'Unknown'),
                        'score': candidate.get('cross_platform_score', 0),
                        'platforms': len(candidate.get('platforms', []))
                    })
            
            # Sort and show top 3
            all_tokens.sort(key=lambda x: x['score'], reverse=True)
            top_tokens = all_tokens[:3]
            
            if top_tokens:
                print(f"🏆 Top Tokens:")
                for i, token in enumerate(top_tokens, 1):
                    print(f"  {i}. {token['symbol']} - {token['score']:.1f} ({token['platforms']} platforms)")
        
        print("-" * 60)
        
    except Exception as e:
        print(f"⚠️ Error in condensed cycle summary: {e}")

def _get_enhanced_wsol_summary(detector, cycle_tokens):
    """Generate enhanced WSOL integration summary with specific metrics"""
    try:
        # Get WSOL matrix status
        matrix_status = {}
        matrix_cache = getattr(detector, 'wsol_matrix_cache', {})
        matrix_timestamp = getattr(detector, 'wsol_matrix_timestamp', None)
        
        if matrix_cache and matrix_timestamp:
            matrix = matrix_cache.get('matrix', {})
            matrix_age_minutes = (time.time() - matrix_timestamp) / 60
            
            # Calculate matrix coverage
            total_tokens = len(matrix)
            wsol_available = sum(1 for token in matrix.values() if token.get('has_wsol_pairs', False))
            coverage_rate = (wsol_available / total_tokens * 100) if total_tokens > 0 else 0
            
            # DEX breakdown
            meteora_count = sum(1 for token in matrix.values() if token.get('meteora_available', False))
            orca_count = sum(1 for token in matrix.values() if token.get('orca_available', False))
            raydium_count = sum(1 for token in matrix.values() if token.get('raydium_available', False))
            jupiter_count = sum(1 for token in matrix.values() if token.get('jupiter_available', False))
            
            matrix_status = {
                'loaded': True,
                'total_tokens': total_tokens,
                'coverage_rate': coverage_rate,
                'age_minutes': matrix_age_minutes,
                'dex_breakdown': {
                    'meteora': (meteora_count, meteora_count/total_tokens*100 if total_tokens > 0 else 0),
                    'orca': (orca_count, orca_count/total_tokens*100 if total_tokens > 0 else 0),
                    'raydium': (raydium_count, raydium_count/total_tokens*100 if total_tokens > 0 else 0),
                    'jupiter': (jupiter_count, jupiter_count/total_tokens*100 if total_tokens > 0 else 0)
                }
            }
        else:
            matrix_status = {'loaded': False}
        
        # Analyze tokens from this cycle for WSOL routing
        cycle_wsol_analysis = {}
        if cycle_tokens and matrix_status.get('loaded', False):
            routing_tiers = {'TIER_1_MULTI_DEX': 0, 'TIER_1_SINGLE_DEX': 0, 'TIER_2_JUPITER_ONLY': 0, 'UNAVAILABLE': 0}
            wsol_scores = []
            
            for token in cycle_tokens:
                token_address = token.get('address', '')
                if token_address:
                    try:
                        wsol_score, wsol_analysis = detector._calculate_wsol_routing_score(token_address)
                        tier = wsol_analysis.get('routing_tier', 'UNAVAILABLE')
                        routing_tiers[tier] += 1
                        wsol_scores.append(wsol_score)
                    except Exception:
                        routing_tiers['UNAVAILABLE'] += 1
                        wsol_scores.append(0)
            
            cycle_wsol_analysis = {
                'total_analyzed': len(cycle_tokens),
                'avg_wsol_score': sum(wsol_scores) / len(wsol_scores) if wsol_scores else 0,
                'max_wsol_score': max(wsol_scores) if wsol_scores else 0,
                'routing_tiers': routing_tiers,
                'wsol_available_count': sum(routing_tiers[tier] for tier in ['TIER_1_MULTI_DEX', 'TIER_1_SINGLE_DEX', 'TIER_2_JUPITER_ONLY'])
            }
        
        return matrix_status, cycle_wsol_analysis
        
    except Exception as e:
        return {'loaded': False, 'error': str(e)}, {}

async def run_6hour_detector():
    """Run detector for 6 hours with 20-minute intervals"""
    
    # Configuration
    TOTAL_DURATION_HOURS = 6
    INTERVAL_MINUTES = 20
    TOTAL_CYCLES = TOTAL_DURATION_HOURS * 3  # 3 scans per hour
    
    print("🎯 HIGH CONVICTION TOKEN DETECTOR - 6 HOUR SESSION")
    print("=" * 60)
    print(f"⏰ Duration: {TOTAL_DURATION_HOURS} hours")
    print(f"🔄 Interval: {INTERVAL_MINUTES} minutes")
    print(f"📊 Total cycles: {TOTAL_CYCLES}")
    print(f"🚀 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Import detector
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        print("✅ Detector imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Initialize detector
    try:
        detector = HighConvictionTokenDetector(debug_mode=False)
        print("✅ Detector initialized")
        
        # Fix logging duplication: Completely disable console handler for HighConvictionDetector
        # The detector's logger has both console and file handlers, causing duplication
        # Since the detector displays output directly, we don't need the logger's console output
        detector_logger = logging.getLogger('HighConvictionDetector')
        console_handlers_to_remove = []
        for handler in detector_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                # This is the console handler (StreamHandler without a file)
                console_handlers_to_remove.append(handler)
        
        for handler in console_handlers_to_remove:
            detector_logger.removeHandler(handler)
            print("🔧 Console handler removed from HighConvictionDetector to prevent duplication")
            print("📝 All detector logs will still be saved to file, but console output comes directly from detector")
                
    except Exception as e:
        print(f"❌ Detector initialization failed: {e}")
        return False
    
    # Session tracking
    session_start = time.time()
    session_end = session_start + (TOTAL_DURATION_HOURS * 3600)
    successful_cycles = 0
    failed_cycles = 0
    total_tokens_found = 0
    total_alerts_sent = 0
    
    try:
        cycle_number = 1
        
        while time.time() < session_end and cycle_number <= TOTAL_CYCLES:
            cycle_start = time.time()
            
            print(f"\n🔍 SCAN CYCLE #{cycle_number}/{TOTAL_CYCLES}")
            print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 40)
            
            try:
                # Run detection cycle
                result = await detector.run_detection_cycle()
                
                # Track results
                if result and result.get('status') == 'completed':
                    successful_cycles += 1
                    total_tokens_found += result.get('high_conviction_candidates', 0)
                    total_alerts_sent += result.get('alerts_sent', 0)
                    
                    print(f"✅ Cycle {cycle_number} completed successfully")
                    print(f"📊 Tokens analyzed: {result.get('total_analyzed', 0)}")
                    print(f"🎯 High conviction: {result.get('high_conviction_candidates', 0)}")
                    print(f"📱 Alerts sent: {result.get('alerts_sent', 0)}")
                    print(f"⏱️ Duration: {result.get('cycle_duration_seconds', 0):.1f}s")
                    
                    # Display scoring summary if available
                    if result.get('total_analyzed', 0) > 0:
                        avg_score = result.get('average_score', 0)
                        if avg_score > 0:
                            print(f"🎯 Average Score: {avg_score:.1f}")
                    
                    # The high conviction detector already displays its own scan summary
                    # Skipping duplicate _display_detailed_scan_summary to avoid redundant logging
                    
                    # Show token breakdown + full enhanced analysis on EVERY cycle
                    try:
                        # Token breakdown (show individual tokens discovered every cycle)
                        try:
                            from prettytable import PrettyTable
                            has_prettytable = True
                        except ImportError:
                            has_prettytable = False
                        
                        _display_cycle_token_breakdown(detector, result, cycle_number, has_prettytable)
                        
                        # Show full enhanced analysis on EVERY cycle
                        print("\n" + "="*60)
                        print("🔬 ENHANCED ANALYSIS")
                        print("="*60)
                        
                        # Ensure detector metrics are up-to-date before analysis
                        try:
                            detector._calculate_final_metrics()
                            # Validate and fix data inconsistencies
                            _validate_detector_data_accuracy(detector, result, cycle_number)
                        except Exception as e:
                            print(f"⚠️ Could not update detector metrics: {e}")
                        
                        # Pure Scoring Analysis
                        _display_scoring_analysis(detector, result, cycle_number)
                        
                        # Pipeline performance analysis
                        _display_pipeline_performance_analysis(detector, cycle_number)
                        
                        # Cost analysis
                        _display_cost_analysis_summary(detector, cycle_number)
                        
                        # Token quality analysis
                        _display_token_quality_analysis(detector, cycle_number)
                        
                        # System health and error analysis
                        _display_error_health_analysis(detector, cycle_number)
                        
                        # Data accuracy report
                        _display_accuracy_report(detector, cycle_number)
                        
                        # Note: Pre-filter analysis is already displayed by the HighConvictionDetector
                        # Removed redundant call to detector._display_pre_filter_analysis()
                        
                        print("="*60)
                    except Exception as e:
                        print(f"⚠️ Could not display detailed scan summary: {e}")
                else:
                    failed_cycles += 1
                    print(f"⚠️ Cycle {cycle_number} completed with issues")
                
            except Exception as e:
                failed_cycles += 1
                print(f"❌ Cycle {cycle_number} failed: {e}")
            
            # Calculate next cycle time
            cycle_duration = time.time() - cycle_start
            next_cycle_time = cycle_start + (INTERVAL_MINUTES * 60)
            time_until_next = next_cycle_time - time.time()
            
            # Progress summary with API usage stats
            elapsed_hours = (time.time() - session_start) / 3600
            remaining_hours = (session_end - time.time()) / 3600
            
            # Get API usage stats from detector (including Jupiter & Meteora)
            api_stats = {}
            try:
                if hasattr(detector, 'session_stats') and detector.session_stats:
                    api_usage = detector.session_stats.get('api_usage_by_service', {})
                    api_stats = {
                        'birdeye': api_usage.get('birdeye', {}).get('total_calls', 0),
                        'dexscreener': api_usage.get('dexscreener', {}).get('total_calls', 0),
                        'rugcheck': api_usage.get('rugcheck', {}).get('total_calls', 0),
                        'jupiter': api_usage.get('jupiter', {}).get('total_calls', 0),
                        'meteora': api_usage.get('meteora', {}).get('total_calls', 0),
                        'pump_fun': api_usage.get('pump_fun', {}).get('total_calls', 0)
                    }
                    total_api_calls = sum(api_stats.values())
                else:
                    total_api_calls = 0
            except Exception:
                total_api_calls = 0
                api_stats = {'birdeye': 0, 'dexscreener': 0, 'rugcheck': 0, 'jupiter': 0, 'meteora': 0, 'pump_fun': 0}
            
            # Get enhanced WSOL summary
            try:
                # Get tokens from this cycle for WSOL analysis
                cycle_tokens = []
                if result and result.get('status') == 'completed':
                    detailed_analyses = result.get('detailed_analyses_data', [])
                    high_conviction_candidates = result.get('high_conviction_candidates_data', [])
                    
                    # Combine tokens for WSOL analysis
                    for analysis in detailed_analyses:
                        if analysis and 'candidate' in analysis:
                            candidate = analysis['candidate']
                            cycle_tokens.append({
                                'address': candidate.get('address', ''),
                                'symbol': candidate.get('symbol', 'Unknown')
                            })
                    
                    for candidate in high_conviction_candidates:
                        if isinstance(candidate, dict):
                            cycle_tokens.append({
                                'address': candidate.get('address', ''),
                                'symbol': candidate.get('symbol', 'Unknown')
                            })
                
                matrix_status, cycle_wsol_analysis = _get_enhanced_wsol_summary(detector, cycle_tokens)
            except Exception as e:
                matrix_status = {'loaded': False, 'error': str(e)}
                cycle_wsol_analysis = {}

            print(f"\n📈 SESSION PROGRESS:")
            print(f"  ✅ Successful cycles: {successful_cycles}")
            print(f"  ❌ Failed cycles: {failed_cycles}")
            print(f"  🎯 Total tokens found: {total_tokens_found}")
            print(f"  📱 Total alerts sent: {total_alerts_sent}")
            print(f"  ⏰ Elapsed: {elapsed_hours:.1f}h | Remaining: {remaining_hours:.1f}h")
            print(f"  📊 API Calls: {total_api_calls} total")
            print(f"    • Birdeye: {api_stats['birdeye']}")
            print(f"    • DexScreener: {api_stats['dexscreener']}")
            print(f"    • RugCheck: {api_stats['rugcheck']}")
            print(f"    • Jupiter: {api_stats['jupiter']}")
            print(f"    • Meteora: {api_stats['meteora']}")
            print(f"    • Pump.fun: {api_stats['pump_fun']}")
            
            # Enhanced WSOL Integration Summary
            print(f"\n🔗 WSOL ROUTING INTEGRATION:")
            if matrix_status.get('loaded', False):
                age_status = "🟢 Fresh" if matrix_status['age_minutes'] < 60 else "🟡 Aging" if matrix_status['age_minutes'] < 120 else "🔴 Stale"
                print(f"  📊 Matrix: {matrix_status['total_tokens']} tokens | {matrix_status['coverage_rate']:.1f}% WSOL coverage | {age_status} ({matrix_status['age_minutes']:.0f}m)")
                
                # DEX breakdown in compact format
                dex_breakdown = matrix_status['dex_breakdown']
                print(f"  🏪 DEX Availability: Meteora {dex_breakdown['meteora'][1]:.1f}% | Orca {dex_breakdown['orca'][1]:.1f}% | Raydium {dex_breakdown['raydium'][1]:.1f}% | Jupiter {dex_breakdown['jupiter'][1]:.1f}%")
                
                # Cycle-specific WSOL analysis
                if cycle_wsol_analysis:
                    available_count = cycle_wsol_analysis['wsol_available_count']
                    total_analyzed = cycle_wsol_analysis['total_analyzed']
                    availability_rate = (available_count / total_analyzed * 100) if total_analyzed > 0 else 0
                    
                    print(f"  🎯 Cycle Routing: {available_count}/{total_analyzed} tokens ({availability_rate:.1f}%) | Avg Score: {cycle_wsol_analysis['avg_wsol_score']:.1f}/18")
                    
                    # Routing tier breakdown
                    tiers = cycle_wsol_analysis['routing_tiers']
                    tier_summary = []
                    if tiers['TIER_1_MULTI_DEX'] > 0:
                        tier_summary.append(f"T1-Multi: {tiers['TIER_1_MULTI_DEX']}")
                    if tiers['TIER_1_SINGLE_DEX'] > 0:
                        tier_summary.append(f"T1-Single: {tiers['TIER_1_SINGLE_DEX']}")
                    if tiers['TIER_2_JUPITER_ONLY'] > 0:
                        tier_summary.append(f"T2-Jup: {tiers['TIER_2_JUPITER_ONLY']}")
                    if tiers['UNAVAILABLE'] > 0:
                        tier_summary.append(f"None: {tiers['UNAVAILABLE']}")
                    
                    if tier_summary:
                        print(f"  ⚡ Routing Tiers: {' | '.join(tier_summary)}")
                else:
                    print(f"  🎯 Cycle Routing: No tokens analyzed this cycle")
            else:
                error_msg = matrix_status.get('error', 'Matrix not loaded')
                print(f"  ❌ Matrix: Not loaded ({error_msg})")
                print(f"  ⚠️ WSOL routing analysis unavailable")
            
            # Wait for next cycle (if not the last one)
            if cycle_number < TOTAL_CYCLES and time.time() < session_end:
                if time_until_next > 0:
                    next_scan_time = datetime.fromtimestamp(next_cycle_time)
                    print(f"\n⏸️ Next scan at: {next_scan_time.strftime('%H:%M:%S')}")
                    print(f"💤 Waiting {time_until_next/60:.1f} minutes...")
                    
                    # Sleep in chunks to allow for interruption
                    while time_until_next > 0 and time.time() < session_end:
                        sleep_time = min(60, time_until_next)  # Sleep max 1 minute at a time
                        await asyncio.sleep(sleep_time)
                        time_until_next = next_cycle_time - time.time()
            
            cycle_number += 1
    
    except KeyboardInterrupt:
        print(f"\n⚠️ Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Session error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Final cleanup and summary
        try:
            await detector.cleanup()
            print("\n✅ Detector cleanup completed")
        except Exception as e:
            print(f"\n⚠️ Cleanup error: {e}")
        
        # Display comprehensive session summary with tables
        try:
            _display_session_summary_tables(detector)
            
            # Display final comprehensive analysis
            print("\n" + "="*80)
            print("🎯 FINAL COMPREHENSIVE SESSION ANALYSIS")
            print("="*80)
            
            # Final pure scoring analysis
            _display_scoring_analysis(detector, {}, "FINAL")
            
            # Final pipeline performance analysis
            _display_pipeline_performance_analysis(detector, "FINAL")
            
            # Final cost analysis
            _display_cost_analysis_summary(detector, "FINAL")
            
            # Final token quality analysis
            _display_token_quality_analysis(detector, "FINAL")
            
            # Final system health analysis
            _display_error_health_analysis(detector, "FINAL")
            
            print("="*80)
            
        except Exception as e:
            print(f"⚠️ Could not display detailed session summary: {e}")
        
        # Final session summary with comprehensive API usage
        total_time = time.time() - session_start
        
        # Get final API usage stats
        final_api_stats = {}
        total_final_api_calls = 0
        api_cost_estimate = 0.0
        
        try:
            if hasattr(detector, 'session_stats') and detector.session_stats:
                api_usage = detector.session_stats.get('api_usage_by_service', {})
                
                # Extract detailed stats for each platform (including Jupiter, Meteora & Pump.fun)
                for platform in ['birdeye', 'dexscreener', 'rugcheck', 'jupiter', 'meteora', 'pump_fun']:
                    platform_data = api_usage.get(platform, {})
                    final_api_stats[platform] = {
                        'calls': platform_data.get('total_calls', 0),
                        'successes': platform_data.get('successful_calls', 0),
                        'failures': platform_data.get('failed_calls', 0),
                        'cost': platform_data.get('estimated_cost_usd', 0.0)
                    }
                    total_final_api_calls += final_api_stats[platform]['calls']
                    api_cost_estimate += final_api_stats[platform]['cost']
        except Exception:
            for platform in ['birdeye', 'dexscreener', 'rugcheck', 'jupiter', 'meteora', 'pump_fun']:
                final_api_stats[platform] = {'calls': 0, 'successes': 0, 'failures': 0, 'cost': 0.0}
        
        # Get final WSOL session summary
        try:
            all_session_tokens = []
            if hasattr(detector, 'session_stats') and detector.session_stats:
                tokens_discovered = detector.session_stats.get('tokens_discovered', {})
                for address, token_data in tokens_discovered.items():
                    all_session_tokens.append({
                        'address': address,
                        'symbol': token_data.get('symbol', 'Unknown')
                    })
            
            final_matrix_status, final_wsol_analysis = _get_enhanced_wsol_summary(detector, all_session_tokens)
        except Exception as e:
            final_matrix_status = {'loaded': False, 'error': str(e)}
            final_wsol_analysis = {}

        print(f"\n🎉 6-HOUR SESSION COMPLETED")
        print("=" * 80)
        print(f"⏰ Total duration: {total_time/3600:.1f} hours")
        print(f"🔄 Cycles completed: {successful_cycles + failed_cycles}")
        print(f"✅ Successful cycles: {successful_cycles}")
        print(f"❌ Failed cycles: {failed_cycles}")
        print(f"📈 Success rate: {(successful_cycles/(successful_cycles+failed_cycles)*100):.1f}%" if (successful_cycles + failed_cycles) > 0 else "N/A")
        print(f"🎯 Total high conviction tokens: {total_tokens_found}")
        print(f"📱 Total alerts sent: {total_alerts_sent}")
        print("")
        print("📊 API USAGE SUMMARY:")
        print(f"  🔗 Total API calls: {total_final_api_calls}")
        print(f"  💰 Estimated cost: ${api_cost_estimate:.4f}")
        print(f"  📈 Calls per hour: {(total_final_api_calls / max(0.1, total_time/3600)):.1f}")
        print("")
        print("🔍 BY PLATFORM:")
        for platform, stats in final_api_stats.items():
            platform_name = platform.title()
            success_rate = (stats['successes'] / max(1, stats['calls'])) * 100 if stats['calls'] > 0 else 0
            print(f"  • {platform_name}: {stats['calls']} calls ({success_rate:.1f}% success) - ${stats['cost']:.4f}")
        print("")
        
        # Final WSOL Integration Summary
        print("🔗 FINAL WSOL ROUTING PERFORMANCE:")
        if final_matrix_status.get('loaded', False):
            print(f"  📊 Matrix Performance: {final_matrix_status['total_tokens']} tokens | {final_matrix_status['coverage_rate']:.1f}% WSOL coverage")
            
            # Final DEX effectiveness summary
            dex_breakdown = final_matrix_status['dex_breakdown']
            print(f"  🏪 DEX Ecosystem: Meteora {dex_breakdown['meteora'][1]:.1f}% | Orca {dex_breakdown['orca'][1]:.1f}% | Raydium {dex_breakdown['raydium'][1]:.1f}% | Jupiter {dex_breakdown['jupiter'][1]:.1f}%")
            
            # Session-wide WSOL routing analysis
            if final_wsol_analysis and final_wsol_analysis.get('total_analyzed', 0) > 0:
                session_available = final_wsol_analysis['wsol_available_count']
                session_total = final_wsol_analysis['total_analyzed']
                session_rate = (session_available / session_total * 100) if session_total > 0 else 0
                
                print(f"  🎯 Session Routing: {session_available}/{session_total} tokens ({session_rate:.1f}%) had WSOL routes")
                print(f"  ⚡ Average WSOL Score: {final_wsol_analysis['avg_wsol_score']:.1f}/18 | Max Score: {final_wsol_analysis['max_wsol_score']:.1f}/18")
                
                # Final routing tier effectiveness
                tiers = final_wsol_analysis['routing_tiers']
                total_tiers = sum(tiers.values())
                if total_tiers > 0:
                    print(f"  📈 Routing Distribution:")
                    if tiers['TIER_1_MULTI_DEX'] > 0:
                        print(f"    • TIER_1_MULTI_DEX: {tiers['TIER_1_MULTI_DEX']}/{total_tiers} ({tiers['TIER_1_MULTI_DEX']/total_tiers*100:.1f}%) - Optimal routing")
                    if tiers['TIER_1_SINGLE_DEX'] > 0:
                        print(f"    • TIER_1_SINGLE_DEX: {tiers['TIER_1_SINGLE_DEX']}/{total_tiers} ({tiers['TIER_1_SINGLE_DEX']/total_tiers*100:.1f}%) - Direct DEX")
                    if tiers['TIER_2_JUPITER_ONLY'] > 0:
                        print(f"    • TIER_2_JUPITER_ONLY: {tiers['TIER_2_JUPITER_ONLY']}/{total_tiers} ({tiers['TIER_2_JUPITER_ONLY']/total_tiers*100:.1f}%) - Aggregated")
                    if tiers['UNAVAILABLE'] > 0:
                        print(f"    • UNAVAILABLE: {tiers['UNAVAILABLE']}/{total_tiers} ({tiers['UNAVAILABLE']/total_tiers*100:.1f}%) - No WSOL routes")
            else:
                print(f"  🎯 Session Routing: No tokens analyzed for WSOL routing")
        else:
            error_msg = final_matrix_status.get('error', 'Matrix not loaded')
            print(f"  ❌ WSOL Matrix: Not available ({error_msg})")
            print(f"  ⚠️ WSOL routing analysis was unavailable for this session")
        print("")
        
        print(f"🏁 Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    return successful_cycles > 0

if __name__ == '__main__':
    try:
        success = asyncio.run(run_6hour_detector())
        if success:
            print("\n🎉 6-hour session completed successfully!")
        else:
            print("\n💥 6-hour session failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Session interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 