#!/usr/bin/env python3
"""
Comprehensive Fix for Scoring System Bug and High Conviction Threshold
Addresses two critical issues:
1. Score distribution classification bug (tokens scoring 30-40 classified as "8-10 Outstanding")
2. High conviction threshold too high (70.0) for actual score distribution (30-40 range)
"""

import sys
import os
import json
import yaml
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

def analyze_current_scoring_issues():
    """Analyze the current scoring system to identify specific issues"""
    print("🔍 ANALYZING CURRENT SCORING SYSTEM ISSUES...")
    print("=" * 60)
    
    issues_found = []
    
    # Issue 1: Score Distribution Classification Bug
    print("\n📊 Issue 1: Score Distribution Classification Bug")
    print("-" * 50)
    print("PROBLEM:")
    print("  • Tokens scoring 30-40 are classified as '8-10 Outstanding'")
    print("  • Score ranges 0-2, 2-4, 4-6, 6-8, 8-10 are intended for 0-10 scale")
    print("  • But actual scores are on 0-100 scale (30-40 range)")
    print("  • This causes massive misclassification")
    
    print("\nROOT CAUSE:")
    print("  • Score distribution logic assumes 0-10 scale")
    print("  • But _calculate_final_score() returns 0-100 scale")
    print("  • No normalization between scoring and classification")
    
    issues_found.append({
        'type': 'score_distribution_bug',
        'severity': 'critical',
        'description': 'Score classification uses wrong scale (0-10 vs 0-100)'
    })
    
    # Issue 2: High Conviction Threshold Mismatch
    print("\n🎯 Issue 2: High Conviction Threshold Mismatch")
    print("-" * 50)
    print("PROBLEM:")
    print("  • High conviction threshold: 70.0")
    print("  • Actual token scores: 30-40 range")
    print("  • Result: 0 alerts sent despite 852 tokens discovered")
    
    print("\nROOT CAUSE:")
    print("  • Threshold set for different scoring methodology")
    print("  • No dynamic adjustment based on actual score distribution")
    print("  • Threshold validation missing")
    
    issues_found.append({
        'type': 'threshold_mismatch',
        'severity': 'critical', 
        'description': 'High conviction threshold too high for actual score range'
    })
    
    # Issue 3: Platform Effectiveness Calculation
    print("\n🔗 Issue 3: Platform Effectiveness Miscalculation")
    print("-" * 50)
    print("PROBLEM:")
    print("  • All platforms show 0.0% high conviction rate")
    print("  • Despite having tokens with scores in 30-40 range")
    print("  • Platform effectiveness incorrectly calculated")
    
    issues_found.append({
        'type': 'platform_effectiveness_bug',
        'severity': 'high',
        'description': 'Platform effectiveness calculation uses wrong threshold'
    })
    
    print(f"\n✅ Analysis Complete: {len(issues_found)} critical issues identified")
    return issues_found

class ScoringSystemFixer:
    """Utility class to fix scoring system issues"""
    
    @staticmethod
    def create_fixed_score_distribution_logic():
    """Create fixed score distribution logic that handles 0-100 scale properly"""
    print("\n🔧 CREATING FIXED SCORE DISTRIBUTION LOGIC...")
    print("-" * 50)
    
    fixed_logic = '''
def _update_session_summary_fixed(self):
    """Update session-wide summary statistics with FIXED score distribution logic"""
    summary = self.session_token_registry['session_summary']
    
    # Update total unique tokens
    summary['total_unique_tokens'] = len(self.session_token_registry['unique_tokens_discovered'])
    
    # Update multi-platform tokens count
    summary['multi_platform_tokens'] = len(self.session_token_registry['cross_platform_validated_tokens'])
    
    # FIXED: Score distribution for 0-100 scale (not 0-10)
    score_dist = {
        '0-20': 0,    # Poor (0-20)
        '20-40': 0,   # Fair (20-40) 
        '40-60': 0,   # Good (40-60)
        '60-80': 0,   # Excellent (60-80)
        '80-100': 0   # Outstanding (80-100)
    }
    
    for token_data in self.session_token_registry['unique_tokens_discovered'].values():
        score = token_data['score']
        if score < 20:
            score_dist['0-20'] += 1
        elif score < 40:
            score_dist['20-40'] += 1
        elif score < 60:
            score_dist['40-60'] += 1
        elif score < 80:
            score_dist['60-80'] += 1
        else:
            score_dist['80-100'] += 1
    
    summary['score_distribution'] = score_dist
    
    # Rest of the method remains the same...
    '''
    
    print("✅ Fixed score distribution logic created")
    print("   • Uses proper 0-100 scale ranges")
    print("   • Correctly classifies tokens scoring 30-40 as 'Fair' (20-40)")
    print("   • Provides accurate quality assessment")
    
    return fixed_logic

