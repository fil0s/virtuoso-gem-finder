#!/usr/bin/env python3
"""
Enhanced Real-time HTML Dashboard for Virtuoso Gem Hunter
Advanced features for professional token monitoring and analysis
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

class EnhancedVirtuosoWebDashboard:
    """Enhanced real-time web dashboard with advanced features"""
    
    def __init__(self, port: int = 9090, debug_mode: bool = False):
        self.port = port
        self.debug_mode = debug_mode
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'virtuoso_gem_hunter_enhanced_2025'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Initialize enhanced logging if available
        try:
            from utils.enhanced_structured_logger import create_enhanced_logger
            self.enhanced_logger = create_enhanced_logger(
                "EnhancedVirtuosoWebDashboard",
                log_level="DEBUG" if debug_mode else "INFO"
            )
            self.session_id = self.enhanced_logger.new_scan_context(
                strategy="enhanced-web-dashboard-monitoring",
                timeframe="dashboard_session"
            )
        except ImportError:
            self.enhanced_logger = None
            self.session_id = None
        
        # Enhanced dashboard state
        self.stats = {
            'cycles_completed': 0,
            'total_tokens_analyzed': 0,
            'high_conviction_found': 0,
            'api_calls_made': 0,
            'api_costs_saved': 0.0,
            'detection_accuracy': 0.0,
            'average_cycle_time': 0,
            'raydium_v3_gems': 0,
            'total_early_gems': 0
        }
        
        # Advanced metrics tracking
        self.performance_metrics = {
            'cycle_times': deque(maxlen=50),
            'tokens_per_cycle': deque(maxlen=50),
            'api_response_times': deque(maxlen=100),
            'stage_performance': {
                'stage1': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage2': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage3': {'processed': 0, 'filtered': 0, 'time': 0},
                'stage4': {'processed': 0, 'filtered': 0, 'time': 0}
            }
        }
        
        # Token tracking with history
        self.token_history = deque(maxlen=1000)
        self.high_conviction_tokens = []
        self.recent_tokens = deque(maxlen=20)
        self.raydium_v3_candidates = deque(maxlen=50)
        
        # Real-time alerts
        self.alert_queue = deque(maxlen=100)
        
        # Session tracking
        self.session_start = datetime.now()
        self.current_cycle = 0
        self.total_cycles = 9
        self.is_running = False
        self.current_status = 'idle'
        self.current_token = None
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_handlers()
        
    def _setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template_string(self._get_enhanced_html_template())
        
        @self.app.route('/api/stats')
        def get_stats():
            return jsonify(self._get_comprehensive_stats())
        
        @self.app.route('/api/tokens')
        def get_tokens():
            return jsonify({
                'high_conviction': self.high_conviction_tokens,
                'recent': list(self.recent_tokens),
                'raydium_v3': list(self.raydium_v3_candidates),
                'total_analyzed': len(self.token_history)
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
            # Send initial state
            emit('initial_state', self._get_comprehensive_stats())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            emit('full_update', self._get_comprehensive_stats())
    
    def _get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        now = datetime.now()
        elapsed = (now - self.session_start).total_seconds()
        
        # Calculate advanced metrics
        avg_cycle_time = statistics.mean(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0
        avg_tokens_per_cycle = statistics.mean(self.performance_metrics['tokens_per_cycle']) if self.performance_metrics['tokens_per_cycle'] else 0
        
        return {
            'basic_stats': self.stats,
            'performance': {
                'average_cycle_time': avg_cycle_time,
                'average_tokens_per_cycle': avg_tokens_per_cycle,
                'total_runtime': elapsed,
                'cycles_per_hour': (self.stats['cycles_completed'] / elapsed * 3600) if elapsed > 0 else 0
            },
            'stage_metrics': self.performance_metrics['stage_performance'],
            'session_info': {
                'start_time': self.session_start.isoformat(),
                'current_cycle': self.current_cycle,
                'total_cycles': self.total_cycles,
                'status': self.current_status,
                'current_token': self.current_token,
                'is_running': self.is_running
            },
            'token_counts': {
                'high_conviction': len(self.high_conviction_tokens),
                'recent': len(self.recent_tokens),
                'raydium_v3': len(self.raydium_v3_candidates),
                'total_history': len(self.token_history)
            }
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        metrics = {
            'efficiency': {
                'api_cost_reduction': f"{self.stats['api_costs_saved']:.2f}%",
                'filtering_effectiveness': self._calculate_filtering_effectiveness(),
                'discovery_rate': self._calculate_discovery_rate()
            },
            'timing': {
                'fastest_cycle': min(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0,
                'slowest_cycle': max(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0,
                'average_cycle': statistics.mean(self.performance_metrics['cycle_times']) if self.performance_metrics['cycle_times'] else 0
            },
            'quality': {
                'high_conviction_rate': (self.stats['high_conviction_found'] / max(1, self.stats['total_tokens_analyzed'])) * 100,
                'raydium_v3_discovery_rate': (self.stats['raydium_v3_gems'] / max(1, self.stats['total_tokens_analyzed'])) * 100
            }
        }
        return metrics
    
    def _calculate_filtering_effectiveness(self) -> Dict[str, float]:
        """Calculate filtering effectiveness for each stage"""
        effectiveness = {}
        for stage, data in self.performance_metrics['stage_performance'].items():
            if data['processed'] > 0:
                effectiveness[stage] = (data['filtered'] / data['processed']) * 100
            else:
                effectiveness[stage] = 0
        return effectiveness
    
    def _calculate_discovery_rate(self) -> float:
        """Calculate token discovery rate per hour"""
        elapsed_hours = (datetime.now() - self.session_start).total_seconds() / 3600
        if elapsed_hours > 0:
            return self.stats['total_tokens_analyzed'] / elapsed_hours
        return 0
    
    def update_stats(self, **kwargs):
        """Update dashboard statistics"""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] = value
        
        # Broadcast update
        self.socketio.emit('stats_update', self._get_comprehensive_stats())
    
    def add_token(self, token_data: Dict[str, Any]):
        """Add a token to tracking"""
        # Add to history
        self.token_history.append({
            **token_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Add to recent tokens
        self.recent_tokens.append(token_data)
        
        # Check if high conviction
        if token_data.get('score', 0) >= 85:
            self.high_conviction_tokens.append(token_data)
            self.stats['high_conviction_found'] = len(self.high_conviction_tokens)
            self._add_alert('high_conviction', f"High conviction token found: {token_data.get('symbol', 'Unknown')}", token_data)
        
        # Check if Raydium v3 candidate
        if token_data.get('discovery_source') == 'raydium_v3_enhanced' or token_data.get('is_early_gem_candidate'):
            self.raydium_v3_candidates.append(token_data)
            self.stats['raydium_v3_gems'] = len(self.raydium_v3_candidates)
        
        # Update total count
        self.stats['total_tokens_analyzed'] = len(self.token_history)
        
        # Broadcast token update
        self._broadcast_token_update()
    
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
    
    def update_cycle_complete(self, cycle_data: Dict[str, Any]):
        """Update dashboard when a cycle completes"""
        self.stats['cycles_completed'] = cycle_data.get('cycle', 0)
        
        # Track performance metrics
        if 'duration' in cycle_data:
            self.performance_metrics['cycle_times'].append(cycle_data['duration'])
        
        if 'tokens_analyzed' in cycle_data:
            self.performance_metrics['tokens_per_cycle'].append(cycle_data['tokens_analyzed'])
        
        # Update stage metrics
        if 'stage_metrics' in cycle_data:
            for stage, metrics in cycle_data['stage_metrics'].items():
                if stage in self.performance_metrics['stage_performance']:
                    self.performance_metrics['stage_performance'][stage].update(metrics)
        
        # Broadcast cycle complete event
        self.socketio.emit('cycle_complete', {
            'cycle': cycle_data.get('cycle', 0),
            'tokens_analyzed': cycle_data.get('tokens_analyzed', 0),
            'high_conviction_found': len(self.high_conviction_tokens),
            'duration': cycle_data.get('duration', 0)
        })
    
    def _broadcast_token_update(self):
        """Broadcast token updates to all clients"""
        self.socketio.emit('tokens_update', {
            'high_conviction': self.high_conviction_tokens[-10:],  # Last 10
            'recent': list(self.recent_tokens)[-20:],  # Last 20
            'raydium_v3': list(self.raydium_v3_candidates)[-10:],  # Last 10
            'stats': self.stats
        })
    
    def start_detection(self, total_cycles: int = 9):
        """Start detection session"""
        self.total_cycles = total_cycles
        self.is_running = True
        self.current_status = 'running'
        self.session_start = datetime.now()
        
        self._add_alert('info', f'Detection session started - {total_cycles} cycles planned')
        self.socketio.emit('detection_started', {
            'total_cycles': total_cycles,
            'start_time': self.session_start.isoformat()
        })
    
    def stop_detection(self):
        """Stop detection session"""
        self.is_running = False
        self.current_status = 'stopped'
        
        self._add_alert('info', 'Detection session stopped')
        self.socketio.emit('detection_stopped', {
            'end_time': datetime.now().isoformat(),
            'total_analyzed': self.stats['total_tokens_analyzed']
        })
    
    def _get_enhanced_html_template(self) -> str:
        """Get enhanced HTML template with advanced features"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtuoso Gem Hunter - Enhanced Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luxon@3.4.4/build/global/luxon.min.js"></script>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #1a1a2e;
            --bg-tertiary: #16213e;
            --surface: rgba(255, 255, 255, 0.05);
            --surface-hover: rgba(255, 255, 255, 0.08);
            --surface-glass: rgba(255, 255, 255, 0.03);
            
            --primary: #00d4ff;
            --secondary: #a855f7;
            --accent: #ff6b6b;
            --success: #4ecdc4;
            --warning: #ffd93d;
            --error: #ff6b6b;
            
            --text-primary: #ffffff;
            --text-secondary: #b8bcc8;
            --text-muted: #6b7280;
            
            --border: rgba(255, 255, 255, 0.1);
            --shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            --glow: 0 0 20px rgba(0, 212, 255, 0.5);
            
            --radius: 16px;
            --radius-sm: 8px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .dashboard-container {
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Enhanced Header */
        .header {
            background: var(--surface-glass);
            backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
            opacity: 0.1;
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.1; }
            50% { transform: scale(1.1); opacity: 0.2; }
        }
        
        .header-content {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .logo {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-bar {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .connection-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--surface);
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
        }
        
        .connection-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        /* Enhanced Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--surface-glass);
            backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 24px;
            border: 1px solid var(--border);
            position: relative;
            overflow: hidden;
            transition: var(--transition);
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow), var(--glow);
            border-color: var(--primary);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover::before {
            transform: scaleX(1);
        }
        
        .stat-icon {
            font-size: 1.5rem;
            margin-bottom: 12px;
            opacity: 0.8;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
            font-variant-numeric: tabular-nums;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-change {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 0.8rem;
            padding: 4px 8px;
            border-radius: var(--radius-sm);
            background: var(--surface);
        }
        
        .stat-change.positive {
            color: var(--success);
            background: rgba(78, 205, 196, 0.1);
        }
        
        .stat-change.negative {
            color: var(--error);
            background: rgba(255, 107, 107, 0.1);
        }
        
        /* Tab Navigation */
        .tab-nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: var(--surface);
            padding: 8px;
            border-radius: var(--radius);
            overflow-x: auto;
        }
        
        .tab-button {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: var(--radius-sm);
            transition: var(--transition);
            white-space: nowrap;
        }
        
        .tab-button:hover {
            background: var(--surface-hover);
            color: var(--text-primary);
        }
        
        .tab-button.active {
            background: var(--primary);
            color: var(--bg-primary);
        }
        
        /* Tab Content */
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Enhanced Token Lists */
        .token-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .token-card {
            background: var(--surface-glass);
            backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 20px;
            border: 1px solid var(--border);
            transition: var(--transition);
            cursor: pointer;
        }
        
        .token-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
            border-color: var(--primary);
        }
        
        .token-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .token-symbol {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .token-score {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--primary);
        }
        
        .token-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .token-metric {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 0.95rem;
            font-weight: 500;
        }
        
        /* Charts Container */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .chart-panel {
            background: var(--surface-glass);
            backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 24px;
            border: 1px solid var(--border);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .chart-controls {
            display: flex;
            gap: 10px;
        }
        
        .chart-button {
            padding: 6px 12px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            font-size: 0.8rem;
            cursor: pointer;
            transition: var(--transition);
        }
        
        .chart-button:hover {
            background: var(--surface-hover);
            color: var(--text-primary);
            border-color: var(--primary);
        }
        
        .chart-button.active {
            background: var(--primary);
            color: var(--bg-primary);
            border-color: var(--primary);
        }
        
        /* Alert System */
        .alerts-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        }
        
        .alert {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            margin-bottom: 10px;
            box-shadow: var(--shadow);
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: start;
            gap: 12px;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .alert-icon {
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        
        .alert-content {
            flex: 1;
        }
        
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
        
        /* Stage Progress */
        .stage-progress {
            background: var(--surface-glass);
            backdrop-filter: blur(20px);
            border-radius: var(--radius);
            padding: 24px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
        }
        
        .stage-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .stages-container {
            display: flex;
            gap: 20px;
            overflow-x: auto;
            padding-bottom: 10px;
        }
        
        .stage-item {
            flex: 1;
            min-width: 200px;
            background: var(--surface);
            border-radius: var(--radius-sm);
            padding: 16px;
            text-align: center;
            position: relative;
            transition: var(--transition);
        }
        
        .stage-item.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--bg-primary);
        }
        
        .stage-item.completed {
            border: 2px solid var(--success);
        }
        
        .stage-number {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stage-name {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .stage-stats {
            font-size: 0.8rem;
            opacity: 0.8;
        }
        
        /* Performance Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            padding: 20px;
            background: var(--surface);
            border-radius: var(--radius);
        }
        
        .metric-item {
            text-align: center;
            padding: 15px;
            background: var(--surface-glass);
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }
        
        /* Responsive Design */
        @media (max-width: 1200px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .token-grid {
                grid-template-columns: 1fr;
            }
            
            .header-content {
                flex-direction: column;
                text-align: center;
            }
            
            .tab-nav {
                justify-content: center;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .dashboard-container {
                padding: 10px;
            }
        }
        
        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--border);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--surface);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary);
        }
    </style>
