#!/usr/bin/env python3
"""
Scoring Breakdown Retrieval Utility
===================================

Utility to retrieve and display detailed scoring breakdowns for alerted tokens.

Usage:
    python3 scripts/retrieve_scoring_breakdown.py <token_address>
    python3 scripts/retrieve_scoring_breakdown.py --list-all
    python3 scripts/retrieve_scoring_breakdown.py --recent <count>

Examples:
    python3 scripts/retrieve_scoring_breakdown.py 9RjwNo6hBPkxayWHCqQD1VjaH8igSizEseNZNbddpump
    python3 scripts/retrieve_scoring_breakdown.py --recent 5
    python3 scripts/retrieve_scoring_breakdown.py --list-all
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ScoringBreakdownRetriever:
    """Utility to retrieve scoring breakdowns"""
    
    def __init__(self):
        self.scoring_dir = Path("data/scoring_breakdowns")
        self.index_file = self.scoring_dir / "scoring_index.json"
        
        # Ensure directories exist
        self.scoring_dir.mkdir(exist_ok=True)
    
    def get_scoring_breakdown(self, token_address: str) -> Optional[Dict]:
        """Get the latest scoring breakdown for a token"""
        if not self.index_file.exists():
            return None
        
        try:
            with open(self.index_file, 'r') as f:
                index = json.load(f)
        except Exception as e:
            print(f"❌ Error reading index file: {e}")
            return None
        
        if token_address not in index:
            return None
        
        breakdown_file = index[token_address]['latest_breakdown_file']
        breakdown_path = self.scoring_dir / breakdown_file
        
        if not breakdown_path.exists():
            return None
        
        try:
            with open(breakdown_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error reading breakdown file: {e}")
            return None
    
    def get_all_alerted_tokens(self) -> Dict[str, Dict]:
        """Get all tokens that have been alerted with their latest info"""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error reading index file: {e}")
            return {}
    
    def get_recent_alerts(self, count: int = 5) -> List[Dict]:
        """Get the most recent alerts with their scoring breakdowns"""
        all_tokens = self.get_all_alerted_tokens()
        
        if not all_tokens:
            return []
        
        # Sort by latest alert timestamp
        sorted_tokens = sorted(
            all_tokens.items(),
            key=lambda x: x[1]['latest_alert'],
            reverse=True
        )
        
        recent_alerts = []
        for token_address, token_info in sorted_tokens[:count]:
            breakdown = self.get_scoring_breakdown(token_address)
            if breakdown:
                recent_alerts.append({
                    'token_address': token_address,
                    'token_info': token_info,
                    'breakdown': breakdown
                })
        
        return recent_alerts
    
    def display_scoring_breakdown(self, token_address: str):
        """Display detailed scoring breakdown for a token"""
        breakdown = self.get_scoring_breakdown(token_address)
        
        if not breakdown:
            print(f"❌ No scoring breakdown found for {token_address}")
            return
        
        print(f"\n🎯 DETAILED SCORING BREAKDOWN")
        print("=" * 60)
        print(f"Token: {token_address}")
        print(f"Final Score: {breakdown['final_score']:.1f}/115")
        print(f"Alert Date: {breakdown['alert_date']}")
        print(f"Alert Time: {breakdown['alert_timestamp']}")
        
        print("\n📊 COMPONENT SCORES:")
        print("-" * 40)
        components = breakdown.get('score_components', {})
        
        # Component mapping with max scores
        component_info = {
            'base_score': ('🏗️ Base Score', 'Variable'),
            'overview_score': ('📊 Overview Analysis', 20),
            'whale_score': ('🐋 Whale Analysis', 15),
            'volume_score': ('📈 Volume/Price Analysis', 15),
            'community_score': ('👥 Community Analysis', 10),
            'security_score': ('🔒 Security Analysis', 10),
            'trading_score': ('💹 Trading Activity', 10),
            'dex_score': ('🏪 DEX Analysis', 10),
            'vlr_score': ('💎 VLR Intelligence', 15)
        }
        
        total_score = 0
        for component, score in components.items():
            if component in component_info:
                name, max_score = component_info[component]
                if isinstance(max_score, int):
                    print(f"  {name}: {score:.1f}/{max_score}")
                else:
                    print(f"  {name}: {score:.1f}")
                total_score += score
        
        print(f"\n🎯 TOTAL CALCULATED: {total_score:.1f}/115")
        
        print("\n🔍 DETAILED BREAKDOWN:")
        print("-" * 40)
        scoring_breakdown = breakdown.get('scoring_breakdown', {})
        
        for component, data in scoring_breakdown.items():
            if isinstance(data, dict) and 'score' in data:
                max_score = data.get('max_score', 'N/A')
                print(f"  {component}: {data['score']:.1f}/{max_score}")
                
                # Show specific details for some components
                if component == 'overview_analysis':
                    market_cap = data.get('market_cap', 0)
                    liquidity = data.get('liquidity', 0)
                    if market_cap > 0:
                        print(f"    💰 Market Cap: ${market_cap:,.0f}")
                    if liquidity > 0:
                        print(f"    🌊 Liquidity: ${liquidity:,.0f}")
                
                elif component == 'whale_analysis':
                    whale_concentration = data.get('whale_concentration', 0)
                    smart_money = data.get('smart_money_detected', False)
                    if whale_concentration > 0:
                        print(f"    🐋 Whale Concentration: {whale_concentration:.1f}%")
                    if smart_money:
                        print(f"    🧠 Smart Money Detected: ✅")
                
                elif component == 'vlr_analysis':
                    vlr = data.get('vlr', 0)
                    gem_potential = data.get('gem_potential', 'LOW')
                    if vlr > 0:
                        print(f"    💎 VLR: {vlr:.2f}")
                    print(f"    🎯 Gem Potential: {gem_potential}")
        
        print("\n" + "=" * 60)
    
    def display_all_tokens(self):
        """Display all alerted tokens with basic info"""
        all_tokens = self.get_all_alerted_tokens()
        
        if not all_tokens:
            print("❌ No alerted tokens found")
            return
        
        print(f"\n📋 ALL ALERTED TOKENS ({len(all_tokens)} total)")
        print("=" * 80)
        
        # Sort by latest alert
        sorted_tokens = sorted(
            all_tokens.items(),
            key=lambda x: x[1]['latest_alert'],
            reverse=True
        )
        
        for i, (token_address, token_info) in enumerate(sorted_tokens, 1):
            latest_score = token_info['latest_score']
            alert_count = token_info['alert_count']
            latest_alert = token_info['latest_alert']
            
            # Parse timestamp
            try:
                alert_dt = datetime.fromisoformat(latest_alert.replace('Z', '+00:00'))
                alert_str = alert_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                alert_str = latest_alert
            
            print(f"{i:2d}. {token_address[:12]}...{token_address[-8:]}")
            print(f"    Score: {latest_score:.1f}/115 | Alerts: {alert_count} | Latest: {alert_str}")
        
        print("\n" + "=" * 80)
    
    def display_recent_alerts(self, count: int = 5):
        """Display recent alerts with scoring summaries"""
        recent_alerts = self.get_recent_alerts(count)
        
        if not recent_alerts:
            print("❌ No recent alerts found")
            return
        
        print(f"\n🔥 RECENT ALERTS (Last {len(recent_alerts)})")
        print("=" * 70)
        
        for i, alert in enumerate(recent_alerts, 1):
            token_address = alert['token_address']
            breakdown = alert['breakdown']
            
            final_score = breakdown['final_score']
            alert_date = breakdown['alert_date']
            
            print(f"\n{i}. {token_address[:12]}...{token_address[-8:]}")
            print(f"   Score: {final_score:.1f}/115 | Date: {alert_date}")
            
            # Show component summary
            components = breakdown.get('score_components', {})
            key_components = ['overview_score', 'whale_score', 'volume_score', 'security_score']
            component_summary = []
            
            for comp in key_components:
                if comp in components:
                    score = components[comp]
                    component_summary.append(f"{comp.split('_')[0]}: {score:.1f}")
            
            if component_summary:
                print(f"   Components: {' | '.join(component_summary)}")
        
        print("\n" + "=" * 70)

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Retrieve and display detailed scoring breakdowns for alerted tokens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 9RjwNo6hBPkxayWHCqQD1VjaH8igSizEseNZNbddpump
  %(prog)s --recent 5
  %(prog)s --list-all
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('token_address', nargs='?', help='Token address to analyze')
    group.add_argument('--list-all', action='store_true', help='List all alerted tokens')
    group.add_argument('--recent', type=int, metavar='COUNT', help='Show recent alerts (default: 5)')
    
    args = parser.parse_args()
    
    retriever = ScoringBreakdownRetriever()
    
    if args.token_address:
        retriever.display_scoring_breakdown(args.token_address)
    elif args.list_all:
        retriever.display_all_tokens()
    elif args.recent is not None:
        count = args.recent if args.recent > 0 else 5
        retriever.display_recent_alerts(count)

if __name__ == "__main__":
    main()
