#!/bin/bash

# VirtuosoHunt - Advanced Token Discovery Orchestrator Launcher
# 🏴‍☠️ Ahoy! Welcome to the Meme Token Pirate Hunt! 🏴‍☠️

# ASCII Art Function
print_pirate_banner() {
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                    🏴‍☠️ VIRTUOSO HUNT - MEME TOKEN PIRATES 🏴‍☠️                    ║
    ╠══════════════════════════════════════════════════════════════════════════════╣
    ║                                                                              ║
    ║                              ⚡ DIAMOND V FLAG ⚡                             ║
    ║                                     ◊ V ◊                                   ║
    ║                                    ╱█████╲                                  ║
    ║                                   ╱███████╲                                 ║
    ║                                  ╱█████████╲                                ║
    ║                                 ╱███████████╲                               ║
    ║                                ╱█████████████╲                              ║
    ║                               ╱███████████████╲                             ║
    ║                              ╱█████████████████╲                            ║
    ║                             ╱███████████████████╲                           ║
    ║                            ╱█████████████████████╲                          ║
    ║                           ╱███████████████████████╲                         ║
    ║                          ╱█████████████████████████╲                        ║
    ║                         ╱███████████████████████████╲                       ║
    ║                        ╱█████████████████████████████╲                      ║
    ║                       ╱███████████████████████████████╲                     ║
    ║                      ╱█████████████████████████████████╲                    ║
    ║                     ╱███████████████████████████████████╲                   ║
    ║                    ╱█████████████████████████████████████╲                  ║
    ║                   ╱███████████████████████████████████████╲                 ║
    ║                  ╱█████████████████████████████████████████╲                ║
    ║                 ╱███████████████████████████████████████████╲               ║
    ║                ╱█████████████████████████████████████████████╲              ║
    ║               ╱███████████████████████████████████████████████╲             ║
    ║              ╱█████████████████████████████████████████████████╲            ║
    ║             ╱███████████████████████████████████████████████████╲           ║
    ║            ╱█████████████████████████████████████████████████████╲          ║
    ║           ╱███████████████████████████████████████████████████████╲         ║
    ║          ╱█████████████████████████████████████████████████████████╲        ║
    ║         ╱███████████████████████████████████████████████████████████╲       ║
    ║        ╱█████████████████████████████████████████████████████████████╲      ║
    ║       ╱███████████████████████████████████████████████████████████████╲     ║
    ║      ╱█████████████████████████████████████████████████████████████████╲    ║
    ║     ╱███████████████████████████████████████████████████████████████████╲   ║
    ║    ╱█████████████████████████████████████████████████████████████████████╲  ║
    ║   ╱███████████████████████████████████████████████████████████████████████╲ ║
    ║  ╱█████████████████████████████████████████████████████████████████████████╲║
    ║ ╱███████████████████████████████████████████████████████████████████████████║
    ║╱█████████████████████████████████████████████████████████████████████████████║
    ║                                                                              ║
    ║                    🚢 AHOY MATEYS! READY FOR TREASURE HUNT! 🚢               ║
    ║                                                                              ║
    ║    ⚔️  BATTLE STATIONS - PREPARING THE FLEET:                                ║
    ║    🔥 Volume Momentum Strategy - Catch the waves!                            ║
    ║    🆕 Recent Listings Strategy - First to the treasure!                      ║
    ║    📈 Price Momentum Strategy - Ride the winds!                              ║
    ║    💧 Liquidity Growth Strategy - Deep waters ahead!                         ║
    ║    ⚡ High Trading Activity Strategy - Battle stations!                      ║
    ║                                                                              ║
    ║    💎 HUNTING EVERY 12 MINUTES - NO TREASURE ESCAPES! 💎                     ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝

    🏴‍☠️ VIRTUOSO HUNT LAUNCHER 🏴‍☠️
    ======================================
    Preparing the ship for the eternal treasure hunt...
    
EOF
}

# Print the banner
print_pirate_banner

echo "🏴‍☠️ STEP 1: CHECKING THE SHIP'S CONDITION..."
echo "============================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment for the crew..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment!"
        echo "   Make sure Python 3 is installed and accessible."
        exit 1
    fi
    echo "✅ Virtual environment created successfully!"
else
    echo "✅ Virtual environment already exists - ship is seaworthy!"
fi

# Activate virtual environment
echo ""
echo "⚓ Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment!"
    exit 1
fi
echo "✅ Virtual environment activated - crew is ready!"

echo ""
echo "🏴‍☠️ STEP 2: LOADING THE CANNONS (DEPENDENCIES)..."
echo "================================================"

# Check if requirements are installed
if [ ! -f ".requirements_installed" ]; then
    echo "📦 Installing requirements - loading ammunition..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements!"
        echo "   Check your requirements.txt file and internet connection."
        exit 1
    fi
    touch .requirements_installed
    echo "✅ Requirements installed successfully - cannons loaded!"
else
    echo "✅ Requirements already installed - cannons ready to fire!"
fi

