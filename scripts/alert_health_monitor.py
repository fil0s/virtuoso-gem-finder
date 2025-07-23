#!/usr/bin/env python3
"""
Alert Health Monitor

Monitors the health of the alerting system and provides detailed statistics.
Can be run standalone or integrated into the main system.
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.enhanced_telegram_alerter import EnhancedTelegramAlerter
from core.config_manager import ConfigManager
from utils.env_loader import load_environment

class AlertHealthMonitor:
    """Monitor alert system health and generate reports"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Load environment
        load_environment()
        
        # Initialize enhanced alerter for testing
        telegram_config = self.config.get('TELEGRAM', {})
        if telegram_config.get('enabled', False):
            import os
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if bot_token and chat_id:
                self.alerter = EnhancedTelegramAlerter(bot_token, chat_id, telegram_config)
            else:
                self.alerter = None
        else:
            self.alerter = None
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "unknown",
            "telegram_config": self._check_telegram_config(),
            "alerter_stats": None,
            "failed_alerts": self._analyze_failed_alerts(),
            "recommendations": []
        }
        
        # Get alerter statistics if available
        if self.alerter:
            report["alerter_stats"] = self.alerter.get_health_status()
            
            # Test connectivity
            connectivity_test = self._test_connectivity()
            report["connectivity_test"] = connectivity_test
            
            # Determine overall system status
            if connectivity_test["success"] and report["alerter_stats"]["success_rate_percent"] >= 90:
                report["system_status"] = "healthy"
            elif connectivity_test["success"] and report["alerter_stats"]["success_rate_percent"] >= 70:
                report["system_status"] = "warning"
            else:
                report["system_status"] = "critical"
        else:
            report["system_status"] = "not_configured"
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _check_telegram_config(self) -> Dict:
        """Check Telegram configuration"""
        import os
        
        telegram_config = self.config.get('TELEGRAM', {})
        
        return {
            "enabled": telegram_config.get('enabled', False),
            "bot_token_present": bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            "chat_id_present": bool(os.getenv('TELEGRAM_CHAT_ID')),
            "max_alerts_per_hour": telegram_config.get('max_alerts_per_hour', 10),
            "alert_format": telegram_config.get('alert_format', 'detailed'),
            "cooldown_minutes": telegram_config.get('cooldown_minutes', 30)
        }
    
    def _test_connectivity(self) -> Dict:
        """Test Telegram connectivity"""
        if not self.alerter:
            return {"success": False, "error": "Alerter not configured"}
        
        try:
            success = self.alerter.send_test_message("🔧 Health check test from Alert Monitor")
            return {
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "error": None if success else "Test message failed"
            }
        except Exception as e:
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _analyze_failed_alerts(self) -> Dict:
        """Analyze failed alerts log"""
        failed_alerts_path = Path("data/failed_alerts.json")
        
        if not failed_alerts_path.exists():
            return {
                "total_failed": 0,
                "recent_failures": 0,
                "common_errors": [],
                "analysis": "No failed alerts log found"
            }
        
        try:
            with open(failed_alerts_path, 'r') as f:
                failed_alerts = json.load(f)
            
            # Analyze recent failures (last 24 hours)
            recent_cutoff = time.time() - (24 * 60 * 60)
            recent_failures = [alert for alert in failed_alerts if alert["timestamp"] > recent_cutoff]
            
            # Count error types
            error_counts = {}
            for alert in failed_alerts:
                for attempt in alert.get("attempts", []):
                    error = attempt.get("error", "Unknown error")
                    error_counts[error] = error_counts.get(error, 0) + 1
            
            # Get most common errors
            common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "total_failed": len(failed_alerts),
                "recent_failures": len(recent_failures),
                "common_errors": [{"error": error, "count": count} for error, count in common_errors],
                "analysis": f"Found {len(failed_alerts)} failed alerts total, {len(recent_failures)} in last 24h"
            }
            
        except Exception as e:
            return {
                "total_failed": 0,
                "recent_failures": 0,
                "common_errors": [],
                "analysis": f"Error reading failed alerts: {e}"
            }
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on health report"""
        recommendations = []
        
        # Check configuration issues
        if not report["telegram_config"]["enabled"]:
            recommendations.append("⚠️ Telegram alerts are disabled in configuration")
        
        if not report["telegram_config"]["bot_token_present"]:
            recommendations.append("❌ TELEGRAM_BOT_TOKEN environment variable is missing")
        
        if not report["telegram_config"]["chat_id_present"]:
            recommendations.append("❌ TELEGRAM_CHAT_ID environment variable is missing")
        
        # Check connectivity
        connectivity = report.get("connectivity_test", {})
        if not connectivity.get("success", False):
            recommendations.append(f"🔌 Telegram connectivity test failed: {connectivity.get('error', 'Unknown error')}")
        
        # Check success rates
        stats = report.get("alerter_stats", {})
        if stats:
            success_rate = stats.get("success_rate_percent", 0)
            recent_rate = stats.get("recent_success_rate_percent", 0)
            
            if success_rate < 70:
                recommendations.append(f"📉 Low overall success rate: {success_rate}% - investigate common errors")
            
            if recent_rate < 90 and recent_rate < success_rate:
                recommendations.append(f"📈 Recent success rate declining: {recent_rate}% vs {success_rate}% overall")
            
            if stats.get("html_parse_errors", 0) > 0:
                recommendations.append(f"🔧 HTML parsing errors detected: {stats['html_parse_errors']} - review message formatting")
            
            if stats.get("rate_limit_hits", 0) > 0:
                recommendations.append(f"⏰ Rate limit hits: {stats['rate_limit_hits']} - consider reducing alert frequency")
        
        # Check failed alerts
        failed_alerts = report.get("failed_alerts", {})
        if failed_alerts.get("recent_failures", 0) > 5:
            recommendations.append(f"⚠️ High recent failure count: {failed_alerts['recent_failures']} in last 24h")
        
        # Check common errors
        common_errors = failed_alerts.get("common_errors", [])
        if common_errors:
            top_error = common_errors[0]
            recommendations.append(f"🔍 Most common error: {top_error['error']} ({top_error['count']} occurrences)")
        
        if not recommendations:
            recommendations.append("✅ Alert system appears healthy - no issues detected")
        
        return recommendations
    
    def print_health_report(self):
        """Print formatted health report to console"""
        report = self.generate_health_report()
        
        print("🏥 ALERT SYSTEM HEALTH REPORT")
        print("=" * 50)
        print(f"📅 Timestamp: {report['timestamp']}")
        print(f"🎯 System Status: {report['system_status'].upper()}")
        
        print("\n📱 TELEGRAM CONFIGURATION")
        print("-" * 30)
        config = report["telegram_config"]
        print(f"Enabled: {config['enabled']}")
        print(f"Bot Token: {'✅' if config['bot_token_present'] else '❌'}")
        print(f"Chat ID: {'✅' if config['chat_id_present'] else '❌'}")
        print(f"Max Alerts/Hour: {config['max_alerts_per_hour']}")
        print(f"Cooldown: {config['cooldown_minutes']} minutes")
        
        # Connectivity test
        if "connectivity_test" in report:
            print("\n🔌 CONNECTIVITY TEST")
            print("-" * 20)
            test = report["connectivity_test"]
            print(f"Status: {'✅ SUCCESS' if test['success'] else '❌ FAILED'}")
            if test.get('error'):
                print(f"Error: {test['error']}")
        
        # Alerter statistics
        if report["alerter_stats"]:
            print("\n📊 ALERTER STATISTICS")
            print("-" * 25)
            stats = report["alerter_stats"]
            print(f"Total Attempts: {stats['total_attempts']}")
            print(f"Successful Sends: {stats['successful_sends']}")
            print(f"Failed Sends: {stats['failed_sends']}")
            print(f"Success Rate: {stats['success_rate_percent']}%")
            print(f"Recent Success Rate: {stats['recent_success_rate_percent']}%")
            print(f"Retry Attempts: {stats['retry_attempts']}")
            print(f"HTML Parse Errors: {stats['html_parse_errors']}")
            print(f"Rate Limit Hits: {stats['rate_limit_hits']}")
            
            if stats['last_success']:
                print(f"Last Success: {stats['last_success']}")
            if stats['last_failure']:
                print(f"Last Failure: {stats['last_failure']}")
        
        # Failed alerts analysis
        failed = report["failed_alerts"]
        if failed["total_failed"] > 0:
            print("\n⚠️ FAILED ALERTS ANALYSIS")
            print("-" * 28)
            print(f"Total Failed: {failed['total_failed']}")
            print(f"Recent Failures (24h): {failed['recent_failures']}")
            
            if failed["common_errors"]:
                print("\\nCommon Errors:")
                for error_info in failed["common_errors"]:
                    print(f"  • {error_info['error']}: {error_info['count']} times")
        
        # Recommendations
        print("\\n💡 RECOMMENDATIONS")
        print("-" * 20)
        for rec in report["recommendations"]:
            print(f"  {rec}")
        
        print("\\n" + "=" * 50)

def main():
    """Main function"""
    monitor = AlertHealthMonitor()
    monitor.print_health_report()

if __name__ == "__main__":
    main()