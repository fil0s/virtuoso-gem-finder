#!/usr/bin/env python3
"""
Dashboard Utilities for Early Gem Detector
Provides real-time insights and visualizations for analysis runs
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math

# Enhanced structured logging
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.enhanced_structured_logger import create_enhanced_logger
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

class BasicDashboard:
    """Basic text-based dashboard for early gem detector insights"""
    
    def __init__(self):
        self.session_data = {
            'start_time': time.time(),
            'cycles': [],
            'total_tokens_analyzed': 0,
            'total_high_conviction': 0,
            'total_alerts_sent': 0,
            'api_calls_saved': 0,
            'best_tokens': [],
            'platform_performance': {},
            'hourly_stats': {}
        }
        
    def add_cycle_data(self, cycle_number: int, result: Dict[str, Any], detector=None):
        """Add data from a completed cycle"""
        try:
            cycle_data = {
                'cycle_number': cycle_number,
                'timestamp': datetime.now().isoformat(),
                'total_analyzed': result.get('total_analyzed', 0),
                'high_conviction_count': len(result.get('high_conviction_tokens', [])),
                'alerts_sent': result.get('alerts_sent', 0),
                'cycle_time': result.get('cycle_time', 0),
                'top_tokens': result.get('high_conviction_tokens', [])[:3],  # Top 3
                'api_efficiency': self._calculate_api_efficiency(detector),
                'platform_breakdown': self._get_platform_breakdown(result.get('all_candidates', []))
            }
            
            self.session_data['cycles'].append(cycle_data)
            self.session_data['total_tokens_analyzed'] += cycle_data['total_analyzed']
            self.session_data['total_high_conviction'] += cycle_data['high_conviction_count']
            self.session_data['total_alerts_sent'] += cycle_data['alerts_sent']
            
            # Update best tokens
            self._update_best_tokens(cycle_data['top_tokens'])
            
            # Update platform performance
            self._update_platform_performance(cycle_data['platform_breakdown'])
            
            # Update hourly stats
            self._update_hourly_stats(cycle_data)
            
        except Exception as e:
            print(f"⚠️ Error adding cycle data to dashboard: {e}")
    
    def _calculate_api_efficiency(self, detector) -> Dict[str, Any]:
        """Calculate API efficiency metrics"""
        try:
            if not detector or not hasattr(detector, 'session_stats'):
                return {'efficiency': 0, 'calls_saved': 0, 'total_calls': 0}
            
            api_usage = detector.session_stats.get('api_usage_by_service', {})
            total_calls = sum(stats.get('total_calls', 0) for stats in api_usage.values())
            batch_calls = sum(stats.get('batch_calls', 0) for stats in api_usage.values())
            
            efficiency = (batch_calls / max(total_calls, 1)) * 100
            calls_saved = batch_calls * 4  # Estimate 4x savings per batch call
            
            return {
                'efficiency': efficiency,
                'calls_saved': calls_saved,
                'total_calls': total_calls,
                'batch_calls': batch_calls
            }
        except Exception:
            return {'efficiency': 0, 'calls_saved': 0, 'total_calls': 0}
    
    def _get_platform_breakdown(self, candidates: List[Dict]) -> Dict[str, int]:
        """Get breakdown of tokens by platform"""
        platform_counts = {}
        for candidate in candidates:
            platform = candidate.get('platform', candidate.get('source', 'unknown'))
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        return platform_counts
    
    def _update_best_tokens(self, new_tokens: List[Dict]):
        """Update the list of best tokens found"""
        for token in new_tokens:
            if token and token.get('score', 0) > 0:
                # Add timestamp and cycle info
                token['found_at'] = datetime.now().isoformat()
                token['cycle'] = len(self.session_data['cycles'])
                self.session_data['best_tokens'].append(token)
        
        # Keep only top 10 tokens by score
        self.session_data['best_tokens'].sort(key=lambda x: x.get('score', 0), reverse=True)
        self.session_data['best_tokens'] = self.session_data['best_tokens'][:10]
    
    def _update_platform_performance(self, platform_breakdown: Dict[str, int]):
        """Update platform performance metrics"""
        for platform, count in platform_breakdown.items():
            if platform not in self.session_data['platform_performance']:
                self.session_data['platform_performance'][platform] = {
                    'total_tokens': 0,
                    'cycles_active': 0,
                    'avg_tokens_per_cycle': 0
                }
            
            self.session_data['platform_performance'][platform]['total_tokens'] += count
            self.session_data['platform_performance'][platform]['cycles_active'] += 1
            self.session_data['platform_performance'][platform]['avg_tokens_per_cycle'] = (
                self.session_data['platform_performance'][platform]['total_tokens'] /
                self.session_data['platform_performance'][platform]['cycles_active']
            )
    
    def _update_hourly_stats(self, cycle_data: Dict):
        """Update hourly statistics"""
        hour = datetime.now().hour
        if hour not in self.session_data['hourly_stats']:
            self.session_data['hourly_stats'][hour] = {
                'cycles': 0,
                'tokens_analyzed': 0,
                'high_conviction': 0,
                'alerts_sent': 0,
                'avg_cycle_time': 0,
                'total_cycle_time': 0
            }
        
        hourly = self.session_data['hourly_stats'][hour]
        hourly['cycles'] += 1
        hourly['tokens_analyzed'] += cycle_data['total_analyzed']
        hourly['high_conviction'] += cycle_data['high_conviction_count']
        hourly['alerts_sent'] += cycle_data['alerts_sent']
        hourly['total_cycle_time'] += cycle_data['cycle_time']
        hourly['avg_cycle_time'] = hourly['total_cycle_time'] / hourly['cycles']
    
    def display_dashboard(self, cycle_number: int, total_cycles: int):
        """Display the main dashboard"""
        try:
            # Clear screen for dashboard effect
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("=" * 80)
            print("🚀 EARLY GEM DETECTOR - REAL-TIME DASHBOARD")
            print("=" * 80)
            
            # Session overview
            self._display_session_overview(cycle_number, total_cycles)
            
            # Performance metrics
            self._display_performance_metrics()
            
            # Top tokens
            self._display_top_tokens()
            
            # Platform performance
            self._display_platform_performance()
            
            # Recent activity
            self._display_recent_activity()
            
            # API efficiency
            self._display_api_efficiency()
            
            print("=" * 80)
            print(f"🔄 Dashboard updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
        except Exception as e:
            print(f"⚠️ Error displaying dashboard: {e}")
    
    def _display_session_overview(self, cycle_number: int, total_cycles: int):
        """Display session overview section"""
        elapsed_time = time.time() - self.session_data['start_time']
        elapsed_hours = elapsed_time / 3600
        progress = (cycle_number / total_cycles) * 100
        
        print(f"\n📊 SESSION OVERVIEW")
        print("-" * 40)
        print(f"⏰ Runtime: {elapsed_hours:.1f}h | Progress: {progress:.1f}% ({cycle_number}/{total_cycles})")
        print(f"🔍 Total Analyzed: {self.session_data['total_tokens_analyzed']:,} tokens")
        print(f"🎯 High Conviction: {self.session_data['total_high_conviction']} tokens")
        print(f"📱 Alerts Sent: {self.session_data['total_alerts_sent']}")
        print(f"⚡ API Calls Saved: ~{self.session_data['api_calls_saved']:,}")
        
        # Progress bar
        progress_bar = self._create_progress_bar(cycle_number, total_cycles)
        print(f"\n📈 Progress: {progress_bar}")
    
    def _display_performance_metrics(self):
        """Display performance metrics"""
        if not self.session_data['cycles']:
            return
            
        print(f"\n⚡ PERFORMANCE METRICS")
        print("-" * 40)
        
        # Calculate averages
        recent_cycles = self.session_data['cycles'][-5:]  # Last 5 cycles
        avg_tokens = sum(c['total_analyzed'] for c in recent_cycles) / len(recent_cycles)
        avg_time = sum(c['cycle_time'] for c in recent_cycles) / len(recent_cycles)
        avg_efficiency = sum(c['api_efficiency']['efficiency'] for c in recent_cycles) / len(recent_cycles)
        
        print(f"📊 Avg Tokens/Cycle: {avg_tokens:.1f}")
        print(f"⏱️ Avg Cycle Time: {avg_time:.1f}s")
        print(f"🚀 Avg Batch Efficiency: {avg_efficiency:.1f}%")
        
        # Token discovery rate
        if self.session_data['total_tokens_analyzed'] > 0:
            discovery_rate = (self.session_data['total_high_conviction'] / 
                            self.session_data['total_tokens_analyzed']) * 100
            print(f"🎯 Discovery Rate: {discovery_rate:.2f}%")
    
    def _display_top_tokens(self):
        """Display top tokens found"""
        if not self.session_data['best_tokens']:
            return
            
        print(f"\n🏆 TOP TOKENS DISCOVERED")
        print("-" * 40)
        
        for i, token in enumerate(self.session_data['best_tokens'][:5], 1):
            symbol = token.get('symbol', 'Unknown')[:10]
            score = token.get('score', 0)
            source = token.get('source', 'unknown')[:8]
            cycle = token.get('cycle', 0)
            
            print(f"{i}. {symbol} - {score:.1f} pts (Cycle {cycle}, {source})")
    
    def _display_platform_performance(self):
        """Display platform performance"""
        if not self.session_data['platform_performance']:
            return
            
        print(f"\n🌐 PLATFORM PERFORMANCE")
        print("-" * 40)
        
        # Sort platforms by total tokens
        sorted_platforms = sorted(
            self.session_data['platform_performance'].items(),
            key=lambda x: x[1]['total_tokens'],
            reverse=True
        )
        
        for platform, stats in sorted_platforms[:5]:
            avg_tokens = stats['avg_tokens_per_cycle']
            total_tokens = stats['total_tokens']
            cycles_active = stats['cycles_active']
            
            print(f"{platform[:12]}: {total_tokens:,} tokens ({avg_tokens:.1f}/cycle, {cycles_active} cycles)")
    
    def _display_recent_activity(self):
        """Display recent activity"""
        if not self.session_data['cycles']:
            return
            
        print(f"\n📊 RECENT ACTIVITY (Last 3 Cycles)")
        print("-" * 40)
        
        recent_cycles = self.session_data['cycles'][-3:]
        for cycle in recent_cycles:
            timestamp = datetime.fromisoformat(cycle['timestamp']).strftime('%H:%M:%S')
            cycle_num = cycle['cycle_number']
            analyzed = cycle['total_analyzed']
            high_conviction = cycle['high_conviction_count']
            cycle_time = cycle['cycle_time']
            
            print(f"Cycle {cycle_num} ({timestamp}): {analyzed} tokens, {high_conviction} high conviction, {cycle_time:.1f}s")
    
    def _display_api_efficiency(self):
        """Display API efficiency metrics"""
        if not self.session_data['cycles']:
            return
            
        print(f"\n🚀 API EFFICIENCY")
        print("-" * 40)
        
        # Get latest efficiency data
        latest_cycle = self.session_data['cycles'][-1]
        efficiency = latest_cycle['api_efficiency']
        
        print(f"📊 Batch Efficiency: {efficiency['efficiency']:.1f}%")
        print(f"🔗 Total API Calls: {efficiency['total_calls']:,}")
        print(f"⚡ Batch Calls: {efficiency['batch_calls']:,}")
        print(f"💰 Estimated Savings: ~{efficiency['calls_saved']:,} calls")
        
        # Cost savings estimate
        cost_savings = efficiency['calls_saved'] * 0.0001  # Rough estimate
        print(f"💵 Cost Savings: ~${cost_savings:.4f}")
    
    def _create_progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Create a text progress bar"""
        try:
            progress = current / total
            filled = int(width * progress)
            bar = "█" * filled + "░" * (width - filled)
            percentage = progress * 100
            return f"|{bar}| {percentage:.1f}%"
        except:
            return f"|{'░' * width}| 0.0%"
    
    def save_session_data(self, filename: Optional[str] = None):
        """Save session data to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dashboard_session_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.session_data, f, indent=2, default=str)
            
            print(f"✅ Session data saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️ Error saving session data: {e}")
    
    def display_compact_dashboard(self, cycle_number: int, total_cycles: int):
        """Display a compact version of the dashboard"""
        try:
            elapsed_time = time.time() - self.session_data['start_time']
            elapsed_hours = elapsed_time / 3600
            progress = (cycle_number / total_cycles) * 100
            
            print(f"\n{'='*60}")
            print(f"🚀 DASHBOARD - Cycle {cycle_number}/{total_cycles} ({progress:.1f}%)")
            print(f"{'='*60}")
            
            # Key metrics in one line
            print(f"⏰ Runtime: {elapsed_hours:.1f}h | 🔍 Analyzed: {self.session_data['total_tokens_analyzed']:,} | 🎯 High Conviction: {self.session_data['total_high_conviction']} | 📱 Alerts: {self.session_data['total_alerts_sent']}")
            
            # Progress bar
            progress_bar = self._create_progress_bar(cycle_number, total_cycles, 30)
            print(f"📈 {progress_bar}")
            
            # Top token if any
            if self.session_data['best_tokens']:
                best_token = self.session_data['best_tokens'][0]
                symbol = best_token.get('symbol', 'Unknown')
                score = best_token.get('score', 0)
                print(f"🏆 Best Token: {symbol} ({score:.1f} pts)")
            
            # API efficiency
            if self.session_data['cycles']:
                latest_cycle = self.session_data['cycles'][-1]
                efficiency = latest_cycle['api_efficiency']['efficiency']
                calls_saved = latest_cycle['api_efficiency']['calls_saved']
                print(f"🚀 API Efficiency: {efficiency:.1f}% | 💰 Saved: ~{calls_saved:,} calls")
            
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"⚠️ Error displaying compact dashboard: {e}")

def create_dashboard(debug_mode: bool = False):
    """Factory function to create dashboard instance with debug support"""
    dashboard = BasicDashboard()
    
    # Set debug mode if BasicDashboard supports it
    if hasattr(dashboard, 'debug_mode'):
        dashboard.debug_mode = debug_mode
    
    if ENHANCED_LOGGING_AVAILABLE and hasattr(dashboard, 'enhanced_logger') and dashboard.enhanced_logger:
        dashboard.enhanced_logger.info("Dashboard factory created instance",
                                     dashboard_type="BasicDashboard",
                                     debug_mode=debug_mode)
    
    return dashboard