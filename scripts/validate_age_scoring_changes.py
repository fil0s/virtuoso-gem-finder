#!/usr/bin/env python3
"""
Enhanced Age Scoring Validation Script

This script validates the enhanced age scoring system against real token data
to ensure it works correctly in production scenarios.

Usage:
    python scripts/validate_age_scoring_changes.py [--sample-size 100] [--compare-old]
"""

import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import glob

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AgeScoringValidator:
    """Validates enhanced age scoring against real token data."""
    
    def __init__(self, sample_size: int = 100, compare_old: bool = False):
        self.sample_size = sample_size
        self.compare_old = compare_old
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Validation results
        self.validation_results = {
            'tokens_tested': 0,
            'ultra_new_count': 0,
            'extremely_new_count': 0,
            'bonus_applications': 0,
            'score_improvements': 0,
            'errors': []
        }
        
    def setup_logging(self):
        """Setup logging for validation."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/age_scoring_validation.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_recent_token_data(self) -> List[Dict[str, Any]]:
        """Load recent token data from test results."""
        self.logger.info("📂 Loading recent token data...")
        
        # Look for recent test results
        results_dir = project_root / "scripts" / "results"
        test_files = []
        
        if results_dir.exists():
            # Find recent test result files
            patterns = [
                "high_conviction_results_*.json",
                "enhanced_results_*.json",
                "test_results_*.json",
                "*_token_analysis_*.json"
            ]
            
            for pattern in patterns:
                test_files.extend(glob.glob(str(results_dir / pattern)))
        
        # Sort by modification time (newest first)
        test_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        all_tokens = []
        files_loaded = 0
        
        for file_path in test_files[:5]:  # Load up to 5 most recent files
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract tokens from different file formats
                tokens = []
                if isinstance(data, dict):
                    if 'tokens' in data:
                        tokens = data['tokens']
                    elif 'discovered_tokens' in data:
                        tokens = data['discovered_tokens']
                    elif 'results' in data:
                        tokens = data['results']
                elif isinstance(data, list):
                    tokens = data
                
                if tokens:
                    all_tokens.extend(tokens)
                    files_loaded += 1
                    self.logger.info(f"📄 Loaded {len(tokens)} tokens from {Path(file_path).name}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load {file_path}: {e}")
        
        self.logger.info(f"📊 Total tokens loaded: {len(all_tokens)} from {files_loaded} files")
        
        # Sample tokens if we have too many
        if len(all_tokens) > self.sample_size:
            import random
            all_tokens = random.sample(all_tokens, self.sample_size)
            self.logger.info(f"📊 Sampled {self.sample_size} tokens for validation")
        
        return all_tokens
    
    def enhanced_age_scoring(self, creation_time: float, current_time: float) -> Tuple[float, float]:
        """Enhanced age scoring function."""
        if not creation_time:
            return 12.5, 1.0
        
        age_seconds = current_time - creation_time
        age_minutes = age_seconds / 60
        age_hours = age_seconds / 3600
        age_days = age_seconds / 86400
        
        # Enhanced 8-tier age scoring with bonus multipliers
        if age_minutes <= 30:      # Ultra-new (≤30 min)
            return 120, 1.20
        elif age_hours <= 2:       # Extremely new (30min-2h)
            return 110, 1.10
        elif age_hours <= 6:       # Very new (2-6h)
            return 100, 1.0
        elif age_hours <= 24:      # New (6-24h)
            return 85, 1.0
        elif age_days <= 3:        # Recent (1-3 days)
            return 65, 1.0
        elif age_days <= 7:        # Moderate (3-7 days)
            return 45, 1.0
        elif age_days <= 30:       # Established (7-30 days)
            return 25, 1.0
        else:                      # Mature (>30 days)
            return 10, 1.0
    
    def old_age_scoring(self, creation_time: float, current_time: float) -> float:
        """Old age scoring function for comparison."""
        if not creation_time:
            return 10
        
        age_hours = (current_time - creation_time) / 3600
        
        if age_hours <= 24:
            return 100
        elif age_hours <= 72:
            return 75
        elif age_hours <= 168:  # 1 week
            return 50
        else:
            return 25
    
    def extract_creation_time(self, token: Dict[str, Any]) -> float:
        """Extract creation time from token data."""
        # Try different possible field names
        time_fields = [
            'creation_time',
            'created_at',
            'timestamp',
            'listing_time',
            'first_seen',
            'launch_time'
        ]
        
        for field in time_fields:
            if field in token and token[field]:
                creation_time = token[field]
                # Handle different time formats
                if isinstance(creation_time, (int, float)):
                    return float(creation_time)
                elif isinstance(creation_time, str):
                    try:
                        return float(creation_time)
                    except ValueError:
                        continue
        
        return None
    
    def validate_token_scoring(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate enhanced age scoring on real token data."""
        self.logger.info("🧪 Validating enhanced age scoring on real tokens...")
        
        current_time = time.time()
        validation_summary = {
            'total_tokens': len(tokens),
            'tokens_with_age': 0,
            'ultra_new_tokens': [],
            'extremely_new_tokens': [],
            'score_comparisons': [],
            'age_distribution': {
                'ultra_new': 0,      # ≤30 min
                'extremely_new': 0,  # 30min-2h
                'very_new': 0,       # 2-6h
                'new': 0,            # 6-24h
                'recent': 0,         # 1-3 days
                'moderate': 0,       # 3-7 days
                'established': 0,    # 7-30 days
                'mature': 0          # >30 days
            }
        }
        
        for i, token in enumerate(tokens):
            try:
                # Extract basic token info
                symbol = token.get('symbol', token.get('name', f'TOKEN_{i}'))
                address = token.get('address', token.get('token_address', 'unknown'))
                
                # Extract creation time
                creation_time = self.extract_creation_time(token)
                
                if not creation_time:
                    self.logger.debug(f"⚠️ No creation time found for {symbol}")
                    continue
                
                validation_summary['tokens_with_age'] += 1
                
                # Calculate age
                age_seconds = current_time - creation_time
                age_minutes = age_seconds / 60
                age_hours = age_seconds / 3600
                age_days = age_seconds / 86400
                
                # Enhanced scoring
                enhanced_score, bonus_multiplier = self.enhanced_age_scoring(creation_time, current_time)
                
                # Old scoring for comparison
                old_score = self.old_age_scoring(creation_time, current_time) if self.compare_old else 0
                
                # Categorize by age
                if age_minutes <= 30:
                    validation_summary['age_distribution']['ultra_new'] += 1
                    validation_summary['ultra_new_tokens'].append({
                        'symbol': symbol,
                        'age_minutes': age_minutes,
                        'enhanced_score': enhanced_score,
                        'bonus_multiplier': bonus_multiplier
                    })
                    self.validation_results['ultra_new_count'] += 1
                elif age_hours <= 2:
                    validation_summary['age_distribution']['extremely_new'] += 1
                    validation_summary['extremely_new_tokens'].append({
                        'symbol': symbol,
                        'age_hours': age_hours,
                        'enhanced_score': enhanced_score,
                        'bonus_multiplier': bonus_multiplier
                    })
                    self.validation_results['extremely_new_count'] += 1
                elif age_hours <= 6:
                    validation_summary['age_distribution']['very_new'] += 1
                elif age_hours <= 24:
                    validation_summary['age_distribution']['new'] += 1
                elif age_days <= 3:
                    validation_summary['age_distribution']['recent'] += 1
                elif age_days <= 7:
                    validation_summary['age_distribution']['moderate'] += 1
                elif age_days <= 30:
                    validation_summary['age_distribution']['established'] += 1
                else:
                    validation_summary['age_distribution']['mature'] += 1
                
                # Track bonus applications
                if bonus_multiplier > 1.0:
                    self.validation_results['bonus_applications'] += 1
                
                # Score comparison
                if self.compare_old:
                    score_comparison = {
                        'symbol': symbol,
                        'age_hours': age_hours,
                        'old_score': old_score,
                        'enhanced_score': enhanced_score,
                        'bonus_multiplier': bonus_multiplier,
                        'improvement': enhanced_score - old_score
                    }
                    validation_summary['score_comparisons'].append(score_comparison)
                    
                    if enhanced_score > old_score:
                        self.validation_results['score_improvements'] += 1
                
                # Log interesting cases
                if age_minutes <= 30:
                    self.logger.info(f"🔥 ULTRA-NEW: {symbol} ({age_minutes:.1f} min) - Score: {enhanced_score}, Bonus: {bonus_multiplier:.2f}x")
                elif age_hours <= 2:
                    self.logger.info(f"⚡ EXTREMELY NEW: {symbol} ({age_hours:.1f}h) - Score: {enhanced_score}, Bonus: {bonus_multiplier:.2f}x")
                
                self.validation_results['tokens_tested'] += 1
                
            except Exception as e:
                error_msg = f"Error processing token {symbol}: {e}"
                self.logger.error(f"❌ {error_msg}")
                self.validation_results['errors'].append(error_msg)
        
        return validation_summary
    
    def analyze_score_distribution(self, validation_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the score distribution and improvements."""
        self.logger.info("📊 Analyzing score distribution...")
        
        age_dist = validation_summary['age_distribution']
        total_with_age = validation_summary['tokens_with_age']
        
        if total_with_age == 0:
            self.logger.warning("⚠️ No tokens with age data found")
            return {}
        
        # Calculate percentages
        distribution_percentages = {}
        for category, count in age_dist.items():
            percentage = (count / total_with_age) * 100
            distribution_percentages[category] = percentage
            self.logger.info(f"📈 {category.replace('_', ' ').title()}: {count} tokens ({percentage:.1f}%)")
        
        # Analyze bonus applications
        bonus_rate = (self.validation_results['bonus_applications'] / total_with_age) * 100
        self.logger.info(f"🎯 Bonus applications: {self.validation_results['bonus_applications']} ({bonus_rate:.1f}%)")
        
        # Analyze improvements (if comparing with old scoring)
        if self.compare_old and validation_summary['score_comparisons']:
            improvements = [comp['improvement'] for comp in validation_summary['score_comparisons']]
            avg_improvement = sum(improvements) / len(improvements)
            improvement_rate = (self.validation_results['score_improvements'] / len(improvements)) * 100
            
            self.logger.info(f"📈 Average score improvement: {avg_improvement:.1f} points")
            self.logger.info(f"📈 Tokens with improved scores: {self.validation_results['score_improvements']} ({improvement_rate:.1f}%)")
        
        return {
            'distribution_percentages': distribution_percentages,
            'bonus_rate': bonus_rate,
            'total_analyzed': total_with_age
        }
    
    def generate_validation_report(self, validation_summary: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate comprehensive validation report."""
        
        report = f"""
# Enhanced Age Scoring Validation Report

## Validation Summary
- **Total Tokens Loaded**: {validation_summary['total_tokens']}
- **Tokens with Age Data**: {validation_summary['tokens_with_age']}
- **Ultra-new Tokens Found**: {self.validation_results['ultra_new_count']}
- **Extremely New Tokens Found**: {self.validation_results['extremely_new_count']}
- **Bonus Applications**: {self.validation_results['bonus_applications']}
- **Errors Encountered**: {len(self.validation_results['errors'])}

## Age Distribution Analysis
"""
        
        if analysis.get('distribution_percentages'):
            for category, percentage in analysis['distribution_percentages'].items():
                count = validation_summary['age_distribution'][category]
                report += f"- **{category.replace('_', ' ').title()}**: {count} tokens ({percentage:.1f}%)\n"
        
        report += f"\n## Bonus Multiplier Analysis\n"
        report += f"- **Bonus Application Rate**: {analysis.get('bonus_rate', 0):.1f}%\n"
        report += f"- **Ultra-new Bonus (20%)**: {self.validation_results['ultra_new_count']} tokens\n"
        report += f"- **Extremely New Bonus (10%)**: {self.validation_results['extremely_new_count']} tokens\n"
        
        if self.compare_old and validation_summary.get('score_comparisons'):
            improvements = [comp['improvement'] for comp in validation_summary['score_comparisons']]
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            improvement_rate = (self.validation_results['score_improvements'] / len(improvements)) * 100 if improvements else 0
            
            report += f"\n## Score Improvement Analysis\n"
            report += f"- **Average Score Improvement**: {avg_improvement:.1f} points\n"
            report += f"- **Improvement Rate**: {improvement_rate:.1f}%\n"
            report += f"- **Tokens with Better Scores**: {self.validation_results['score_improvements']}\n"
        
        # Ultra-new tokens details
        if validation_summary['ultra_new_tokens']:
            report += f"\n## Ultra-new Tokens (≤30 minutes)\n"
            for token in validation_summary['ultra_new_tokens'][:10]:  # Show first 10
                report += f"- **{token['symbol']}**: {token['age_minutes']:.1f} min old, Score: {token['enhanced_score']}, Bonus: {token['bonus_multiplier']:.2f}x\n"
        
        # Extremely new tokens details
        if validation_summary['extremely_new_tokens']:
            report += f"\n## Extremely New Tokens (30min-2h)\n"
            for token in validation_summary['extremely_new_tokens'][:10]:  # Show first 10
                report += f"- **{token['symbol']}**: {token['age_hours']:.1f}h old, Score: {token['enhanced_score']}, Bonus: {token['bonus_multiplier']:.2f}x\n"
        
        if self.validation_results['errors']:
            report += f"\n## Errors Encountered\n"
            for error in self.validation_results['errors'][:5]:  # Show first 5 errors
                report += f"- {error}\n"
        
        report += f"\n## Validation Status\n"
        if len(self.validation_results['errors']) == 0:
            report += "✅ **VALIDATION PASSED** - Enhanced age scoring working correctly\n"
        elif len(self.validation_results['errors']) < validation_summary['tokens_with_age'] * 0.1:
            report += "⚠️ **VALIDATION PASSED WITH WARNINGS** - Minor issues detected\n"
        else:
            report += "❌ **VALIDATION FAILED** - Significant issues detected\n"
        
        report += f"\nGenerated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def run_validation(self) -> bool:
        """Run complete validation process."""
        self.logger.info("🚀 Starting Enhanced Age Scoring Validation")
        
        try:
            # Load token data
            tokens = self.load_recent_token_data()
            
            if not tokens:
                self.logger.error("❌ No token data found for validation")
                return False
            
            # Validate scoring
            validation_summary = self.validate_token_scoring(tokens)
            
            # Analyze results
            analysis = self.analyze_score_distribution(validation_summary)
            
            # Generate report
            report = self.generate_validation_report(validation_summary, analysis)
            report_path = project_root / "docs" / "summaries" / "ENHANCED_AGE_SCORING_VALIDATION_RESULTS.md"
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            self.logger.info(f"📄 Validation report saved: {report_path}")
            
            # Determine validation success
            error_rate = len(self.validation_results['errors']) / max(1, self.validation_results['tokens_tested'])
            success = error_rate < 0.1  # Less than 10% error rate
            
            if success:
                self.logger.info("🎉 Validation completed successfully!")
            else:
                self.logger.error(f"❌ Validation failed - Error rate: {error_rate:.1%}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Validation failed with error: {e}")
            return False

def main():
    """Main entry point for validation script."""
    
    parser = argparse.ArgumentParser(description='Enhanced Age Scoring Validation')
    parser.add_argument('--sample-size', type=int, default=100, help='Number of tokens to sample for validation')
    parser.add_argument('--compare-old', action='store_true', help='Compare with old scoring system')
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Run validation
    validator = AgeScoringValidator(sample_size=args.sample_size, compare_old=args.compare_old)
    success = validator.run_validation()
    
    if success:
        print("\n🎉 Validation completed successfully!")
        print("📄 Check the validation report for detailed results")
        sys.exit(0)
    else:
        print("\n❌ Validation failed - check logs for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 