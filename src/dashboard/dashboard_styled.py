#!/usr/bin/env python3
"""
Styled Dashboard for Early Gem Detector
Modern dark-mode interface with futuristic aesthetic
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
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.enhanced_structured_logger import create_enhanced_logger
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

class StyledDashboard:
    """Modern dark-mode dashboard with futuristic styling"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
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
        
        # Initialize enhanced logging if available
        if ENHANCED_LOGGING_AVAILABLE:
            self.enhanced_logger = create_enhanced_logger(
                "StyledDashboard",
                log_level="DEBUG" if debug_mode else "INFO"
            )
            self.session_id = self.enhanced_logger.new_scan_context(
                strategy="styled-dashboard-monitoring",
                timeframe="dashboard_session",
            )
        else:
            self.enhanced_logger = None
            self.session_id = None
        
        # Color scheme - futuristic neon theme
        self.colors = {
            'primary': '\033[95m',      # Magenta
            'secondary': '\033[96m',    # Cyan
            'cyan': '\033[96m',         # Cyan (alias)
            'accent': '\033[93m',       # Yellow
            'success': '\033[92m',      # Green
            'warning': '\033[91m',      # Red
            'info': '\033[94m',         # Blue
            'purple': '\033[35m',       # Purple
            'pink': '\033[38;5;213m',   # Pink
            'orange': '\033[38;5;208m', # Orange
            'reset': '\033[0m',         # Reset
            'bold': '\033[1m',          # Bold
            'dim': '\033[2m',           # Dim
            'bg_dark': '\033[40m',      # Dark background
            'bg_purple': '\033[48;5;54m', # Purple background
        }
        
        # Glassmorphism effect characters
        self.glass_chars = {
            'top_left': '╭',
            'top_right': '╮',
            'bottom_left': '╰',
            'bottom_right': '╯',
            'horizontal': '─',
            'vertical': '│',
            'card_fill': '░',
            'glow': '▓',
            'shine': '▒'
        }
        
        # Neon progress bar characters
        self.progress_chars = {
            'filled': '█',
            'partial': '▓',
            'empty': '░',
            'glow_left': '▌',
            'glow_right': '▐'
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
                'top_tokens': result.get('high_conviction_tokens', [])[:3],
                'api_efficiency': self._calculate_api_efficiency(detector),
                'platform_breakdown': self._get_platform_breakdown(result.get('all_candidates', []))
            }
            
            self.session_data['cycles'].append(cycle_data)
            self.session_data['total_tokens_analyzed'] += cycle_data['total_analyzed']
            self.session_data['total_high_conviction'] += cycle_data['high_conviction_count']
            self.session_data['total_alerts_sent'] += cycle_data['alerts_sent']
            
            self._update_best_tokens(cycle_data['top_tokens'])
            self._update_platform_performance(cycle_data['platform_breakdown'])
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
            calls_saved = batch_calls * 4
            
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
                token['found_at'] = datetime.now().isoformat()
                token['cycle'] = len(self.session_data['cycles'])
                self.session_data['best_tokens'].append(token)
        
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
    
    def _create_glass_card(self, title: str, content: str, width: int = 60) -> str:
        """Create a glassmorphism-style card"""
        c = self.colors
        g = self.glass_chars
        
        # Create the card frame
        top_border = f"{c['cyan']}{g['top_left']}{g['horizontal'] * (width - 2)}{g['top_right']}{c['reset']}"
        bottom_border = f"{c['cyan']}{g['bottom_left']}{g['horizontal'] * (width - 2)}{g['bottom_right']}{c['reset']}"
        
        # Title with glow effect
        title_line = f"{c['cyan']}{g['vertical']}{c['bold']}{c['accent']} {title:<{width-4}} {c['reset']}{c['cyan']}{g['vertical']}{c['reset']}"
        
        # Content lines
        content_lines = []
        for line in content.split('\n'):
            if line.strip():
                padded_line = f"{line:<{width-4}}"
                content_lines.append(f"{c['cyan']}{g['vertical']}{c['reset']} {padded_line} {c['cyan']}{g['vertical']}{c['reset']}")
        
        # Separator
        separator = f"{c['cyan']}{g['vertical']}{c['dim']}{g['horizontal'] * (width - 2)}{c['reset']}{c['cyan']}{g['vertical']}{c['reset']}"
        
        return '\n'.join([top_border, title_line, separator] + content_lines + [bottom_border])
    
    def _create_neon_progress_bar(self, current: int, total: int, width: int = 40) -> str:
        """Create a neon-glowing progress bar"""
        c = self.colors
        p = self.progress_chars
        
        try:
            progress = current / total
            filled = int(width * progress)
            
            # Create the progress bar with neon glow effect
            bar_parts = []
            
            # Filled portion (pink/magenta glow)
            if filled > 0:
                bar_parts.append(f"{c['pink']}{p['filled'] * filled}{c['reset']}")
            
            # Partial character for smooth transition
            if filled < width:
                remaining = width - filled
                bar_parts.append(f"{c['dim']}{p['empty'] * remaining}{c['reset']}")
            
            bar = ''.join(bar_parts)
            percentage = progress * 100
            
            # Add glow brackets
            return f"{c['cyan']}{p['glow_left']}{bar}{p['glow_right']}{c['reset']} {c['accent']}{percentage:.1f}%{c['reset']}"
            
        except:
            return f"{c['dim']}{p['empty'] * width}{c['reset']} {c['accent']}0.0%{c['reset']}"
    
    def _create_metric_display(self, value: Any, label: str, icon: str = "💎", color: str = "accent") -> str:
        """Create a styled metric display"""
        c = self.colors
        
        # Format large numbers
        if isinstance(value, (int, float)) and value >= 1000:
            if value >= 1000000:
                formatted_value = f"{value/1000000:.1f}M"
            elif value >= 1000:
                formatted_value = f"{value/1000:.1f}K"
            else:
                formatted_value = f"{value:,.0f}"
        else:
            formatted_value = str(value)
        
        return f"{icon} {c[color]}{c['bold']}{formatted_value}{c['reset']} {c['dim']}{label}{c['reset']}"
    
    def display_futuristic_dashboard(self, cycle_number: int, total_cycles: int):
        """Display the main futuristic dashboard"""
        try:
            # Clear screen for dashboard effect
            os.system('clear' if os.name == 'posix' else 'cls')
            
            c = self.colors
            
            # Cosmic header with gradient effect
            print(f"{c['bg_purple']}{c['bold']}{c['accent']}")
            print("╔══════════════════════════════════════════════════════════════════════════════╗")
            print("║  🚀 EARLY GEM DETECTOR - FUTURISTIC DASHBOARD 🌌                           ║")
            print("╚══════════════════════════════════════════════════════════════════════════════╝")
            print(f"{c['reset']}")
            
            # Session overview card
            self._display_cosmic_overview(cycle_number, total_cycles)
            
            # Metrics grid
            self._display_neon_metrics()
            
            # Top tokens with glow effect
            self._display_glowing_tokens()
            
            # Platform performance
            self._display_platform_matrix()
            
            # API efficiency with animated bars
            self._display_efficiency_matrix()
            
            # Footer with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{c['dim']}╭────────────────────────────────────────────────────────────────────────────────╮{c['reset']}")
            print(f"{c['dim']}│{c['reset']} {c['cyan']}🔄 Dashboard updated at: {c['accent']}{timestamp}{c['reset']}{c['dim']} │{c['reset']}")
            print(f"{c['dim']}╰────────────────────────────────────────────────────────────────────────────────╯{c['reset']}")
            
        except Exception as e:
            print(f"⚠️ Error displaying futuristic dashboard: {e}")
    
    def _display_cosmic_overview(self, cycle_number: int, total_cycles: int):
        """Display cosmic-themed session overview"""
        c = self.colors
        
        elapsed_time = time.time() - self.session_data['start_time']
        elapsed_hours = elapsed_time / 3600
        progress = (cycle_number / total_cycles) * 100
        
        # Create overview content
        overview_content = (
            f"🌟 Runtime: {c['accent']}{elapsed_hours:.1f}h{c['reset']} │ "
            f"🎯 Progress: {c['pink']}{progress:.1f}%{c['reset']} │ "
            f"🔄 Cycle: {c['cyan']}{cycle_number}/{total_cycles}{c['reset']}\n"
            f"🔍 Analyzed: {c['success']}{self.session_data['total_tokens_analyzed']:,}{c['reset']} tokens │ "
            f"💎 High Conviction: {c['primary']}{self.session_data['total_high_conviction']}{c['reset']} │ "
            f"📱 Alerts: {c['orange']}{self.session_data['total_alerts_sent']}{c['reset']}\n"
            f"⚡ API Saved: {c['accent']}{self.session_data['api_calls_saved']:,}{c['reset']} calls"
        )
        
        print(self._create_glass_card("🌌 SESSION OVERVIEW", overview_content, 80))
        
        # Neon progress bar
        print(f"\n{c['dim']}Progress:{c['reset']}")
        progress_bar = self._create_neon_progress_bar(cycle_number, total_cycles, 60)
        print(f"  {progress_bar}")
    
    def _display_neon_metrics(self):
        """Display metrics in neon style"""
        c = self.colors
        
        if not self.session_data['cycles']:
            return
        
        print(f"\n{c['purple']}╔════════════════════════════════════════════════════════════════════════════════╗{c['reset']}")
        print(f"{c['purple']}║{c['reset']} {c['bold']}{c['accent']}⚡ PERFORMANCE MATRIX{c['reset']}{c['purple']} ║{c['reset']}")
        print(f"{c['purple']}╚════════════════════════════════════════════════════════════════════════════════╝{c['reset']}")
        
        # Calculate averages
        recent_cycles = self.session_data['cycles'][-5:]
        avg_tokens = sum(c['total_analyzed'] for c in recent_cycles) / len(recent_cycles)
        avg_time = sum(c['cycle_time'] for c in recent_cycles) / len(recent_cycles)
        avg_efficiency = sum(c['api_efficiency']['efficiency'] for c in recent_cycles) / len(recent_cycles)
        
        # Discovery rate
        discovery_rate = 0
        if self.session_data['total_tokens_analyzed'] > 0:
            discovery_rate = (self.session_data['total_high_conviction'] / 
                            self.session_data['total_tokens_analyzed']) * 100
        
        # Create metrics display
        metrics = [
            self._create_metric_display(f"{avg_tokens:.1f}", "avg tokens/cycle", "🔍", "cyan"),
            self._create_metric_display(f"{avg_time:.1f}s", "avg cycle time", "⏱️", "pink"),
            self._create_metric_display(f"{avg_efficiency:.1f}%", "batch efficiency", "🚀", "accent"),
            self._create_metric_display(f"{discovery_rate:.2f}%", "discovery rate", "🎯", "success")
        ]
        
        # Display in grid format
        for i in range(0, len(metrics), 2):
            line = "  ".join(metrics[i:i+2])
            print(f"  {line}")
    
    def _display_glowing_tokens(self):
        """Display top tokens with glow effect"""
        c = self.colors
        
        if not self.session_data['best_tokens']:
            return
        
        print(f"\n{c['pink']}╔════════════════════════════════════════════════════════════════════════════════╗{c['reset']}")
        print(f"{c['pink']}║{c['reset']} {c['bold']}{c['accent']}💎 TOP GEMS DISCOVERED{c['reset']}{c['pink']} ║{c['reset']}")
        print(f"{c['pink']}╚════════════════════════════════════════════════════════════════════════════════╝{c['reset']}")
        
        for i, token in enumerate(self.session_data['best_tokens'][:5], 1):
            symbol = token.get('symbol', 'Unknown')[:12]
            score = token.get('score', 0)
            source = token.get('source', 'unknown')[:10]
            cycle = token.get('cycle', 0)
            
            # Color based on score
            if score >= 90:
                score_color = 'accent'  # Gold
            elif score >= 80:
                score_color = 'pink'    # Pink
            elif score >= 70:
                score_color = 'cyan'    # Cyan
            else:
                score_color = 'success' # Green
            
            rank_icon = ["🥇", "🥈", "🥉", "🏅", "⭐"][i-1] if i <= 5 else "💫"
            
            print(f"  {rank_icon} {c['bold']}{symbol:<12}{c['reset']} │ "
                  f"{c[score_color]}{score:.1f} pts{c['reset']} │ "
                  f"{c['dim']}Cycle {cycle}{c['reset']} │ "
                  f"{c['purple']}{source}{c['reset']}")
    
    def _display_platform_matrix(self):
        """Display platform performance matrix"""
        c = self.colors
        
        if not self.session_data['platform_performance']:
            return
        
        print(f"\n{c['cyan']}╔════════════════════════════════════════════════════════════════════════════════╗{c['reset']}")
        print(f"{c['cyan']}║{c['reset']} {c['bold']}{c['accent']}🌐 PLATFORM MATRIX{c['reset']}{c['cyan']} ║{c['reset']}")
        print(f"{c['cyan']}╚════════════════════════════════════════════════════════════════════════════════╝{c['reset']}")
        
        # Sort platforms by total tokens
        sorted_platforms = sorted(
            self.session_data['platform_performance'].items(),
            key=lambda x: x[1]['total_tokens'],
            reverse=True
        )
        
        for platform, stats in sorted_platforms[:5]:
            total_tokens = stats['total_tokens']
            avg_tokens = stats['avg_tokens_per_cycle']
            cycles_active = stats['cycles_active']
            
            # Create mini progress bar for relative performance
            max_tokens = max(p[1]['total_tokens'] for p in sorted_platforms)
            relative_progress = (total_tokens / max_tokens) * 20 if max_tokens > 0 else 0
            mini_bar = f"{c['pink']}{'█' * int(relative_progress)}{c['dim']}{'░' * (20 - int(relative_progress))}{c['reset']}"
            
            print(f"  {c['bold']}{platform[:12]:<12}{c['reset']} │ "
                  f"{mini_bar} │ "
                  f"{c['success']}{total_tokens:,}{c['reset']} tokens │ "
                  f"{c['dim']}{avg_tokens:.1f}/cycle{c['reset']}")
    
    def _display_efficiency_matrix(self):
        """Display API efficiency matrix"""
        c = self.colors
        
        if not self.session_data['cycles']:
            return
        
        print(f"\n{c['accent']}╔════════════════════════════════════════════════════════════════════════════════╗{c['reset']}")
        print(f"{c['accent']}║{c['reset']} {c['bold']}{c['accent']}🚀 EFFICIENCY MATRIX{c['reset']}{c['accent']} ║{c['reset']}")
        print(f"{c['accent']}╚════════════════════════════════════════════════════════════════════════════════╝{c['reset']}")
        
        # Get latest efficiency data
        latest_cycle = self.session_data['cycles'][-1]
        efficiency = latest_cycle['api_efficiency']
        
        # Create efficiency bars
        batch_bar = self._create_neon_progress_bar(int(efficiency['efficiency']), 100, 30)
        
        print(f"  💫 Batch Efficiency: {batch_bar}")
        print(f"  🔗 Total API Calls: {c['cyan']}{efficiency['total_calls']:,}{c['reset']}")
        print(f"  ⚡ Batch Calls: {c['pink']}{efficiency['batch_calls']:,}{c['reset']}")
        print(f"  💰 Calls Saved: {c['success']}~{efficiency['calls_saved']:,}{c['reset']}")
        
        # Cost savings
        cost_savings = efficiency['calls_saved'] * 0.0001
        print(f"  💵 Cost Savings: {c['accent']}${cost_savings:.4f}{c['reset']}")
    
    def display_compact_futuristic_dashboard(self, cycle_number: int, total_cycles: int):
        """Display compact version of futuristic dashboard"""
        try:
            c = self.colors
            
            elapsed_time = time.time() - self.session_data['start_time']
            elapsed_hours = elapsed_time / 3600
            progress = (cycle_number / total_cycles) * 100
            
            # Compact futuristic header
            print(f"\n{c['bg_purple']}{c['bold']}{c['accent']}")
            print("╔══════════════════════════════════════════════════════════════════════════════╗")
            print(f"║  🚀 FUTURISTIC DASHBOARD - Cycle {cycle_number}/{total_cycles} ({progress:.1f}%) 🌌")
            print("╚══════════════════════════════════════════════════════════════════════════════╝")
            print(f"{c['reset']}")
            
            # Key metrics in neon style
            metrics_line = (
                f"🌟 {c['accent']}{elapsed_hours:.1f}h{c['reset']} │ "
                f"🔍 {c['cyan']}{self.session_data['total_tokens_analyzed']:,}{c['reset']} │ "
                f"💎 {c['pink']}{self.session_data['total_high_conviction']}{c['reset']} │ "
                f"📱 {c['orange']}{self.session_data['total_alerts_sent']}{c['reset']}"
            )
            print(f"  {metrics_line}")
            
            # Neon progress bar
            progress_bar = self._create_neon_progress_bar(cycle_number, total_cycles, 50)
            print(f"  📈 {progress_bar}")
            
            # Best token highlight
            if self.session_data['best_tokens']:
                best_token = self.session_data['best_tokens'][0]
                symbol = best_token.get('symbol', 'Unknown')
                score = best_token.get('score', 0)
                print(f"  🏆 Best Gem: {c['bold']}{c['accent']}{symbol}{c['reset']} ({c['pink']}{score:.1f} pts{c['reset']})")
            
            # API efficiency
            if self.session_data['cycles']:
                latest_cycle = self.session_data['cycles'][-1]
                efficiency = latest_cycle['api_efficiency']['efficiency']
                calls_saved = latest_cycle['api_efficiency']['calls_saved']
                print(f"  🚀 Efficiency: {c['cyan']}{efficiency:.1f}%{c['reset']} │ "
                      f"💰 Saved: {c['success']}~{calls_saved:,}{c['reset']} calls")
            
            # Bottom border
            print(f"{c['dim']}╰────────────────────────────────────────────────────────────────────────────────╯{c['reset']}")
            
        except Exception as e:
            print(f"⚠️ Error displaying compact futuristic dashboard: {e}")
    
    def save_session_data(self, filename: Optional[str] = None):
        """Save session data to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"futuristic_dashboard_session_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.session_data, f, indent=2, default=str)
            
            c = self.colors
            print(f"✅ {c['success']}Session data saved to:{c['reset']} {c['accent']}{filename}{c['reset']}")
            
        except Exception as e:
            print(f"⚠️ Error saving session data: {e}")

def create_futuristic_dashboard(debug_mode: bool = False):
    """Factory function to create futuristic dashboard instance with debug support"""
    dashboard = StyledDashboard(debug_mode=debug_mode)
    
    if ENHANCED_LOGGING_AVAILABLE and dashboard.enhanced_logger:
        dashboard.enhanced_logger.info("Styled Dashboard factory created instance",
                                     dashboard_type="StyledDashboard",
                                     debug_mode=debug_mode,
                                     theme="futuristic_neon")
    
    return dashboard