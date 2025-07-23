#!/bin/bash

# ====================================================================================
# VIRTUOSO GEM HUNTER - ENVIRONMENT SETUP SCRIPT
# ====================================================================================
# This script automates the initial setup of environment configuration

set -e  # Exit on any error

echo "🚀 Virtuoso Gem Hunter - Environment Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running from correct directory
if [ ! -f "monitor.py" ]; then
    print_error "Please run this script from the virtuoso_gem_hunter root directory"
    exit 1
fi

echo
print_info "Setting up environment configuration..."

# 1. Setup .env file
echo
echo "1. Environment Variables Setup"
echo "==============================="

if [ -f ".env" ]; then
    print_warning ".env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping .env file creation"
    else
        cp env.template .env
        print_status "Created new .env file from template"
    fi
else
    cp env.template .env
    print_status "Created .env file from template"
fi

# 2. Setup config.yaml
echo
echo "2. Configuration File Setup"
echo "============================"

if [ -f "config/config.yaml" ]; then
    print_status "config.yaml already exists"
else
    cp config/config.example.yaml config/config.yaml
    print_status "Created config.yaml from example template"
fi

# 3. Create necessary directories
echo
echo "3. Directory Structure Setup"
echo "============================"

mkdir -p logs data debug temp/app_cache
print_status "Created necessary directories"

# 4. Check Python environment
echo
echo "4. Python Environment Check"
echo "============================"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python 3 found: $PYTHON_VERSION"
else
    print_error "Python 3 not found! Please install Python 3.8 or higher"
    exit 1
fi

# 5. Virtual environment setup
echo
echo "5. Virtual Environment Setup"
echo "============================"

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# 6. Install dependencies
echo
echo "6. Dependencies Installation"
echo "============================"

source venv/bin/activate

if [ ! -f ".requirements_installed" ] || [ requirements.txt -nt .requirements_installed ]; then
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    touch .requirements_installed
    print_status "Dependencies installed successfully"
else
    print_status "Dependencies already up to date"
fi

# 7. Configuration guidance
echo
echo "=========================================="
echo "🎯 NEXT STEPS - MANUAL CONFIGURATION"
echo "=========================================="

print_info "Your environment is set up! Now you need to configure your API keys:"
echo

echo "📝 1. Edit your .env file with actual values:"
echo "   nano .env  # or use your preferred editor"
echo

print_warning "   REQUIRED: Set your Birdeye API key"
echo "   - Get it from: https://docs.birdeye.so/"
echo "   - Replace: BIRDEYE_API_KEY=your_birdeye_api_key_here"
echo

print_info "   OPTIONAL: Set up Telegram alerts"
echo "   - Create bot: Message @BotFather on Telegram"
echo "   - Get chat ID: Message @userinfobot on Telegram"
echo "   - Update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
echo

echo "📋 2. Review and customize config.yaml (optional):"
echo "   nano config/config.yaml"
echo

echo "🧪 3. Test your setup:"
echo "   ./run_monitor.sh"
echo

echo "📚 4. Read the documentation:"
echo "   - QUICKSTART.md for quick start guide"
echo "   - README.md for comprehensive documentation"
echo

# 8. Final validation
echo "=========================================="
echo "🔍 SETUP VALIDATION"
echo "=========================================="

validation_passed=true

# Check critical files
if [ -f ".env" ]; then
    print_status ".env file exists"
else
    print_error ".env file missing"
    validation_passed=false
fi

if [ -f "config/config.yaml" ]; then
    print_status "config.yaml exists"
else
    print_error "config.yaml missing"
    validation_passed=false
fi

if [ -d "venv" ]; then
    print_status "Virtual environment ready"
else
    print_error "Virtual environment missing"
    validation_passed=false
fi

if [ -f ".requirements_installed" ]; then
    print_status "Dependencies installed"
else
    print_error "Dependencies not installed"
    validation_passed=false
fi

echo
if [ "$validation_passed" = true ]; then
    print_status "Environment setup completed successfully!"
    echo
    print_info "Ready to configure API keys and run the monitor"
else
    print_error "Setup validation failed. Please check the errors above."
    exit 1
fi

echo "==========================================" 