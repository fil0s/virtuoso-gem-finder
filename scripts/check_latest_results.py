#!/usr/bin/env python3

import json
import glob
import os

def check_latest_results():
    # Find latest result file
    result_files = glob.glob('results/cross_platform_analysis_*.json')
    if not result_files:
        print("No analysis results found")
        return
    
    latest_file = max(result_files, key=os.path.getctime)
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print('🎯 Latest Cross-Platform Analysis Results')
    print('=' * 50)
    print(f'📁 File: {os.path.basename(latest_file)}')
    print(f'⏰ Timestamp: {data.get("timestamp", "N/A")}')
    print(f'⚡ Execution Time: {data.get("execution_time_seconds", 0):.2f}s')
    print(f'🪙 Total Tokens: {data.get("correlations", {}).get("total_tokens", 0)}')
    
    high_conviction = data.get('correlations', {}).get('high_conviction_tokens', [])
    print(f'💎 High-Conviction Tokens: {len(high_conviction)}')
    
    for i, token in enumerate(high_conviction[:3]):
        print(f'  {i+1}. {token.get("symbol", "N/A")} - Score: {token.get("conviction_score", 0):.1f}/10')
        print(f'     Address: {token.get("address", "N/A")[:20]}...')
        print(f'     Platforms: {token.get("platforms", [])}')
        print(f'     Price: ${token.get("price", 0):.6f}')
        print(f'     Volume 24h: ${token.get("volume_24h", 0):,.0f}')
    
    # Cache statistics
    cache_stats = data.get('cache_statistics', {})
    if cache_stats:
        print(f'\n🚀 Cache Performance:')
        print(f'   Hit Rate: {cache_stats.get("hit_rate_percent", 0):.1f}%')
        print(f'   Cost Savings: ${cache_stats.get("estimated_cost_savings_usd", 0):.4f}')

if __name__ == "__main__":
    check_latest_results() 