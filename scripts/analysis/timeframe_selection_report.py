#!/usr/bin/env python
"""
Timeframe Selection Analysis Report Generator

This script analyzes the log files from a monitor run and generates a report
on how effectively the enhanced timeframe selection worked with tokens of different ages.
"""

import os
import sys
import re
import json
import argparse
from collections import defaultdict
from datetime import datetime
import logging

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TimeframeReport")

class TimeframeAnalyzer:
    """Analyzes monitor logs to evaluate timeframe selection performance"""
    
    def __init__(self, log_file):
        self.log_file = log_file
        self.tokens = {}
        self.timeframe_stats = defaultdict(lambda: {'success': 0, 'failure': 0})
        self.age_category_stats = defaultdict(lambda: {'success': 0, 'failure': 0})
        self.fallback_usage = defaultdict(int)
        
        # Regular expressions for log pattern matching
        self.token_age_pattern = re.compile(r"Token (\w+) age: ([\d.]+) days, category: (\w+)")
        self.timeframe_pattern = re.compile(r"Selected timeframe: (\w+)")
        self.ohlcv_success_pattern = re.compile(r"Successfully fetched (\d+) OHLCV candles using (\w+)")
        self.ohlcv_failure_pattern = re.compile(r"(Failed|No data available) .* timeframe (\w+)")
        self.fallback_pattern = re.compile(r"Trying fallback timeframe (\w+)")
        
    def analyze_logs(self):
        """Process the log file and extract timeframe selection data"""
        logger.info(f"Analyzing log file: {self.log_file}")
        
        if not os.path.exists(self.log_file):
            logger.error(f"Log file not found: {self.log_file}")
            return
            
        with open(self.log_file, 'r') as f:
            current_token = None
            current_age = None
            current_category = None
            
            for line in f:
                # Extract token age information
                age_match = self.token_age_pattern.search(line)
                if age_match:
                    current_token = age_match.group(1)
                    current_age = float(age_match.group(2))
                    current_category = age_match.group(3)
                    
                    # Initialize token data
                    if current_token not in self.tokens:
                        self.tokens[current_token] = {
                            'address': current_token,
                            'age_days': current_age,
                            'category': current_category,
                            'timeframes': [],
                            'fallbacks_used': [],
                            'success': False
                        }
                
                # Track selected timeframe
                timeframe_match = self.timeframe_pattern.search(line)
                if timeframe_match and current_token:
                    selected_timeframe = timeframe_match.group(1)
                    self.tokens[current_token]['timeframes'].append(selected_timeframe)
                
                # Track fallback timeframes
                fallback_match = self.fallback_pattern.search(line)
                if fallback_match and current_token:
                    fallback_tf = fallback_match.group(1)
                    self.tokens[current_token]['fallbacks_used'].append(fallback_tf)
                    self.fallback_usage[fallback_tf] += 1
                
                # Track OHLCV success
                success_match = self.ohlcv_success_pattern.search(line)
                if success_match and current_token:
                    candle_count = int(success_match.group(1))
                    used_timeframe = success_match.group(2)
                    
                    self.tokens[current_token]['success'] = True
                    self.tokens[current_token]['candle_count'] = candle_count
                    self.tokens[current_token]['successful_timeframe'] = used_timeframe
                    
                    # Update stats
                    self.timeframe_stats[used_timeframe]['success'] += 1
                    self.age_category_stats[current_category]['success'] += 1
                
                # Track OHLCV failures
                failure_match = self.ohlcv_failure_pattern.search(line)
                if failure_match and current_token:
                    failed_timeframe = failure_match.group(2)
                    
                    # Only count failures if we don't already have a success
                    if not self.tokens[current_token].get('success', False):
                        self.timeframe_stats[failed_timeframe]['failure'] += 1
        
        # Calculate final stats for tokens that had no success
        for token_data in self.tokens.values():
            if not token_data.get('success', False):
                self.age_category_stats[token_data['category']]['failure'] += 1
                
        logger.info(f"Analysis complete. Processed {len(self.tokens)} tokens.")
    
    def generate_report(self):
        """Generate a comprehensive report on timeframe selection effectiveness"""
        
        # Calculate success rates
        timeframe_success_rates = {}
        for tf, stats in self.timeframe_stats.items():
            total = stats['success'] + stats['failure']
            if total > 0:
                success_rate = (stats['success'] / total) * 100
            else:
                success_rate = 0
            timeframe_success_rates[tf] = {
                'success_count': stats['success'],
                'failure_count': stats['failure'],
                'total': total,
                'success_rate': success_rate
            }
            
        age_category_success_rates = {}
        for category, stats in self.age_category_stats.items():
            total = stats['success'] + stats['failure']
            if total > 0:
                success_rate = (stats['success'] / total) * 100
            else:
                success_rate = 0
            age_category_success_rates[category] = {
                'success_count': stats['success'],
                'failure_count': stats['failure'],
                'total': total,
                'success_rate': success_rate
            }
            
        # Overall stats
        success_tokens = sum(1 for t in self.tokens.values() if t.get('success', False))
        total_tokens = len(self.tokens)
        overall_success_rate = (success_tokens / total_tokens) * 100 if total_tokens > 0 else 0
        
        # Fallback usage effectiveness
        fallback_effectiveness = {}
        for token_data in self.tokens.values():
            if token_data.get('success', False) and token_data.get('fallbacks_used'):
                successful_tf = token_data.get('successful_timeframe')
                if successful_tf in token_data.get('fallbacks_used', []):
                    # This was a successful fallback
                    if successful_tf not in fallback_effectiveness:
                        fallback_effectiveness[successful_tf] = {
                            'attempts': 0,
                            'successes': 0
                        }
                    fallback_effectiveness[successful_tf]['successes'] += 1
        
        # Update with attempts
        for tf, count in self.fallback_usage.items():
            if tf not in fallback_effectiveness:
                fallback_effectiveness[tf] = {
                    'attempts': count,
                    'successes': 0
                }
            else:
                fallback_effectiveness[tf]['attempts'] = count
                
        # Calculate success rates for fallbacks
        for tf, stats in fallback_effectiveness.items():
            if stats['attempts'] > 0:
                stats['success_rate'] = (stats['successes'] / stats['attempts']) * 100
            else:
                stats['success_rate'] = 0
        
        # Compile full report
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'log_file': self.log_file,
            'overall_stats': {
                'total_tokens': total_tokens,
                'successful_tokens': success_tokens,
                'failed_tokens': total_tokens - success_tokens,
                'overall_success_rate': overall_success_rate
            },
            'timeframe_stats': timeframe_success_rates,
            'age_category_stats': age_category_success_rates,
            'fallback_effectiveness': fallback_effectiveness,
            'tokens': self.tokens
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Generate timeframe selection analysis report')
    parser.add_argument('--log-file', type=str, required=True, help='Path to the monitor log file')
    parser.add_argument('--output', type=str, required=True, help='Path for the output report JSON file')
    
    args = parser.parse_args()
    
    analyzer = TimeframeAnalyzer(args.log_file)
    analyzer.analyze_logs()
    report = analyzer.generate_report()
    
    # Create directory for output if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Save report to file
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to: {args.output}")
    
    # Print summary to console
    print("\n===== TIMEFRAME SELECTION REPORT SUMMARY =====")
    print(f"Total tokens analyzed: {report['overall_stats']['total_tokens']}")
    print(f"Overall success rate: {report['overall_stats']['overall_success_rate']:.1f}%")
    
    print("\nSuccess rate by age category:")
    for category, stats in sorted(report['age_category_stats'].items()):
        print(f"  {category}: {stats['success_rate']:.1f}% ({stats['success_count']}/{stats['total']})")
    
    print("\nSuccess rate by timeframe:")
    for tf, stats in sorted(report['timeframe_stats'].items()):
        if stats['total'] > 0:
            print(f"  {tf}: {stats['success_rate']:.1f}% ({stats['success_count']}/{stats['total']})")
    
    print("\nFallback effectiveness:")
    for tf, stats in sorted(report['fallback_effectiveness'].items(), 
                           key=lambda x: x[1]['success_rate'], reverse=True):
        if stats['attempts'] > 0:
            print(f"  {tf}: {stats['success_rate']:.1f}% ({stats['successes']}/{stats['attempts']})")
    
    print("\nReport complete!")

if __name__ == "__main__":
    main() 