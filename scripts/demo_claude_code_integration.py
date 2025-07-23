#!/usr/bin/env python3
"""
Claude Code Integration Demo for Virtuoso Gem Hunter
===================================================

This script demonstrates how to integrate Claude Code with your quantitative trading system.
Run this after setting up Claude Code authentication.
"""

import os
import subprocess
import json
from datetime import datetime

def run_claude_command(prompt, model="sonnet", print_output=True):
    """Run a Claude Code command and return the result."""
    cmd = ["claude"]
    if model:
        cmd.extend(["--model", model])
    if print_output:
        cmd.append("--print")
    cmd.append(prompt)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def demo_codebase_analysis():
    """Demo: Analyze the codebase structure."""
    print("🔍 DEMO 1: Codebase Analysis")
    print("=" * 50)
    
    prompt = """
    Analyze the structure of this quantitative trading system. Focus on:
    1. Main components and their relationships
    2. API integration patterns
    3. Token discovery strategies
    4. Data flow between modules
    
    Provide a high-level architectural overview.
    """
    
    print("Running Claude Code analysis...")
    result = run_claude_command(prompt, model="sonnet")
    print(result)
    return result

def demo_api_optimization():
    """Demo: API optimization suggestions."""
    print("\n💰 DEMO 2: API Cost Optimization")
    print("=" * 50)
    
    prompt = """
    Review the API connectors in the api/ directory and suggest optimizations for:
    1. Rate limiting efficiency
    2. Batch processing opportunities
    3. Caching strategies
    4. Cost reduction techniques
    
    Focus on birdeye_connector.py and jupiter_connector.py.
    """
    
    print("Running API optimization analysis...")
    result = run_claude_command(prompt, model="sonnet")
    print(result)
    return result

def demo_bug_investigation():
    """Demo: Help with debugging common issues."""
    print("\n🐛 DEMO 3: Bug Investigation")
    print("=" * 50)
    
    prompt = """
    Examine the smart money detection system and identify potential issues:
    1. Look at services/smart_money_detector.py
    2. Check for common bugs in skill calculations
    3. Suggest improvements for accuracy
    4. Identify edge cases that might cause problems
    
    Provide specific code fixes if issues are found.
    """
    
    print("Running bug investigation...")
    result = run_claude_command(prompt, model="sonnet")
    print(result)
    return result

def demo_feature_enhancement():
    """Demo: Suggest feature enhancements."""
    print("\n🚀 DEMO 4: Feature Enhancement Suggestions")
    print("=" * 50)
    
    prompt = """
    Based on the current token discovery strategies, suggest 3 new features that could improve:
    1. Detection accuracy
    2. Execution speed
    3. Profit potential
    
    For each suggestion, provide:
    - Implementation approach
    - Required API integrations
    - Estimated complexity
    """
    
    print("Running feature enhancement analysis...")
    result = run_claude_command(prompt, model="opus")  # Use Opus for complex analysis
    print(result)
    return result

def demo_documentation_generation():
    """Demo: Generate documentation."""
    print("\n📚 DEMO 5: Documentation Generation")
    print("=" * 50)
    
    prompt = """
    Generate comprehensive documentation for the high conviction token detector:
    1. Analyze scripts/high_conviction_token_detector.py
    2. Create API documentation
    3. Explain the scoring algorithm
    4. Provide usage examples
    5. Document configuration options
    
    Format as markdown.
    """
    
    print("Generating documentation...")
    result = run_claude_command(prompt, model="sonnet")
    print(result)
    return result

def check_claude_installation():
    """Check if Claude Code is properly installed."""
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Claude Code installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Claude Code not properly installed")
            return False
    except FileNotFoundError:
        print("❌ Claude Code not found. Please install it first.")
        return False

def main():
    """Run all Claude Code integration demos."""
    print("🤖 Claude Code Integration Demo for Virtuoso Gem Hunter")
    print("=" * 60)
    
    # Check installation
    if not check_claude_installation():
        print("\nPlease install Claude Code first:")
        print("npm install -g @anthropic-ai/claude-code")
        return
    
    print("\n⚠️  IMPORTANT: Make sure you've authenticated with Claude Code")
    print("Run: claude \"Hello\" to complete authentication if you haven't already")
    
    input("\nPress Enter to continue with demos...")
    
    # Run demos
    demos = [
        demo_codebase_analysis,
        demo_api_optimization,
        demo_bug_investigation,
        demo_feature_enhancement,
        demo_documentation_generation
    ]
    
    results = {}
    for demo in demos:
        try:
            result = demo()
            results[demo.__name__] = result
        except Exception as e:
            print(f"Error in {demo.__name__}: {str(e)}")
            results[demo.__name__] = f"Error: {str(e)}"
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"scripts/results/claude_code_demo_results_{timestamp}.json"
    
    os.makedirs("scripts/results", exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n🎉 Claude Code integration demo complete!")
    print("\nNext steps:")
    print("1. Review the analysis results")
    print("2. Try interactive mode: claude")
    print("3. Integrate Claude Code into your development workflow")
    print("4. Check the setup guide: docs/guides/CLAUDE_CODE_SETUP_GUIDE.md")

if __name__ == "__main__":
    main() 