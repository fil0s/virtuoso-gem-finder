#!/usr/bin/env python3

import os
import subprocess
import json
import glob
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

def get_tracked_positions():
    """Get currently tracked positions from the position tracker database"""
    try:
        db_path = "../data/position_tracker.db"
        if not os.path.exists(db_path):
            return {}
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT token_address, token_symbol, entry_price, current_pnl_percent, status, created_at
            FROM positions 
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        
        positions = {}
        for row in cursor.fetchall():
            positions[row[0]] = {
                'symbol': row[1],
                'entry_price': row[2],
                'pnl_percent': row[3],
                'status': row[4],
                'created_at': row[5]
            }
        
        conn.close()
        return positions
    except Exception as e:
        return {}

def get_recent_alerts():
    """Get recent Telegram alerts from logs"""
    alerts = []
    try:
        # Check multiple log sources
        log_patterns = [
            "../logs/telegram_*.log",
            "../logs/cross_platform_*.log", 
            "../6hour_test_fixed_*.log",
            "../logs/high_conviction_*.log"
        ]
        
        all_logs = []
        for pattern in log_patterns:
            all_logs.extend(glob.glob(pattern))
        
        if not all_logs:
            return []
        
        # Check each log file for alert-related messages
        for log_file in all_logs:
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Look for alert-related messages
                for line in lines[-200:]:  # Last 200 lines
                    if any(keyword in line.lower() for keyword in [
                        'alert sent', 'high-conviction token', 'telegram alert', 
                        'position alert', 'exit signal', 'tracking alert'
                    ]):
                        alerts.append({
                            'timestamp': line.split(' - ')[0] if ' - ' in line else 'N/A',
                            'message': line.strip(),
                            'source': os.path.basename(log_file)
                        })
            except:
                continue
        
        # Sort by timestamp (most recent first) and return last 10
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return alerts[-10:]
    except:
        return []

