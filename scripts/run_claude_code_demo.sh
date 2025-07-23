#!/bin/bash

# Claude Code Integration Demo Launcher
# =====================================

echo "🤖 Claude Code Integration Demo for Virtuoso Gem Hunter"
echo "========================================================"

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code not found!"
    echo "Please install it first: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "✅ Claude Code found: $(claude --version)"

# Check if user is authenticated
echo ""
echo "🔐 Testing authentication..."
if claude --print "test" &> /dev/null; then
    echo "✅ Authentication successful"
else
    echo "⚠️  Authentication required"
    echo "Please run: claude \"Hello\" to authenticate first"
    echo ""
    read -p "Press Enter to continue with authentication..."
    claude "Hello, I'm setting up Claude Code for my quantitative trading system"
fi

echo ""
echo "🚀 Starting Claude Code integration demo..."
echo ""

# Run the Python demo
python3 scripts/demo_claude_code_integration.py

echo ""
echo "📚 For more information, see: docs/guides/CLAUDE_CODE_SETUP_GUIDE.md" 