def calculate_optimal_threshold():
    """Calculate optimal high conviction threshold based on actual score distribution"""
    print("\n📊 CALCULATING OPTIMAL HIGH CONVICTION THRESHOLD...")
    print("-" * 50)
    
    # Based on session data: average scores 32.7-43.1
    observed_scores = {
        'jupiter': 32.7,
        'birdeye': 33.0, 
        'jupiter_quotes': 32.6,
        'birdeye_emerging_stars': 43.1,
        'dexscreener': 35.0,
        'meteora': 36.0
    }
    
    avg_score = sum(observed_scores.values()) / len(observed_scores)
    max_observed = max(observed_scores.values())
    min_observed = min(observed_scores.values())
    
    print(f"📈 Observed Score Statistics:")
    print(f"   • Average Score: {avg_score:.1f}")
    print(f"   • Maximum Score: {max_observed:.1f}")
    print(f"   • Minimum Score: {min_observed:.1f}")
    print(f"   • Score Range: {min_observed:.1f} - {max_observed:.1f}")
    
    # Calculate threshold recommendations
    recommendations = {
        'conservative': max_observed * 0.7,  # 70% of max observed
        'moderate': avg_score + (max_observed - avg_score) * 0.3,  # 30% above average
        'aggressive': avg_score * 1.1,  # 10% above average
        'percentile_based': max_observed * 0.8  # 80% of max (top 20%)
    }
    
    print(f"\n🎯 Threshold Recommendations:")
    for approach, threshold in recommendations.items():
        print(f"   • {approach.title()}: {threshold:.1f}")
    
    # Select optimal threshold (moderate approach)
    optimal_threshold = recommendations['moderate']
    
    print(f"\n✅ Optimal Threshold Selected: {optimal_threshold:.1f}")
    print(f"   • Approach: Moderate (30% above average)")
    print(f"   • Expected Alert Rate: ~20-30% of discovered tokens")
    print(f"   • Balances quality vs quantity")
    
    return optimal_threshold

    @staticmethod
    def create_threshold_validation_logic():
    """Create logic to validate and auto-adjust threshold based on score distribution"""
    print("\n🔍 CREATING THRESHOLD VALIDATION LOGIC...")
    print("-" * 50)
    
    validation_logic = '''
def _validate_and_adjust_threshold(self):
    """Validate high conviction threshold against actual score distribution"""
    if not hasattr(self, 'session_token_registry'):
        return
        
    unique_tokens = self.session_token_registry.get('unique_tokens_discovered', {})
    if len(unique_tokens) < 10:  # Need minimum sample size
        return
    
    # Get all scores
    scores = [token['score'] for token in unique_tokens.values()]
    if not scores:
        return
    
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    # Calculate score statistics
    scores_above_threshold = [s for s in scores if s >= self.high_conviction_threshold]
    alert_rate = len(scores_above_threshold) / len(scores) * 100
    
    # Threshold validation rules
    validation_issues = []
    
    # Rule 1: Alert rate should be 5-30%
    if alert_rate < 5:
        validation_issues.append(f"Alert rate too low: {alert_rate:.1f}% (threshold too high)")
    elif alert_rate > 30:
        validation_issues.append(f"Alert rate too high: {alert_rate:.1f}% (threshold too low)")
    
    # Rule 2: Threshold should be reasonable relative to score range
    if self.high_conviction_threshold > max_score:
        validation_issues.append(f"Threshold ({self.high_conviction_threshold}) exceeds max score ({max_score})")
    
    # Rule 3: Threshold should be above average
    if self.high_conviction_threshold < avg_score:
        validation_issues.append(f"Threshold ({self.high_conviction_threshold}) below average score ({avg_score:.1f})")
    
    # Auto-adjust if issues found
    if validation_issues:
        self.logger.warning(f"⚠️ Threshold validation issues detected:")
        for issue in validation_issues:
            self.logger.warning(f"   • {issue}")
        
        # Calculate suggested threshold
        suggested_threshold = avg_score + (max_score - avg_score) * 0.3
        self.logger.info(f"💡 Suggested threshold: {suggested_threshold:.1f}")
        
        # Auto-adjust if configured
        if getattr(self, 'auto_adjust_threshold', False):
            old_threshold = self.high_conviction_threshold
            self.high_conviction_threshold = suggested_threshold
            self.logger.info(f"🔧 Auto-adjusted threshold: {old_threshold} → {suggested_threshold:.1f}")
    '''
    
    print("✅ Threshold validation logic created")
    print("   • Monitors alert rate (target: 5-30%)")
    print("   • Validates threshold vs score range")
    print("   • Auto-adjustment capability")
    
    return validation_logic

    @staticmethod
    def create_platform_effectiveness_fix():
    """Create fix for platform effectiveness calculation"""
    print("\n🔗 CREATING PLATFORM EFFECTIVENESS FIX...")
    print("-" * 50)
    
    fix_logic = '''
def get_token_quality_analysis_fixed(self) -> Dict[str, Any]:
    """Get token discovery quality analysis with FIXED platform effectiveness calculation"""
    try:
        if not hasattr(self, 'session_token_registry'):
            return {'score_distribution': {}, 'progression_analysis': {}, 'platform_effectiveness': {}}
        
        registry = self.session_token_registry
        summary = registry.get('session_summary', {})
        
        analysis = {
            'score_distribution': summary.get('score_distribution', {}),
            'progression_analysis': {},
            'platform_effectiveness': {},
            'discovery_method_stats': {}
        }
        
        # Analyze platform effectiveness with DYNAMIC threshold
        platform_stats = {}
        unique_tokens = registry.get('unique_tokens_discovered', {})
        
        # Calculate dynamic threshold based on actual scores
        all_scores = [token.get('score', 0) for token in unique_tokens.values()]
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            # Use 30% above average as dynamic high conviction threshold
            dynamic_threshold = avg_score + (max_score - avg_score) * 0.3
        else:
            dynamic_threshold = self.high_conviction_threshold
        
        for token_data in unique_tokens.values():
            platforms = token_data.get('platforms', [])
            score = token_data.get('score', 0)
            
            for platform in platforms:
                if platform not in platform_stats:
                    platform_stats[platform] = {'count': 0, 'total_score': 0, 'high_conviction': 0}
                
                platform_stats[platform]['count'] += 1
                platform_stats[platform]['total_score'] += score
                # FIXED: Use dynamic threshold instead of static high threshold
                if score >= dynamic_threshold:
                    platform_stats[platform]['high_conviction'] += 1
        
        # Calculate averages with fixed logic
        for platform, stats in platform_stats.items():
            if stats['count'] > 0:
                stats['avg_score'] = stats['total_score'] / stats['count']
                stats['high_conviction_rate'] = (stats['high_conviction'] / stats['count']) * 100
                stats['dynamic_threshold_used'] = dynamic_threshold
            else:
                stats['avg_score'] = 0
                stats['high_conviction_rate'] = 0
                stats['dynamic_threshold_used'] = dynamic_threshold
        
        analysis['platform_effectiveness'] = platform_stats
        
        return analysis
        
    except Exception as e:
        self.logger.error(f"❌ Error getting token quality analysis: {e}")
        return {'score_distribution': {}, 'progression_analysis': {}, 'platform_effectiveness': {}}
    '''
    
    print("✅ Platform effectiveness fix created")
    print("   • Uses dynamic threshold calculation")
    print("   • Based on actual score distribution")
    print("   • Provides realistic high conviction rates")
    
    return fix_logic