</head>
<body>
    <div class="alerts-container" id="alerts-container"></div>
    
    <div class="dashboard-container">
        <!-- Enhanced Header -->
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <span>🚀</span>
                    <span>Virtuoso Gem Hunter</span>
                    <span style="font-size: 0.8rem; opacity: 0.7;">Enhanced v2.0</span>
                </div>
                <div class="status-bar">
                    <div class="connection-status">
                        <div class="connection-dot"></div>
                        <span id="connection-text">Connected</span>
                    </div>
                    <div class="timer" id="session-timer">00:00:00</div>
                </div>
            </div>
        </div>
        
        <!-- Enhanced Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🔄</div>
                <div class="stat-value" id="cycles-completed">0</div>
                <div class="stat-label">Cycles Completed</div>
                <div class="stat-change positive" id="cycles-change">+0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔍</div>
                <div class="stat-value" id="tokens-analyzed">0</div>
                <div class="stat-label">Tokens Analyzed</div>
                <div class="stat-change positive" id="tokens-change">+0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-value" id="high-conviction">0</div>
                <div class="stat-label">High Conviction</div>
                <div class="stat-change" id="conviction-change">+0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💎</div>
                <div class="stat-value" id="raydium-gems">0</div>
                <div class="stat-label">Raydium V3 Gems</div>
                <div class="stat-change" id="raydium-change">+0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💰</div>
                <div class="stat-value" id="api-saved">0%</div>
                <div class="stat-label">API Costs Saved</div>
                <div class="stat-change positive" id="savings-change">+0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-value" id="discovery-rate">0</div>
                <div class="stat-label">Tokens/Hour</div>
                <div class="stat-change" id="rate-change">+0%</div>
            </div>
        </div>
        
        <!-- Stage Progress -->
        <div class="stage-progress">
            <div class="stage-header">
                <h3>4-Stage Analysis Progress</h3>
                <div id="current-cycle">Cycle 0/9</div>
            </div>
            <div class="stages-container">
                <div class="stage-item" id="stage-1">
                    <div class="stage-number">1</div>
                    <div class="stage-name">Discovery Triage</div>
                    <div class="stage-stats">0 processed</div>
                </div>
                <div class="stage-item" id="stage-2">
                    <div class="stage-number">2</div>
                    <div class="stage-name">Enhanced Analysis</div>
                    <div class="stage-stats">0 processed</div>
                </div>
                <div class="stage-item" id="stage-3">
                    <div class="stage-number">3</div>
                    <div class="stage-name">Market Validation</div>
                    <div class="stage-stats">0 processed</div>
                </div>
                <div class="stage-item" id="stage-4">
                    <div class="stage-number">4</div>
                    <div class="stage-name">OHLCV Analysis</div>
                    <div class="stage-stats">0 processed</div>
                </div>
            </div>
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-button active" onclick="switchTab('tokens')">🔥 Live Tokens</button>
            <button class="tab-button" onclick="switchTab('performance')">📊 Performance</button>
            <button class="tab-button" onclick="switchTab('raydium')">💎 Raydium V3</button>
            <button class="tab-button" onclick="switchTab('analytics')">📈 Analytics</button>
            <button class="tab-button" onclick="switchTab('history')">📜 History</button>
        </div>
        
        <!-- Tab Contents -->
        <div class="tab-content active" id="tokens-tab">
            <div class="token-grid" id="live-tokens-grid">
                <!-- Live tokens will be populated here -->
            </div>
        </div>
        
        <div class="tab-content" id="performance-tab">
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value" id="avg-cycle-time">0s</div>
                    <div class="metric-label">Avg Cycle Time</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="fastest-cycle">0s</div>
                    <div class="metric-label">Fastest Cycle</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="api-efficiency">0%</div>
                    <div class="metric-label">API Efficiency</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value" id="filter-rate">0%</div>
                    <div class="metric-label">Filter Rate</div>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-panel">
                    <div class="chart-header">
                        <h3 class="chart-title">Tokens per Cycle</h3>
                        <div class="chart-controls">
                            <button class="chart-button active" onclick="updateChart('tokens', 'line')">Line</button>
                            <button class="chart-button" onclick="updateChart('tokens', 'bar')">Bar</button>
                        </div>
                    </div>
                    <canvas id="tokens-chart" height="300"></canvas>
                </div>
                
                <div class="chart-panel">
                    <div class="chart-header">
                        <h3 class="chart-title">Stage Performance</h3>
                        <div class="chart-controls">
                            <button class="chart-button active" onclick="updateChart('stages', 'bar')">Bar</button>
                            <button class="chart-button" onclick="updateChart('stages', 'pie')">Pie</button>
                        </div>
                    </div>
                    <canvas id="stages-chart" height="300"></canvas>
                </div>
            </div>
        </div>
        
        <div class="tab-content" id="raydium-tab">
            <div class="token-grid" id="raydium-tokens-grid">
                <!-- Raydium V3 tokens will be populated here -->
            </div>
        </div>
        
        <div class="tab-content" id="analytics-tab">
            <div class="charts-grid">
                <div class="chart-panel">
                    <div class="chart-header">
                        <h3 class="chart-title">Discovery Sources</h3>
                    </div>
                    <canvas id="sources-chart" height="300"></canvas>
                </div>
                
                <div class="chart-panel">
                    <div class="chart-header">
                        <h3 class="chart-title">Score Distribution</h3>
                    </div>
                    <canvas id="distribution-chart" height="300"></canvas>
                </div>
            </div>
        </div>
        
        <div class="tab-content" id="history-tab">
            <div id="history-container">
                <!-- Token history will be populated here -->
            </div>
        </div>
    </div>
    
    <script>
        // Socket.IO connection
        const socket = io();
        
        // Chart instances
        let charts = {};
        
        // State management
        let state = {
            tokens: [],
            alerts: [],
            performance: {},
            sessionStart: null
        };
        
        // Initialize dashboard
        function initDashboard() {
            setupCharts();
            setupEventHandlers();
            startSessionTimer();
        }
        
        // Setup charts
        function setupCharts() {
            // Tokens per cycle chart
            const tokensCtx = document.getElementById('tokens-chart').getContext('2d');
            charts.tokens = new Chart(tokensCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Tokens Analyzed',
                        data: [],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        tension: 0.4
                    }]
                },
                options: getChartOptions()
            });
            
            // Stage performance chart
            const stagesCtx = document.getElementById('stages-chart').getContext('2d');
            charts.stages = new Chart(stagesCtx, {
                type: 'bar',
                data: {
                    labels: ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4'],
                    datasets: [{
                        label: 'Tokens Processed',
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'rgba(0, 212, 255, 0.5)',
                            'rgba(168, 85, 247, 0.5)',
                            'rgba(78, 205, 196, 0.5)',
                            'rgba(255, 107, 107, 0.5)'
                        ]
                    }]
                },
                options: getChartOptions()
            });
            
            // Discovery sources chart
            const sourcesCtx = document.getElementById('sources-chart').getContext('2d');
            charts.sources = new Chart(sourcesCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#00d4ff',
                            '#a855f7',
                            '#4ecdc4',
                            '#ff6b6b',
                            '#ffd93d'
                        ]
                    }]
                },
                options: {
                    ...getChartOptions(),
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
            
            // Score distribution chart
            const distributionCtx = document.getElementById('distribution-chart').getContext('2d');
            charts.distribution = new Chart(distributionCtx, {
                type: 'bar',
                data: {
                    labels: ['0-20', '20-40', '40-60', '60-80', '80-100'],
                    datasets: [{
                        label: 'Token Count',
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(168, 85, 247, 0.5)'
                    }]
                },
                options: getChartOptions()
            });
        }
        
        // Common chart options
        function getChartOptions() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500
                },
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#b8bcc8' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#b8bcc8' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            };
        }
        
        // Setup event handlers
        function setupEventHandlers() {
            // Socket events
            socket.on('connect', () => {
                updateConnectionStatus(true);
            });
            
            socket.on('disconnect', () => {
                updateConnectionStatus(false);
            });
            
            socket.on('initial_state', (data) => {
                updateDashboard(data);
            });
            
            socket.on('stats_update', (data) => {
                updateStats(data);
            });
            
            socket.on('tokens_update', (data) => {
                updateTokens(data);
            });
            
            socket.on('new_alert', (alert) => {
                showAlert(alert);
            });
            
            socket.on('cycle_complete', (data) => {
                updateCycleComplete(data);
            });
        }
        
        // Update connection status
        function updateConnectionStatus(connected) {
            const dot = document.querySelector('.connection-dot');
            const text = document.getElementById('connection-text');
            
            if (connected) {
                dot.style.background = '#4ecdc4';
                text.textContent = 'Connected';
            } else {
                dot.style.background = '#ff6b6b';
                text.textContent = 'Disconnected';
            }
        }
        
        // Update dashboard with comprehensive data
        function updateDashboard(data) {
            updateStats(data);
            updateStageProgress(data.stage_metrics);
            updatePerformanceMetrics(data.performance);
        }
        
        // Update statistics
        function updateStats(data) {
            const stats = data.basic_stats || data;
            
            // Update stat values with animation
            animateValue('cycles-completed', stats.cycles_completed || 0);
            animateValue('tokens-analyzed', stats.total_tokens_analyzed || 0);
            animateValue('high-conviction', stats.high_conviction_found || 0);
            animateValue('raydium-gems', stats.raydium_v3_gems || 0);
            animateValue('api-saved', Math.round(stats.api_costs_saved || 0) + '%');
            
            // Calculate discovery rate
            if (data.performance) {
                animateValue('discovery-rate', Math.round(data.performance.cycles_per_hour || 0));
            }
            
            // Update current cycle
            if (data.session_info) {
                document.getElementById('current-cycle').textContent = 
                    `Cycle ${data.session_info.current_cycle}/${data.session_info.total_cycles}`;
            }
        }
        
        // Animate value changes
        function animateValue(elementId, newValue) {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            const currentValue = parseInt(element.textContent) || 0;
            if (currentValue === newValue) return;
            
            const increment = (newValue - currentValue) / 20;
            let current = currentValue;
            
            const timer = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
                    element.textContent = newValue;
                    clearInterval(timer);
                } else {
                    element.textContent = Math.round(current);
                }
            }, 50);
        }
        
        // Update stage progress
        function updateStageProgress(stageMetrics) {
            if (!stageMetrics) return;
            
            Object.entries(stageMetrics).forEach(([stage, data]) => {
                const stageNum = stage.replace('stage', '');
                const element = document.getElementById(`stage-${stageNum}`);
                if (element) {
                    const statsElement = element.querySelector('.stage-stats');
                    statsElement.textContent = `${data.processed} processed`;
                    
                    if (data.processed > 0) {
                        element.classList.add('completed');
                    }
                }
            });
        }
        
        // Update performance metrics
        function updatePerformanceMetrics(performance) {
            if (!performance) return;
            
            document.getElementById('avg-cycle-time').textContent = 
                Math.round(performance.average_cycle_time || 0) + 's';
            document.getElementById('fastest-cycle').textContent = 
                Math.round(performance.fastest_cycle || 0) + 's';
        }
        
        // Update tokens display
        function updateTokens(data) {
            const grid = document.getElementById('live-tokens-grid');
            grid.innerHTML = '';
            
            // Combine high conviction and recent tokens
            const allTokens = [...(data.high_conviction || []), ...(data.recent || [])];
            const uniqueTokens = Array.from(new Map(allTokens.map(t => [t.address, t])).values());
            
            uniqueTokens.slice(0, 12).forEach(token => {
                const card = createTokenCard(token);
                grid.appendChild(card);
            });
            
            // Update Raydium tab
            if (data.raydium_v3) {
                const raydiumGrid = document.getElementById('raydium-tokens-grid');
                raydiumGrid.innerHTML = '';
                data.raydium_v3.forEach(token => {
                    const card = createTokenCard(token, true);
                    raydiumGrid.appendChild(card);
                });
            }
        }
        
        // Create token card element
        function createTokenCard(token, isRadium = false) {
            const card = document.createElement('div');
            card.className = 'token-card';
            if (token.score >= 85) {
                card.style.borderColor = '#4ecdc4';
                card.style.boxShadow = '0 0 20px rgba(78, 205, 196, 0.3)';
            }
            
            card.innerHTML = `
                <div class="token-header">
                    <div class="token-symbol">${token.symbol || 'Unknown'}</div>
                    <div class="token-score">${Math.round(token.score || 0)}</div>
                </div>
                <div class="token-details">
                    <div class="token-metric">
                        <div class="metric-label">Market Cap</div>
                        <div class="metric-value">$${formatNumber(token.market_cap || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">Volume 24h</div>
                        <div class="metric-value">$${formatNumber(token.volume_24h || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">Liquidity</div>
                        <div class="metric-value">$${formatNumber(token.liquidity || 0)}</div>
                    </div>
                    <div class="token-metric">
                        <div class="metric-label">Source</div>
                        <div class="metric-value">${token.discovery_source || 'Unknown'}</div>
                    </div>
                </div>
                ${isRadium ? '<div style="margin-top: 10px; color: #a855f7;">💎 Early Gem Candidate</div>' : ''}
            `;
            
            return card;
        }
        
        // Format large numbers
        function formatNumber(num) {
            if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
            if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
            return num.toFixed(2);
        }
        
        // Show alert
        function showAlert(alert) {
            const container = document.getElementById('alerts-container');
            const alertEl = document.createElement('div');
            alertEl.className = 'alert';
            
            const icon = alert.type === 'high_conviction' ? '🎯' : 
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
        
        // Update cycle complete
        function updateCycleComplete(data) {
            // Update tokens chart
            if (charts.tokens) {
                charts.tokens.data.labels.push(`Cycle ${data.cycle}`);
                charts.tokens.data.datasets[0].data.push(data.tokens_analyzed);
                
                // Limit to last 20 points
                if (charts.tokens.data.labels.length > 20) {
                    charts.tokens.data.labels.shift();
                    charts.tokens.data.datasets[0].data.shift();
                }
                
                charts.tokens.update();
            }
            
            // Show cycle complete alert
            showAlert({
                type: 'info',
                message: `Cycle ${data.cycle} completed - ${data.tokens_analyzed} tokens analyzed`
            });
        }
        
        // Tab switching
        function switchTab(tabName) {
            // Update buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
        }
        
        // Session timer
        function startSessionTimer() {
            setInterval(() => {
                if (!state.sessionStart) {
                    state.sessionStart = new Date();
                }
                
                const elapsed = new Date() - state.sessionStart;
                const hours = Math.floor(elapsed / 3600000);
                const minutes = Math.floor((elapsed % 3600000) / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                
                document.getElementById('session-timer').textContent = 
                    `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        }
        
        // Initialize on load
        document.addEventListener('DOMContentLoaded', initDashboard);
    </script>
</body>
</html>
        '''
    
    def run_server(self):
        """Run the Flask server"""
        print(f"🌐 Starting Enhanced Virtuoso Web Dashboard on http://localhost:{self.port}")
        print(f"🚀 Dashboard will auto-open in your browser...")
        print(f"✨ Enhanced features: Real-time alerts, Raydium V3 tracking, Performance analytics")
        
        # Auto-open browser
        threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()
        
        # Run server
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)

# Example usage
if __name__ == "__main__":
    dashboard = EnhancedVirtuosoWebDashboard(port=9090, debug_mode=True)
    dashboard.start_detection()
    dashboard.run_server()