def analyze_latest_results():
    """Analyze the latest analysis results for comprehensive token info"""
    try:
        result_files = glob.glob("../scripts/results/cross_platform_analysis_*.json")
        if not result_files:
            return None
        
        latest_file = max(result_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        return data
    except Exception as e:
        return None

def get_token_details(address: str, all_token_data: Dict):
    """Get detailed token information from the full dataset"""
    # First check the raw_data normalized_tokens (which is a dict with address keys)
    raw_data = all_token_data.get('raw_data', {})
    normalized_tokens = raw_data.get('normalized_tokens', {})
    
    if address in normalized_tokens:
        token_info = normalized_tokens[address]
        # Extract the actual token data from the nested structure
        data = token_info.get('data', {})
        
        # Try to get symbol/name from any platform data
        for platform_name, platform_data in data.items():
            if isinstance(platform_data, dict):
                if 'symbol' in platform_data:
                    return {'symbol': platform_data['symbol'], 'price': platform_data.get('price'), **platform_data}
                elif 'name' in platform_data:
                    return {'symbol': platform_data['name'], 'price': platform_data.get('price'), **platform_data}
                elif 'description' in platform_data:
                    # Use description as name if no symbol/name available
                    desc = platform_data['description'][:12]
                    return {'symbol': desc, 'price': platform_data.get('price'), **platform_data}
    
    # Also check platform_data in raw_data
    platform_data = raw_data.get('platform_data', {})
    for platform_name, tokens in platform_data.items():
        if isinstance(tokens, list):
            for token in tokens:
                if token.get('address') == address:
                    return token
    
    # Fallback: return address as symbol
    return {'symbol': address[:8] + '...', 'address': address}

def format_token_info(tokens: List[Dict], tracked_positions: Dict, all_token_data: Dict, max_tokens: int = 10):
    """Format token information with tracking and alert status"""
    if not tokens:
        return "No tokens found"
    
    output = []
    for i, token in enumerate(tokens[:max_tokens]):
        address = token.get('address', 'N/A')
        score = token.get('score', 0)
        platforms = token.get('platforms', [])
        
        # Get detailed token info
        details = get_token_details(address, all_token_data)
        symbol = details.get('symbol') or details.get('name', 'Unknown')
        if len(symbol) > 12:
            symbol = symbol[:9] + "..."
        
        # Check if tracked
        is_tracked = address in tracked_positions
        tracking_status = "🔄 TRACKED" if is_tracked else "⚪ Not tracked"
        
        # Get P&L if tracked
        pnl_info = ""
        if is_tracked:
            pnl = tracked_positions[address].get('pnl_percent', 0)
            if pnl > 0:
                pnl_info = f" (+{pnl:.1f}%)"
            elif pnl < 0:
                pnl_info = f" ({pnl:.1f}%)"
        
        # Format platforms
        platform_map = {"dexscreener": "DEX", "rugcheck": "RUG", "birdeye": "BE"}
        platform_str = "|".join([platform_map.get(p, p[:3].upper()) for p in platforms])
        if not platform_str:
            platform_str = "N/A"
        
        # Add price info if available
        price_info = ""
        if details.get('price'):
            price = float(details['price'])
            if price < 0.001:
                price_info = f" ${price:.8f}"
            else:
                price_info = f" ${price:.4f}"
        
        # Format address (show first 8 and last 4 characters)
        addr_short = f"{address[:8]}...{address[-4:]}" if len(address) > 12 else address
        
        output.append(f"   {i+1:2d}. {symbol:12s} | {score:4.1f} | {platform_str:7s} | {tracking_status}{pnl_info}{price_info}")
        output.append(f"       📍 {addr_short}")
    
    return "\n".join(output)

def monitor_fixed_test():
    print("🎯 Fixed 6-Hour Test Monitor")
    print("=" * 40)
    
    # Check if process is running
    try:
        result = subprocess.run(['pgrep', '-f', 'run_6hour_cross_platform_test'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pid = result.stdout.strip()
            print(f"✅ Test is RUNNING (PID: {pid})")
        else:
            print("❌ Test is NOT RUNNING")
            return
    except:
        print("❌ Could not check test status")
        return
    
    # Find the latest fixed log file
    import glob
    log_files = glob.glob("../6hour_test_fixed_*.log")
    if not log_files:
        print("❌ No fixed test log files found")
        return
    
    latest_log = max(log_files, key=os.path.getctime)
    print(f"📝 Log file: {latest_log}")
    
    # Count errors and successes
    try:
        with open(latest_log, 'r') as f:
            content = f.read()
        
        # Count different types of events
        error_count = content.count('ERROR')
        invalid_var_count = content.count('Invalid variable type')
        success_count = content.count('✅ Success')
        analysis_completed = content.count('Analysis completed')
        
        print(f"\n📊 Statistics:")
        print(f"   ✅ Successful API calls: {success_count}")
        print(f"   🔄 Analyses completed: {analysis_completed}")
        print(f"   ❌ Total errors: {error_count}")
        print(f"   🚫 Invalid variable errors: {invalid_var_count}")
        
        # Show recent activity
        lines = content.split('\n')
        recent_lines = [line for line in lines[-50:] if any(keyword in line for keyword in ['✅ Success', 'Analysis completed', 'ERROR'])]
        
        if recent_lines:
            print(f"\n📋 Recent Activity (last {len(recent_lines)} events):")
            for line in recent_lines[-5:]:
                if '✅ Success' in line:
                    endpoint = line.split('✅ Success: ')[1].split(' - ')[0] if '✅ Success: ' in line else 'unknown'
                    print(f"   ✅ {endpoint}")
                elif 'Analysis completed' in line:
                    time_match = line.split(' in ')[1].split('s')[0] if ' in ' in line else 'unknown'
                    print(f"   🔄 Analysis completed in {time_match}s")
                elif 'ERROR' in line:
                    error_msg = line.split('ERROR - ')[1][:50] if 'ERROR - ' in line else line[:50]
                    print(f"   ❌ {error_msg}...")
        
        # Check if the boolean parameter error is fixed
        if invalid_var_count == 0:
            print(f"\n🎉 SUCCESS: Boolean parameter error is FIXED!")
        else:
            print(f"\n⚠️  WARNING: Still seeing {invalid_var_count} boolean parameter errors")
            
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
    
    # Get comprehensive token analysis
    print(f"\n" + "="*80)
    print(f"📊 COMPREHENSIVE TOKEN ANALYSIS")
    print(f"="*80)
    
    latest_results = analyze_latest_results()
    tracked_positions = get_tracked_positions()
    recent_alerts = get_recent_alerts()
    
    if latest_results:
        correlations = latest_results.get('correlations', {})
        
        # High-conviction tokens
        high_conviction = correlations.get('high_conviction_tokens', [])
        if high_conviction:
            print(f"\n💎 HIGH-CONVICTION TOKENS ({len(high_conviction)}):")
            print(f"{'':4s}{'Token':12s} | {'Score':5s} | {'Platforms':7s} | {'Status':15s}")
            print(f"   " + "-"*50)
            print(format_token_info(high_conviction, tracked_positions, latest_results, 5))
        
        # Multi-platform tokens (these are the most relevant)
        multi_platform = correlations.get('multi_platform_tokens', [])
        if multi_platform:
            print(f"\n📈 MULTI-PLATFORM TOKENS ({len(multi_platform)}):")
            print(f"{'':4s}{'Token':12s} | {'Score':5s} | {'Platforms':7s} | {'Status':15s}")
            print(f"   " + "-"*50)
            # Sort by score descending
            sorted_tokens = sorted(multi_platform, key=lambda x: x.get('score', 0), reverse=True)
            print(format_token_info(sorted_tokens, tracked_positions, latest_results, 15))
    
    # Currently tracked positions
    if tracked_positions:
        print(f"\n🔄 CURRENTLY TRACKED POSITIONS ({len(tracked_positions)}):")
        print(f"{'':4s}{'Token':12s} | {'Entry $':8s} | {'P&L %':7s} | {'Status':10s} | {'Since':12s}")
        print(f"   " + "-"*60)
        
        for i, (address, pos) in enumerate(tracked_positions.items(), 1):
            symbol = pos['symbol'][:11]
            entry_price = f"${pos['entry_price']:.6f}" if pos['entry_price'] else "N/A"
            pnl = pos['pnl_percent'] or 0
            pnl_str = f"{pnl:+6.1f}%" if pnl != 0 else "  0.0%"
            status = pos['status']
            created = pos['created_at'][:10] if pos['created_at'] else "N/A"
            
            pnl_color = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
            print(f"   {i:2d}. {symbol:12s} | {entry_price:8s} | {pnl_str:7s} {pnl_color} | {status:10s} | {created}")
    else:
        print(f"\n🔄 CURRENTLY TRACKED POSITIONS: None")
    
    # Recent alerts
    if recent_alerts:
        print(f"\n📢 RECENT ALERTS ({len(recent_alerts)}):")
        for i, alert in enumerate(recent_alerts[-5:], 1):
            if isinstance(alert, dict):
                timestamp = alert['timestamp'][-8:] if alert['timestamp'] != 'N/A' else 'N/A'
                message = alert['message'].split(' - ')[-1][:60] if ' - ' in alert['message'] else alert['message'][:60]
                source = alert['source'][:10]
                print(f"   {i}. [{timestamp}] {message} ({source})")
            else:
                # Handle old format
                if ' - ' in alert:
                    timestamp = alert.split(' - ')[0][-8:]  # Last 8 chars (HH:MM:SS)
                    message = alert.split(' - ')[-1][:60]  # First 60 chars of message
                    print(f"   {i}. [{timestamp}] {message}")
                else:
                    print(f"   {i}. {alert[:70]}")
    else:
        print(f"\n📢 RECENT ALERTS: None found")
    
    # Analysis summary
    if latest_results:
        print(f"\n📋 ANALYSIS SUMMARY:")
        exec_time = latest_results.get('execution_time_seconds', 0)
        timestamp = latest_results.get('timestamp', 'N/A')
        summary = latest_results.get('summary', {})
        
        print(f"   ⏰ Last Analysis: {timestamp}")
        print(f"   ⚡ Execution Time: {exec_time:.2f}s")
        print(f"   🪙 Total Tokens: {summary.get('total_tokens_analyzed', 0)}")
        print(f"   🔗 Platforms Active: {summary.get('platforms_active', 0)}")
        print(f"   🎯 Multi-Platform: {summary.get('multi_platform_tokens', 0)}")
        print(f"   💎 High-Conviction: {summary.get('high_conviction_tokens', 0)}")
        
        # Platform breakdown
        platform_stats = latest_results.get('platform_statistics', {})
        if platform_stats:
            print(f"\n   🔗 Platform Performance:")
            for platform, stats in platform_stats.items():
                count = stats.get('tokens_fetched', 0)
                success = stats.get('success_rate', 0)
                print(f"      {platform:12s}: {count:3d} tokens ({success:5.1f}% success)")
        
        # Cost optimization
        cache_stats = latest_results.get('cache_statistics', {})
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate_percent', 0)
            savings = cache_stats.get('estimated_cost_savings_usd', 0)
            print(f"\n   💰 Cost Optimization:")
            print(f"      Cache Hit Rate: {hit_rate:.1f}%")
            print(f"      Cost Savings: ${savings:.4f}")
        
        # Show insights if available
        insights = latest_results.get('insights', {})
        if insights and isinstance(insights, dict):
            print(f"\n   🧠 Key Insights:")
            cross_platform_rate = insights.get('cross_platform_validation_rate', 0)
            print(f"      Cross-platform rate: {cross_platform_rate:.1f}%")
            if insights.get('recommendations'):
                for rec in insights['recommendations'][:2]:  # Show first 2 recommendations
                    print(f"      💡 {rec}")
        elif insights and isinstance(insights, list):
            print(f"\n   🧠 Key Insights:")
            for insight in insights[:3]:  # Show first 3 insights
                print(f"      💡 {insight}")
    
    print(f"\n" + "="*80)

if __name__ == "__main__":
    monitor_fixed_test() 