echo ""
echo "🏴‍☠️ STEP 3: CHECKING THE TREASURE MAP (.env)..."
echo "==============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "🗺️  The treasure map is missing! You need to configure your API keys."
    echo ""
    echo "📋 To create your treasure map (.env file):"
    echo "   1. Copy the template: cp config/env.template .env"
    echo "   2. Edit .env with your API keys:"
    echo "      - BIRDEYE_API_KEY=your_birdeye_api_key"
    echo "      - TELEGRAM_BOT_TOKEN=your_telegram_bot_token (optional)"
    echo "      - TELEGRAM_CHAT_ID=your_telegram_chat_id (optional)"
    echo ""
    echo "🚨 Cannot sail without the treasure map!"
    exit 1
else
    echo "✅ Treasure map (.env) found - coordinates locked in!"
fi

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "📋 Config file not found, creating from template..."
    if [ -f "config/config.example.yaml" ]; then
        cp config/config.example.yaml config/config.yaml
        echo "✅ Created config/config.yaml - ship's navigation configured!"
    else
        echo "⚠️  No config template found - sailing with default settings!"
    fi
else
    echo "✅ Ship's navigation config found - course plotted!"
fi

echo ""
echo "🏴‍☠️ STEP 4: PREPARING THE SHIP'S QUARTERS..."
echo "============================================"

# Create necessary directories
mkdir -p logs data debug reports
echo "✅ Created ship's quarters:"
echo "   📁 logs/ - Captain's log"
echo "   📁 data/ - Treasure storage"
echo "   📁 debug/ - Navigation charts"
echo "   📁 reports/ - Treasure maps"

echo ""
echo "🏴‍☠️ STEP 5: FINAL PREPARATIONS..."
echo "================================"

# Check API key
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "⚠️  WARNING: BIRDEYE_API_KEY not set in environment"
    echo "   Make sure your .env file contains: BIRDEYE_API_KEY=your_api_key"
    echo "   The hunt will attempt to load from .env file..."
fi

# Check Python version
python_version=$(python3 --version 2>&1)
echo "🐍 Python version: $python_version"

# Check available disk space
available_space=$(df -h . | tail -1 | awk '{print $4}')
echo "💾 Available disk space: $available_space"

# Check system resources
if command -v free &> /dev/null; then
    memory_info=$(free -h | grep '^Mem:' | awk '{print $7}')
    echo "🧠 Available memory: $memory_info"
fi

echo ""
echo "🏴‍☠️ STEP 6: HOISTING THE DIAMOND V FLAG..."
echo "=========================================="

cat << 'EOF'
                    ⚡ DIAMOND V FLAG RAISED ⚡
                           ◊ V ◊
                          ╱█████╲
                         ╱███████╲
                        ╱█████████╲
                       ╱███████████╲
                      ╱█████████████╲
                     ╱███████████████╲
                    ╱█████████████████╲
                   ╱███████████████████╲
                  ╱█████████████████████╲
                 ╱███████████████████████╲
                ╱█████████████████████████╲
               ╱███████████████████████████╲
              ╱█████████████████████████████╲
             ╱███████████████████████████████╲
            ╱█████████████████████████████████╲
           ╱███████████████████████████████████╲
          ╱█████████████████████████████████████╲
         ╱███████████████████████████████████████╲
        ╱█████████████████████████████████████████╲
       ╱███████████████████████████████████████████╲
      ╱█████████████████████████████████████████████╲
     ╱███████████████████████████████████████████████╲
    ╱█████████████████████████████████████████████████╲
   ╱███████████████████████████████████████████████████╲
  ╱█████████████████████████████████████████████████████╲
 ╱███████████████████████████████████████████████████████╲
╱█████████████████████████████████████████████████████████╲
EOF

echo ""
echo "🏴‍☠️ ALL SYSTEMS READY - LAUNCHING THE HUNT!"
echo "==========================================="
echo "🚢 Setting sail for the eternal treasure hunt..."
echo "⚔️  Strategies will execute every 12 minutes"
echo "📊 Reports will be generated after each hourly cycle"
echo "💎 No treasure token shall escape our hunt!"
echo ""
echo "🏴‍☠️ TO STOP THE HUNT: Press Ctrl+C"
echo "📱 Monitor progress via Telegram (if configured)"
echo "📁 Check reports/ directory for treasure maps"
echo ""
echo "⚡ LAUNCHING VIRTUOSO HUNT ORCHESTRATOR... ⚡"
echo "=============================================="

# Launch the hunt with error handling
python virtuoso_hunt.py

# Check exit code and provide appropriate message
exit_code=$?
echo ""
echo "=============================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ VirtuosoHunt completed successfully!"
    echo "🏴‍☠️ The hunt ends, but the legend lives on!"
elif [ $exit_code -eq 130 ]; then
    echo "🏴‍☠️ Hunt stopped by Captain's orders (Ctrl+C)!"
    echo "⚔️  The crew rests, but treasure awaits!"
else
    echo "❌ VirtuosoHunt exited with error code: $exit_code"
    echo "💀 Check the logs for details of what went wrong!"
    echo "🔧 The ship may need repairs before the next voyage!"
fi

echo ""
echo "🏴‍☠️ VOYAGE SUMMARY:"
echo "   📁 Logs saved in: logs/"
echo "   📊 Reports saved in: reports/"
echo "   💾 Data cached in: data/"
echo ""
echo "⚔️  Ready for the next treasure hunt, Captain!"
echo "==============================================" 