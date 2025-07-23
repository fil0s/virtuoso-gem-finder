#!/usr/bin/env python3
"""
Alert Threshold Testing Tool

Test different alert thresholds to find optimal settings for your trading strategy.
Analyzes historical data to see how different thresholds would have performed.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager
from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics
from services.logger_setup import LoggerSetup

class ThresholdTestingTool:
    """Test alert thresholds against historical data"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger_setup = LoggerSetup('ThresholdTester')
        self.logger = self.logger_setup.logger
        
        # Load historical token data
        self.historical_data = self._load_historical_data()
        
    def _load_historical_data(self) -> List[Dict]:
        """Load historical token registry data"""
        data_dir = Path("data")
        token_registries = list(data_dir.glob("token_registry_*.json"))
        
        all_tokens = []
        
        for registry_file in sorted(token_registries)[-10:]:  # Last 10 sessions
            try:
                with open(registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                # Extract tokens from all scans
                for scan_key, scan_data in registry_data.get("all_tokens_by_scan", {}).items():
                    if isinstance(scan_data, list):
                        for token in scan_data:
                            if isinstance(token, dict) and 'score' in token:
                                all_tokens.append(token)
                
            except Exception as e:
                self.logger.warning(f"Could not load {registry_file}: {e}")
        
        self.logger.info(f"Loaded {len(all_tokens)} historical tokens for analysis")
        return all_tokens
    
    def test_threshold_range(self, min_threshold: float = 20.0, max_threshold: float = 80.0, step: float = 5.0) -> Dict:
        """Test a range of thresholds and analyze performance"""
        
        results = {
            "test_parameters": {
                "min_threshold": min_threshold,
                "max_threshold": max_threshold,
                "step": step,
                "total_tokens": len(self.historical_data)
            },
            "threshold_results": [],
            "recommendations": []
        }
        
        print(f"🧪 Testing thresholds from {min_threshold} to {max_threshold} (step: {step})")
        print(f"📊 Analyzing {len(self.historical_data)} historical tokens")
        print("-" * 50)
        
        # Test each threshold
        threshold = min_threshold
        while threshold <= max_threshold:
            result = self._test_single_threshold(threshold)
            results["threshold_results"].append(result)
            
            # Print progress
            alert_rate = result["alert_rate_percent"]
            avg_score = result["average_alerted_score"]
            quality_score = result["quality_metrics"]["overall_quality"]
            
            print(f"Threshold {threshold:4.1f}: {result['alerts_triggered']:3d} alerts ({alert_rate:4.1f}%) | Avg Score: {avg_score:4.1f} | Quality: {quality_score:4.1f}")
            
            threshold += step
        
        # Generate recommendations
        results["recommendations"] = self._generate_threshold_recommendations(results["threshold_results"])
        
        return results
    
    def _test_single_threshold(self, threshold: float) -> Dict:
        """Test a single threshold value"""
        
        alerted_tokens = []
        high_quality_alerts = 0
        medium_quality_alerts = 0
        low_quality_alerts = 0
        
        for token in self.historical_data:
            score = token.get('score', 0)
            
            # Check if token would trigger alert
            if score >= threshold:
                alerted_tokens.append(token)
                
                # Categorize quality based on multiple factors
                quality = self._assess_token_quality(token)
                if quality >= 80:
                    high_quality_alerts += 1
                elif quality >= 60:
                    medium_quality_alerts += 1
                else:
                    low_quality_alerts += 1
        
        # Calculate metrics
        total_tokens = len(self.historical_data)
        alerts_triggered = len(alerted_tokens)
        alert_rate = (alerts_triggered / total_tokens * 100) if total_tokens > 0 else 0
        
        avg_score = statistics.mean([t.get('score', 0) for t in alerted_tokens]) if alerted_tokens else 0
        
        # Quality distribution
        quality_metrics = {
            "high_quality_count": high_quality_alerts,
            "medium_quality_count": medium_quality_alerts,
            "low_quality_count": low_quality_alerts,
            "high_quality_percent": (high_quality_alerts / alerts_triggered * 100) if alerts_triggered > 0 else 0,
            "overall_quality": self._calculate_overall_quality_score(high_quality_alerts, medium_quality_alerts, low_quality_alerts)
        }
        
        return {
            "threshold": threshold,
            "alerts_triggered": alerts_triggered,
            "alert_rate_percent": round(alert_rate, 1),
            "average_alerted_score": round(avg_score, 1),
            "quality_metrics": quality_metrics,
            "sample_tokens": alerted_tokens[:3]  # First 3 for review
        }
    
    def _assess_token_quality(self, token: Dict) -> float:
        """Assess token quality based on multiple factors"""
        quality_score = 0
        
        # Base score contributes 40%
        base_score = token.get('score', 0)
        quality_score += (base_score / 100) * 40
        
        # Market cap assessment (20%)
        market_cap = token.get('market_cap', 0)
        if market_cap > 10_000_000:
            quality_score += 20  # Established projects
        elif market_cap > 1_000_000:
            quality_score += 15  # Medium projects
        elif market_cap > 100_000:
            quality_score += 10  # Small projects
        else:
            quality_score += 5   # Micro projects
        
        # Liquidity assessment (20%)
        liquidity = token.get('liquidity', 0)
        if liquidity > 1_000_000:
            quality_score += 20  # High liquidity
        elif liquidity > 500_000:
            quality_score += 15  # Good liquidity
        elif liquidity > 100_000:
            quality_score += 10  # Moderate liquidity
        else:
            quality_score += 5   # Low liquidity
        
        # Platform diversity (10%)
        platforms = token.get('platforms', [])
        platform_count = len(platforms) if platforms else 0
        if platform_count >= 4:
            quality_score += 10
        elif platform_count >= 3:
            quality_score += 7
        elif platform_count >= 2:
            quality_score += 5
        else:
            quality_score += 2
        
        # Volume assessment (10%)
        volume_24h = token.get('volume_24h', 0)
        if volume_24h > 1_000_000:
            quality_score += 10
        elif volume_24h > 500_000:
            quality_score += 7
        elif volume_24h > 100_000:
            quality_score += 5
        else:
            quality_score += 2
        
        return min(quality_score, 100)  # Cap at 100
    
    def _calculate_overall_quality_score(self, high: int, medium: int, low: int) -> float:
        """Calculate overall quality score for a threshold"""
        total = high + medium + low
        if total == 0:
            return 0
        
        # Weighted score: high=3, medium=2, low=1
        weighted_score = (high * 3 + medium * 2 + low * 1) / (total * 3) * 100
        return round(weighted_score, 1)
    
    def _generate_threshold_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations based on threshold testing"""
        recommendations = []
        
        if not results:
            return ["❌ No results to analyze"]
        
        # Find optimal thresholds for different strategies
        conservative_threshold = self._find_optimal_threshold(results, strategy="conservative")
        balanced_threshold = self._find_optimal_threshold(results, strategy="balanced")
        aggressive_threshold = self._find_optimal_threshold(results, strategy="aggressive")
        
        recommendations.extend([
            f"🛡️ Conservative (high quality): {conservative_threshold['threshold']} (Quality: {conservative_threshold['quality_metrics']['overall_quality']}%)",
            f"⚖️ Balanced (moderate alerts): {balanced_threshold['threshold']} (Quality: {balanced_threshold['quality_metrics']['overall_quality']}%)",
            f"🚀 Aggressive (more alerts): {aggressive_threshold['threshold']} (Quality: {aggressive_threshold['quality_metrics']['overall_quality']}%)"
        ])
        
        # Current threshold analysis
        current_threshold = self.config.get("ANALYSIS", {}).get("alert_score_threshold", 35.0)
        current_result = next((r for r in results if r["threshold"] == current_threshold), None)
        
        if current_result:
            recommendations.append(f"📊 Current threshold ({current_threshold}): {current_result['alerts_triggered']} alerts, {current_result['quality_metrics']['overall_quality']}% quality")
        
        # Quality insights
        high_quality_thresholds = [r for r in results if r["quality_metrics"]["overall_quality"] >= 80]
        if high_quality_thresholds:
            best_quality = max(high_quality_thresholds, key=lambda x: x["quality_metrics"]["overall_quality"])
            recommendations.append(f"💎 Highest quality alerts at threshold: {best_quality['threshold']} ({best_quality['quality_metrics']['overall_quality']}% quality)")
        
        return recommendations
    
    def _find_optimal_threshold(self, results: List[Dict], strategy: str) -> Dict:
        """Find optimal threshold for different strategies"""
        
        if strategy == "conservative":
            # Prioritize quality over quantity
            viable_results = [r for r in results if r["quality_metrics"]["overall_quality"] >= 70]
            if viable_results:
                return max(viable_results, key=lambda x: x["quality_metrics"]["overall_quality"])
        
        elif strategy == "balanced":
            # Balance between quality and alert frequency
            viable_results = [r for r in results if 5 <= r["alert_rate_percent"] <= 20]
            if viable_results:
                return max(viable_results, key=lambda x: x["quality_metrics"]["overall_quality"])
        
        elif strategy == "aggressive":
            # More alerts, but still maintain minimum quality
            viable_results = [r for r in results if r["quality_metrics"]["overall_quality"] >= 50]
            if viable_results:
                return max(viable_results, key=lambda x: x["alerts_triggered"])
        
        # Fallback to best overall result
        return max(results, key=lambda x: x["quality_metrics"]["overall_quality"])
    
    def test_current_configuration(self) -> Dict:
        """Test the current alert configuration"""
        
        current_config = self.config.get("ANALYSIS", {})
        alert_threshold = current_config.get("alert_score_threshold", 35.0)
        high_conviction_threshold = current_config.get("scoring", {}).get("cross_platform", {}).get("high_conviction_threshold", 44.5)
        
        print(f"🔍 Testing Current Configuration")
        print(f"Alert Threshold: {alert_threshold}")
        print(f"High Conviction Threshold: {high_conviction_threshold}")
        print("-" * 40)
        
        alert_result = self._test_single_threshold(alert_threshold)
        conviction_result = self._test_single_threshold(high_conviction_threshold)
        
        return {
            "alert_threshold_result": alert_result,
            "high_conviction_result": conviction_result,
            "configuration": {
                "alert_threshold": alert_threshold,
                "high_conviction_threshold": high_conviction_threshold
            }
        }
    
    def send_test_alert(self, threshold: float) -> bool:
        """Send a test alert using specified threshold"""
        
        # Find a token that would trigger at this threshold
        test_token = None
        for token in self.historical_data:
            if token.get('score', 0) >= threshold:
                test_token = token
                break
        
        if not test_token:
            print(f"❌ No historical tokens found that would trigger at threshold {threshold}")
            return False
        
        # Set up Telegram alerter
        telegram_config = self.config.get('TELEGRAM', {})
        if not telegram_config.get('enabled', False):
            print("❌ Telegram alerts are disabled in configuration")
            return False
        
        import os
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not found in environment")
            return False
        
        try:
            alerter = TelegramAlerter(bot_token, chat_id, telegram_config, self.logger_setup)
            
            # Create test metrics
            test_metrics = MinimalTokenMetrics(
                symbol=test_token.get('symbol', 'TEST'),
                address=test_token.get('address', 'TestAddress123'),
                price=test_token.get('price', 0.001),
                name=test_token.get('name', 'Test Token'),
                market_cap=test_token.get('market_cap', 0),
                liquidity=test_token.get('liquidity', 0),
                volume_24h=test_token.get('volume_24h', 0),
                score=test_token.get('score', 0)
            )
            
            # Send test alert
            success = alerter.send_gem_alert(
                test_metrics, 
                test_token.get('score', 0),
                scan_id=f"threshold_test_{threshold}"
            )
            
            if success:
                print(f"✅ Test alert sent for threshold {threshold}")
                print(f"   Token: {test_metrics.symbol} (Score: {test_token.get('score', 0)})")
                return True
            else:
                print(f"❌ Failed to send test alert")
                return False
                
        except Exception as e:
            print(f"❌ Error sending test alert: {e}")
            return False

def main():
    """Main function"""
    tool = ThresholdTestingTool()
    
    print("🧪 Alert Threshold Testing Tool")
    print("Choose an action:")
    print("1. Test current configuration")
    print("2. Test threshold range")
    print("3. Send test alert")
    print("4. Quick optimization scan")
    
    choice = input("\\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        results = tool.test_current_configuration()
        print("\\n📊 Current Configuration Results:")
        print(f"Alert Threshold ({results['configuration']['alert_threshold']}): {results['alert_threshold_result']['alerts_triggered']} alerts")
        print(f"High Conviction ({results['configuration']['high_conviction_threshold']}): {results['high_conviction_result']['alerts_triggered']} alerts")
        
    elif choice == "2":
        min_thresh = float(input("Min threshold (default 20): ") or "20")
        max_thresh = float(input("Max threshold (default 80): ") or "80")
        step = float(input("Step size (default 5): ") or "5")
        
        results = tool.test_threshold_range(min_thresh, max_thresh, step)
        
        print("\\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"  {rec}")
            
    elif choice == "3":
        threshold = float(input("Enter threshold to test: "))
        tool.send_test_alert(threshold)
        
    elif choice == "4":
        print("\\n🚀 Quick Optimization Scan (25-60 range)")
        results = tool.test_threshold_range(25, 60, 2.5)
        
        print("\\n🎯 Top Recommendations:")
        for rec in results["recommendations"][:3]:
            print(f"  {rec}")

if __name__ == "__main__":
    main()