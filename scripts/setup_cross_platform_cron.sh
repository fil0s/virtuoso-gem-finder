#!/bin/bash

# Setup script for Cross-Platform Token Analyzer Cron Job
# Adds a cron job to run analysis every 15 minutes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_COMMAND="*/15 * * * * cd $SCRIPT_DIR && ./run_cross_platform_analysis.sh >> logs/cross_platform_cron.log 2>&1"

echo "🚀 Setting up Cross-Platform Token Analyzer Cron Job..."
echo "================================================"

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cross_platform_analysis"; then
    echo "⚠️  Cron job already exists!"
    echo "Current cron jobs:"
    crontab -l | grep cross_platform
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
    
    # Remove existing cron job
    crontab -l | grep -v "cross_platform_analysis" | crontab -
    echo "🗑️  Removed existing cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📋 Cron job details:"
    echo "   Schedule: Every 15 minutes"
    echo "   Command: $CRON_COMMAND"
    echo "   Log file: logs/cross_platform_cron.log"
    echo ""
    echo "🔍 Current cron jobs:"
    crontab -l
    echo ""
    echo "📝 To remove this cron job later, run:"
    echo "   crontab -e"
    echo "   (then delete the line containing 'cross_platform_analysis')"
else
    echo "❌ Failed to add cron job"
    exit 1
fi 