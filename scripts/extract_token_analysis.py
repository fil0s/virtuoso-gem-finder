#!/usr/bin/env python3
"""
Token Analysis Extractor
Extracts detailed token information from all strategies for comprehensive documentation.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger

# Import all strategies
from core.strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy,
    SmartMoneyWhaleStrategy
)


class TokenAnalysisExtractor:
    """Extract and analyze tokens from all strategies for comprehensive documentation."""
    
    def __init__(self):
        """Initialize the token analysis extractor."""
        self.logger_setup = LoggerSetup("TokenAnalysisExtractor")
        self.logger = self.logger_setup.logger
        self.structured_logger = get_structured_logger('TokenAnalysisExtractor')
        
        # Results storage
        self.all_tokens = {}
        self.strategy_tokens = {}
        self.token_overlap_matrix = {}
        self.analysis_timestamp = int(time.time())
        
        # Initialize strategies
        self.strategies = self._initialize_strategies()
    
    async def _initialize_birdeye_api(self) -> BirdeyeAPI:
        """Initialize BirdeyeAPI with required dependencies."""
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        # Check API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY environment variable not set")
        
        # Initialize services
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Create config for BirdeyeAPI
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        # Create logger for BirdeyeAPI
        from services.logger_setup import LoggerSetup
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ BirdeyeAPI initialized successfully")
        return birdeye_api
        
    def _initialize_strategies(self) -> List[Any]:
        """Initialize all token discovery strategies."""
        strategies = []
        
        try:
            # Initialize each strategy with consistent logger
            strategy_classes = [
                VolumeMomentumStrategy,
                RecentListingsStrategy,
                PriceMomentumStrategy, 
                LiquidityGrowthStrategy,
                HighTradingActivityStrategy,
                SmartMoneyWhaleStrategy
            ]
            
            for strategy_class in strategy_classes:
                try:
                    strategy = strategy_class(logger=self.logger)
                    strategies.append(strategy)
                    self.logger.info(f"✅ Initialized {strategy.name}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {strategy_class.__name__}: {e}")
            
            self.logger.info(f"🚀 Initialized {len(strategies)} strategies total")
            return strategies
            
        except Exception as e:
            self.logger.error(f"Error initializing strategies: {e}")
            return []
    
    async def extract_all_tokens(self) -> Dict[str, Any]:
        """Extract tokens from all strategies."""
        self.logger.info("🔍 Starting comprehensive token extraction")
        self.logger.info("=" * 80)
        
        # Initialize Birdeye API
        birdeye_api = await self._initialize_birdeye_api()
        scan_id = f"token_extraction_{self.analysis_timestamp}"
        
        try:
            # Execute all strategies and collect tokens
            for i, strategy in enumerate(self.strategies, 1):
                strategy_name = strategy.name
                self.logger.info(f"🔍 [{i}/{len(self.strategies)}] Extracting tokens from {strategy_name}")
                
                start_time = time.time()
                
                try:
                    # Execute strategy
                    tokens = await strategy.execute(birdeye_api, scan_id=f"{scan_id}_{strategy_name.lower().replace(' ', '_')}")
                    execution_time = time.time() - start_time
                    
                    # Store tokens with detailed information
                    self.strategy_tokens[strategy_name] = {
                        "tokens": tokens,
                        "token_count": len(tokens),
                        "execution_time": execution_time,
                        "strategy_instance": strategy
                    }
                    
                    # Add to global token collection
                    for token in tokens:
                        token_address = token.get("address")
                        if token_address:
                            if token_address not in self.all_tokens:
                                self.all_tokens[token_address] = {
                                    "token_data": token,
                                    "found_by_strategies": [],
                                    "strategy_count": 0
                                }
                            
                            self.all_tokens[token_address]["found_by_strategies"].append(strategy_name)
                            self.all_tokens[token_address]["strategy_count"] += 1
                    
                    self.logger.info(f"✅ {strategy_name}: {len(tokens)} tokens in {execution_time:.2f}s")
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.logger.error(f"❌ {strategy_name} failed: {e}")
                    
                    # Store error results
                    self.strategy_tokens[strategy_name] = {
                        "tokens": [],
                        "token_count": 0,
                        "execution_time": execution_time,
                        "error": str(e)
                    }
            
            # Calculate overlap matrix
            self._calculate_overlap_matrix()
            
            # Generate comprehensive analysis
            analysis = self._generate_comprehensive_analysis()
            
            self.logger.info("✅ Token extraction complete!")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in token extraction: {e}")
            raise
    
    def _calculate_overlap_matrix(self):
        """Calculate token overlap between strategies."""
        strategy_names = list(self.strategy_tokens.keys())
        
        for strategy1 in strategy_names:
            self.token_overlap_matrix[strategy1] = {}
            tokens1 = set(t.get("address") for t in self.strategy_tokens[strategy1]["tokens"] if t.get("address"))
            
            for strategy2 in strategy_names:
                if strategy1 == strategy2:
                    self.token_overlap_matrix[strategy1][strategy2] = 1.0
                else:
                    tokens2 = set(t.get("address") for t in self.strategy_tokens[strategy2]["tokens"] if t.get("address"))
                    
                    if tokens1 or tokens2:
                        if len(tokens1.union(tokens2)) > 0:
                            overlap = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))
                        else:
                            overlap = 0.0
                        self.token_overlap_matrix[strategy1][strategy2] = overlap
                    else:
                        self.token_overlap_matrix[strategy1][strategy2] = 0.0
    
    def _generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis of all extracted tokens."""
        
        # Strategy performance summary
        strategy_summary = {}
        for strategy_name, data in self.strategy_tokens.items():
            strategy_summary[strategy_name] = {
                "token_count": data["token_count"],
                "execution_time": data.get("execution_time", 0),
                "tokens_per_second": data["token_count"] / data.get("execution_time", 1) if data.get("execution_time", 0) > 0 else 0,
                "error": data.get("error")
            }
        
        # Token overlap analysis
        unique_tokens = len(self.all_tokens)
        multi_strategy_tokens = len([addr for addr, data in self.all_tokens.items() if data["strategy_count"] > 1])
        single_strategy_tokens = unique_tokens - multi_strategy_tokens
        
        # Quality analysis by discovery count
        quality_by_discovery = {}
        for token_data in self.all_tokens.values():
            count = token_data["strategy_count"]
            if count not in quality_by_discovery:
                quality_by_discovery[count] = []
            
            # Get token quality score if available
            score = token_data["token_data"].get("score", 50.0)  # Default score
            quality_by_discovery[count].append(score)
        
        # Calculate averages
        quality_averages = {}
        for count, scores in quality_by_discovery.items():
            quality_averages[count] = {
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "token_count": len(scores)
            }
        
        return {
            "analysis_metadata": {
                "timestamp": self.analysis_timestamp,
                "analysis_date": datetime.fromtimestamp(self.analysis_timestamp).isoformat(),
                "total_strategies": len(self.strategies),
                "successful_strategies": len([s for s in strategy_summary.values() if not s.get("error")]),
                "total_unique_tokens": unique_tokens
            },
            "strategy_performance": strategy_summary,
            "token_overlap_analysis": {
                "total_unique_tokens": unique_tokens,
                "multi_strategy_tokens": multi_strategy_tokens,
                "single_strategy_tokens": single_strategy_tokens,
                "cross_validation_rate": multi_strategy_tokens / unique_tokens if unique_tokens > 0 else 0,
                "overlap_matrix": self.token_overlap_matrix
            },
            "quality_analysis": quality_averages,
            "detailed_tokens": self.all_tokens,
            "strategy_tokens": self.strategy_tokens
        }
    
    async def create_comprehensive_document(self, analysis: Dict[str, Any]) -> str:
        """Create comprehensive markdown document."""
        
        doc = f"""# Comprehensive Token Discovery Strategy Analysis
## Analysis Date: {analysis['analysis_metadata']['analysis_date']}

---

## 📊 Executive Summary

This comprehensive analysis examines the performance and token discovery capabilities of **{analysis['analysis_metadata']['total_strategies']} cryptocurrency token discovery strategies**, providing detailed insights into their effectiveness, overlap patterns, and individual token discoveries.

### 🎯 Key Findings

- **Total Unique Tokens Discovered**: {analysis['analysis_metadata']['total_unique_tokens']}
- **Successful Strategy Executions**: {analysis['analysis_metadata']['successful_strategies']}/{analysis['analysis_metadata']['total_strategies']}
- **Cross-Validation Rate**: {analysis['token_overlap_analysis']['cross_validation_rate']:.1%} of tokens found by multiple strategies
- **Strategy Diversification**: {analysis['token_overlap_analysis']['single_strategy_tokens']} tokens ({analysis['token_overlap_analysis']['single_strategy_tokens']/analysis['analysis_metadata']['total_unique_tokens']*100:.1f}%) are unique to individual strategies

---

## 🏆 Strategy Performance Ranking

"""
        
        # Add strategy performance table
        doc += "| Rank | Strategy | Tokens Found | Execution Time (s) | Tokens/Second | Status |\n"
        doc += "|------|----------|--------------|-------------------|---------------|--------|\n"
        
        # Sort strategies by token count
        sorted_strategies = sorted(analysis['strategy_performance'].items(), 
                                 key=lambda x: x[1]['token_count'], reverse=True)
        
        for rank, (strategy_name, data) in enumerate(sorted_strategies, 1):
            status = "✅ Success" if not data.get('error') else f"❌ Error: {data['error']}"
            doc += f"| {rank} | {strategy_name} | {data['token_count']} | {data['execution_time']:.2f} | {data['tokens_per_second']:.2f} | {status} |\n"
        
        doc += "\n---\n\n"
        
        # Add overlap analysis
        doc += "## 🔄 Token Overlap Analysis\n\n"
        doc += f"### Cross-Strategy Token Discovery\n\n"
        doc += f"- **Unique Tokens**: {analysis['token_overlap_analysis']['total_unique_tokens']}\n"
        doc += f"- **Multi-Strategy Tokens**: {analysis['token_overlap_analysis']['multi_strategy_tokens']} ({analysis['token_overlap_analysis']['cross_validation_rate']:.1%})\n"
        doc += f"- **Single-Strategy Tokens**: {analysis['token_overlap_analysis']['single_strategy_tokens']} ({analysis['token_overlap_analysis']['single_strategy_tokens']/analysis['analysis_metadata']['total_unique_tokens']*100:.1f}%)\n\n"
        
        # Add overlap matrix
        doc += "### Strategy Overlap Matrix\n\n"
        doc += "| Strategy | "
        strategy_names = list(analysis['token_overlap_analysis']['overlap_matrix'].keys())
        doc += " | ".join([name.replace(" Strategy", "") for name in strategy_names]) + " |\n"
        doc += "|" + "---|" * (len(strategy_names) + 1) + "\n"
        
        for strategy1 in strategy_names:
            doc += f"| {strategy1.replace(' Strategy', '')} |"
            for strategy2 in strategy_names:
                overlap = analysis['token_overlap_analysis']['overlap_matrix'][strategy1][strategy2]
                if strategy1 == strategy2:
                    doc += " 100% |"
                else:
                    doc += f" {overlap:.1%} |"
            doc += "\n"
        
        doc += "\n---\n\n"
        
        # Add detailed token table
        doc += "## 📋 Comprehensive Token Discovery Table\n\n"
        doc += "### All Discovered Tokens\n\n"
        
        doc += "| Token Symbol | Token Name | Address | Market Cap | Price | 24h Change | Strategies Found By | Discovery Count |\n"
        doc += "|--------------|------------|---------|------------|-------|------------|-------------------|----------------|\n"
        
        # Sort tokens by strategy count (most cross-validated first)
        sorted_tokens = sorted(analysis['detailed_tokens'].items(), 
                             key=lambda x: x[1]['strategy_count'], reverse=True)
        
        for token_address, token_info in sorted_tokens:
            token_data = token_info['token_data']
            symbol = token_data.get('symbol', 'N/A')
            name = token_data.get('name', 'N/A')
            market_cap = token_data.get('market_cap', 0)
            price = token_data.get('price', 0)
            price_change_24h = token_data.get('price_change_24h_percent', 0)
            
            # Format market cap
            if market_cap > 1_000_000_000:
                market_cap_str = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap > 1_000_000:
                market_cap_str = f"${market_cap/1_000_000:.2f}M"
            elif market_cap > 1_000:
                market_cap_str = f"${market_cap/1_000:.2f}K"
            else:
                market_cap_str = f"${market_cap:.2f}"
            
            # Format price
            if price > 1:
                price_str = f"${price:.4f}"
            else:
                price_str = f"${price:.8f}"
            
            # Format price change
            change_sign = "+" if price_change_24h >= 0 else ""
            price_change_str = f"{change_sign}{price_change_24h:.2f}%"
            
            # Truncate address for display
            display_address = f"{token_address[:8]}...{token_address[-8:]}"
            
            # Format strategies
            strategies_str = ", ".join([s.replace(" Strategy", "") for s in token_info['found_by_strategies']])
            
            doc += f"| {symbol} | {name} | `{display_address}` | {market_cap_str} | {price_str} | {price_change_str} | {strategies_str} | {token_info['strategy_count']} |\n"
        
        doc += "\n---\n\n"
        
        # Add strategy-specific token lists
        doc += "## 📈 Strategy-Specific Token Discoveries\n\n"
        
        for strategy_name, data in analysis['strategy_tokens'].items():
            if data['token_count'] > 0:
                doc += f"### {strategy_name}\n\n"
                doc += f"**Tokens Found**: {data['token_count']} | **Execution Time**: {data['execution_time']:.2f}s | **Rate**: {data['tokens_per_second']:.2f} tokens/sec\n\n"
                
                doc += "| Symbol | Name | Market Cap | Price | 24h Change | Address |\n"
                doc += "|--------|------|------------|-------|------------|----------|\n"
                
                for token in data['tokens']:
                    symbol = token.get('symbol', 'N/A')
                    name = token.get('name', 'N/A')
                    market_cap = token.get('market_cap', 0)
                    price = token.get('price', 0)
                    price_change_24h = token.get('price_change_24h_percent', 0)
                    address = token.get('address', 'N/A')
                    
                    # Format values
                    if market_cap > 1_000_000_000:
                        market_cap_str = f"${market_cap/1_000_000_000:.2f}B"
                    elif market_cap > 1_000_000:
                        market_cap_str = f"${market_cap/1_000_000:.2f}M"
                    elif market_cap > 1_000:
                        market_cap_str = f"${market_cap/1_000:.2f}K"
                    else:
                        market_cap_str = f"${market_cap:.2f}"
                    
                    if price > 1:
                        price_str = f"${price:.4f}"
                    else:
                        price_str = f"${price:.8f}"
                    
                    change_sign = "+" if price_change_24h >= 0 else ""
                    price_change_str = f"{change_sign}{price_change_24h:.2f}%"
                    
                    display_address = f"{address[:8]}...{address[-8:]}" if len(address) > 16 else address
                    
                    doc += f"| {symbol} | {name} | {market_cap_str} | {price_str} | {price_change_str} | `{display_address}` |\n"
                
                doc += "\n"
        
        doc += "\n---\n\n"
        
        # Add quality analysis
        doc += "## 🎯 Quality Analysis by Discovery Count\n\n"
        doc += "Analysis of token quality based on how many strategies discovered them:\n\n"
        
        doc += "| Discovery Count | Token Count | Average Quality Score | Interpretation |\n"
        doc += "|----------------|-------------|---------------------|----------------|\n"
        
        for count in sorted(analysis['quality_analysis'].keys(), reverse=True):
            data = analysis['quality_analysis'][count]
            if count == 1:
                interpretation = "Unique discoveries - may be niche opportunities"
            elif count == 2:
                interpretation = "Moderate validation - worth investigating"
            elif count >= 3:
                interpretation = "High validation - strong consensus"
            else:
                interpretation = "Unknown"
            
            doc += f"| {count} | {data['token_count']} | {data['avg_score']:.2f} | {interpretation} |\n"
        
        doc += "\n---\n\n"
        
        # Add recommendations
        doc += "## 🎯 Strategic Recommendations\n\n"
        doc += "### Portfolio Diversification Strategy\n\n"
        
        # Find best performing strategies
        top_strategies = sorted(analysis['strategy_performance'].items(), 
                               key=lambda x: x[1]['token_count'], reverse=True)[:3]
        
        doc += f"**Primary Strategies** (High Volume Discovery):\n"
        for strategy_name, data in top_strategies:
            if data['token_count'] > 0:
                doc += f"- **{strategy_name}**: {data['token_count']} tokens - Best for broad market coverage\n"
        
        doc += f"\n**Specialized Strategies** (Quality Focus):\n"
        specialized = [s for s in analysis['strategy_performance'].items() if s[1]['token_count'] > 0 and s[0] not in [t[0] for t in top_strategies]]
        for strategy_name, data in specialized:
            doc += f"- **{strategy_name}**: {data['token_count']} tokens - Best for targeted opportunities\n"
        
        doc += f"\n### Implementation Recommendations\n\n"
        doc += f"1. **Multi-Strategy Approach**: Use combination of high-volume and specialized strategies\n"
        doc += f"2. **Cross-Validation Focus**: Prioritize tokens found by 2+ strategies ({analysis['token_overlap_analysis']['multi_strategy_tokens']} tokens)\n"
        doc += f"3. **Unique Opportunity Mining**: Don't ignore single-strategy discoveries ({analysis['token_overlap_analysis']['single_strategy_tokens']} unique tokens)\n"
        doc += f"4. **Quality Filtering**: Implement additional quality checks for high-volume discoveries\n\n"
        
        doc += "---\n\n"
        doc += f"*Analysis generated on {analysis['analysis_metadata']['analysis_date']}*\n"
        doc += f"*Total execution time: {sum(d['execution_time'] for d in analysis['strategy_performance'].values()):.2f} seconds*\n"
        
        return doc
    
    async def save_analysis(self, analysis: Dict[str, Any], document: str):
        """Save analysis results and documentation."""
        try:
            # Create results directory
            results_dir = Path("docs")
            results_dir.mkdir(exist_ok=True)
            
            timestamp_str = datetime.fromtimestamp(self.analysis_timestamp).strftime("%Y%m%d_%H%M%S")
            
            # Save raw analysis data
            analysis_file = results_dir / f"comprehensive_token_analysis_{timestamp_str}.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            # Save comprehensive document
            doc_file = results_dir / f"Comprehensive_Token_Discovery_Analysis_{timestamp_str}.md"
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(document)
            
            self.logger.info(f"📊 Analysis data saved to: {analysis_file}")
            self.logger.info(f"📋 Comprehensive document saved to: {doc_file}")
            
            return str(doc_file)
            
        except Exception as e:
            self.logger.error(f"Error saving analysis: {e}")
            raise


async def main():
    """Main function to run comprehensive token analysis."""
    print("🚀 Starting Comprehensive Token Analysis & Documentation")
    print("=" * 80)
    
    try:
        extractor = TokenAnalysisExtractor()
        
        # Extract all tokens
        analysis = await extractor.extract_all_tokens()
        
        # Create comprehensive document
        document = await extractor.create_comprehensive_document(analysis)
        
        # Save results
        doc_path = await extractor.save_analysis(analysis, document)
        
        print("\n" + "=" * 80)
        print("✅ COMPREHENSIVE TOKEN ANALYSIS COMPLETE!")
        print("=" * 80)
        print(f"📊 Total Unique Tokens: {analysis['analysis_metadata']['total_unique_tokens']}")
        print(f"📈 Successful Strategies: {analysis['analysis_metadata']['successful_strategies']}/{analysis['analysis_metadata']['total_strategies']}")
        print(f"🔄 Cross-Validation Rate: {analysis['token_overlap_analysis']['cross_validation_rate']:.1%}")
        print(f"📋 Documentation saved to: {doc_path}")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 