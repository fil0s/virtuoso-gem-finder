#!/usr/bin/env python3
"""
🔍 TEST: FACTOR INTERACTION ANALYSIS IN TELEGRAM ALERTS

This script demonstrates the new interaction analysis section that will appear
in Telegram alerts, showing users WHY a token received its score.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics

def create_sample_interaction_analysis():
    """Create sample interaction analysis data to demonstrate the alert format"""
    
    # Example 1: High-quality gem with amplifications
    high_quality_sample = {
        'scoring_methodology': 'INTERACTION-BASED (Mathematical Fix Applied)',
        'final_score': 87.5,
        'interaction_analysis': {
            'danger_interactions': [],  # No dangers detected
            'amplification_interactions': [
                {
                    'explanation': 'Smart Money + Volume Surge',
                    'impact': 15.2,
                    'factors': ['smart_money_score', 'volume_momentum']
                },
                {
                    'explanation': 'Multi-Platform + Security',
                    'impact': 12.8,
                    'factors': ['cross_platform_validation', 'security_score']
                }
            ],
            'contradiction_interactions': [
                {
                    'explanation': 'High Volume vs Limited Platforms',
                    'impact': -5.3,
                    'factors': ['volume_momentum', 'cross_platform_validation']
                }
            ]
        },
        'risk_assessment': {
            'risk_level': 'MEDIUM',
            'confidence_level': 0.85
        },
        'score_comparison': {
            'linear_score_flawed': 72.0,
            'interaction_score_corrected': 87.5,
            'mathematical_improvement': 21.5
        }
    }
    
    # Example 2: Dangerous token with multiple warnings
    dangerous_sample = {
        'scoring_methodology': 'INTERACTION-BASED (Mathematical Fix Applied)',
        'final_score': 8.2,
        'interaction_analysis': {
            'danger_interactions': [
                {
                    'explanation': 'High VLR + Low Liquidity = Manipulation',
                    'impact': -85.7,
                    'factors': ['vlr_ratio', 'liquidity']
                },
                {
                    'explanation': 'Whale Dominance + Poor Security',
                    'impact': -12.1,
                    'factors': ['whale_concentration', 'security_score']
                }
            ],
            'amplification_interactions': [],
            'contradiction_interactions': [
                {
                    'explanation': 'High Volume vs Red Flag Pattern',
                    'impact': -8.9,
                    'factors': ['volume_momentum', 'security_score']
                }
            ]
        },
        'risk_assessment': {
            'risk_level': 'CRITICAL',
            'confidence_level': 0.92
        },
        'score_comparison': {
            'linear_score_flawed': 81.3,
            'interaction_score_corrected': 8.2,
            'mathematical_improvement': -89.9
        }
    }
    
    return high_quality_sample, dangerous_sample

def simulate_alert_display():
    """Simulate how the interaction analysis will appear in Telegram alerts"""
    
    print("🔍 TELEGRAM ALERT INTERACTION ANALYSIS DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Create a mock telegram alerter (without actual bot token)
    alerter = TelegramAlerter("mock_token", "mock_chat_id")
    
    high_quality, dangerous = create_sample_interaction_analysis()
    
    # Example 1: High-quality gem
    print("📊 EXAMPLE 1: HIGH-QUALITY GEM WITH AMPLIFICATIONS")
    print("-" * 50)
    
    breakdown_text = alerter._build_scoring_breakdown_section(
        enhanced_data=None, 
        score_breakdown=high_quality
    )
    
    # Extract just the interaction analysis part
    lines = breakdown_text.split('\n')
    interaction_start = -1
    for i, line in enumerate(lines):
        if 'FACTOR INTERACTION ANALYSIS' in line:
            interaction_start = i
            break
    
    if interaction_start >= 0:
        interaction_lines = lines[interaction_start:interaction_start + 15]  # Show relevant section
        for line in interaction_lines:
            # Convert HTML tags for console display
            clean_line = line.replace('<b>', '').replace('</b>', '').strip()
            if clean_line:
                print(clean_line)
    
    print()
    print("📊 EXAMPLE 2: DANGEROUS TOKEN WITH WARNINGS")
    print("-" * 50)
    
    breakdown_text = alerter._build_scoring_breakdown_section(
        enhanced_data=None, 
        score_breakdown=dangerous
    )
    
    # Extract interaction analysis part
    lines = breakdown_text.split('\n')
    interaction_start = -1
    for i, line in enumerate(lines):
        if 'FACTOR INTERACTION ANALYSIS' in line:
            interaction_start = i
            break
    
    if interaction_start >= 0:
        interaction_lines = lines[interaction_start:interaction_start + 20]  # Show relevant section
        for line in interaction_lines:
            # Convert HTML tags for console display
            clean_line = line.replace('<b>', '').replace('</b>', '').strip()
            if clean_line:
                print(clean_line)
    
    print()
    print("✅ INTERACTION ANALYSIS ENHANCEMENT COMPLETE!")
    print("   🧠 Users now see WHY tokens get their scores")
    print("   🚨 Danger patterns are clearly highlighted")
    print("   🚀 Signal amplifications are shown")
    print("   ⚖️ Contradictions are identified")
    print("   🎯 Risk assessment with confidence levels")
    print("   📊 Mathematical improvement over linear scoring")

def demonstrate_alert_types():
    """Show different types of interaction patterns that will appear"""
    
    print("\n🎯 INTERACTION PATTERN EXAMPLES")
    print("=" * 40)
    
    patterns = [
        {
            'title': '🚨 PUMP & DUMP DETECTION',
            'example': '⚠️ High VLR + Low Liquidity = Manipulation (-85%)'
        },
        {
            'title': '🚀 SMART MONEY AMPLIFICATION', 
            'example': '📈 Smart Money + Volume Surge (+15%)'
        },
        {
            'title': '⚖️ SIGNAL CONTRADICTION',
            'example': '🔀 High Security vs Whale Dominance (-8%)'
        },
        {
            'title': '💎 OPTIMAL CONDITIONS',
            'example': '📈 Multi-Platform + High Liquidity + Security (+18%)'
        },
        {
            'title': '🔍 STEALTH GEM DISCOVERY',
            'example': '📈 Low Volume + Smart Money + Good Security (+12%)'
        }
    ]
    
    for pattern in patterns:
        print(f"  {pattern['title']}:")
        print(f"    {pattern['example']}")
        print()

if __name__ == "__main__":
    simulate_alert_display()
    demonstrate_alert_types() 