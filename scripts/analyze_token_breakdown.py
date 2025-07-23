#!/usr/bin/env python3
"""
Token Analysis Breakdown
Extracts and analyzes all tokens that were discovered and analyzed during the session
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict

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

def extract_token_data(scan_results: List[Dict]) -> Dict[str, Dict]:
    """Extract comprehensive token data from all scans."""
    all_tokens = {}
    token_discovery_stats = defaultdict(int)
    token_analysis_stats = defaultdict(int)
    
    for scan_idx, scan in enumerate(scan_results, 1):
        scan_id = scan.get('scan_id', f'scan_{scan_idx}')
        
        # Extract discovered tokens
        discovered_tokens = scan.get('tokens_discovered', 0)
        token_discovery_stats[scan_id] = discovered_tokens
        
        # Extract analyzed tokens
        analyzed_tokens = scan.get('tokens_analyzed', 0)
        token_analysis_stats[scan_id] = analyzed_tokens
        
        # Look for detailed token analysis results
        if 'token_analysis_results' in scan:
            token_results = scan['token_analysis_results']
            if isinstance(token_results, dict):
                for token_address, token_data in token_results.items():
                    if token_address not in all_tokens:
                        all_tokens[token_address] = {
                            'address': token_address,
                            'first_seen_scan': scan_id,
                            'analysis_count': 0,
                            'scans_analyzed': [],
                            'token_data': {}
                        }
                    
                    all_tokens[token_address]['analysis_count'] += 1
                    all_tokens[token_address]['scans_analyzed'].append(scan_id)
                    
                    # Merge token data
                    if isinstance(token_data, dict):
                        all_tokens[token_address]['token_data'].update(token_data)
        
        # Look for batch analysis results
        if 'batch_analysis_results' in scan:
            batch_results = scan['batch_analysis_results']
            if isinstance(batch_results, list):
                for batch in batch_results:
                    if isinstance(batch, dict) and 'tokens' in batch:
                        for token_data in batch['tokens']:
                            if isinstance(token_data, dict) and 'address' in token_data:
                                token_address = token_data['address']
                                
                                if token_address not in all_tokens:
                                    all_tokens[token_address] = {
                                        'address': token_address,
                                        'first_seen_scan': scan_id,
                                        'analysis_count': 0,
                                        'scans_analyzed': [],
                                        'token_data': {}
                                    }
                                
                                all_tokens[token_address]['analysis_count'] += 1
                                if scan_id not in all_tokens[token_address]['scans_analyzed']:
                                    all_tokens[token_address]['scans_analyzed'].append(scan_id)
                                
                                # Merge token data
                                all_tokens[token_address]['token_data'].update(token_data)
        
        # Look for ultra batch results
        if 'ultra_batch_results' in scan:
            ultra_results = scan['ultra_batch_results']
            if isinstance(ultra_results, dict):
                for workflow_id, workflow_data in ultra_results.items():
                    if isinstance(workflow_data, dict) and 'analyzed_tokens' in workflow_data:
                        analyzed_tokens_data = workflow_data['analyzed_tokens']
                        if isinstance(analyzed_tokens_data, list):
                            for token_data in analyzed_tokens_data:
                                if isinstance(token_data, dict) and 'address' in token_data:
                                    token_address = token_data['address']
                                    
                                    if token_address not in all_tokens:
                                        all_tokens[token_address] = {
                                            'address': token_address,
                                            'first_seen_scan': scan_id,
                                            'analysis_count': 0,
                                            'scans_analyzed': [],
                                            'token_data': {}
                                        }
                                    
                                    all_tokens[token_address]['analysis_count'] += 1
                                    if scan_id not in all_tokens[token_address]['scans_analyzed']:
                                        all_tokens[token_address]['scans_analyzed'].append(scan_id)
                                    
                                    # Merge token data
                                    all_tokens[token_address]['token_data'].update(token_data)
    
    return {
        'tokens': all_tokens,
        'discovery_stats': dict(token_discovery_stats),
        'analysis_stats': dict(token_analysis_stats)
    }

def analyze_token_characteristics(token_data: Dict[str, Dict]) -> Dict:
    """Analyze characteristics of discovered tokens."""
    analysis = {
        'total_unique_tokens': len(token_data['tokens']),
        'tokens_by_analysis_count': defaultdict(int),
        'tokens_by_first_scan': defaultdict(int),
        'token_attributes': {
            'has_symbol': 0,
            'has_name': 0,
            'has_price': 0,
            'has_market_cap': 0,
            'has_volume': 0,
            'has_liquidity': 0,
            'has_security_analysis': 0,
            'has_social_data': 0
        },
        'price_ranges': {
            'micro_cap': 0,  # < $1M
            'small_cap': 0,  # $1M - $10M
            'mid_cap': 0,    # $10M - $100M
            'large_cap': 0   # > $100M
        },
        'token_ages': {
            'very_new': 0,   # < 1 day
            'new': 0,        # 1-7 days
            'established': 0, # 7-30 days
            'mature': 0      # > 30 days
        }
    }
    
    for token_address, token_info in token_data['tokens'].items():
        # Analysis count distribution
        analysis_count = token_info['analysis_count']
        analysis['tokens_by_analysis_count'][analysis_count] += 1
        
        # First scan distribution
        first_scan = token_info['first_seen_scan']
        analysis['tokens_by_first_scan'][first_scan] += 1
        
        # Token attributes analysis
        token_details = token_info['token_data']
        
        if 'symbol' in token_details:
            analysis['token_attributes']['has_symbol'] += 1
        if 'name' in token_details:
            analysis['token_attributes']['has_name'] += 1
        if 'price' in token_details or 'priceUsd' in token_details:
            analysis['token_attributes']['has_price'] += 1
        if 'mc' in token_details or 'market_cap' in token_details:
            analysis['token_attributes']['has_market_cap'] += 1
        if 'v24hUSD' in token_details or 'volume' in token_details:
            analysis['token_attributes']['has_volume'] += 1
        if 'liquidity' in token_details:
            analysis['token_attributes']['has_liquidity'] += 1
        if 'security' in token_details or 'security_analysis' in token_details:
            analysis['token_attributes']['has_security_analysis'] += 1
        if 'social' in token_details or 'social_data' in token_details:
            analysis['token_attributes']['has_social_data'] += 1
        
        # Market cap analysis
        market_cap = None
        if 'mc' in token_details:
            market_cap = token_details['mc']
        elif 'market_cap' in token_details:
            market_cap = token_details['market_cap']
        
        if market_cap and isinstance(market_cap, (int, float)):
            if market_cap < 1_000_000:
                analysis['price_ranges']['micro_cap'] += 1
            elif market_cap < 10_000_000:
                analysis['price_ranges']['small_cap'] += 1
            elif market_cap < 100_000_000:
                analysis['price_ranges']['mid_cap'] += 1
            else:
                analysis['price_ranges']['large_cap'] += 1
    
    return analysis

def generate_token_breakdown_report(token_data: Dict, analysis: Dict) -> str:
    """Generate comprehensive token breakdown report."""
    report = []
    report.append("🪙 TOKEN ANALYSIS BREAKDOWN - COMPREHENSIVE REPORT")
    report.append("=" * 65)
    report.append("")
    
    # Overview
    report.append("📊 OVERVIEW")
    report.append("-" * 30)
    report.append(f"• Total Unique Tokens Analyzed: {analysis['total_unique_tokens']:,}")
    report.append(f"• Total Discovery Events: {sum(token_data['discovery_stats'].values()):,}")
    report.append(f"• Total Analysis Events: {sum(token_data['analysis_stats'].values()):,}")
    report.append("")
    
    # Discovery and Analysis Stats by Scan
    report.append("📈 DISCOVERY & ANALYSIS BY SCAN")
    report.append("-" * 30)
    for scan_id in sorted(token_data['discovery_stats'].keys()):
        discovered = token_data['discovery_stats'].get(scan_id, 0)
        analyzed = token_data['analysis_stats'].get(scan_id, 0)
        report.append(f"• {scan_id}: {discovered} discovered, {analyzed} analyzed")
    report.append("")
    
    # Token Analysis Frequency
    report.append("🔄 TOKEN ANALYSIS FREQUENCY")
    report.append("-" * 30)
    for count in sorted(analysis['tokens_by_analysis_count'].keys()):
        num_tokens = analysis['tokens_by_analysis_count'][count]
        percentage = (num_tokens / analysis['total_unique_tokens']) * 100
        report.append(f"• Analyzed {count} times: {num_tokens} tokens ({percentage:.1f}%)")
    report.append("")
    
    # Token Attributes Coverage
    report.append("📋 TOKEN DATA COVERAGE")
    report.append("-" * 30)
    total_tokens = analysis['total_unique_tokens']
    for attr, count in analysis['token_attributes'].items():
        percentage = (count / total_tokens) * 100 if total_tokens > 0 else 0
        attr_name = attr.replace('has_', '').replace('_', ' ').title()
        report.append(f"• {attr_name}: {count} tokens ({percentage:.1f}%)")
    report.append("")
    
    # Market Cap Distribution
    report.append("💰 MARKET CAP DISTRIBUTION")
    report.append("-" * 30)
    total_with_mc = sum(analysis['price_ranges'].values())
    if total_with_mc > 0:
        for cap_range, count in analysis['price_ranges'].items():
            percentage = (count / total_with_mc) * 100
            range_name = cap_range.replace('_', ' ').title()
            if cap_range == 'micro_cap':
                range_desc = "< $1M"
            elif cap_range == 'small_cap':
                range_desc = "$1M - $10M"
            elif cap_range == 'mid_cap':
                range_desc = "$10M - $100M"
            else:
                range_desc = "> $100M"
            report.append(f"• {range_name} ({range_desc}): {count} tokens ({percentage:.1f}%)")
    else:
        report.append("• No market cap data available")
    report.append("")
    
    # Top Analyzed Tokens
    report.append("🏆 TOP 20 MOST ANALYZED TOKENS")
    report.append("-" * 30)
    
    # Sort tokens by analysis count
    sorted_tokens = sorted(
        token_data['tokens'].items(),
        key=lambda x: x[1]['analysis_count'],
        reverse=True
    )
    
    for i, (token_address, token_info) in enumerate(sorted_tokens[:20], 1):
        analysis_count = token_info['analysis_count']
        scans = ', '.join(token_info['scans_analyzed'])
        token_details = token_info['token_data']
        
        # Extract key info
        symbol = token_details.get('symbol', 'Unknown')
        name = token_details.get('name', 'Unknown')
        price = token_details.get('priceUsd', token_details.get('price', 'N/A'))
        market_cap = token_details.get('mc', token_details.get('market_cap', 'N/A'))
        
        report.append(f"  {i:2d}. {symbol} ({name})")
        report.append(f"      • Address: {token_address}")
        report.append(f"      • Analyzed: {analysis_count} times")
        report.append(f"      • Scans: {scans}")
        if price != 'N/A':
            report.append(f"      • Price: ${price}")
        if market_cap != 'N/A':
            if isinstance(market_cap, (int, float)):
                if market_cap >= 1_000_000:
                    report.append(f"      • Market Cap: ${market_cap/1_000_000:.2f}M")
                else:
                    report.append(f"      • Market Cap: ${market_cap:,.0f}")
            else:
                report.append(f"      • Market Cap: {market_cap}")
        report.append("")
    
    # Token Discovery Timeline
    report.append("⏰ TOKEN DISCOVERY TIMELINE")
    report.append("-" * 30)
    for scan_id in sorted(analysis['tokens_by_first_scan'].keys()):
        count = analysis['tokens_by_first_scan'][scan_id]
        report.append(f"• {scan_id}: {count} new tokens first discovered")
    report.append("")
    
    # Summary Statistics
    report.append("📊 SUMMARY STATISTICS")
    report.append("-" * 30)
    
    if analysis['total_unique_tokens'] > 0:
        total_analyses = sum(token_info['analysis_count'] for token_info in token_data['tokens'].values())
        avg_analyses_per_token = total_analyses / analysis['total_unique_tokens']
        report.append(f"• Average analyses per token: {avg_analyses_per_token:.1f}")
        
        # Most common analysis count
        most_common_count = max(analysis['tokens_by_analysis_count'].items(), key=lambda x: x[1])
        report.append(f"• Most common analysis frequency: {most_common_count[0]} times ({most_common_count[1]} tokens)")
        
        # Data completeness
        data_completeness = (analysis['token_attributes']['has_symbol'] / analysis['total_unique_tokens']) * 100
        report.append(f"• Data completeness (symbol): {data_completeness:.1f}%")
    
    report.append("")
    report.append("🎯 TOKEN ANALYSIS COMPLETE!")
    report.append("=" * 65)
    
    return "\n".join(report)

def save_detailed_token_data(token_data: Dict, filename: str):
    """Save detailed token data to JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(token_data, f, indent=2, default=str)
        print(f"📄 Detailed token data saved to: {filename}")
    except Exception as e:
        print(f"❌ Error saving detailed token data: {e}")

def main():
    """Main execution function."""
    print("🔄 Loading scan results for token analysis...")
    scan_results = load_scan_results()
    
    if not scan_results:
        print("❌ No scan results found!")
        return
    
    print(f"✅ Loaded {len(scan_results)} scan results")
    print("🔍 Extracting token data...")
    
    token_data = extract_token_data(scan_results)
    
    print(f"📊 Analyzing {len(token_data['tokens'])} unique tokens...")
    analysis = analyze_token_characteristics(token_data)
    
    print("📋 Generating comprehensive report...")
    report = generate_token_breakdown_report(token_data, analysis)
    print()
    print(report)
    
    # Save report and detailed data
    timestamp = int(datetime.now().timestamp())
    report_file = f"data/token_breakdown_report_{timestamp}.txt"
    data_file = f"data/detailed_token_data_{timestamp}.json"
    
    try:
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
        save_detailed_token_data(token_data, data_file)
        
    except Exception as e:
        print(f"\n❌ Error saving files: {e}")

if __name__ == "__main__":
    main() 