#!/usr/bin/env python3
"""
WSOL Matrix Scheduler Service
Automatically refreshes WSOL availability matrix every 30-60 minutes
Monitors performance and provides health metrics
"""

import asyncio
import logging
import time
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil

class WSolMatrixScheduler:
    """Automated WSOL matrix refresh and monitoring service"""
    
    def __init__(self, refresh_interval_minutes: int = 45):
        self.refresh_interval = refresh_interval_minutes * 60  # Convert to seconds
        self.logger = logging.getLogger("WSolMatrixScheduler")
        self.scheduler_start_time = datetime.now()
        self.refresh_count = 0
        self.successful_refreshes = 0
        self.failed_refreshes = 0
        self.last_refresh_time = None
        self.last_matrix_file = None
        self.performance_metrics = {
            'refresh_times': [],
            'matrix_sizes': [],
            'coverage_rates': [],
            'error_count': 0
        }
        self.health_status = 'UNKNOWN'
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    async def start_scheduler(self):
        """Start the automated WSOL matrix refresh scheduler"""
        self.logger.info(f"🔄 Starting WSOL Matrix Scheduler (refresh every {self.refresh_interval/60:.0f} minutes)")
        
        # Initial refresh
        await self._refresh_matrix()
        
        # Schedule periodic refreshes
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self._refresh_matrix()
            except KeyboardInterrupt:
                self.logger.info("⏹️  Scheduler stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _refresh_matrix(self):
        """Execute WSOL matrix refresh"""
        refresh_start = time.time()
        self.refresh_count += 1
        
        self.logger.info(f"🔄 Starting WSOL matrix refresh #{self.refresh_count}")
        
        try:
            # Run the optimized WSOL matrix builder
            result = subprocess.run(
                ['python', 'optimized_wsol_matrix_builder.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            refresh_duration = time.time() - refresh_start
            
            if result.returncode == 0:
                self.successful_refreshes += 1
                self.last_refresh_time = datetime.now()
                
                # Analyze the new matrix file
                matrix_analysis = self._analyze_latest_matrix()
                
                # Update performance metrics
                self.performance_metrics['refresh_times'].append(refresh_duration)
                if matrix_analysis:
                    self.performance_metrics['matrix_sizes'].append(matrix_analysis['token_count'])
                    self.performance_metrics['coverage_rates'].append(matrix_analysis['overall_coverage'])
                
                # Keep only last 20 metrics
                for metric_list in self.performance_metrics.values():
                    if isinstance(metric_list, list) and len(metric_list) > 20:
                        metric_list[:] = metric_list[-20:]
                
                self.health_status = 'HEALTHY'
                
                self.logger.info(f"✅ Matrix refresh completed in {refresh_duration:.1f}s")
                if matrix_analysis:
                    self.logger.info(f"📊 Matrix: {matrix_analysis['token_count']} tokens, {matrix_analysis['overall_coverage']:.1f}% WSOL coverage")
                    
            else:
                self.failed_refreshes += 1
                self.performance_metrics['error_count'] += 1
                self.health_status = 'DEGRADED'
                
                self.logger.error(f"❌ Matrix refresh failed (exit code {result.returncode})")
                self.logger.error(f"STDERR: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.failed_refreshes += 1
            self.performance_metrics['error_count'] += 1
            self.health_status = 'DEGRADED'
            self.logger.error("❌ Matrix refresh timed out after 5 minutes")
            
        except Exception as e:
            self.failed_refreshes += 1
            self.performance_metrics['error_count'] += 1
            self.health_status = 'UNHEALTHY'
            self.logger.error(f"❌ Matrix refresh error: {e}")
    
    def _analyze_latest_matrix(self) -> Optional[Dict[str, Any]]:
        """Analyze the most recent WSOL matrix file"""
        try:
            import glob
            
            # Find the latest matrix file
            matrix_files = glob.glob("complete_wsol_matrix_*.json")
            if not matrix_files:
                return None
                
            latest_file = max(matrix_files, key=os.path.getmtime)
            self.last_matrix_file = latest_file
            
            # Load and analyze
            with open(latest_file, 'r') as f:
                matrix_data = json.load(f)
            
            matrix = matrix_data.get('matrix', {})
            token_count = len(matrix)
            
            if token_count == 0:
                return None
            
            # Calculate coverage statistics
            meteora_count = sum(1 for token in matrix.values() if token.get('meteora_available', False))
            orca_count = sum(1 for token in matrix.values() if token.get('orca_available', False))
            raydium_count = sum(1 for token in matrix.values() if token.get('raydium_available', False))
            jupiter_count = sum(1 for token in matrix.values() if token.get('jupiter_available', False))
            
            # Overall coverage (any WSOL availability)
            any_wsol_count = sum(1 for token in matrix.values() 
                               if any([token.get('meteora_available', False),
                                     token.get('orca_available', False),
                                     token.get('raydium_available', False),
                                     token.get('jupiter_available', False)]))
            
            overall_coverage = (any_wsol_count / token_count) * 100 if token_count > 0 else 0
            
            return {
                'token_count': token_count,
                'overall_coverage': overall_coverage,
                'dex_coverage': {
                    'meteora': (meteora_count / token_count) * 100,
                    'orca': (orca_count / token_count) * 100,
                    'raydium': (raydium_count / token_count) * 100,
                    'jupiter': (jupiter_count / token_count) * 100
                },
                'file_path': latest_file,
                'file_age_minutes': (time.time() - os.path.getmtime(latest_file)) / 60
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing matrix: {e}")
            return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        uptime = datetime.now() - self.scheduler_start_time
        
        # Calculate averages
        avg_refresh_time = sum(self.performance_metrics['refresh_times']) / len(self.performance_metrics['refresh_times']) if self.performance_metrics['refresh_times'] else 0
        avg_coverage = sum(self.performance_metrics['coverage_rates']) / len(self.performance_metrics['coverage_rates']) if self.performance_metrics['coverage_rates'] else 0
        
        success_rate = (self.successful_refreshes / self.refresh_count) * 100 if self.refresh_count > 0 else 0
        
        return {
            'scheduler_status': {
                'health': self.health_status,
                'uptime_hours': uptime.total_seconds() / 3600,
                'refresh_interval_minutes': self.refresh_interval / 60
            },
            'refresh_statistics': {
                'total_refreshes': self.refresh_count,
                'successful_refreshes': self.successful_refreshes,
                'failed_refreshes': self.failed_refreshes,
                'success_rate_percent': success_rate,
                'last_refresh': self.last_refresh_time.isoformat() if self.last_refresh_time else None
            },
            'performance_metrics': {
                'avg_refresh_time_seconds': avg_refresh_time,
                'avg_wsol_coverage_percent': avg_coverage,
                'error_count': self.performance_metrics['error_count'],
                'last_matrix_file': self.last_matrix_file
            },
            'system_health': {
                'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_percent': psutil.Process().cpu_percent()
            }
        }
    
    def get_health_status(self) -> str:
        """Get current health status"""
        if self.refresh_count == 0:
            return 'STARTING'
        
        # Check recent performance
        recent_failures = 0
        if self.refresh_count >= 3:
            recent_failures = min(3, self.failed_refreshes)
        
        if recent_failures == 0:
            return 'HEALTHY'
        elif recent_failures <= 1:
            return 'DEGRADED'
        else:
            return 'UNHEALTHY'
    
    def should_alert(self) -> bool:
        """Check if scheduler should send health alerts"""
        # Alert if more than 2 consecutive failures
        if self.failed_refreshes >= 2 and self.successful_refreshes == 0:
            return True
            
        # Alert if last refresh was more than 2x the interval ago
        if self.last_refresh_time:
            time_since_last = datetime.now() - self.last_refresh_time
            if time_since_last.total_seconds() > (self.refresh_interval * 2):
                return True
                
        return False

async def main():
    """Main scheduler execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WSOL Matrix Scheduler')
    parser.add_argument('--interval', type=int, default=45, 
                       help='Refresh interval in minutes (default: 45)')
    parser.add_argument('--status', action='store_true',
                       help='Show status and exit')
    
    args = parser.parse_args()
    
    scheduler = WSolMatrixScheduler(refresh_interval_minutes=args.interval)
    
    if args.status:
        # Show current status
        performance = scheduler.get_performance_summary()
        print("📊 WSOL Matrix Scheduler Status:")
        print(json.dumps(performance, indent=2, default=str))
        return
    
    # Start the scheduler
    try:
        await scheduler.start_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️  Scheduler stopped")
    finally:
        # Print final summary
        performance = scheduler.get_performance_summary()
        print("\n📊 Final Performance Summary:")
        print(json.dumps(performance, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main()) 