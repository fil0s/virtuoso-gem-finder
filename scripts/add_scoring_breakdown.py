#!/usr/bin/env python3
"""
Script to add detailed scoring breakdown to high conviction token detector
"""
import re

def add_scoring_breakdown():
    """Add detailed scoring breakdown to the high conviction detector"""
    
    # Read the current file
    with open('scripts/high_conviction_token_detector.py', 'r') as f:
        content = f.read()
    
    # 1. Update the _calculate_final_score method signature and implementation
    old_signature = "def _calculate_final_score(self, candidate: Dict[str, Any], overview_data: Dict[str, Any], \n                             whale_analysis: Dict[str, Any], volume_price_analysis: Dict[str, Any],\n                             community_boost_analysis: Dict[str, Any], security_analysis: Dict[str, Any], \n                             trading_activity: Dict[str, Any]) -> float:"
    
    new_signature = "def _calculate_final_score(self, candidate: Dict[str, Any], overview_data: Dict[str, Any], \n                             whale_analysis: Dict[str, Any], volume_price_analysis: Dict[str, Any],\n                             community_boost_analysis: Dict[str, Any], security_analysis: Dict[str, Any], \n                             trading_activity: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:"
    
    content = content.replace(old_signature, new_signature)
    
    # 2. Find and replace the return statement in _calculate_final_score
    old_return = """            return final_score
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating final score: {e}")
            # Return base score as fallback
            return candidate.get('score', 0)"""
    
    new_return = """            # Create detailed scoring breakdown
            scoring_breakdown = {
                'base_score': base_score,
                'cross_platform_validation': {
                    'platforms': candidate.get('platforms', []),
                    'platform_count': len(candidate.get('platforms', [])),
                    'validation_bonus': base_score
                },
                'overview_analysis': {
                    'market_cap': overview_data.get('market_cap', 0) if overview_data else 0,
                    'liquidity': overview_data.get('liquidity', 0) if overview_data else 0,
                    'price_change_1h': overview_data.get('price_change_1h', 0) if overview_data else 0,
                    'price_change_24h': overview_data.get('price_change_24h', 0) if overview_data else 0,
                    'holders': overview_data.get('holders', 0) if overview_data else 0,
                    'score': overview_score,
                    'max_score': 20
                },
                'whale_analysis': {
                    'whale_concentration': whale_analysis.get('whale_concentration', 0) if whale_analysis else 0,
                    'smart_money_detected': whale_analysis.get('smart_money_detected', False) if whale_analysis else False,
                    'score': whale_score,
                    'max_score': 15
                },
                'volume_price_analysis': {
                    'volume_trend': volume_price_analysis.get('volume_trend', 'unknown') if volume_price_analysis else 'unknown',
                    'price_momentum': volume_price_analysis.get('price_momentum', 'unknown') if volume_price_analysis else 'unknown',
                    'score': volume_score,
                    'max_score': 15
                },
                'community_analysis': {
                    'social_score': community_boost_analysis.get('social_score', 0) if community_boost_analysis else 0,
                    'community_strength': community_boost_analysis.get('community_strength', 'unknown') if community_boost_analysis else 'unknown',
                    'score': community_score,
                    'max_score': 10
                },
                'security_analysis': {
                    'security_score_raw': security_analysis.get('security_score', 100) if security_analysis else 100,
                    'risk_factors': security_analysis.get('risk_factors', []) if security_analysis else [],
                    'risk_factor_count': len(security_analysis.get('risk_factors', [])) if security_analysis else 0,
                    'score': security_score,
                    'max_score': 10
                },
                'trading_activity': {
                    'recent_activity_score': trading_activity.get('recent_activity_score', 0) if trading_activity else 0,
                    'buy_sell_ratio': trading_activity.get('buy_sell_ratio', 0) if trading_activity else 0,
                    'transaction_count': trading_activity.get('transaction_count', 0) if trading_activity else 0,
                    'score': trading_score,
                    'max_score': 10
                },
                'final_score_summary': {
                    'base_score': base_score,
                    'overview_score': overview_score,
                    'whale_score': whale_score,
                    'volume_score': volume_score,
                    'community_score': community_score,
                    'security_score': security_score,
                    'trading_score': trading_score,
                    'total_before_cap': base_score + overview_score + whale_score + volume_score + community_score + security_score + trading_score,
                    'final_score': final_score,
                    'max_possible_score': 100
                }
            }
            
            return final_score, scoring_breakdown
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating final score: {e}")
            # Return base score as fallback with minimal breakdown
            fallback_breakdown = {
                'base_score': candidate.get('score', 0),
                'error': str(e),
                'final_score_summary': {
                    'final_score': candidate.get('score', 0)
                }
            }
            return candidate.get('score', 0), fallback_breakdown"""
    
    content = content.replace(old_return, new_return)
    
    # 3. Update the calls to _calculate_final_score in _perform_detailed_analysis
    old_call = """            # Calculate final score even with partial data
            final_score = self._calculate_final_score(
                candidate, 
                analysis_results['overview_data'], 
                analysis_results['whale_analysis'], 
                analysis_results['volume_price_analysis'],
                analysis_results['community_boost_analysis'], 
                analysis_results['security_analysis'], 
                analysis_results['trading_activity']
            )"""
    
    new_call = """            # Calculate final score even with partial data
            final_score, scoring_breakdown = self._calculate_final_score(
                candidate, 
                analysis_results['overview_data'], 
                analysis_results['whale_analysis'], 
                analysis_results['volume_price_analysis'],
                analysis_results['community_boost_analysis'], 
                analysis_results['security_analysis'], 
                analysis_results['trading_activity']
            )"""
    
    content = content.replace(old_call, new_call)
    
    # 4. Update the detailed_analysis dictionary to include scoring_breakdown
    old_detailed_analysis = """            # Create detailed analysis result
            detailed_analysis = {
                'candidate': candidate,
                'final_score': final_score,
                'overview_data': analysis_results['overview_data'],
                'whale_analysis': analysis_results['whale_analysis'],
                'volume_price_analysis': analysis_results['volume_price_analysis'],
                'community_boost_analysis': analysis_results['community_boost_analysis'],
                'security_analysis': analysis_results['security_analysis'],
                'trading_activity': analysis_results['trading_activity'],
                'analysis_timestamp': datetime.now().isoformat(),
                'scan_id': scan_id,
                'analysis_success_rate': (successful_analyses/total_analyses)*100,
                'analysis_errors': analysis_errors,
                'successful_analyses': successful_analyses,
                'total_analyses': total_analyses
            }"""
    
    new_detailed_analysis = """            # Create detailed analysis result
            detailed_analysis = {
                'candidate': candidate,
                'final_score': final_score,
                'scoring_breakdown': scoring_breakdown,
                'overview_data': analysis_results['overview_data'],
                'whale_analysis': analysis_results['whale_analysis'],
                'volume_price_analysis': analysis_results['volume_price_analysis'],
                'community_boost_analysis': analysis_results['community_boost_analysis'],
                'security_analysis': analysis_results['security_analysis'],
                'trading_activity': analysis_results['trading_activity'],
                'analysis_timestamp': datetime.now().isoformat(),
                'scan_id': scan_id,
                'analysis_success_rate': (successful_analyses/total_analyses)*100,
                'analysis_errors': analysis_errors,
                'successful_analyses': successful_analyses,
                'total_analyses': total_analyses
            }"""
    
    content = content.replace(old_detailed_analysis, new_detailed_analysis)
    
    # 5. Also update the partial analysis section
    old_partial = """                final_score = self._calculate_final_score("""
    
    new_partial = """                final_score, scoring_breakdown = self._calculate_final_score("""
    
    # Find the specific instance in the partial analysis section
    if "Returning partial analysis" in content:
        # Find the section and replace it
        partial_section_start = content.find("🔄 Returning partial analysis")
        if partial_section_start != -1:
            # Find the section containing the _calculate_final_score call
            section_start = content.rfind("final_score = self._calculate_final_score(", 0, partial_section_start + 200)
            if section_start != -1:
                section_end = content.find(")", section_start) + 1
                old_section = content[section_start:section_end]
                new_section = old_section.replace("final_score = self._calculate_final_score(", "final_score, scoring_breakdown = self._calculate_final_score(")
                content = content.replace(old_section, new_section)
    
    # Write the updated content back to the file
    with open('scripts/high_conviction_token_detector.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully added detailed scoring breakdown to high conviction detector")
    print("📊 Changes made:")
    print("  • Updated _calculate_final_score to return tuple with breakdown")
    print("  • Added comprehensive scoring_breakdown to detailed analysis results")
    print("  • Updated all calls to _calculate_final_score")
    print("  • Enhanced JSON output with exact scoring details")

if __name__ == "__main__":
    add_scoring_breakdown() 