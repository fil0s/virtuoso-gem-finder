#!/usr/bin/env python3
"""
Comprehensive Token Breakdown Report
Analyzes all tokens that were discovered and analyzed during the 8-hour session
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict, Counter
import re

def load_token_addresses() -> List[str]:
    """Load all analyzed token addresses."""
    try:
        with open("data/analyzed_token_addresses.txt", 'r') as f:
            addresses = [line.strip() for line in f if line.strip()]
        return addresses
    except FileNotFoundError:
        print("❌ Token addresses file not found!")
        return []

def analyze_token_patterns(addresses: List[str]) -> Dict:
    """Analyze patterns in token addresses."""
    analysis = {
        'total_tokens': len(addresses),
        'address_patterns': {
            'pump_fun_tokens': 0,
            'ethereum_tokens': 0,
            'solana_tokens': 0,
            'other_tokens': 0
        },
        'address_lengths': defaultdict(int),
        'character_patterns': {
            'all_lowercase': 0,
            'all_uppercase': 0, 
            'mixed_case': 0,
            'contains_numbers': 0,
            'alphanumeric_only': 0
        },
        'common_prefixes': defaultdict(int),
        'common_suffixes': defaultdict(int)
    }
    
    for address in addresses:
        # Address length analysis
        analysis['address_lengths'][len(address)] += 1
        
        # Pattern analysis
        if address.endswith('pump'):
            analysis['address_patterns']['pump_fun_tokens'] += 1
        elif address.startswith('0x') and len(address) == 42:
            analysis['address_patterns']['ethereum_tokens'] += 1
        elif len(address) >= 32 and not address.startswith('0x'):
            analysis['address_patterns']['solana_tokens'] += 1
        else:
            analysis['address_patterns']['other_tokens'] += 1
        
        # Character pattern analysis
        if address.islower():
            analysis['character_patterns']['all_lowercase'] += 1
        elif address.isupper():
            analysis['character_patterns']['all_uppercase'] += 1
        else:
            analysis['character_patterns']['mixed_case'] += 1
        
        if any(c.isdigit() for c in address):
            analysis['character_patterns']['contains_numbers'] += 1
        
        if address.replace('0x', '').isalnum():
            analysis['character_patterns']['alphanumeric_only'] += 1
        
        # Prefix/suffix analysis (first/last 4 characters)
        if len(address) >= 8:
            prefix = address[:4]
            suffix = address[-4:]
            analysis['common_prefixes'][prefix] += 1
            analysis['common_suffixes'][suffix] += 1
    
    return analysis

def extract_token_timeline_from_logs() -> Dict:
    """Extract token discovery timeline from logs."""
    timeline = defaultdict(list)
    scan_tokens = defaultdict(set)
    
    try:
        with open("logs/virtuoso_gem_hunter.log", 'r') as f:
            current_scan = None
            for line in f:
                # Detect scan start
                if "SCAN" in line and "COMPLETE" in line:
                    scan_match = re.search(r'SCAN (\d+)', line)
                    if scan_match:
                        current_scan = f"scan_{scan_match.group(1)}"
                
                # Extract token addresses with timestamps
                if "'address':" in line:
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    address_match = re.search(r"'address': '([^']+)'", line)
                    
                    if timestamp_match and address_match:
                        timestamp = timestamp_match.group(1)
                        address = address_match.group(1)
                        
                        if len(address) >= 20:  # Valid token address
                            timeline[timestamp].append(address)
                            if current_scan:
                                scan_tokens[current_scan].add(address)
    
    except FileNotFoundError:
        print("⚠️ Log file not found, timeline analysis skipped")
    
    return {
        'timeline': dict(timeline),
        'scan_tokens': {scan: list(tokens) for scan, tokens in scan_tokens.items()}
    }

def analyze_scan_performance() -> Dict:
    """Analyze scan performance from logs."""
    scan_stats = {}
    
    try:
        with open("logs/virtuoso_gem_hunter.log", 'r') as f:
            current_scan_data = {}
            
            for line in f:
                # Extract scan completion data
                if "SCAN" in line and "COMPLETE" in line:
                    scan_match = re.search(r'SCAN (\d+)', line)
                    if scan_match:
                        scan_num = scan_match.group(1)
                        current_scan_data = {'scan': scan_num}
                
                # Extract performance metrics
                if "Total API calls:" in line and current_scan_data:
                    api_calls_match = re.search(r'Total API calls: (\d+)', line)
                    if api_calls_match:
                        current_scan_data['api_calls'] = int(api_calls_match.group(1))
                
                if "Total compute units:" in line and current_scan_data:
                    cu_match = re.search(r'Total compute units: (\d+)', line)
                    if cu_match:
                        current_scan_data['compute_units'] = int(cu_match.group(1))
                
                if "Total duration:" in line and current_scan_data:
                    duration_match = re.search(r'Total duration: ([\d.]+)s', line)
                    if duration_match:
                        current_scan_data['duration'] = float(duration_match.group(1))
                        
                        # Save completed scan data
                        scan_id = current_scan_data.get('scan', 'unknown')
                        scan_stats[f"scan_{scan_id}"] = current_scan_data.copy()
                        current_scan_data = {}
    
    except FileNotFoundError:
        print("⚠️ Log file not found, scan performance analysis skipped")
    
    return scan_stats

def generate_comprehensive_token_report(addresses: List[str], analysis: Dict, timeline: Dict, scan_stats: Dict) -> str:
    """Generate comprehensive token breakdown report."""
    report = []
    report.append("🪙 COMPREHENSIVE TOKEN ANALYSIS - 8-HOUR SESSION BREAKDOWN")
    report.append("=" * 70)
    report.append("")
    
    # Executive Summary
    report.append("📊 EXECUTIVE SUMMARY")
    report.append("-" * 40)
    report.append(f"• Total Unique Tokens Analyzed: {analysis['total_tokens']:,}")
    report.append(f"• Session Duration: 8 hours (9 scans)")
    report.append(f"• Average Tokens per Scan: {analysis['total_tokens'] / 9:.1f}")
    report.append(f"• Token Discovery Rate: {analysis['total_tokens'] / 8:.1f} tokens/hour")
    report.append("")
    
    # Token Platform Distribution
    report.append("🌐 TOKEN PLATFORM DISTRIBUTION")
    report.append("-" * 40)
    patterns = analysis['address_patterns']
    total = analysis['total_tokens']
    
    for platform, count in patterns.items():
        percentage = (count / total) * 100 if total > 0 else 0
        platform_name = platform.replace('_', ' ').title()
        report.append(f"• {platform_name}: {count:,} tokens ({percentage:.1f}%)")
    report.append("")
    
    # Address Length Analysis
    report.append("📏 ADDRESS LENGTH DISTRIBUTION")
    report.append("-" * 40)
    sorted_lengths = sorted(analysis['address_lengths'].items())
    for length, count in sorted_lengths:
        percentage = (count / total) * 100 if total > 0 else 0
        report.append(f"• {length} characters: {count:,} tokens ({percentage:.1f}%)")
    report.append("")
    
    # Character Pattern Analysis
    report.append("🔤 CHARACTER PATTERN ANALYSIS")
    report.append("-" * 40)
    char_patterns = analysis['character_patterns']
    for pattern, count in char_patterns.items():
        percentage = (count / total) * 100 if total > 0 else 0
        pattern_name = pattern.replace('_', ' ').title()
        report.append(f"• {pattern_name}: {count:,} tokens ({percentage:.1f}%)")
    report.append("")
    
    # Top Prefixes and Suffixes
    report.append("🏷️ COMMON ADDRESS PATTERNS")
    report.append("-" * 40)
    
    # Top 10 prefixes
    top_prefixes = sorted(analysis['common_prefixes'].items(), key=lambda x: x[1], reverse=True)[:10]
    report.append("Top 10 Address Prefixes:")
    for i, (prefix, count) in enumerate(top_prefixes, 1):
        percentage = (count / total) * 100 if total > 0 else 0
        report.append(f"  {i:2d}. '{prefix}': {count:,} tokens ({percentage:.1f}%)")
    
    report.append("")
    
    # Top 10 suffixes
    top_suffixes = sorted(analysis['common_suffixes'].items(), key=lambda x: x[1], reverse=True)[:10]
    report.append("Top 10 Address Suffixes:")
    for i, (suffix, count) in enumerate(top_suffixes, 1):
        percentage = (count / total) * 100 if total > 0 else 0
        report.append(f"  {i:2d}. '{suffix}': {count:,} tokens ({percentage:.1f}%)")
    
    report.append("")
    
    # Scan Performance Analysis
    if scan_stats:
        report.append("📈 SCAN PERFORMANCE BREAKDOWN")
        report.append("-" * 40)
        
        total_api_calls = sum(scan.get('api_calls', 0) for scan in scan_stats.values())
        total_compute_units = sum(scan.get('compute_units', 0) for scan in scan_stats.values())
        total_duration = sum(scan.get('duration', 0) for scan in scan_stats.values())
        
        report.append(f"• Total API Calls Across All Scans: {total_api_calls:,}")
        report.append(f"• Total Compute Units: {total_compute_units:,}")
        report.append(f"• Total Processing Time: {total_duration:.1f} seconds")
        report.append(f"• Average API Calls per Scan: {total_api_calls / len(scan_stats):.1f}")
        report.append(f"• Average Processing Time per Scan: {total_duration / len(scan_stats):.1f}s")
        report.append("")
        
        # Individual scan breakdown
        report.append("Individual Scan Performance:")
        for scan_id in sorted(scan_stats.keys()):
            scan_data = scan_stats[scan_id]
            api_calls = scan_data.get('api_calls', 0)
            compute_units = scan_data.get('compute_units', 0)
            duration = scan_data.get('duration', 0)
            
            report.append(f"  • {scan_id.upper()}:")
            report.append(f"    - API Calls: {api_calls:,}")
            report.append(f"    - Compute Units: {compute_units:,}")
            report.append(f"    - Duration: {duration:.1f}s")
    
    report.append("")
    
    # Token Discovery Timeline
    if timeline['scan_tokens']:
        report.append("⏰ TOKEN DISCOVERY BY SCAN")
        report.append("-" * 40)
        
        for scan_id in sorted(timeline['scan_tokens'].keys()):
            token_count = len(timeline['scan_tokens'][scan_id])
            report.append(f"• {scan_id.upper()}: {token_count:,} unique tokens discovered")
        
        report.append("")
    
    # Sample Token Addresses
    report.append("🔍 SAMPLE TOKEN ADDRESSES")
    report.append("-" * 40)
    
    # Group by platform
    pump_tokens = [addr for addr in addresses if addr.endswith('pump')]
    eth_tokens = [addr for addr in addresses if addr.startswith('0x') and len(addr) == 42]
    solana_tokens = [addr for addr in addresses if len(addr) >= 32 and not addr.startswith('0x') and not addr.endswith('pump')]
    
    if pump_tokens:
        report.append("Pump.fun Tokens (Sample):")
        for i, token in enumerate(pump_tokens[:5], 1):
            report.append(f"  {i}. {token}")
        if len(pump_tokens) > 5:
            report.append(f"     ... and {len(pump_tokens) - 5:,} more")
        report.append("")
    
    if eth_tokens:
        report.append("Ethereum Tokens (Sample):")
        for i, token in enumerate(eth_tokens[:5], 1):
            report.append(f"  {i}. {token}")
        if len(eth_tokens) > 5:
            report.append(f"     ... and {len(eth_tokens) - 5:,} more")
        report.append("")
    
    if solana_tokens:
        report.append("Solana Tokens (Sample):")
        for i, token in enumerate(solana_tokens[:5], 1):
            report.append(f"  {i}. {token}")
        if len(solana_tokens) > 5:
            report.append(f"     ... and {len(solana_tokens) - 5:,} more")
        report.append("")
    
    # Key Insights
    report.append("💡 KEY INSIGHTS & FINDINGS")
    report.append("-" * 40)
    
    # Platform dominance
    if patterns['pump_fun_tokens'] > patterns['ethereum_tokens'] and patterns['pump_fun_tokens'] > patterns['solana_tokens']:
        report.append("• 🎯 Pump.fun tokens dominate the discovery results")
    elif patterns['ethereum_tokens'] > patterns['solana_tokens']:
        report.append("• 🎯 Ethereum tokens are most prevalent in discoveries")
    else:
        report.append("• 🎯 Solana tokens are most prevalent in discoveries")
    
    # Diversity analysis
    unique_prefixes = len(analysis['common_prefixes'])
    diversity_score = unique_prefixes / total if total > 0 else 0
    if diversity_score > 0.8:
        report.append("• 🌈 High token diversity - wide variety of projects discovered")
    elif diversity_score > 0.5:
        report.append("• 🌈 Moderate token diversity - good mix of different projects")
    else:
        report.append("• 🌈 Lower token diversity - some clustering in project types")
    
    # Discovery efficiency
    if total > 800:
        report.append("• 🚀 Excellent discovery rate - system effectively finding new tokens")
    elif total > 500:
        report.append("• 🚀 Good discovery rate - system performing well")
    else:
        report.append("• 🚀 Moderate discovery rate - room for optimization")
    
    # Pattern insights
    if patterns['pump_fun_tokens'] / total > 0.7:
        report.append("• 📊 Strong focus on meme/community tokens (Pump.fun)")
    
    if char_patterns['contains_numbers'] / total > 0.9:
        report.append("• 🔢 Most tokens use alphanumeric addresses (standard format)")
    
    report.append("")
    report.append("🎯 TOKEN ANALYSIS COMPLETE!")
    report.append("=" * 70)
    
    return "\n".join(report)

def main():
    """Main execution function."""
    print("🔄 Loading analyzed token addresses...")
    addresses = load_token_addresses()
    
    if not addresses:
        print("❌ No token addresses found!")
        return
    
    print(f"✅ Loaded {len(addresses):,} unique token addresses")
    print("🔍 Analyzing token patterns...")
    
    analysis = analyze_token_patterns(addresses)
    
    print("📅 Extracting timeline data...")
    timeline = extract_token_timeline_from_logs()
    
    print("📊 Analyzing scan performance...")
    scan_stats = analyze_scan_performance()
    
    print("📋 Generating comprehensive report...")
    report = generate_comprehensive_token_report(addresses, analysis, timeline, scan_stats)
    
    print()
    print(report)
    
    # Save report and token list
    timestamp = int(datetime.now().timestamp())
    report_file = f"data/comprehensive_token_breakdown_{timestamp}.txt"
    token_list_file = f"data/all_analyzed_tokens_{timestamp}.json"
    
    try:
        # Save report
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        # Save detailed token data
        token_data = {
            'total_tokens': len(addresses),
            'addresses': addresses,
            'analysis': analysis,
            'timeline': timeline,
            'scan_stats': scan_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(token_list_file, 'w') as f:
            json.dump(token_data, f, indent=2, default=str)
        print(f"📄 Detailed data saved to: {token_list_file}")
        
    except Exception as e:
        print(f"\n❌ Error saving files: {e}")

if __name__ == "__main__":
    main() 