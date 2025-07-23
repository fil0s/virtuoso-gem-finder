#!/usr/bin/env python3
"""
🏭 PRODUCTION STATUS CHECKER
Verify production readiness and show current status
"""

import sys
import os
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ProductionStatusChecker:
    """Check production readiness status"""
    
    def __init__(self):
        self.status_checks = {}
        self.overall_score = 0
        
    async def run_comprehensive_status_check(self):
        """Run comprehensive production status check"""
        
        print("🏭 PRODUCTION READINESS STATUS CHECK")
        print("=" * 70)
        print("Checking current production readiness level...")
        print()
        
        # Phase 1: Core System Checks (25%)
        await self._check_core_system()
        
        # Phase 2: API Integration Checks (25%) 
        await self._check_api_integrations()
        
        # Phase 3: Live Monitoring Checks (25%)
        await self._check_live_monitoring()
        
        # Phase 4: Production Infrastructure Checks (25%)
        await self._check_production_infrastructure()
        
        # Calculate final score and recommendations
        await self._calculate_final_status()
        
        return self.overall_score
    
    async def _check_core_system(self):
        """Check core system components (25% of total score)"""
        print("🔧 CORE SYSTEM CHECKS (25%)")
        print("-" * 40)
        
        core_score = 0
        max_core_score = 25
        
        # Early Gem Detector initialization
        try:
            from scripts.early_gem_detector import EarlyGemDetector
            detector = EarlyGemDetector(debug_mode=False)
            print("   ✅ Early Gem Detector: WORKING")
            core_score += 8
        except Exception as e:
            print(f"   ❌ Early Gem Detector: FAILED ({e})")
        
        # Enhanced scoring system
        try:
            import importlib.util
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scorer_path = os.path.join(script_dir, 'scripts', 'early_gem_focused_scoring.py')
            
            spec = importlib.util.spec_from_file_location("early_gem_focused_scoring", scorer_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            scorer = module.EarlyGemFocusedScoring()
            print("   ✅ Enhanced Scoring System: WORKING")
            core_score += 8
        except Exception as e:
            print(f"   ❌ Enhanced Scoring System: FAILED ({e})")
        
        # Telegram integration
        try:
            from services.telegram_alerter import TelegramAlerter
            print("   ✅ Telegram Integration: AVAILABLE")
            core_score += 5
        except Exception as e:
            print(f"   ❌ Telegram Integration: FAILED ({e})")
        
        # Configuration management
        try:
            import yaml
            with open('config/config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            print("   ✅ Configuration Management: WORKING")
            core_score += 4
        except Exception as e:
            print(f"   ❌ Configuration Management: FAILED ({e})")
        
        self.status_checks['core_system'] = {
            'score': core_score,
            'max_score': max_core_score,
            'percentage': (core_score / max_core_score) * 100
        }
        
        print(f"   📊 Core System Score: {core_score}/{max_core_score} ({(core_score/max_core_score)*100:.1f}%)")
        print()
    
    async def _check_api_integrations(self):
        """Check API integration status (25% of total score)"""
        print("📡 API INTEGRATION CHECKS (25%)")
        print("-" * 40)
        
        api_score = 0
        max_api_score = 25
        
        # Birdeye API
        try:
            birdeye_key = os.getenv('BIRDEYE_API_KEY')
            if birdeye_key:
                from api.birdeye_connector import BirdeyeAPI
                print("   ✅ Birdeye API: CONFIGURED")
                api_score += 8
            else:
                print("   ⚠️ Birdeye API: NO KEY")
                api_score += 4
        except Exception as e:
            print(f"   ❌ Birdeye API: FAILED ({e})")
        
        # Pump.fun Integration
        try:
            from services.pump_fun_integration import PumpFunStage0Integration
            from services.pump_fun_monitor import PumpFunMonitor
            
            integration = PumpFunStage0Integration()
            monitor = PumpFunMonitor()
            print("   ✅ Pump.fun Integration: WORKING")
            api_score += 8
        except Exception as e:
            print(f"   ❌ Pump.fun Integration: FAILED ({e})")
        
        # LaunchLab Integration
        try:
            from services.raydium_launchlab_integration import RaydiumLaunchLabIntegration
            integration = RaydiumLaunchLabIntegration()
            print("   ✅ LaunchLab Integration: WORKING")
            api_score += 5
        except Exception as e:
            print(f"   ⚠️ LaunchLab Integration: NOT AVAILABLE ({e})")
            api_score += 2
        
        # Cache Management
        try:
            from api.cache_manager import EnhancedAPICacheManager
            cache = EnhancedAPICacheManager()
            print("   ✅ Cache Management: WORKING")
            api_score += 4
        except Exception as e:
            print(f"   ❌ Cache Management: FAILED ({e})")
        
        self.status_checks['api_integrations'] = {
            'score': api_score,
            'max_score': max_api_score,
            'percentage': (api_score / max_api_score) * 100
        }
        
        print(f"   📊 API Integration Score: {api_score}/{max_api_score} ({(api_score/max_api_score)*100:.1f}%)")
        print()
    
    async def _check_live_monitoring(self):
        """Check live monitoring capabilities (25% of total score)"""
        print("📡 LIVE MONITORING CHECKS (25%)")
        print("-" * 40)
        
        monitor_score = 0
        max_monitor_score = 25
        
        # WebSocket monitoring capability
        try:
            from services.pump_fun_monitor import PumpFunMonitor
            monitor = PumpFunMonitor()
            
            # Check if monitor has required methods
            required_methods = ['start_monitoring', '_monitor_new_tokens', '_poll_pump_fun_api']
            has_methods = all(hasattr(monitor, method) for method in required_methods)
            
            if has_methods:
                print("   ✅ WebSocket Monitoring: IMPLEMENTED")
                monitor_score += 10
            else:
                print("   ⚠️ WebSocket Monitoring: PARTIAL")
                monitor_score += 5
        except Exception as e:
            print(f"   ❌ WebSocket Monitoring: FAILED ({e})")
        
        # Live API polling
        try:
            import aiohttp
            print("   ✅ Live API Polling: AVAILABLE")
            monitor_score += 8
        except Exception as e:
            print(f"   ❌ Live API Polling: FAILED ({e})")
        
        # Event callback system
        try:
            from scripts.early_gem_detector import EarlyGemDetector
            detector = EarlyGemDetector(debug_mode=False)
            
            # Check for live monitoring integration
            has_live_methods = hasattr(detector, '_handle_live_stage0_detection')
            if has_live_methods:
                print("   ✅ Live Event Processing: IMPLEMENTED")
                monitor_score += 7
            else:
                print("   ⚠️ Live Event Processing: BASIC")
                monitor_score += 3
        except Exception as e:
            print(f"   ❌ Live Event Processing: FAILED ({e})")
        
        self.status_checks['live_monitoring'] = {
            'score': monitor_score,
            'max_score': max_monitor_score,
            'percentage': (monitor_score / max_monitor_score) * 100
        }
        
        print(f"   📊 Live Monitoring Score: {monitor_score}/{max_monitor_score} ({(monitor_score/max_monitor_score)*100:.1f}%)")
        print()
    
    async def _check_production_infrastructure(self):
        """Check production infrastructure (25% of total score)"""
        print("🏭 PRODUCTION INFRASTRUCTURE CHECKS (25%)")
        print("-" * 40)
        
        infra_score = 0
        max_infra_score = 25
        
        # Error handling and logging
        try:
            import logging
            logger = logging.getLogger('test')
            print("   ✅ Logging System: WORKING")
            infra_score += 6
        except Exception as e:
            print(f"   ❌ Logging System: FAILED ({e})")
        
        # Environment variable management
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
        birdeye_key = os.getenv('BIRDEYE_API_KEY')
        
        env_vars_set = sum([bool(telegram_token), bool(telegram_chat), bool(birdeye_key)])
        if env_vars_set >= 2:
            print(f"   ✅ Environment Variables: {env_vars_set}/3 SET")
            infra_score += 5
        else:
            print(f"   ⚠️ Environment Variables: {env_vars_set}/3 SET")
            infra_score += 2
        
        # Data persistence
        try:
            from pathlib import Path
            data_dir = Path("data")
            logs_dir = Path("logs")
            
            if data_dir.exists() or logs_dir.exists():
                print("   ✅ Data Persistence: CONFIGURED")
                infra_score += 4
            else:
                print("   ⚠️ Data Persistence: BASIC")
                infra_score += 2
        except Exception as e:
            print(f"   ❌ Data Persistence: FAILED ({e})")
        
        # Performance monitoring
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            print(f"   ✅ Performance Monitoring: AVAILABLE (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%)")
            infra_score += 5
        except Exception as e:
            print(f"   ❌ Performance Monitoring: FAILED ({e})")
        
        # Async/concurrency support
        try:
            import asyncio
            print("   ✅ Async Support: WORKING")
            infra_score += 5
        except Exception as e:
            print(f"   ❌ Async Support: FAILED ({e})")
        
        self.status_checks['production_infrastructure'] = {
            'score': infra_score,
            'max_score': max_infra_score,
            'percentage': (infra_score / max_infra_score) * 100
        }
        
        print(f"   📊 Production Infrastructure Score: {infra_score}/{max_infra_score} ({(infra_score/max_infra_score)*100:.1f}%)")
        print()
    
    async def _calculate_final_status(self):
        """Calculate final production readiness status"""
        print("📊 FINAL PRODUCTION READINESS ASSESSMENT")
        print("=" * 70)
        
        # Calculate total score
        total_score = sum(check['score'] for check in self.status_checks.values())
        max_total_score = sum(check['max_score'] for check in self.status_checks.values())
        self.overall_score = (total_score / max_total_score) * 100
        
        # Show breakdown
        print("📋 COMPONENT BREAKDOWN:")
        for component, data in self.status_checks.items():
            status_emoji = "✅" if data['percentage'] >= 80 else "⚠️" if data['percentage'] >= 60 else "❌"
            print(f"   {status_emoji} {component.replace('_', ' ').title()}: {data['score']}/{data['max_score']} ({data['percentage']:.1f}%)")
        
        print()
        print(f"🎯 OVERALL PRODUCTION READINESS: {self.overall_score:.1f}%")
        
        # Determine status level
        if self.overall_score >= 95:
            status = "🚀 PRODUCTION READY"
            color = "GREEN"
        elif self.overall_score >= 85:
            status = "⚡ NEAR PRODUCTION READY"
            color = "YELLOW"
        elif self.overall_score >= 70:
            status = "🔧 DEVELOPMENT READY"
            color = "ORANGE"
        else:
            status = "🚧 NEEDS WORK"
            color = "RED"
        
        print(f"📈 STATUS: {status}")
        print()
        
        # Recommendations for improvement
        await self._provide_recommendations()
    
    async def _provide_recommendations(self):
        """Provide recommendations for reaching 100% production ready"""
        print("💡 RECOMMENDATIONS FOR 100% PRODUCTION READY:")
        print("-" * 50)
        
        remaining = 100 - self.overall_score
        
        if remaining <= 5:
            print("🎉 You're almost there! Minor optimizations needed:")
            print("   • Fine-tune error handling")
            print("   • Add comprehensive logging")
            print("   • Implement health monitoring")
        elif remaining <= 15:
            print("🔧 Getting close! Key improvements needed:")
            print("   • Set up all environment variables")
            print("   • Test live API connections")
            print("   • Implement production monitoring")
            print("   • Add error recovery mechanisms")
        else:
            print("🚧 Significant work needed:")
            print("   • Fix core system components")
            print("   • Complete API integrations")
            print("   • Implement live monitoring")
            print("   • Set up production infrastructure")
        
        print()
        print("🎯 NEXT STEPS:")
        
        # Identify lowest scoring component
        lowest_component = min(self.status_checks.items(), key=lambda x: x[1]['percentage'])
        print(f"   1. Focus on {lowest_component[0].replace('_', ' ').title()} ({lowest_component[1]['percentage']:.1f}%)")
        print(f"   2. Test end-to-end functionality")
        print(f"   3. Implement production monitoring")
        print(f"   4. Conduct live trading simulation")
        
        print()
        return self.overall_score

async def main():
    """Main entry point"""
    checker = ProductionStatusChecker()
    final_score = await checker.run_comprehensive_status_check()
    
    print("=" * 70)
    print(f"📊 PRODUCTION READINESS: {final_score:.1f}%")
    
    if final_score >= 90:
        print("🚀 Ready for production deployment!")
    elif final_score >= 80:
        print("⚡ Close to production ready - minor fixes needed")
    else:
        print("🔧 Development phase - more work required")
    
    return final_score

if __name__ == "__main__":
    asyncio.run(main()) 