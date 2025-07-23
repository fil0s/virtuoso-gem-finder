#!/usr/bin/env python3
"""
Comprehensive Session Summary Analysis
Analyzes the completed 8-hour optimized scan test session results
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

def load_scan_results() -> List[Dict]:
    """Load all scan result files."""
    data_dir = "data"
    scan_files = [f for f in os.listdir(data_dir) if f.startswith("scan_") and f.endswith(".json")]
    scan_files.sort(key=lambda x: int(x.split("_")[1]))
    
    results = []
    for file in scan_files:
        if len(file.split("_")) >= 3:  # Ensure proper format
            try:
                with open(os.path.join(data_dir, file), 'r') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Error loading {file}: {e}")
    
    return results

def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"

def calculate_session_metrics(scan_results: List[Dict]) -> Dict:
    """Calculate comprehensive session metrics."""
    if not scan_results:
        return {}
    
    # Basic aggregation
    total_api_calls = sum(scan.get('api_calls', 0) for scan in scan_results)
    total_compute_units = sum(scan.get('compute_units', 0) for scan in scan_results)
    total_tokens_discovered = sum(scan.get('tokens_discovered', 0) for scan in scan_results)
    total_tokens_analyzed = sum(scan.get('tokens_analyzed', 0) for scan in scan_results)
    
    # Session duration
    start_time = min(scan.get('start_time', 0) for scan in scan_results)
    end_times = []
    for scan in scan_results:
        scan_start = scan.get('start_time', 0)
        scan_duration = scan.get('total_duration', 0)
        end_times.append(scan_start + scan_duration)
    
    session_duration = max(end_times) - start_time if end_times else 0
    
    # Cost calculation
    estimated_usd_cost = (total_compute_units / 3_000_000) * 99  # $99 per 3M CUs
    
    # Performance metrics
    avg_scan_duration = sum(scan.get('total_duration', 0) for scan in scan_results) / len(scan_results)
    avg_api_calls_per_scan = total_api_calls / len(scan_results)
    avg_tokens_per_scan = total_tokens_discovered / len(scan_results)
    
    # Success rate
    successful_scans = sum(1 for scan in scan_results if not scan.get('error'))
    success_rate = (successful_scans / len(scan_results)) * 100
    
    return {
        'total_scans': len(scan_results),
        'successful_scans': successful_scans,
        'success_rate_percent': success_rate,
        'session_duration_hours': session_duration / 3600,
        'session_duration_formatted': format_duration(session_duration),
        'total_api_calls': total_api_calls,
        'total_compute_units': total_compute_units,
        'estimated_usd_cost': estimated_usd_cost,
        'total_tokens_discovered': total_tokens_discovered,
        'total_tokens_analyzed': total_tokens_analyzed,
        'avg_scan_duration': avg_scan_duration,
        'avg_api_calls_per_scan': avg_api_calls_per_scan,
        'avg_tokens_per_scan': avg_tokens_per_scan,
        'api_calls_per_minute': total_api_calls / (session_duration / 60) if session_duration > 0 else 0,
        'tokens_per_hour': total_tokens_discovered / (session_duration / 3600) if session_duration > 0 else 0
    }

def analyze_optimization_performance(scan_results: List[Dict]) -> Dict:
    """Analyze optimization performance across scans."""
    optimization_data = {
        'ultra_batch_usage': 0,
        'parallel_discovery_usage': 0,
        'enhanced_caching_usage': 0,
        'cross_strategy_sharing_usage': 0,
        'avg_calls_per_token': 0,
        'avg_cus_per_token': 0,
        'stage_performance': {
            'discovery': {'total_duration': 0, 'total_tokens': 0, 'total_calls': 0},
            'strategy': {'total_duration': 0, 'total_tokens': 0, 'total_calls': 0},
            'analysis': {'total_duration': 0, 'total_tokens': 0, 'total_calls': 0}
        }
    }
    
    total_analyzed_tokens = 0
    total_analysis_calls = 0
    
    for scan in scan_results:
        # Count optimization usage
        gains = scan.get('optimization_gains', {})
        if gains.get('ultra_batch_enabled'):
            optimization_data['ultra_batch_usage'] += 1
        if gains.get('parallel_discovery_enabled'):
            optimization_data['parallel_discovery_usage'] += 1
        if gains.get('enhanced_caching_enabled'):
            optimization_data['enhanced_caching_usage'] += 1
        if gains.get('cross_strategy_sharing_enabled'):
            optimization_data['cross_strategy_sharing_usage'] += 1
        
        # Aggregate stage performance
        stage_perf = scan.get('stage_performance', {})
        for stage in ['discovery', 'strategy', 'analysis']:
            if stage in stage_perf:
                stage_data = stage_perf[stage]
                optimization_data['stage_performance'][stage]['total_duration'] += stage_data.get('duration', 0)
                optimization_data['stage_performance'][stage]['total_tokens'] += stage_data.get('tokens', 0)
                optimization_data['stage_performance'][stage]['total_calls'] += stage_data.get('api_calls', 0)
        
        # Track analysis efficiency
        analyzed = scan.get('tokens_analyzed', 0)
        if analyzed > 0:
            analysis_stage = stage_perf.get('analysis', {})
            analysis_calls = analysis_stage.get('api_calls', 0)
            total_analyzed_tokens += analyzed
            total_analysis_calls += analysis_calls
    
    # Calculate averages
    if total_analyzed_tokens > 0:
        optimization_data['avg_calls_per_token'] = total_analysis_calls / total_analyzed_tokens
        
    # Calculate stage averages
    num_scans = len(scan_results)
    for stage in optimization_data['stage_performance']:
        stage_data = optimization_data['stage_performance'][stage]
        stage_data['avg_duration'] = stage_data['total_duration'] / num_scans
        stage_data['avg_tokens'] = stage_data['total_tokens'] / num_scans
        stage_data['avg_calls'] = stage_data['total_calls'] / num_scans
    
    return optimization_data

def analyze_endpoint_usage(scan_results: List[Dict]) -> Dict:
    """Analyze endpoint usage patterns."""
    endpoint_stats = {}
    
    for scan in scan_results:
        cost_breakdown = scan.get('cost_breakdown', {})
        cost_summary = cost_breakdown.get('cost_summary', {})
        
        calls_by_endpoint = cost_summary.get('calls_by_endpoint', {})
        cost_by_endpoint = cost_summary.get('cost_by_endpoint', {})
        
        for endpoint, calls in calls_by_endpoint.items():
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'total_calls': 0, 'total_cost': 0}
            
            endpoint_stats[endpoint]['total_calls'] += calls
            endpoint_stats[endpoint]['total_cost'] += cost_by_endpoint.get(endpoint, 0)
    
    # Calculate averages and sort by usage
    for endpoint in endpoint_stats:
        stats = endpoint_stats[endpoint]
        stats['avg_cost_per_call'] = stats['total_cost'] / stats['total_calls'] if stats['total_calls'] > 0 else 0
    
    # Sort by total calls
    sorted_endpoints = sorted(endpoint_stats.items(), key=lambda x: x[1]['total_calls'], reverse=True)
    
    return {
        'endpoint_stats': dict(sorted_endpoints),
        'total_unique_endpoints': len(endpoint_stats),
        'most_used_endpoint': sorted_endpoints[0] if sorted_endpoints else None,
        'highest_cost_endpoint': max(endpoint_stats.items(), key=lambda x: x[1]['total_cost']) if endpoint_stats else None
    }

def generate_comprehensive_report(scan_results: List[Dict]) -> str:
    """Generate a comprehensive session report."""
    if not scan_results:
        return "❌ No scan results found!"
    
    session_metrics = calculate_session_metrics(scan_results)
    optimization_analysis = analyze_optimization_performance(scan_results)
    endpoint_analysis = analyze_endpoint_usage(scan_results)
    
    report = []
    report.append("🎯 OPTIMIZED SCAN SESSION - COMPREHENSIVE SUMMARY")
    report.append("=" * 60)
    report.append("")
    
    # Session Overview
    report.append("📊 SESSION OVERVIEW")
    report.append("-" * 30)
    report.append(f"• Total Scans: {session_metrics['total_scans']}")
    report.append(f"• Successful Scans: {session_metrics['successful_scans']} ({session_metrics['success_rate_percent']:.1f}%)")
    report.append(f"• Session Duration: {session_metrics['session_duration_formatted']}")
    report.append(f"• Tokens Discovered: {session_metrics['total_tokens_discovered']:,}")
    report.append(f"• Tokens Analyzed: {session_metrics['total_tokens_analyzed']:,}")
    report.append("")
    
    # Performance Metrics
    report.append("⚡ PERFORMANCE METRICS")
    report.append("-" * 30)
    report.append(f"• Total API Calls: {session_metrics['total_api_calls']:,}")
    report.append(f"• Total Compute Units: {session_metrics['total_compute_units']:,}")
    report.append(f"• Estimated Cost: ${session_metrics['estimated_usd_cost']:.4f}")
    report.append(f"• API Calls/Minute: {session_metrics['api_calls_per_minute']:.1f}")
    report.append(f"• Tokens/Hour: {session_metrics['tokens_per_hour']:.1f}")
    report.append(f"• Avg Scan Duration: {format_duration(session_metrics['avg_scan_duration'])}")
    report.append("")
    
    # Optimization Analysis
    report.append("🚀 OPTIMIZATION PERFORMANCE")
    report.append("-" * 30)
    report.append(f"• Ultra-Batch Enabled: {optimization_analysis['ultra_batch_usage']}/{session_metrics['total_scans']} scans")
    report.append(f"• Parallel Discovery: {optimization_analysis['parallel_discovery_usage']}/{session_metrics['total_scans']} scans")
    report.append(f"• Enhanced Caching: {optimization_analysis['enhanced_caching_usage']}/{session_metrics['total_scans']} scans")
    report.append(f"• Cross-Strategy Sharing: {optimization_analysis['cross_strategy_sharing_usage']}/{session_metrics['total_scans']} scans")
    report.append(f"• Avg API Calls/Token: {optimization_analysis['avg_calls_per_token']:.1f}")
    report.append("")
    
    # Stage Performance
    report.append("📈 STAGE PERFORMANCE BREAKDOWN")
    report.append("-" * 30)
    for stage, data in optimization_analysis['stage_performance'].items():
        report.append(f"• {stage.title()}:")
        report.append(f"  - Avg Duration: {format_duration(data['avg_duration'])}")
        report.append(f"  - Avg Tokens: {data['avg_tokens']:.1f}")
        report.append(f"  - Avg API Calls: {data['avg_calls']:.1f}")
    report.append("")
    
    # Endpoint Analysis
    report.append("📡 ENDPOINT USAGE ANALYSIS")
    report.append("-" * 30)
    report.append(f"• Total Unique Endpoints: {endpoint_analysis['total_unique_endpoints']}")
    
    if endpoint_analysis['most_used_endpoint']:
        endpoint, stats = endpoint_analysis['most_used_endpoint']
        report.append(f"• Most Used: {endpoint} ({stats['total_calls']:,} calls)")
    
    if endpoint_analysis['highest_cost_endpoint']:
        endpoint, stats = endpoint_analysis['highest_cost_endpoint']
        report.append(f"• Highest Cost: {endpoint} ({stats['total_cost']:,} CUs)")
    
    report.append("")
    report.append("🔝 TOP 5 ENDPOINTS BY USAGE:")
    for i, (endpoint, stats) in enumerate(list(endpoint_analysis['endpoint_stats'].items())[:5]):
        report.append(f"  {i+1}. {endpoint}")
        report.append(f"     • Calls: {stats['total_calls']:,}")
        report.append(f"     • Cost: {stats['total_cost']:,} CUs")
        report.append(f"     • Avg Cost/Call: {stats['avg_cost_per_call']:.1f} CUs")
    
    report.append("")
    
    # Key Insights
    report.append("💡 KEY INSIGHTS")
    report.append("-" * 30)
    
    # Calculate efficiency metrics
    if session_metrics['total_tokens_analyzed'] > 0:
        efficiency = session_metrics['total_api_calls'] / session_metrics['total_tokens_analyzed']
        report.append(f"• API Efficiency: {efficiency:.1f} calls per analyzed token")
    
    cost_per_token = session_metrics['estimated_usd_cost'] / session_metrics['total_tokens_analyzed'] if session_metrics['total_tokens_analyzed'] > 0 else 0
    report.append(f"• Cost Efficiency: ${cost_per_token:.6f} per analyzed token")
    
    # Success rate analysis
    if session_metrics['success_rate_percent'] == 100:
        report.append("• ✅ Perfect Success Rate: All scans completed successfully")
    else:
        report.append(f"• ⚠️ Success Rate: {session_metrics['success_rate_percent']:.1f}% - Some scans encountered issues")
    
    # Performance consistency
    scan_durations = [scan.get('total_duration', 0) for scan in scan_results]
    if scan_durations:
        duration_std = (sum((d - session_metrics['avg_scan_duration'])**2 for d in scan_durations) / len(scan_durations))**0.5
        consistency = "High" if duration_std < 10 else "Medium" if duration_std < 30 else "Low"
        report.append(f"• Performance Consistency: {consistency} (σ={duration_std:.1f}s)")
    
    report.append("")
    report.append("🎉 SESSION COMPLETED SUCCESSFULLY!")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """Main execution function."""
    print("🔄 Loading scan results...")
    scan_results = load_scan_results()
    
    if not scan_results:
        print("❌ No scan results found in data directory!")
        return
    
    print(f"✅ Loaded {len(scan_results)} scan results")
    print()
    
    # Generate and display report
    report = generate_comprehensive_report(scan_results)
    print(report)
    
    # Save report to file
    timestamp = int(datetime.now().timestamp())
    report_file = f"data/session_summary_report_{timestamp}.txt"
    
    try:
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"\n❌ Error saving report: {e}")

if __name__ == "__main__":
    main() 