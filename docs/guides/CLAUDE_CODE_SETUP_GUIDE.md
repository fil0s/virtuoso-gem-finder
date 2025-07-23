# Claude Code Setup Guide for Virtuoso Gem Hunter

## Overview
Claude Code is Anthropic's command-line AI assistant that provides deep codebase understanding and can make coordinated changes across multiple files. This guide will help you integrate it with your quantitative trading system.

## ✅ Installation Complete
- **Status**: Claude Code v1.0.35 is installed
- **Command**: `claude` (not `claude-code`)
- **Location**: `/usr/local/bin/claude`

## 🔐 Authentication Setup

You have two authentication options:

### Option 1: Claude Pro/Max Subscription (Recommended)
- **Pro Plan**: $17/month (annual) or $20/month - includes Claude Code with Sonnet 4
- **Max Plans**: $100-200/month - includes Claude Code with both Sonnet 4 & Opus 4
- **Benefits**: Higher usage limits, access to latest models

### Option 2: Anthropic Console (Pay-as-you-go)
- **Pricing**: Standard API rates
- **Benefits**: No monthly subscription, pay only for usage
- **Setup**: Create account at console.anthropic.com

## 🚀 Getting Started

### 1. First Run & Authentication
```bash
claude "Hello, can you help me understand my codebase?"
```
This will trigger the authentication flow where you'll be prompted to sign in.

### 2. Basic Commands
```bash
# Interactive session
claude

# One-off questions
claude "Explain the token discovery strategy"

# Continue previous conversation
claude --continue

# Resume specific session
claude --resume

# Use specific model
claude --model opus "Complex refactoring task"
```

## 🎯 Practical Use Cases for Your Trading System

### 1. Codebase Understanding
```bash
claude "Analyze the relationship between the token discovery strategies and API connectors. Show me the data flow."
```

### 2. Bug Investigation
```bash
claude "I'm seeing API rate limit issues in the birdeye connector. Help me debug and optimize the rate limiting."
```

### 3. Performance Optimization
```bash
claude "Review the cross-platform token analyzer for performance bottlenecks and suggest optimizations."
```

### 4. Feature Implementation
```bash
claude "I want to add a new DeFi protocol integration. Help me implement it following the existing patterns."
```

### 5. Code Refactoring
```bash
claude "Refactor the smart money detection system to be more modular and testable."
```

### 6. Documentation Generation
```bash
claude "Generate comprehensive API documentation for all the connector classes."
```

## 🛠 Configuration Options

### Model Selection
```bash
# Set default model
claude config set model opus

# Available models: sonnet, opus, haiku
```

### Tool Permissions
```bash
# Allow specific tools
claude config set allowedTools "Bash(git:*) Edit FileSearch"

# Disallow dangerous tools
claude config set disallowedTools "Bash(rm:*) Bash(sudo:*)"
```

### Directory Access
```bash
# Add additional directories
claude --add-dir /path/to/additional/code
```

## 💡 Best Practices for Trading Systems

### 1. **Cost Management**
- Use `--print` flag for non-interactive queries to save tokens
- Start with Sonnet 4 for most tasks, use Opus 4 for complex analysis
- Monitor usage through your subscription dashboard

### 2. **Security Considerations**
- Never share API keys or sensitive trading data in prompts
- Use `--disallowedTools` to restrict dangerous operations
- Review all suggested changes before applying

### 3. **Workflow Integration**
```bash
# Create aliases for common tasks
alias claude-analyze="claude --model sonnet 'Analyze the current token discovery performance'"
alias claude-debug="claude --model opus 'Help me debug the current issue'"
```

### 4. **Version Control Integration**
```bash
# Before major changes
git checkout -b claude-refactor-$(date +%Y%m%d)

# Let Claude help with commits
claude "Generate a comprehensive commit message for these changes"
```

## 🔍 Debugging Common Issues

### Authentication Problems
```bash
# Check configuration
claude config list

# Reset authentication
claude config remove apiKey
```

### Model Access Issues
```bash
# Check available models
claude config get model

# Fall back to different model
claude --fallback-model sonnet "Your query here"
```

### Permission Errors
```bash
# Check current permissions
claude config get allowedTools

# Accept trust dialog
claude config set hasTrustDialogAccepted true
```

## 📊 Integration with Your Current Workflow

### 1. **API Optimization**
Claude Code can help optimize your API usage patterns:
```bash
claude "Review all API connectors and suggest batching strategies to reduce costs"
```

### 2. **Strategy Enhancement**
```bash
claude "Analyze the high conviction token detector and suggest improvements based on the latest results"
```

### 3. **Monitoring Integration**
```bash
claude "Help me create better alerting for the trading system based on the current monitoring setup"
```

### 4. **Testing Automation**
```bash
claude "Generate comprehensive unit tests for the smart money detection system"
```

## 🎯 Next Steps

1. **Authenticate**: Run `claude` and complete the sign-in process
2. **Test Basic Functionality**: Try the example commands above
3. **Explore Your Codebase**: Ask Claude to analyze your token discovery system
4. **Set Up Workflows**: Create aliases and configurations for your common tasks
5. **Integrate with Development**: Use Claude for debugging, refactoring, and feature development

## 📚 Advanced Features

### MCP (Model Context Protocol) Integration
```bash
# Configure MCP servers for extended capabilities
claude mcp --help
```

### IDE Integration
```bash
# Auto-connect to VS Code or JetBrains
claude --ide
```

### Batch Processing
```bash
# Process multiple files
claude --print "Optimize all API connector files" > optimization_report.md
```

## ⚠️ Important Notes

- Claude Code works locally and asks permission before making changes
- It integrates with your existing tools (git, npm, etc.)
- All file modifications require explicit approval
- Usage is tracked against your subscription or API limits

## 🆘 Support

- Documentation: https://docs.anthropic.com/claude-code
- Issues: Check `claude doctor` for health diagnostics
- Updates: Run `claude update` to check for new versions

---

**Ready to supercharge your quantitative trading development with AI assistance!** 🚀📈 