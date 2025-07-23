#!/usr/bin/env python3
"""
COMPREHENSIVE SCORING SYSTEM AND THRESHOLD FIX
Generated: 2025-06-23 23:00:27

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
            score_dist = {
                '0-20': 0,    # Poor (0-20)
                '20-40': 0,   # Fair (20-40) 
                '40-60': 0,   # Good (40-60)
                '60-80': 0,   # Excellent (60-80)
                '80-100': 0   # Outstanding (80-100)
            }
            
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
            progression_analysis = {}
            for address, score_history in detector_self.session_token_registry['token_scores'].items():
                if len(score_history) > 1:
                    first_score = score_history[0]['score']
                    last_score = score_history[-1]['score']
                    improvement = last_score - first_score
                    
                    if improvement > 0.5:
                        progression_analysis[address] = {
                            'type': 'improving',
                            'improvement': improvement,
                            'scans': len(score_history)
                        }
                    elif improvement < -0.5:
                        progression_analysis[address] = {
                            'type': 'declining',
                            'decline': abs(improvement),
                            'scans': len(score_history)
                        }
                    else:
                        progression_analysis[address] = {
                            'type': 'stable',
                            'variance': improvement,
                            'scans': len(score_history)
                        }
            
            summary['score_progression_analysis'] = progression_analysis
        
        # Replace the method
        import types
        self.detector._update_session_summary = types.MethodType(_update_session_summary_fixed, self.detector)
        self.logger.info("✅ Score distribution classification fixed (0-100 scale)")
    
    def _adjust_high_conviction_threshold(self):
        """Adjust high conviction threshold based on actual score distribution"""
        
        # Calculate optimal threshold
        unique_tokens = self.detector.session_token_registry.get('unique_tokens_discovered', {})
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
        
        self.logger.info(f"🎯 High conviction threshold adjusted: {old_threshold} → {optimal_threshold:.1f}")
        self.logger.info(f"   • Based on {len(scores)} token sample")
        self.logger.info(f"   • Average score: {avg_score:.1f}")
        self.logger.info(f"   • Max score: {max_score:.1f}")
    
    def _fix_platform_effectiveness(self):
        """Fix platform effectiveness calculation with dynamic threshold"""
        
        def get_token_quality_analysis_fixed(detector_self):
            """Fixed version with dynamic threshold for platform effectiveness"""
            try:
                if not hasattr(detector_self, 'session_token_registry'):
                    return {'score_distribution': {}, 'progression_analysis': {}, 'platform_effectiveness': {}}
                
                registry = detector_self.session_token_registry
                summary = registry.get('session_summary', {})
                
                analysis = {
                    'score_distribution': summary.get('score_distribution', {}),
                    'progression_analysis': {},
                    'platform_effectiveness': {},
                    'discovery_method_stats': {}
                }
                
                # Calculate dynamic threshold
                unique_tokens = registry.get('unique_tokens_discovered', {})
                all_scores = [token.get('score', 0) for token in unique_tokens.values()]
                
                if all_scores:
                    avg_score = sum(all_scores) / len(all_scores)
                    max_score = max(all_scores)
                    dynamic_threshold = avg_score + (max_score - avg_score) * 0.3
                else:
                    dynamic_threshold = detector_self.high_conviction_threshold
                
                # Analyze platform effectiveness with dynamic threshold
                platform_stats = {}
                for token_data in unique_tokens.values():
                    platforms = token_data.get('platforms', [])
                    score = token_data.get('score', 0)
                    
                    for platform in platforms:
                        if platform not in platform_stats:
                            platform_stats[platform] = {'count': 0, 'total_score': 0, 'high_conviction': 0}
                        
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
                progression = summary.get('score_progression_analysis', {})
                progression_stats = {
                    'improving_count': len([p for p in progression.values() if p.get('type') == 'improving']),
                    'declining_count': len([p for p in progression.values() if p.get('type') == 'declining']),
                    'stable_count': len([p for p in progression.values() if p.get('type') == 'stable']),
                    'best_improvement': 0,
                    'worst_decline': 0,
                    'average_change': 0.0,
                    'volatility_score': 0.0
                }
                
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
                detector_self.logger.error(f"❌ Error getting token quality analysis: {e}")
                return {'score_distribution': {}, 'progression_analysis': {}, 'platform_effectiveness': {}}
        
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
                
            unique_tokens = detector_self.session_token_registry.get('unique_tokens_discovered', {})
            if len(unique_tokens) < 10:
                return
            
            scores = [token['score'] for token in unique_tokens.values()]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            
            scores_above_threshold = [s for s in scores if s >= detector_self.high_conviction_threshold]
            alert_rate = len(scores_above_threshold) / len(scores) * 100
            
            validation_issues = []
            
            if alert_rate < 5:
                validation_issues.append(f"Alert rate too low: {alert_rate:.1f}% (threshold too high)")
            elif alert_rate > 30:
                validation_issues.append(f"Alert rate too high: {alert_rate:.1f}% (threshold too low)")
            
            if detector_self.high_conviction_threshold > max_score:
                validation_issues.append(f"Threshold ({detector_self.high_conviction_threshold}) exceeds max score ({max_score})")
            
            if validation_issues:
                detector_self.logger.warning(f"⚠️ Threshold validation issues:")
                for issue in validation_issues:
                    detector_self.logger.warning(f"   • {issue}")
                
                suggested_threshold = avg_score + (max_score - avg_score) * 0.3
                detector_self.logger.info(f"💡 Suggested threshold: {suggested_threshold:.1f}")
                
                # Auto-adjust if enabled
                if getattr(detector_self, 'auto_adjust_threshold', True):
                    old_threshold = detector_self.high_conviction_threshold
                    detector_self.high_conviction_threshold = suggested_threshold
                    detector_self.logger.info(f"🔧 Auto-adjusted threshold: {old_threshold} → {suggested_threshold:.1f}")
        
        # Add the method
        import types
        self.detector.validate_and_adjust_threshold = types.MethodType(validate_and_adjust_threshold, self.detector)
        self.detector.auto_adjust_threshold = True
        self.logger.info("✅ Threshold validation and auto-adjustment added")

# Usage example:
# fix = ScoringSystemFix(detector_instance)
# fix.apply_all_fixes()
