#!/usr/bin/env python3
"""
Analyze All Discovered Tokens from 30-Scan Session
Extracts and displays comprehensive information about all tokens found
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_discovered_tokens():
    """Analyze all discovered tokens from the session"""
    
    print("🪙" * 80)
    print("🪙 ALL DISCOVERED TOKENS - 30 SCAN SESSION ANALYSIS")
    print("🪙" * 80)
    
    # Read token registry files
    data_dir = Path("data")
    token_registries = list(data_dir.glob("token_registry_*.json"))
    
    if not token_registries:
        print("❌ No token registry files found")
        return
    
    # Get the most recent non-empty registry
    all_tokens = {}
    latest_file = None
    
    for registry_file in sorted(token_registries, key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(registry_file, 'r') as f:
                data = json.load(f)
                if data and 'unique_tokens_discovered' in data and data['unique_tokens_discovered']:
                    all_tokens = data
                    latest_file = registry_file
                    break
        except Exception as e:
            print(f"⚠️ Error reading {registry_file}: {e}")
            continue
    
    if not all_tokens:
        print("❌ No token data found in registry files")
        return
    
    print(f"📁 Reading from: {latest_file.name}")
    print(f"📅 File timestamp: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Extract tokens
    unique_tokens = all_tokens.get('unique_tokens_discovered', {})
    cross_platform_tokens = all_tokens.get('cross_platform_validated_tokens', {})
    high_conviction_tokens = all_tokens.get('high_conviction_tokens', {})
    session_summary = all_tokens.get('session_summary', {})
    
    print(f"\n📊 DISCOVERY SUMMARY:")
    print(f"  🪙 Total Unique Tokens: {len(unique_tokens)}")
    print(f"  🔗 Cross-Platform Validated: {len(cross_platform_tokens)}")
    print(f"  🎯 High Conviction Tokens: {len(high_conviction_tokens)}")
    
    if not unique_tokens:
        print("\n❌ No tokens were discovered during the 30-scan session")
        return
    
    # Sort tokens by score (highest first)
    sorted_tokens = sorted(unique_tokens.items(), 
                          key=lambda x: x[1].get('score', 0), 
                          reverse=True)
    
    print(f"\n🪙 ALL DISCOVERED TOKENS ({len(sorted_tokens)}):")
    print("=" * 120)
    
    for i, (address, token_data) in enumerate(sorted_tokens, 1):
        symbol = token_data.get('symbol', 'Unknown')
        name = token_data.get('name', '')
        score = token_data.get('score', 0)
        platforms = token_data.get('platforms', [])
        detailed_analyzed = token_data.get('detailed_analyzed', False)
        scan_number = token_data.get('scan_number', 'Unknown')
        timestamp = token_data.get('timestamp', '')
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = timestamp
        
        # Create status indicators
        analysis_indicator = "✨" if detailed_analyzed else "📊"
        platform_str = " + ".join(platforms) if platforms else "Unknown"
        conviction_indicator = "🎯" if score >= 70 else "🔍" if score >= 50 else "📈"
        
        print(f"\n{i:2d}. {analysis_indicator} {symbol} {'(' + name + ')' if name else ''}")
        print(f"    {conviction_indicator} Score: {score:.1f} | Platforms: {platform_str}")
        print(f"    📍 Address: {address}")
        print(f"    🕐 Discovered: Scan #{scan_number} at {time_str}")
        
        # Additional details if available
        source_breakdown = token_data.get('source_breakdown', {})
        if source_breakdown:
            multi_platform = source_breakdown.get('multi_platform', False)
            if multi_platform:
                print(f"    🔗 Multi-platform validated")
        
        # Price and market data (if available)
        price = token_data.get('price', 0)
        volume_24h = token_data.get('volume_24h', 0)
        market_cap = token_data.get('market_cap', 0)
        
        if price > 0 or volume_24h > 0 or market_cap > 0:
            print(f"    💰 Price: ${price:.6f} | Volume: ${volume_24h:,.0f} | MC: ${market_cap:,.0f}")
    
    # Score distribution analysis
    print(f"\n📈 SCORE DISTRIBUTION:")
    score_ranges = {
        '60-100': [t for t in unique_tokens.values() if t.get('score', 0) >= 60],
        '50-59': [t for t in unique_tokens.values() if 50 <= t.get('score', 0) < 60],
        '40-49': [t for t in unique_tokens.values() if 40 <= t.get('score', 0) < 50],
        '30-39': [t for t in unique_tokens.values() if 30 <= t.get('score', 0) < 40],
        '20-29': [t for t in unique_tokens.values() if 20 <= t.get('score', 0) < 30],
        'Below 20': [t for t in unique_tokens.values() if t.get('score', 0) < 20]
    }
    
    for score_range, tokens in score_ranges.items():
        if tokens:
            print(f"  📊 Score {score_range}: {len(tokens)} tokens")
    
    # Platform analysis
    print(f"\n🔗 PLATFORM ANALYSIS:")
    platform_counts = defaultdict(int)
    for token in unique_tokens.values():
        for platform in token.get('platforms', []):
            platform_counts[platform] += 1
    
    for platform, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  📡 {platform.title()}: {count} tokens")
    
    # High conviction analysis
    if high_conviction_tokens:
        print(f"\n🎯 HIGH CONVICTION TOKENS ({len(high_conviction_tokens)}):")
        for address, token in high_conviction_tokens.items():
            symbol = token.get('symbol', 'Unknown')
            score = token.get('score', 0)
            print(f"  🚀 {symbol} - Score: {score:.1f} ({address[:16]}...)")
    else:
        print(f"\n🎯 HIGH CONVICTION TOKENS:")
        print(f"  ❌ No tokens met the high conviction threshold (70.0)")
        print(f"  💡 Highest scoring token: {max(unique_tokens.values(), key=lambda x: x.get('score', 0)).get('symbol', 'Unknown')} with {max(t.get('score', 0) for t in unique_tokens.values()):.1f}")
    
    # Timing analysis
    print(f"\n⏰ DISCOVERY TIMING:")
    scan_counts = defaultdict(int)
    for token in unique_tokens.values():
        scan_num = token.get('scan_number', 'Unknown')
        scan_counts[scan_num] += 1
    
    for scan_num in sorted(scan_counts.keys()):
        count = scan_counts[scan_num]
        print(f"  🔍 Scan #{scan_num}: {count} tokens discovered")
    
    # Recommendations based on findings
    print(f"\n💡 ANALYSIS & RECOMMENDATIONS:")
    
    max_score = max(t.get('score', 0) for t in unique_tokens.values()) if unique_tokens else 0
    avg_score = sum(t.get('score', 0) for t in unique_tokens.values()) / len(unique_tokens) if unique_tokens else 0
    
    print(f"  📊 Score Statistics:")
    print(f"    • Highest Score: {max_score:.1f}")
    print(f"    • Average Score: {avg_score:.1f}")
    print(f"    • Tokens above 50: {len([t for t in unique_tokens.values() if t.get('score', 0) >= 50])}")
    print(f"    • Tokens above 40: {len([t for t in unique_tokens.values() if t.get('score', 0) >= 40])}")
    
    if max_score < 70:
        print(f"\n  🎯 THRESHOLD RECOMMENDATIONS:")
        print(f"    • Current high conviction threshold (70.0) too high for discovered tokens")
        print(f"    • Consider lowering to {max_score - 5:.0f} to capture best tokens")
        print(f"    • Or lower to {avg_score + 10:.0f} for moderate conviction alerts")
    
    if len(unique_tokens) > 0:
        print(f"\n  🔍 DISCOVERY INSIGHTS:")
        all_multi_platform = all(len(t.get('platforms', [])) > 1 for t in unique_tokens.values())
        if all_multi_platform:
            print(f"    • All tokens are cross-platform validated (good quality)")
        
        birdeye_count = sum(1 for t in unique_tokens.values() if 'birdeye' in t.get('platforms', []))
        dex_count = sum(1 for t in unique_tokens.values() if 'dexscreener' in t.get('platforms', []))
        print(f"    • Birdeye coverage: {birdeye_count}/{len(unique_tokens)} tokens")
        print(f"    • DexScreener coverage: {dex_count}/{len(unique_tokens)} tokens")
    
    print(f"\n🪙" * 80)
    print(f"🪙 END TOKEN DISCOVERY ANALYSIS")
    print(f"🪙" * 80)

if __name__ == "__main__":
    try:
        analyze_discovered_tokens()
    except Exception as e:
        print(f"❌ Error analyzing tokens: {e}")
        import traceback
        traceback.print_exc() 