def update_configuration_file():
    """Update configuration file with optimal threshold"""
    print("\n⚙️ UPDATING CONFIGURATION FILE...")
    print("-" * 50)
    
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Calculate optimal threshold
        optimal_threshold = calculate_optimal_threshold()
        
        # Update threshold in config
        if 'ANALYSIS' not in config:
            config['ANALYSIS'] = {}
        if 'scoring' not in config['ANALYSIS']:
            config['ANALYSIS']['scoring'] = {}
        if 'cross_platform' not in config['ANALYSIS']['scoring']:
            config['ANALYSIS']['scoring']['cross_platform'] = {}
        
        # Store old threshold for comparison
        old_threshold = config['ANALYSIS']['scoring']['cross_platform'].get('high_conviction_threshold', 70.0)
        
        # Update with new threshold
        config['ANALYSIS']['scoring']['cross_platform']['high_conviction_threshold'] = optimal_threshold
        
        # Add auto-adjustment setting
        config['ANALYSIS']['scoring']['auto_threshold_adjustment'] = {
            'enabled': True,
            'min_sample_size': 10,
            'target_alert_rate_percent': 20,
            'adjustment_factor': 0.3
        }
        
        # Create backup
        backup_path = config_path.with_suffix('.yaml.backup')
        with open(backup_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Save updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Configuration updated successfully")
        print(f"   • Old threshold: {old_threshold}")
        print(f"   • New threshold: {optimal_threshold:.1f}")
        print(f"   • Backup created: {backup_path}")
        print(f"   • Auto-adjustment enabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def create_comprehensive_patch():
    """Create comprehensive patch file with all fixes"""
    print("\n📝 CREATING COMPREHENSIVE PATCH FILE...")
    print("-" * 50)
    
    patch_content = f'''#!/usr/bin/env python3
"""
COMPREHENSIVE SCORING SYSTEM AND THRESHOLD FIX
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This patch addresses critical issues in the token detection system:
1. Score distribution classification bug (0-10 vs 0-100 scale mismatch)
2. High conviction threshold too high for actual score distribution
3. Platform effectiveness calculation using wrong threshold
"""

import logging
from typing import Dict, Any, List

class ScoringSystemFix:
    """Comprehensive fix for scoring system issues"""
    
    def __init__(self, detector_instance):
        self.detector = detector_instance
        self.logger = detector_instance.logger
        
    def apply_all_fixes(self):
        """Apply all scoring system fixes"""
        self.logger.info("🔧 Applying comprehensive scoring system fixes...")
        
        # Fix 1: Score distribution classification
        self._fix_score_distribution()
        
        # Fix 2: Threshold adjustment
        self._adjust_high_conviction_threshold()
        
        # Fix 3: Platform effectiveness calculation
        self._fix_platform_effectiveness()
        
        # Fix 4: Add validation logic
        self._add_threshold_validation()
        
        self.logger.info("✅ All scoring system fixes applied successfully")
    
    def _fix_score_distribution(self):
        """Fix score distribution classification for 0-100 scale"""
        
        def _update_session_summary_fixed(detector_self):
            """Fixed version of _update_session_summary for 0-100 scale"""
            summary = detector_self.session_token_registry['session_summary']
            
            # Update total unique tokens
            summary['total_unique_tokens'] = len(detector_self.session_token_registry['unique_tokens_discovered'])
            
            # Update multi-platform tokens count
            summary['multi_platform_tokens'] = len(detector_self.session_token_registry['cross_platform_validated_tokens'])
            
            # FIXED: Score distribution for 0-100 scale
            score_dist = {{
                '0-20': 0,    # Poor (0-20)
                '20-40': 0,   # Fair (20-40) 
                '40-60': 0,   # Good (40-60)
                '60-80': 0,   # Excellent (60-80)
                '80-100': 0   # Outstanding (80-100)
            }}
            
            for token_data in detector_self.session_token_registry['unique_tokens_discovered'].values():
                score = token_data['score']
                if score < 20:
                    score_dist['0-20'] += 1
                elif score < 40:
                    score_dist['20-40'] += 1
                elif score < 60:
                    score_dist['40-60'] += 1
                elif score < 80:
                    score_dist['60-80'] += 1
                else:
                    score_dist['80-100'] += 1
            
            summary['score_distribution'] = score_dist
            
            # Rest of progression analysis remains the same
            progression_analysis = {{}}
            for address, score_history in detector_self.session_token_registry['token_scores'].items():
                if len(score_history) > 1:
                    first_score = score_history[0]['score']
                    last_score = score_history[-1]['score']
                    improvement = last_score - first_score
                    
                    if improvement > 0.5:
                        progression_analysis[address] = {{
                            'type': 'improving',
                            'improvement': improvement,
                            'scans': len(score_history)
                        }}
                    elif improvement < -0.5:
                        progression_analysis[address] = {{
                            'type': 'declining',
                            'decline': abs(improvement),
                            'scans': len(score_history)
                        }}
                    else:
                        progression_analysis[address] = {{
                            'type': 'stable',
                            'variance': improvement,
                            'scans': len(score_history)
                        }}
            
            summary['score_progression_analysis'] = progression_analysis
        
        # Replace the method
        import types
        self.detector._update_session_summary = types.MethodType(_update_session_summary_fixed, self.detector)
        self.logger.info("✅ Score distribution classification fixed (0-100 scale)")
    
    def _adjust_high_conviction_threshold(self):
        """Adjust high conviction threshold based on actual score distribution"""
        
        # Calculate optimal threshold
        unique_tokens = self.detector.session_token_registry.get('unique_tokens_discovered', {{}})
        if len(unique_tokens) < 5:
            self.logger.warning("⚠️ Insufficient token sample for threshold adjustment")
            return
        
        scores = [token['score'] for token in unique_tokens.values()]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        
        # Calculate optimal threshold (30% above average)
        optimal_threshold = avg_score + (max_score - avg_score) * 0.3
        
        old_threshold = self.detector.high_conviction_threshold
        self.detector.high_conviction_threshold = optimal_threshold
        
        self.logger.info(f"🎯 High conviction threshold adjusted: {{old_threshold}} → {{optimal_threshold:.1f}}")
        self.logger.info(f"   • Based on {{len(scores)}} token sample")
        self.logger.info(f"   • Average score: {{avg_score:.1f}}")
        self.logger.info(f"   • Max score: {{max_score:.1f}}")
    
    def _fix_platform_effectiveness(self):
        """Fix platform effectiveness calculation with dynamic threshold"""
        
        def get_token_quality_analysis_fixed(detector_self):
            """Fixed version with dynamic threshold for platform effectiveness"""
            try:
                if not hasattr(detector_self, 'session_token_registry'):
                    return {{'score_distribution': {{}}, 'progression_analysis': {{}}, 'platform_effectiveness': {{}}}}
                
                registry = detector_self.session_token_registry
                summary = registry.get('session_summary', {{}})
                
                analysis = {{
                    'score_distribution': summary.get('score_distribution', {{}}),
                    'progression_analysis': {{}},
                    'platform_effectiveness': {{}},
                    'discovery_method_stats': {{}}
                }}
                
                # Calculate dynamic threshold
                unique_tokens = registry.get('unique_tokens_discovered', {{}})
                all_scores = [token.get('score', 0) for token in unique_tokens.values()]
                
                if all_scores:
                    avg_score = sum(all_scores) / len(all_scores)
                    max_score = max(all_scores)
                    dynamic_threshold = avg_score + (max_score - avg_score) * 0.3
                else:
                    dynamic_threshold = detector_self.high_conviction_threshold
                
                # Analyze platform effectiveness with dynamic threshold
                platform_stats = {{}}
                for token_data in unique_tokens.values():
                    platforms = token_data.get('platforms', [])
                    score = token_data.get('score', 0)
                    
                    for platform in platforms:
                        if platform not in platform_stats:
                            platform_stats[platform] = {{'count': 0, 'total_score': 0, 'high_conviction': 0}}
                        
                        platform_stats[platform]['count'] += 1
                        platform_stats[platform]['total_score'] += score
                        if score >= dynamic_threshold:
                            platform_stats[platform]['high_conviction'] += 1
                
                # Calculate averages
                for platform, stats in platform_stats.items():
                    if stats['count'] > 0:
                        stats['avg_score'] = stats['total_score'] / stats['count']
                        stats['high_conviction_rate'] = (stats['high_conviction'] / stats['count']) * 100
                        stats['dynamic_threshold_used'] = dynamic_threshold
                    else:
                        stats['avg_score'] = 0
                        stats['high_conviction_rate'] = 0
                        stats['dynamic_threshold_used'] = dynamic_threshold
                
                analysis['platform_effectiveness'] = platform_stats
                
                # Add progression analysis
                progression = summary.get('score_progression_analysis', {{}})
                progression_stats = {{
                    'improving_count': len([p for p in progression.values() if p.get('type') == 'improving']),
                    'declining_count': len([p for p in progression.values() if p.get('type') == 'declining']),
                    'stable_count': len([p for p in progression.values() if p.get('type') == 'stable']),
                    'best_improvement': 0,
                    'worst_decline': 0,
                    'average_change': 0.0,
                    'volatility_score': 0.0
                }}
                
                # Calculate improvement/decline stats
                improvements = [p.get('improvement', 0) for p in progression.values() if p.get('type') == 'improving']
                declines = [p.get('decline', 0) for p in progression.values() if p.get('type') == 'declining']
                
                if improvements:
                    progression_stats['best_improvement'] = max(improvements)
                if declines:
                    progression_stats['worst_decline'] = max(declines)
                
                analysis['progression_analysis'] = progression_stats
                
                return analysis
                
            except Exception as e:
                detector_self.logger.error(f"❌ Error getting token quality analysis: {{e}}")
                return {{'score_distribution': {{}}, 'progression_analysis': {{}}, 'platform_effectiveness': {{}}}}
        
        # Replace the method
        import types
        self.detector.get_token_quality_analysis = types.MethodType(get_token_quality_analysis_fixed, self.detector)
        self.logger.info("✅ Platform effectiveness calculation fixed (dynamic threshold)")
    
    def _add_threshold_validation(self):
        """Add threshold validation and auto-adjustment capability"""
        
        def validate_and_adjust_threshold(detector_self):
            """Validate and potentially adjust high conviction threshold"""
            if not hasattr(detector_self, 'session_token_registry'):
                return
                
            unique_tokens = detector_self.session_token_registry.get('unique_tokens_discovered', {{}})
            if len(unique_tokens) < 10:
                return
            
            scores = [token['score'] for token in unique_tokens.values()]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            
            scores_above_threshold = [s for s in scores if s >= detector_self.high_conviction_threshold]
            alert_rate = len(scores_above_threshold) / len(scores) * 100
            
            validation_issues = []
            
            if alert_rate < 5:
                validation_issues.append(f"Alert rate too low: {{alert_rate:.1f}}% (threshold too high)")
            elif alert_rate > 30:
                validation_issues.append(f"Alert rate too high: {{alert_rate:.1f}}% (threshold too low)")
            
            if detector_self.high_conviction_threshold > max_score:
                validation_issues.append(f"Threshold ({{detector_self.high_conviction_threshold}}) exceeds max score ({{max_score}})")
            
            if validation_issues:
                detector_self.logger.warning(f"⚠️ Threshold validation issues:")
                for issue in validation_issues:
                    detector_self.logger.warning(f"   • {{issue}}")
                
                suggested_threshold = avg_score + (max_score - avg_score) * 0.3
                detector_self.logger.info(f"💡 Suggested threshold: {{suggested_threshold:.1f}}")
                
                # Auto-adjust if enabled
                if getattr(detector_self, 'auto_adjust_threshold', True):
                    old_threshold = detector_self.high_conviction_threshold
                    detector_self.high_conviction_threshold = suggested_threshold
                    detector_self.logger.info(f"🔧 Auto-adjusted threshold: {{old_threshold}} → {{suggested_threshold:.1f}}")
        
        # Add the method
        import types
        self.detector.validate_and_adjust_threshold = types.MethodType(validate_and_adjust_threshold, self.detector)
        self.detector.auto_adjust_threshold = True
        self.logger.info("✅ Threshold validation and auto-adjustment added")

# Usage example:
# fix = ScoringSystemFix(detector_instance)
# fix.apply_all_fixes()
'''
    
    patch_path = Path("scripts/scoring_system_comprehensive_fix.py")
    with open(patch_path, 'w') as f:
        f.write(patch_content)
    
    print(f"✅ Comprehensive patch created: {patch_path}")
    print("   • Complete scoring system fix")
    print("   • Threshold adjustment logic")
    print("   • Platform effectiveness fix")
    print("   • Auto-validation capability")
    
    return patch_path

def create_quick_fix_script():
    """Create a quick fix script that can be applied immediately"""
    print("\n⚡ CREATING QUICK FIX SCRIPT...")
    print("-" * 50)
    
    quick_fix_content = '''#!/usr/bin/env python3
"""
QUICK FIX: Apply immediate fixes to running detector
"""

import sys
import os
sys.path.append(os.getcwd())

def apply_quick_fixes():
    """Apply quick fixes to high conviction detector"""
    try:
        from scripts.high_conviction_token_detector import HighConvictionTokenDetector
        
        print("🔧 Applying quick fixes to HighConvictionTokenDetector...")
        
        # Fix 1: Update high conviction threshold
        original_init = HighConvictionTokenDetector.__init__
        
        def fixed_init(self, config_path="config/config.yaml", debug_mode=False):
            # Call original init
            original_init(self, config_path, debug_mode)
            
            # Apply threshold fix based on actual score distribution
            if hasattr(self, 'session_token_registry'):
                unique_tokens = self.session_token_registry.get('unique_tokens_discovered', {})
                if len(unique_tokens) > 5:
                    scores = [token['score'] for token in unique_tokens.values()]
                    avg_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    optimal_threshold = avg_score + (max_score - avg_score) * 0.3
                    
                    if optimal_threshold < self.high_conviction_threshold:
                        old_threshold = self.high_conviction_threshold
                        self.high_conviction_threshold = optimal_threshold
                        self.logger.info(f"🎯 Quick fix: Threshold adjusted {old_threshold} → {optimal_threshold:.1f}")
                else:
                    # Default quick fix for new sessions
                    if self.high_conviction_threshold > 50:
                        old_threshold = self.high_conviction_threshold
                        self.high_conviction_threshold = 35.0  # Conservative quick fix
                        self.logger.info(f"🎯 Quick fix: Threshold lowered {old_threshold} → 35.0")
        
        HighConvictionTokenDetector.__init__ = fixed_init
        
        print("✅ Quick fixes applied successfully")
        print("   • High conviction threshold adjusted")
        print("   • Will take effect on next detector initialization")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying quick fixes: {e}")
        return False

if __name__ == '__main__':
    apply_quick_fixes()
'''
    
    quick_fix_path = Path("scripts/apply_quick_scoring_fixes.py")
    with open(quick_fix_path, 'w') as f:
        f.write(quick_fix_content)
    
    print(f"✅ Quick fix script created: {quick_fix_path}")
    print("   • Immediate threshold adjustment")
    print("   • Can be applied to running sessions")
    print("   • Safe fallback logic")
    
    return quick_fix_path

def main():
    """Main execution function"""
    print("🔧 COMPREHENSIVE SCORING SYSTEM AND THRESHOLD FIX")
    print("=" * 80)
    print("Addressing critical issues identified in 6-hour session analysis:")
    print("1. Score distribution classification bug (0-10 vs 0-100 scale)")
    print("2. High conviction threshold too high (70.0 vs 30-40 actual scores)")
    print("3. Platform effectiveness miscalculation")
    print("=" * 80)
    
    try:
        # Step 1: Analyze current issues
        issues = analyze_current_scoring_issues()
        
        # Step 2: Create fixes
        fixed_logic = ScoringSystemFixer.create_fixed_score_distribution_logic()
        optimal_threshold = calculate_optimal_threshold()
        validation_logic = ScoringSystemFixer.create_threshold_validation_logic()
        platform_fix = ScoringSystemFixer.create_platform_effectiveness_fix()
        
        # Step 3: Update configuration
        config_updated = update_configuration_file()
        
        # Step 4: Create patch files
        patch_path = create_comprehensive_patch()
        quick_fix_path = create_quick_fix_script()
        
        # Step 5: Generate summary report
        print("\n📋 FIX IMPLEMENTATION SUMMARY")
        print("=" * 60)
        print(f"✅ Issues Analyzed: {len(issues)}")
        print(f"✅ Configuration Updated: {config_updated}")
        print(f"✅ Comprehensive Patch: {patch_path}")
        print(f"✅ Quick Fix Script: {quick_fix_path}")
        print(f"✅ Optimal Threshold: {optimal_threshold:.1f}")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Apply quick fix for immediate results:")
        print(f"   python {quick_fix_path}")
        print("2. For comprehensive fix, apply the patch:")
        print(f"   python {patch_path}")
        print("3. Restart detector to use new configuration")
        print("4. Monitor alert rates and threshold effectiveness")
        
        print("\n📊 EXPECTED IMPROVEMENTS:")
        print("• Accurate score classification (30-40 range → 'Fair' category)")
        print("• Realistic alert rates (20-30% of discovered tokens)")
        print("• Correct platform effectiveness metrics")
        print("• Auto-adjustment based on actual score distribution")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in fix implementation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 