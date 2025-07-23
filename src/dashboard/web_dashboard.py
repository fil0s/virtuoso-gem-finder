#!/usr/bin/env python3
"""
Integrated Enhanced Web Dashboard for Virtuoso Gem Hunter
Seamlessly combines existing functionality with advanced features
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import threading
import webbrowser
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import queue
from collections import deque
import statistics

class VirtuosoWebDashboard:
    """Enhanced real-time web dashboard with seamless integration"""
    
    def __init__(self, port: int = 9090, debug_mode: bool = False):
        self.port = port
        self.debug_mode = debug_mode
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'virtuoso_gem_hunter_2025'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize enhanced logging if available
        try:
            from utils.enhanced_structured_logger import create_enhanced_logger
            self.enhanced_logger = create_enhanced_logger(
                "VirtuosoWebDashboard",
                log_level="DEBUG" if debug_mode else "INFO"
            )
            self.session_id = self.enhanced_logger.new_scan_context(
                strategy="web-dashboard-monitoring",
                timeframe="dashboard_session"
            )
        except ImportError:
            self.enhanced_logger = None
            self.session_id = None
        
        # Enhanced Dashboard state (backward compatible)
        self.stats = {
            'cycles_completed': 0,
            'total_tokens_analyzed': 0,
            'high_conviction_found': 0,
            'api_calls_made': 0,
            'current_cycle': 0,
            'start_time': None,
            'estimated_completion': None,
            'last_update': time.time(),
            'status': 'idle',
            'current_token': None,
            'rate_limit_status': 'healthy',
            'cache_hits': 0,
            'cache_misses': 0,
            # New enhanced fields
            'api_costs_saved': 0.0,
            'raydium_v3_gems': 0,
            'total_early_gems': 0,
            'average_cycle_time': 0,
            'stage_performance': {
                'stage1': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage2': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage3': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage4': {'processed': 0, 'filtered': 0, 'time': 0}
            }
        }
        
        # Enhanced token tracking
        self.recent_tokens = deque(maxlen=50)  # Convert to deque for efficiency
        self.high_conviction_tokens = []
        self.raydium_v3_candidates = deque(maxlen=50)
        self.error_log = []
        self.cycle_history = deque(maxlen=20)
        
        # Performance metrics
        self.performance_metrics = {
            'cycle_times': deque(maxlen=50),
            'tokens_per_cycle': deque(maxlen=50),
            'api_response_times': deque(maxlen=100)
        }
        
        # Real-time alerts
        self.alert_queue = deque(maxlen=100)
        
        # Optimization: Track last broadcast state to enable diff updates
        self._last_broadcast_stats = {}
        self._last_broadcast_tokens = {'recent': [], 'high_conviction': []}
        
        # Optimization: Limit data retention
        self.MAX_RECENT_TOKENS = 50
        self.MAX_CYCLE_HISTORY = 20
        self.MAX_CHART_POINTS = 50
        
        # Data update queue
        self.update_queue = queue.Queue()
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_handlers()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template_string(self._get_enhanced_html_template())
        
        @self.app.route('/api/dashboard')
        def dashboard_data():
            # Backward compatible endpoint
            return jsonify({
                'stats': self.stats,
                'recent_tokens': list(self.recent_tokens)[-10:],
                'high_conviction': self.high_conviction_tokens[-10:],
                'cycle_history': list(self.cycle_history)[-20:]
            })
        
        @self.app.route('/api/stats')
        def get_stats():
            return jsonify(self._get_comprehensive_stats())
        
        @self.app.route('/api/tokens')
        def get_tokens():
            return jsonify({
                'high_conviction': self.high_conviction_tokens,
                'recent': list(self.recent_tokens),
                'raydium_v3': list(self.raydium_v3_candidates),
                'total_analyzed': len(self.recent_tokens)
            })
        
        @self.app.route('/api/performance')
        def get_performance():
            return jsonify(self._calculate_performance_metrics())
        
        @self.app.route('/api/alerts')
        def get_alerts():
            return jsonify(list(self.alert_queue))
    
    def _setup_socketio_handlers(self):
        """Setup Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            emit('initial_state', self._get_comprehensive_stats())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            emit('full_update', self._get_comprehensive_stats())
        
        @self.socketio.on('request_refresh')
        def handle_refresh():
            # Backward compatible
            self.emit_update()
            self.emit_tokens_update()
    
    def _get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        # Calculate advanced metrics
        avg_cycle_time = statistics.mean(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0
        avg_tokens_per_cycle = statistics.mean(self.performance_metrics['tokens_per_cycle']) if self.performance_metrics['tokens_per_cycle'] else 0
        
        return {
            'stats': self.stats,
            'performance': {
                'average_cycle_time': avg_cycle_time,
                'average_tokens_per_cycle': avg_tokens_per_cycle,
                'cycles_per_hour': (self.stats['cycles_completed'] / max(1, (time.time() - (self.stats.get('start_time') or time.time())) / 3600))
            },
            'token_counts': {
                'high_conviction': len(self.high_conviction_tokens),
                'recent': len(self.recent_tokens),
                'raydium_v3': len(self.raydium_v3_candidates)
            }
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        metrics = {
            'efficiency': {
                'api_cost_reduction': f"{self.stats.get('api_costs_saved', 0):.2f}%",
                'discovery_rate': self._calculate_discovery_rate()
            },
            'timing': {
                'fastest_cycle': min(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0,
                'slowest_cycle': max(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0,
                'average_cycle': statistics.mean(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0
            },
            'quality': {
                'high_conviction_rate': (self.stats['high_conviction_found'] / max(1, self.stats['total_tokens_analyzed'])) * 100,
                'raydium_v3_discovery_rate': (self.stats.get('raydium_v3_gems', 0) / max(1, self.stats['total_tokens_analyzed'])) * 100
            }
        }
        return metrics
    
    def _calculate_discovery_rate(self) -> float:
        """Calculate token discovery rate per hour"""
        start_time = self.stats.get('start_time')
        if start_time:
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours > 0:
                return self.stats['total_tokens_analyzed'] / elapsed_hours
        return 0
    
    def start_detection(self, total_cycles: int = 9):
        """Start the detection process with dashboard updates"""
        self.stats['start_time'] = time.time()  # Store as timestamp
        self.stats['estimated_completion'] = (datetime.now() + timedelta(hours=3)).isoformat()
        self.stats['status'] = 'running'
        self.stats['total_cycles'] = total_cycles
        
        self._add_alert('info', f'Detection session started - {total_cycles} cycles planned')
        self.emit_update()
        
    def update_stats(self, **kwargs):
        """Update dashboard statistics"""
        # Handle special fields
        if 'current_cycle' in kwargs:
            self.stats['current_cycle'] = kwargs['current_cycle']
            
        # Update all provided stats
        for key, value in kwargs.items():
            if key in self.stats or key in ['api_costs_saved', 'raydium_v3_gems', 'stage_performance']:
                self.stats[key] = value
                
        self.stats['last_update'] = time.time()
        self.emit_update()
        
    def add_token(self, token_data: Dict[str, Any], is_high_conviction: bool = False):
        """Enhanced add_token with full metadata support"""
        # Enrich token data with defaults
        enriched_token = {
            'address': token_data.get('address', 'Unknown'),
            'symbol': token_data.get('symbol', 'Unknown'),
            'name': token_data.get('name', ''),
            'score': token_data.get('score', 0),
            'market_cap': token_data.get('market_cap', token_data.get('marketCap', 0)),
            'volume_24h': token_data.get('volume_24h', token_data.get('volume24h', 0)),
            'liquidity': token_data.get('liquidity', 0),
            'price_change_24h': token_data.get('price_change_24h', 0),
            'discovery_source': token_data.get('discovery_source', token_data.get('source', 'unknown')),
            'platform': token_data.get('platform', 'unknown'),
            'token_age': token_data.get('token_age', 'unknown'),
            'holder_count': token_data.get('holder_count', 0),
            'timestamp': datetime.now().isoformat(),
            'current_stage': token_data.get('current_stage', 1),
            'is_early_gem_candidate': token_data.get('is_early_gem_candidate', False),
            'volume_tvl_ratio': token_data.get('volume_tvl_ratio', 0)
        }
        
        # Add to recent tokens
        self.recent_tokens.append(enriched_token)
        
        # Track high conviction
        if is_high_conviction or enriched_token['score'] >= 85:
            self.high_conviction_tokens.append(enriched_token)
            self.stats['high_conviction_found'] = len(self.high_conviction_tokens)
            self._add_alert('high_conviction', 
                          f"High conviction token found: {enriched_token['symbol']} (Score: {enriched_token['score']})", 
                          enriched_token)
        
        # Track Raydium V3 candidates
        if enriched_token.get('discovery_source') == 'raydium_v3_enhanced' or enriched_token.get('is_early_gem_candidate'):
            self.raydium_v3_candidates.append(enriched_token)
            self.stats['raydium_v3_gems'] = len(self.raydium_v3_candidates)
            if enriched_token.get('is_early_gem_candidate'):
                self._add_alert('raydium_gem', 
                              f"Raydium V3 early gem: {enriched_token['symbol']} (TVL ratio: {enriched_token.get('volume_tvl_ratio', 0):.2f})", 
                              enriched_token)
        
        # Update total count
        self.stats['total_tokens_analyzed'] = len(self.recent_tokens)
        
        # Optimization: Only emit if there are connected clients
        if hasattr(self.socketio, 'server') and self.socketio.server.manager.rooms:
            self.emit_tokens_update()
    
    def _add_alert(self, alert_type: str, message: str, data: Any = None):
        """Add an alert to the queue"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.alert_queue.append(alert)
        self.socketio.emit('new_alert', alert)
    
    def update_stage_performance(self, stage: str, processed: int, filtered: int, time_taken: float):
        """Update stage performance metrics"""
        if stage in self.stats['stage_performance']:
            self.stats['stage_performance'][stage] = {
                'processed': processed,
                'filtered': filtered,
                'time': time_taken
            }
        self.emit_update()
        
    def complete_cycle(self, cycle_num: int, tokens_analyzed: int, high_conviction_found: int):
        """Enhanced cycle completion with performance tracking"""
        # Calculate cycle time
        if hasattr(self, '_cycle_start_time'):
            cycle_time = time.time() - self._cycle_start_time
            self.performance_metrics['cycle_times'].append(cycle_time)
            self.stats['average_cycle_time'] = statistics.mean(self.performance_metrics['cycle_times'])
        
        # Track tokens per cycle
        self.performance_metrics['tokens_per_cycle'].append(tokens_analyzed)
        
        cycle_data = {
            'cycle': cycle_num,
            'tokens_analyzed': tokens_analyzed,
            'high_conviction_found': high_conviction_found,
            'timestamp': datetime.now().isoformat(),
            'duration': self.performance_metrics['cycle_times'][-1] if self.performance_metrics['cycle_times'] else 0
        }
        self.cycle_history.append(cycle_data)
        
        self.stats['cycles_completed'] = cycle_num
        self.stats['current_cycle'] = cycle_num
        
        self.socketio.emit('cycle_complete', cycle_data)
        self.emit_update()
        
    def start_cycle(self):
        """Mark the start of a new cycle"""
        self._cycle_start_time = time.time()
        
    def emit_update(self):
        """Emit stats update with diff optimization"""
        # Include comprehensive stats
        comprehensive_stats = {
            **self.stats,
            'performance_metrics': {
                'average_cycle_time': self.stats.get('average_cycle_time', 0),
                'api_cost_savings': self.stats.get('api_costs_saved', 0),
                'discovery_rate': self._calculate_discovery_rate()
            }
        }
        
        # Optimization: Only broadcast if data actually changed
        if comprehensive_stats != self._last_broadcast_stats:
            self.socketio.emit('stats_update', comprehensive_stats)
            self._last_broadcast_stats = comprehensive_stats.copy()
        
    def emit_tokens_update(self):
        """Enhanced tokens update with rich data"""
        current_data = {
            'recent': list(self.recent_tokens)[-20:],  # Last 20 for recent
            'high_conviction': self.high_conviction_tokens[-10:],  # Last 10 high conviction
            'raydium_v3': list(self.raydium_v3_candidates)[-10:],  # Last 10 Raydium gems
            'stats_summary': {
                'total_analyzed': self.stats['total_tokens_analyzed'],
                'high_conviction_count': len(self.high_conviction_tokens),
                'raydium_count': len(self.raydium_v3_candidates)
            }
        }
        
        # Optimization: Only broadcast if token data changed
        if current_data != self._last_broadcast_tokens:
            self.socketio.emit('tokens_update', current_data)
            self._last_broadcast_tokens = current_data.copy()
    
    def _get_enhanced_html_template(self) -> str:
        """Get enhanced HTML template with seamless integration"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtuoso Gem Hunter Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        /* Enhanced styles that preserve existing look while adding new features */
        :root {
            --background-primary: #0f0f23;
            --background-secondary: #1a1a2e;
            --background-tertiary: #16213e;
            --background-gradient: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            
            --surface: rgba(255, 255, 255, 0.05);
            --surface-hover: rgba(255, 255, 255, 0.08);
            --surface-active: rgba(255, 255, 255, 0.1);
            --surface-glass: rgba(255, 255, 255, 0.03);
            
            --primary-color: #00d4ff;
            --secondary-color: #a855f7;
            --accent-color: #ff6b6b;
            --success-color: #4ecdc4;
            --warning-color: #ffd93d;
            --error-color: #ff6b6b;
            
            --text-primary: #ffffff;
            --text-secondary: #a3a3a3;
            --text-muted: #6b7280;
            
            --border: rgba(255, 255, 255, 0.1);
            --border-accent: rgba(0, 212, 255, 0.3);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            --shadow-hover: 0 16px 48px rgba(0, 0, 0, 0.4);
            --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.3);
            
            --border-radius: 16px;
            --border-radius-small: 8px;
            --border-radius-large: 24px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--background-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(168, 85, 247, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 60%, rgba(255, 107, 157, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: clamp(16px, 4vw, 32px);
            display: flex;
            flex-direction: column;
            gap: clamp(20px, 3vw, 30px);
        }
        
        /* Enhanced header with better styling */
        .header {
            text-align: center;
            padding: clamp(24px, 4vw, 40px);
            background: var(--surface-glass);
            backdrop-filter: blur(24px) saturate(180%);
            border-radius: var(--border-radius-large);
            border: 1px solid var(--border);
            box-shadow: var(--shadow), var(--shadow-glow);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color), var(--accent-color));
            animation: gradient-shift 3s ease-in-out infinite;
        }
        
        @keyframes gradient-shift {
            0%, 100% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
        }
        
        h1 {
            font-size: clamp(2rem, 5vw, 3rem);
            margin-bottom: 16px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            margin-bottom: 20px;
        }
        
        .timer {
            font-size: clamp(1.5rem, 3vw, 2rem);
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            color: var(--primary-color);
            display: inline-block;
            padding: 8px 20px;
            background: var(--surface);
            border-radius: var(--border-radius);
            border: 1px solid var(--border);
        }
        
        /* Enhanced stats grid with better cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: clamp(16px, 2vw, 24px);
        }
        
        .stat-card {
            background: var(--surface-glass);
            backdrop-filter: blur(24px) saturate(180%);
            border-radius: var(--border-radius);
            padding: clamp(20px, 3vw, 28px);
            text-align: center;
            transition: var(--transition);
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-hover), var(--shadow-glow);
            border-color: var(--border-accent);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .stat-card:hover::before {
            opacity: 1;
        }
        
        .stat-icon {
            font-size: 2rem;
            margin-bottom: 12px;
            display: block;
            opacity: 0.8;
        }
        
        .stat-value {
            font-size: clamp(1.8rem, 4vw, 2.4rem);
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: clamp(0.85rem, 2vw, 0.95rem);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* New: Stat trend indicator */
        .stat-trend {
            position: absolute;
            top: 16px;
            right: 16px;
            font-size: 0.8rem;
            padding: 4px 8px;
            border-radius: var(--border-radius-small);
            background: var(--surface);
        }
        
        .stat-trend.positive { color: var(--success-color); }
        .stat-trend.negative { color: var(--error-color); }
        
        /* Enhanced progress section */
        .progress-section {
            background: var(--surface-glass);
            backdrop-filter: blur(24px) saturate(180%);
            border-radius: var(--border-radius);
            padding: clamp(24px, 4vw, 32px);
            border: 1px solid var(--border);
            box-shadow: var(--shadow), var(--shadow-glow);
            position: relative;
        }
        
        .progress-section h3 {
            color: var(--primary-color);
            margin-bottom: 20px;
            font-size: clamp(1.2rem, 3vw, 1.4rem);
            font-weight: 600;
        }
        
        /* New: Stage indicators */
        .stage-indicators {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            gap: 10px;
        }
        
        .stage-indicator {
            flex: 1;
            text-align: center;
            padding: 12px;
            background: var(--surface);
            border-radius: var(--border-radius-small);
            border: 1px solid var(--border);
            transition: var(--transition);
        }
        
        .stage-indicator.active {
            background: var(--primary-color);
            color: var(--background-primary);
            border-color: var(--primary-color);
        }
        
        .stage-indicator.completed {
            border-color: var(--success-color);
            color: var(--success-color);
        }
        
        .stage-number {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        
        .stage-name {
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .progress-bar {
            background: var(--surface);
            border-radius: 12px;
            height: 24px;
            overflow: hidden;
            position: relative;
            margin-bottom: 16px;
            border: 1px solid var(--border);
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--secondary-color), var(--primary-color));
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-text {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-top: 8px;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .status-indicator.status-idle { background: var(--text-muted); }
        .status-indicator.status-running { background: var(--success-color); }
        .status-indicator.status-paused { background: var(--warning-color); }
        .status-indicator.status-error { background: var(--error-color); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }
        
        /* Enhanced content grid */
        .content-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: clamp(20px, 4vw, 32px);
        }
        
        @media (max-width: 900px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .panel {
            background: var(--surface-glass);
            backdrop-filter: blur(24px) saturate(180%);
            border-radius: var(--border-radius);
            padding: clamp(20px, 4vw, 32px);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            transition: var(--transition);
            height: fit-content;
            position: relative;
        }
        
        .panel:hover {
            box-shadow: var(--shadow-hover);
        }
        
        .panel h3 {
            margin-bottom: 20px;
            color: var(--primary-color);
            font-size: clamp(1.2rem, 3vw, 1.4rem);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        /* Enhanced token list */
        .token-list {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 8px;
        }
        
        .token-item {
            background: var(--surface);
            padding: 16px;
            margin-bottom: 12px;
            border-radius: var(--border-radius-small);
            border-left: 3px solid var(--primary-color);
            transition: var(--transition);
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .token-item:hover {
            background: var(--surface-hover);
            transform: translateX(4px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        
        .token-item.high-conviction {
            border-left-color: var(--success-color);
            background: linear-gradient(135deg, var(--surface) 0%, rgba(78, 205, 196, 0.05) 100%);
        }
        
        /* Enhanced token display */
        .token-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .token-symbol {
            font-weight: 700;
            font-size: 1.1rem;
        }
        
        .token-score {
            font-weight: 700;
            font-size: 1.2rem;
            color: var(--primary-color);
        }
        
        .token-address {
            font-family: monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin: 8px 0;
            word-break: break-all;
        }
        
        /* New: Token metrics */
        .token-metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 12px;
        }
        
        .token-metric {
            display: flex;
            flex-direction: column;
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        /* Enhanced chart styling */
        .cycle-chart {
            height: 300px;
            max-height: 400px;
        }
        
        /* Loading state */
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
            font-style: italic;
        }
        
        /* Alert system */
        .alerts-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        }
        
        .alert {
            background: var(--background-secondary);
            border: 1px solid var(--border);
            border-radius: var(--border-radius);
            padding: 16px;
            margin-bottom: 10px;
            box-shadow: var(--shadow);
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: start;
            gap: 12px;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .alert-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        
        .alert-content { flex: 1; }
        
        .alert-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .alert-message {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .alert-close {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 1.2rem;
            padding: 0;
            transition: var(--transition);
        }
        
        .alert-close:hover {
            color: var(--text-primary);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .stage-indicators {
                flex-wrap: wrap;
            }
            
            .stage-indicator {
                flex: 1 1 45%;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 10px;
            }
            
            .alerts-container {
                left: 10px;
                right: 10px;
                max-width: none;
            }
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--surface);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 4px;
            transition: background 0.3s ease;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-color);
        }
    </style>
</head>
<body>
    <div class="alerts-container" id="alerts-container"></div>
    
    <div class="container">
        <div class="header">
            <h1>🚀 Virtuoso Gem Hunter</h1>
            <div class="subtitle">Advanced 4-Stage Token Analysis System</div>
            <div class="timer" id="timer">00:00:00</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-icon">🔄</span>
                <div class="stat-value" id="cycles-completed">0</div>
                <div class="stat-label">Cycles Completed</div>
                <div class="stat-trend positive" id="cycles-trend" style="display: none;">+0%</div>
            </div>
            <div class="stat-card">
                <span class="stat-icon">🔍</span>
                <div class="stat-value" id="tokens-analyzed">0</div>
                <div class="stat-label">Tokens Analyzed</div>
                <div class="stat-trend" id="tokens-trend" style="display: none;">+0%</div>
            </div>
            <div class="stat-card">
                <span class="stat-icon">🎯</span>
                <div class="stat-value" id="high-conviction">0</div>
                <div class="stat-label">High Conviction</div>
                <div class="stat-trend" id="conviction-trend" style="display: none;">+0%</div>
            </div>
            <div class="stat-card">
                <span class="stat-icon">💎</span>
                <div class="stat-value" id="raydium-gems">0</div>
                <div class="stat-label">Raydium V3 Gems</div>
                <div class="stat-trend" id="raydium-trend" style="display: none;">+0%</div>
            </div>
            <div class="stat-card">
                <span class="stat-icon">💰</span>
                <div class="stat-value" id="api-costs-saved">0%</div>
                <div class="stat-label">API Costs Saved</div>
                <div class="stat-trend positive" id="savings-trend" style="display: none;">+0%</div>
            </div>
            <div class="stat-card">
                <span class="stat-icon">⚡</span>
                <div class="stat-value" id="discovery-rate">0</div>
                <div class="stat-label">Tokens/Hour</div>
                <div class="stat-trend" id="rate-trend" style="display: none;">+0%</div>
            </div>
        </div>
        
        <div class="progress-section">
            <h3>4-Stage Analysis Progress</h3>
            
            <div class="stage-indicators" id="stage-indicators">
                <div class="stage-indicator" id="stage-1">
                    <div class="stage-number">1</div>
                    <div class="stage-name">Discovery</div>
                </div>
                <div class="stage-indicator" id="stage-2">
                    <div class="stage-number">2</div>
                    <div class="stage-name">Analysis</div>
                </div>
                <div class="stage-indicator" id="stage-3">
                    <div class="stage-number">3</div>
                    <div class="stage-name">Validation</div>
                </div>
                <div class="stage-indicator" id="stage-4">
                    <div class="stage-number">4</div>
                    <div class="stage-name">OHLCV</div>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill" id="cycle-progress" style="width: 0%"></div>
            </div>
            <div class="progress-text">
                <span class="status-indicator" id="status-indicator"></span>
                <span id="status-text">Initializing...</span>
            </div>
        </div>
        
        <div class="content-grid">
            <div class="panel">
                <h3>🔥 High Conviction Tokens</h3>
                <div class="token-list" id="high-conviction-list">
                    <div class="loading">No high conviction tokens found yet...</div>
                </div>
            </div>
            
            <div class="panel">
                <h3>📊 Recent Analysis</h3>
                <div class="token-list" id="recent-tokens-list">
                    <div class="loading">Starting analysis...</div>
                </div>
            </div>
        </div>
        
        <div class="panel" style="margin-top: 30px;">
            <h3>📈 Cycle Performance</h3>
            <canvas id="cycleChart" class="cycle-chart"></canvas>
        </div>
    </div>

    <script>
        const socket = io();
        let cycleChart = null;
        let lastStats = {};
        
        // Initialize chart
        function initChart() {
            const ctx = document.getElementById('cycleChart').getContext('2d');
            cycleChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Tokens per Cycle',
                        data: [],
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'High Conviction',
                        data: [],
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 500
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff' }
                        }
                    },
                    scales: {
                        x: { 
                            ticks: { color: '#b3b3b3' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: { 
                            ticks: { color: '#b3b3b3' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }
        
        // Format number for display
        function formatNumber(num) {
            if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
            if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
            return parseFloat(num).toFixed(2);
        }
        
        // Update timer
        let timerInterval = null;
        function updateTimer(startTime) {
            if (!startTime) return;
            
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            
            const startTimestamp = typeof startTime === 'number' ? startTime * 1000 : new Date(startTime).getTime();
            
            timerInterval = setInterval(() => {
                const now = Date.now();
                const elapsed = now - startTimestamp;
                
                const hours = Math.floor(elapsed / (1000 * 60 * 60));
                const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((elapsed % (1000 * 60)) / 1000);
                
                const timerElement = document.getElementById('timer');
                if (timerElement) {
                    timerElement.textContent = 
                        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }
            }, 1000);
        }
        
        // Update stage indicators
        function updateStageIndicators(stageData) {
            if (!stageData) return;
            
            Object.entries(stageData).forEach(([stage, data]) => {
                const stageNum = stage.replace('stage', '');
                const indicator = document.getElementById(`stage-${stageNum}`);
                if (indicator && data.processed > 0) {
                    indicator.classList.add('completed');
                }
            });
        }
        
        // Calculate and show trends
        function updateTrends(stats) {
            // Update trends based on previous values
            const trends = {
                'cycles': stats.cycles_completed - (lastStats.cycles_completed || 0),
                'tokens': stats.total_tokens_analyzed - (lastStats.total_tokens_analyzed || 0),
                'conviction': stats.high_conviction_found - (lastStats.high_conviction_found || 0),
                'raydium': (stats.raydium_v3_gems || 0) - (lastStats.raydium_v3_gems || 0)
            };
            
            // Show/update trend indicators
            Object.entries(trends).forEach(([key, change]) => {
                const trendEl = document.getElementById(`${key}-trend`);
                if (trendEl && change !== 0) {
                    trendEl.style.display = 'block';
                    trendEl.textContent = change > 0 ? `+${change}` : `${change}`;
                    trendEl.className = `stat-trend ${change > 0 ? 'positive' : 'negative'}`;
                }
            });
            
            lastStats = {...stats};
        }
        
        // Socket event handlers
        socket.on('stats_update', function(data) {
            // Update basic stats
            document.getElementById('cycles-completed').textContent = data.cycles_completed;
            document.getElementById('tokens-analyzed').textContent = data.total_tokens_analyzed;
            document.getElementById('high-conviction').textContent = data.high_conviction_found;
            document.getElementById('api-calls').textContent = data.api_calls_made;
            
            // Update enhanced stats
            if (data.raydium_v3_gems !== undefined) {
                document.getElementById('raydium-gems').textContent = data.raydium_v3_gems;
            }
            if (data.api_costs_saved !== undefined) {
                document.getElementById('api-costs-saved').textContent = Math.round(data.api_costs_saved) + '%';
            }
            if (data.performance_metrics && data.performance_metrics.discovery_rate !== undefined) {
                document.getElementById('discovery-rate').textContent = Math.round(data.performance_metrics.discovery_rate);
            }
            
            // Update stage indicators
            if (data.stage_performance) {
                updateStageIndicators(data.stage_performance);
            }
            
            // Update trends
            updateTrends(data);
            
            // Update status
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            
            statusIndicator.className = `status-indicator status-${data.status}`;
            statusText.textContent = data.current_token ? 
                `Analyzing: ${data.current_token.substring(0, 8)}...` : 
                data.status.charAt(0).toUpperCase() + data.status.slice(1);
            
            // Update progress
            const progress = data.current_cycle > 0 ? (data.current_cycle / (data.total_cycles || 9)) * 100 : 0;
            document.getElementById('cycle-progress').style.width = `${progress}%`;
            
            // Start timer if needed
            if (data.start_time && !document.getElementById('timer').dataset.started) {
                updateTimer(data.start_time);
                document.getElementById('timer').dataset.started = 'true';
            }
        });
        
        socket.on('tokens_update', function(data) {
            // Update high conviction tokens
            const highConvictionList = document.getElementById('high-conviction-list');
            if (data.high_conviction && data.high_conviction.length > 0) {
                const fragment = document.createDocumentFragment();
                data.high_conviction.forEach(token => {
                    const tokenDiv = createEnhancedTokenElement(token, true);
                    fragment.appendChild(tokenDiv);
                });
                highConvictionList.innerHTML = '';
                highConvictionList.appendChild(fragment);
            } else {
                highConvictionList.innerHTML = '<div class="loading">No high conviction tokens found yet...</div>';
            }
            
            // Update recent tokens with enhanced display
            const recentList = document.getElementById('recent-tokens-list');
            if (data.recent && data.recent.length > 0) {
                const fragment = document.createDocumentFragment();
                data.recent.forEach(token => {
                    const tokenDiv = createEnhancedTokenElement(token, false);
                    fragment.appendChild(tokenDiv);
                });
                recentList.innerHTML = '';
                recentList.appendChild(fragment);
            } else {
                recentList.innerHTML = '<div class="loading">Starting analysis...</div>';
            }
        });
        
        // Create enhanced token element
        function createEnhancedTokenElement(token, isHighConviction) {
            const tokenDiv = document.createElement('div');
            tokenDiv.className = `token-item ${isHighConviction ? 'high-conviction' : ''}`;
            
            // Determine stage indicator
            const stageIndicator = token.current_stage ? 
                `<span style="font-size: 0.8rem; color: var(--text-muted);">Stage ${token.current_stage}</span>` : '';
            
            tokenDiv.innerHTML = `
                <div class="token-header">
                    <div>
                        <span class="token-symbol">${token.symbol || 'Unknown'}</span>
                        ${token.is_early_gem_candidate ? ' <span style="color: var(--secondary-color);">💎</span>' : ''}
                    </div>
                    <div style="text-align: right;">
                        <div class="token-score">${Math.round(token.score || 0)}</div>
                        ${stageIndicator}
                    </div>
                </div>
                <div class="token-address">${token.address}</div>
                <div class="token-metrics">
                    <div class="token-metric">
                        <div class="metric-label">Market Cap</div>
                        <div class="metric-value">$${formatNumber(token.market_cap || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">24h Volume</div>
                        <div class="metric-value">$${formatNumber(token.volume_24h || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">Liquidity</div>
                        <div class="metric-value">$${formatNumber(token.liquidity || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">Source</div>
                        <div class="metric-value">${token.discovery_source || token.source || 'Unknown'}</div>
                    </div>
                </div>
            `;
            
            // Add click handler to copy address
            tokenDiv.addEventListener('click', () => {
                navigator.clipboard.writeText(token.address);
                showAlert({
                    type: 'info',
                    message: `Address copied: ${token.address.substring(0, 8)}...`
                });
            });
            
            return tokenDiv;
        }
        
        socket.on('cycle_complete', function(data) {
            if (cycleChart) {
                // Limit chart data points
                const maxPoints = 50;
                if (cycleChart.data.labels.length >= maxPoints) {
                    cycleChart.data.labels.shift();
                    cycleChart.data.datasets[0].data.shift();
                    cycleChart.data.datasets[1].data.shift();
                }
                
                cycleChart.data.labels.push(`Cycle ${data.cycle}`);
                cycleChart.data.datasets[0].data.push(data.tokens_analyzed);
                cycleChart.data.datasets[1].data.push(data.high_conviction_found);
                
                cycleChart.update('none');
            }
        });
        
        // Alert handling
        socket.on('new_alert', function(alert) {
            showAlert(alert);
        });
        
        function showAlert(alert) {
            const container = document.getElementById('alerts-container');
            const alertEl = document.createElement('div');
            alertEl.className = 'alert';
            
            const icon = alert.type === 'high_conviction' ? '🎯' : 
                         alert.type === 'raydium_gem' ? '💎' :
                         alert.type === 'warning' ? '⚠️' : 
                         alert.type === 'error' ? '❌' : 'ℹ️';
            
            alertEl.innerHTML = `
                <div class="alert-icon">${icon}</div>
                <div class="alert-content">
                    <div class="alert-title">${alert.type.replace('_', ' ').toUpperCase()}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
                <button class="alert-close" onclick="this.parentElement.remove()">×</button>
            `;
            
            container.appendChild(alertEl);
            
            // Auto remove after 10 seconds
            setTimeout(() => {
                alertEl.remove();
            }, 10000);
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            
            // Handle initial connection
            socket.on('initial_state', function(data) {
                if (data.stats) {
                    socket.emit('stats_update', data.stats);
                }
            });
        });
    </script>
</body>
</html>
        '''
    
    def run_server(self):
        """Run the Flask server"""
        print(f"🌐 Starting Virtuoso Web Dashboard on http://localhost:{self.port}")
        print(f"🚀 Dashboard will auto-open in your browser...")
        print(f"✨ Enhanced features enabled: Raydium V3 tracking, Performance metrics, Rich token data")
        
        # Auto-open browser
        threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()
        
        # Run server
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)

# For backward compatibility
if __name__ == "__main__":
    dashboard = VirtuosoWebDashboard(port=8080)
    dashboard.start_detection()
    dashboard.update_stats(current_token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    dashboard.run_server()