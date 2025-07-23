#!/usr/bin/env python3
"""
Real-time HTML Dashboard for Virtuoso Gem Hunter
Provides live web interface for monitoring detection cycles
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
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import queue

class VirtuosoWebDashboard:
    """Real-time web dashboard for monitoring gem detection"""
    
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
        
        # Dashboard state
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
            'cache_misses': 0
        }
        
        self.recent_tokens = []
        self.high_conviction_tokens = []
        self.error_log = []
        self.cycle_history = []
        
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
        self._setup_socket_events()
        
        self.logger = logging.getLogger('WebDashboard')
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return self.render_dashboard()
            
        @self.app.route('/api/stats')
        def get_stats():
            return jsonify(self.stats)
            
        @self.app.route('/api/tokens')
        def get_tokens():
            return jsonify({
                'recent': self.recent_tokens[-10:],
                'high_conviction': self.high_conviction_tokens
            })
            
        @self.app.route('/api/cycles')
        def get_cycles():
            return jsonify(self.cycle_history)
            
    def _setup_socket_events(self):
        """Setup SocketIO events for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('stats_update', self.stats)
            emit('tokens_update', {
                'recent': self.recent_tokens[-10:],
                'high_conviction': self.high_conviction_tokens
            })
            
    def render_dashboard(self):
        """Render the main dashboard HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Virtuoso Gem Hunter - Live Dashboard</title>
    <meta name="color-scheme" content="dark light">
    <meta name="theme-color" content="#0f0f23">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            /* Modern Dark Theme - Inspired by Web3 Aesthetics */
            --primary-color: #00d4ff;
            --secondary-color: #ff6b9d;
            --accent-color: #a855f7;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            
            /* Dark Mode Backgrounds */
            --background-primary: #0f0f23;
            --background-secondary: #1a1a2e;
            --background-tertiary: #16213e;
            --background-gradient: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            
            /* Glassmorphism Surfaces */
            --surface: rgba(255, 255, 255, 0.05);
            --surface-hover: rgba(255, 255, 255, 0.08);
            --surface-active: rgba(255, 255, 255, 0.12);
            --surface-glass: rgba(255, 255, 255, 0.03);
            
            /* Typography */
            --text-primary: #ffffff;
            --text-secondary: #a3a3a3;
            --text-muted: #737373;
            
            /* Borders & Effects */
            --border: rgba(255, 255, 255, 0.08);
            --border-accent: rgba(168, 85, 247, 0.3);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            --shadow-hover: 0 16px 48px rgba(0, 0, 0, 0.6);
            --shadow-glow: 0 0 20px rgba(168, 85, 247, 0.15);
            
            /* Modern Radii */
            --border-radius: 16px;
            --border-radius-small: 12px;
            --border-radius-large: 24px;
            
            /* Smooth Transitions */
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background-gradient);
            background-attachment: fixed;
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.6;
            
            /* Enhanced backdrop */
            position: relative;
        }
        
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
        
        /* Light Mode Override (for users who prefer light) */
        @media (prefers-color-scheme: light) {
            :root {
                --background-primary: #fafafa;
                --background-secondary: #f4f4f5;
                --background-tertiary: #e4e4e7;
                --background-gradient: linear-gradient(135deg, #fafafa 0%, #f4f4f5 50%, #e4e4e7 100%);
                
                --surface: rgba(0, 0, 0, 0.02);
                --surface-hover: rgba(0, 0, 0, 0.04);
                --surface-active: rgba(0, 0, 0, 0.06);
                --surface-glass: rgba(255, 255, 255, 0.8);
                
                --text-primary: #18181b;
                --text-secondary: #52525b;
                --text-muted: #71717a;
                
                --border: rgba(0, 0, 0, 0.06);
                --border-accent: rgba(168, 85, 247, 0.2);
                --shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
                --shadow-hover: 0 16px 48px rgba(0, 0, 0, 0.12);
                --shadow-glow: 0 0 20px rgba(168, 85, 247, 0.1);
            }
        }
        
        /* Manual Dark Mode Toggle Support */
        [data-theme="dark"] {
            --background-primary: #0f0f23;
            --background-secondary: #1a1a2e;
            --background-tertiary: #16213e;
            --surface: rgba(255, 255, 255, 0.05);
            --text-primary: #ffffff;
            --text-secondary: #a3a3a3;
        }
        
        [data-theme="light"] {
            --background-primary: #fafafa;
            --background-secondary: #f4f4f5;
            --surface: rgba(0, 0, 0, 0.02);
            --text-primary: #18181b;
            --text-secondary: #52525b;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: clamp(16px, 4vw, 32px);
            display: flex;
            flex-direction: column;
            gap: clamp(20px, 3vw, 30px);
        }
        
        /* Improved scrollbar styling */
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
            background-size: 400% 100%;
            animation: gradientShift 4s ease-in-out infinite;
        }
        
        .header::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            right: -50%;
            bottom: -50%;
            background: conic-gradient(from 0deg, transparent, var(--accent-color), transparent);
            opacity: 0.03;
            animation: rotate 20s linear infinite;
            pointer-events: none;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .header h1 {
            font-size: clamp(2rem, 5vw, 2.8rem);
            font-weight: 700;
            background: linear-gradient(45deg, var(--secondary-color), var(--primary-color), var(--accent-color), var(--success-color));
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease-in-out infinite;
            margin-bottom: 8px;
        }
        
        .header p {
            font-size: clamp(1rem, 2.5vw, 1.2rem);
            color: var(--text-secondary);
            margin-bottom: 16px;
            font-weight: 400;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: clamp(16px, 3vw, 24px);
        }
        
        /* Responsive grid adjustments */
        @media (min-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
        
        .stat-card {
            background: var(--surface-glass);
            backdrop-filter: blur(24px) saturate(180%);
            border-radius: var(--border-radius);
            padding: clamp(18px, 3vw, 28px);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary-color);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-8px);
            box-shadow: var(--shadow-hover);
            background: var(--surface-hover);
        }
        
        .stat-card:hover::before {
            transform: scaleX(1);
        }
        
        .stat-card-icon {
            font-size: 2rem;
            margin-bottom: 12px;
            display: block;
            opacity: 0.7;
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
        
        .stat-trend {
            font-size: 0.8rem;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .stat-trend.positive {
            color: var(--success-color);
        }
        
        .stat-trend.negative {
            color: var(--error-color);
        }
        
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
            display: flex;
            align-items: center;
            gap: 8px;
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
        
        .panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.01) 100%);
            border-radius: var(--border-radius);
            pointer-events: none;
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
        
        .token-list {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 8px;
        }
        
        .token-list:empty::after {
            content: 'No data available';
            display: block;
            text-align: center;
            color: var(--text-secondary);
            font-style: italic;
            padding: 40px 20px;
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
        
        .token-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.03), transparent);
            transform: translateX(-100%);
            transition: transform 0.6s ease;
        }
        
        .token-item:hover::before {
            transform: translateX(100%);
        }
        
        /* Panel controls */
        .panel-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        
        .filter-btn, .refresh-btn, .chart-btn {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: var(--border-radius-small);
            font-size: 0.85rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .filter-btn:hover, .refresh-btn:hover, .chart-btn:hover {
            background: var(--surface-hover);
            color: var(--text-primary);
            transform: translateY(-1px);
        }
        
        .filter-btn.active, .chart-btn.active {
            background: var(--primary-color);
            color: var(--background-primary);
            border-color: var(--primary-color);
        }
        
        /* Chart enhancements */
        .chart-panel {
            grid-column: 1 / -1;
        }
        
        .chart-controls {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            justify-content: center;
        }
        
        .chart-container {
            position: relative;
            border-radius: var(--border-radius-small);
            background: rgba(0, 0, 0, 0.1);
            padding: 16px;
        }
        
        .chart-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 16px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
        }
        
        .chart-stat {
            text-align: center;
        }
        
        .chart-stat-label {
            display: block;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }
        
        .chart-stat-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        /* Progress details */
        .progress-details {
            margin-top: 12px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .token-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        
        .token-symbol {
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--text-primary);
        }
        
        .token-score {
            background: var(--primary-color);
            color: var(--background-primary);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .token-address {
            font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 8px;
            background: rgba(0, 0, 0, 0.2);
            padding: 4px 8px;
            border-radius: 4px;
            word-break: break-all;
            border: 1px solid var(--border);
        }
        
        .token-metadata {
            display: flex;
            gap: 12px;
            margin-top: 8px;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        
        .token-metadata span {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .status-indicator {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 8px;
            position: relative;
        }
        
        .status-indicator::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
        }
        
        .status-running { 
            color: var(--primary-color); 
            animation: pulse 2s infinite;
        }
        
        .status-running::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--primary-color);
            opacity: 0.3;
            animation: ripple 2s infinite;
        }
        
        .status-idle { color: var(--text-secondary); }
        .status-error { 
            color: var(--error-color);
            animation: pulse 1s infinite;
        }
        
        @keyframes ripple {
            0% {
                transform: scale(0.5);
                opacity: 0.8;
            }
            100% {
                transform: scale(2);
                opacity: 0;
            }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .high-conviction {
            border-left-color: var(--secondary-color) !important;
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 107, 107, 0.05));
            position: relative;
        }
        
        .high-conviction::after {
            content: '🔥';
            position: absolute;
            top: 8px;
            right: 8px;
            font-size: 1.2rem;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-4px);
            }
            60% {
                transform: translateY(-2px);
            }
        }
        
        .cycle-chart {
            height: clamp(200px, 40vw, 300px);
            margin-top: 20px;
            border-radius: var(--border-radius-small);
            background: rgba(0, 0, 0, 0.1);
            padding: 8px;
        }
        
        /* Enhanced responsive design */
        @media (max-width: 768px) {
            .container {
                padding: 16px;
                gap: 20px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 16px;
            }
            
            .content-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .panel {
                padding: 20px;
            }
            
            .token-list {
                max-height: 300px;
            }
        }
        
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .stat-card {
                padding: 16px;
            }
            
            .header {
                padding: 20px;
            }
            
            .progress-section,
            .panel {
                padding: 16px;
            }
        }
        
        .loading {
            text-align: center;
            color: #4ecdc4;
            margin: 20px 0;
        }
        
        .timer {
            font-size: clamp(1.3rem, 3vw, 1.8rem);
            font-weight: 700;
            color: var(--primary-color);
            text-align: center;
            margin: 16px 0;
            font-variant-numeric: tabular-nums;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(78, 205, 196, 0.3);
        }
        
        /* Loading states */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            color: var(--primary-color);
            font-style: italic;
        }
        
        .loading::before {
            content: '';
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            margin-right: 12px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Token score styling */
        .token-score.high {
            background: var(--success-color);
        }
        
        .token-score.medium {
            background: var(--warning-color);
        }
        
        .token-score.low {
            background: var(--text-secondary);
        }
        
        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Focus styles for keyboard navigation */
        .stat-card:focus,
        .token-item:focus,
        .panel:focus,
        .filter-btn:focus,
        .refresh-btn:focus,
        .chart-btn:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --surface: rgba(255, 255, 255, 0.15);
                --border: rgba(255, 255, 255, 0.3);
            }
        }
        
        /* Tooltip system */
        [data-tooltip] {
            position: relative;
        }
        
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--background-primary);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: var(--border-radius-small);
            font-size: 0.8rem;
            white-space: nowrap;
            border: 1px solid var(--border);
            z-index: 1000;
            margin-bottom: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Virtuoso Gem Hunter</h1>
            <p>Real-time Solana Token Detection Dashboard</p>
            <div class="timer" id="timer">--:--:--</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="cycles-completed">0</div>
                <div class="stat-label">Cycles Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="tokens-analyzed">0</div>
                <div class="stat-label">Tokens Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="high-conviction">0</div>
                <div class="stat-label">High Conviction Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="api-calls">0</div>
                <div class="stat-label">API Calls Made</div>
            </div>
        </div>
        
        <div class="progress-section">
            <h3>Current Cycle Progress</h3>
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
                    // Optimization: Disable animations for better performance
                    animation: {
                        duration: 0
                    },
                    // Optimization: Reduce redraw frequency
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
        
        // Update timer with optimization
        let timerInterval = null;
        function updateTimer(startTime, estimatedCompletion) {
            if (!startTime) return;
            
            // Optimization: Clear existing timer to prevent memory leaks
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            
            timerInterval = setInterval(() => {
                const now = new Date().getTime();
                const start = new Date(startTime).getTime();
                const elapsed = now - start;
                
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
        
        // Socket event handlers
        socket.on('stats_update', function(data) {
            document.getElementById('cycles-completed').textContent = data.cycles_completed;
            document.getElementById('tokens-analyzed').textContent = data.total_tokens_analyzed;
            document.getElementById('high-conviction').textContent = data.high_conviction_found;
            document.getElementById('api-calls').textContent = data.api_calls_made;
            
            // Update status
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            
            statusIndicator.className = `status-indicator status-${data.status}`;
            statusText.textContent = data.current_token ? 
                `Analyzing: ${data.current_token.substring(0, 8)}...` : 
                data.status.charAt(0).toUpperCase() + data.status.slice(1);
            
            // Update progress
            const progress = data.current_cycle > 0 ? (data.current_cycle / 9) * 100 : 0;
            document.getElementById('cycle-progress').style.width = `${progress}%`;
            
            if (data.start_time && !document.getElementById('timer').dataset.started) {
                updateTimer(data.start_time, data.estimated_completion);
                document.getElementById('timer').dataset.started = 'true';
            }
        });
        
        socket.on('tokens_update', function(data) {
            // Update high conviction tokens with DOM optimization
            const highConvictionList = document.getElementById('high-conviction-list');
            if (data.high_conviction && data.high_conviction.length > 0) {
                // Optimization: Use DocumentFragment for efficient DOM updates
                const fragment = document.createDocumentFragment();
                data.high_conviction.forEach(token => {
                    const tokenDiv = document.createElement('div');
                    tokenDiv.className = 'token-item high-conviction';
                    tokenDiv.innerHTML = `
                        <strong>${token.symbol || 'Unknown'}</strong> - Score: ${token.score || 'N/A'}
                        <div class="token-address">${token.address}</div>
                    `;
                    fragment.appendChild(tokenDiv);
                });
                highConvictionList.innerHTML = '';
                highConvictionList.appendChild(fragment);
            } else {
                highConvictionList.innerHTML = '<div class="loading">No high conviction tokens found yet...</div>';
            }
            
            // Update recent tokens with DOM optimization
            const recentList = document.getElementById('recent-tokens-list');
            if (data.recent && data.recent.length > 0) {
                // Optimization: Use DocumentFragment for efficient DOM updates
                const fragment = document.createDocumentFragment();
                data.recent.forEach(token => {
                    const tokenDiv = document.createElement('div');
                    tokenDiv.className = 'token-item';
                    tokenDiv.innerHTML = `
                        <strong>${token.symbol || 'Unknown'}</strong> - Score: ${token.score || 'N/A'}
                        <div class="token-address">${token.address}</div>
                    `;
                    fragment.appendChild(tokenDiv);
                });
                recentList.innerHTML = '';
                recentList.appendChild(fragment);
            } else {
                recentList.innerHTML = '<div class="loading">Starting analysis...</div>';
            }
        });
        
        socket.on('cycle_complete', function(data) {
            if (cycleChart) {
                // Optimization: Limit chart data points to prevent memory bloat
                const maxPoints = 50;
                if (cycleChart.data.labels.length >= maxPoints) {
                    cycleChart.data.labels.shift();
                    cycleChart.data.datasets[0].data.shift();
                    cycleChart.data.datasets[1].data.shift();
                }
                
                cycleChart.data.labels.push(`Cycle ${data.cycle}`);
                cycleChart.data.datasets[0].data.push(data.tokens_analyzed);
                cycleChart.data.datasets[1].data.push(data.high_conviction_found);
                
                // Optimization: Use animation: false for better performance
                cycleChart.update('none');
            }
        });
        
        // Enhanced interactivity functions
        function refreshTokenData() {
            socket.emit('request_refresh');
            const btn = document.querySelector('.refresh-btn');
            if (btn) {
                btn.innerHTML = '<span style="animation: spin 1s linear infinite;">🔄</span> Refreshing...';
                setTimeout(() => {
                    btn.innerHTML = '<span>🔄</span> Refresh';
                }, 2000);
            }
        }
        
        function switchChartType(type) {
            document.querySelectorAll('.chart-btn').forEach(btn => btn.classList.remove('active'));
            const targetBtn = document.querySelector(`[data-chart="${type}"]`);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }
        }
        
        function filterTokens(filter) {
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            const targetBtn = document.querySelector(`[data-filter="${filter}"]`);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }
        }
        
        // Theme Management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Add a subtle animation
            document.body.style.transition = 'background 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            initChart();
            
            // Theme toggle event listener
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', toggleTheme);
            }
            
            // Add event listeners for interactive elements
            document.querySelectorAll('.chart-btn').forEach(btn => {
                btn.addEventListener('click', () => switchChartType(btn.dataset.chart));
            });
            
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', () => filterTokens(btn.dataset.filter));
            });
            
            // Add tooltips and enhanced interactions
            document.querySelectorAll('.stat-card').forEach(card => {
                card.addEventListener('click', () => {
                    card.style.transform = 'scale(0.98)';
                    setTimeout(() => {
                        card.style.transform = '';
                    }, 150);
                });
            });
            
            // Enhanced keyboard navigation
            document.addEventListener('keydown', function(e) {
                // Ctrl/Cmd + R for refresh
                if (e.key === 'r' || e.key === 'R') {
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        refreshTokenData();
                    }
                }
                // T for theme toggle
                if (e.key === 't' || e.key === 'T') {
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        toggleTheme();
                    }
                }
            });
            
            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                }
            });
        });
    </script>
</body>
</html>
        '''
    
    def start_detection(self, total_cycles: int = 9):
        """Start the detection process with dashboard updates"""
        self.stats['start_time'] = datetime.now().isoformat()
        self.stats['estimated_completion'] = (datetime.now() + timedelta(hours=3)).isoformat()
        self.stats['status'] = 'running'
        self.emit_update()
        
    def update_stats(self, **kwargs):
        """Update dashboard statistics"""
        self.stats.update(kwargs)
        self.stats['last_update'] = time.time()
        self.emit_update()
        
    def add_token(self, token_data: Dict[str, Any], is_high_conviction: bool = False):
        """Add a token to the dashboard with optimized updates"""
        self.recent_tokens.append(token_data)
        if len(self.recent_tokens) > self.MAX_RECENT_TOKENS:
            self.recent_tokens.pop(0)
            
        if is_high_conviction:
            self.high_conviction_tokens.append(token_data)
            
        # Optimization: Only emit if there are connected clients
        if hasattr(self.socketio, 'server') and self.socketio.server.manager.rooms:
            self.emit_tokens_update()
        
    def complete_cycle(self, cycle_num: int, tokens_analyzed: int, high_conviction_found: int):
        """Mark a cycle as complete with memory management"""
        cycle_data = {
            'cycle': cycle_num,
            'tokens_analyzed': tokens_analyzed,
            'high_conviction_found': high_conviction_found,
            'timestamp': datetime.now().isoformat()
        }
        self.cycle_history.append(cycle_data)
        
        # Optimization: Limit cycle history to prevent memory bloat
        if len(self.cycle_history) > self.MAX_CYCLE_HISTORY:
            self.cycle_history.pop(0)
        
        self.stats['cycles_completed'] = cycle_num
        self.stats['current_cycle'] = cycle_num
        
        self.socketio.emit('cycle_complete', cycle_data)
        self.emit_update()
        
    def emit_update(self):
        """Emit stats update with diff optimization"""
        # Optimization: Only broadcast if data actually changed
        if self.stats != self._last_broadcast_stats:
            self.socketio.emit('stats_update', self.stats)
            self._last_broadcast_stats = self.stats.copy()
        
    def emit_tokens_update(self):
        """Emit tokens update with diff optimization"""
        current_data = {
            'recent': self.recent_tokens[-10:],
            'high_conviction': self.high_conviction_tokens
        }
        
        # Optimization: Only broadcast if token data changed
        if current_data != self._last_broadcast_tokens:
            self.socketio.emit('tokens_update', current_data)
            self._last_broadcast_tokens = current_data.copy()
        
    def run_server(self):
        """Run the Flask server"""
        print(f"🌐 Starting Virtuoso Web Dashboard on http://localhost:{self.port}")
        print(f"🚀 Dashboard will auto-open in your browser...")
        
        # Auto-open browser
        threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{self.port}')).start()
        
        # Run server
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)

# Example usage for integration
if __name__ == "__main__":
    dashboard = VirtuosoWebDashboard(port=8080)
    
    # Example of how to integrate with detector
    dashboard.start_detection()
    dashboard.update_stats(current_token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    
    # Run the server
    dashboard.run_server()