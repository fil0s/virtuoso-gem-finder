#!/bin/bash

# Early Gem Hunter - Optimized scoring for ultra-early token detection
# This script uses the already configured early_gem_scoring_weights

echo "🎯 EARLY GEM HUNTING MODE ACTIVATED"
echo "====================================="

# Check if early gem config exists
if ! grep -q "early_gem_scoring_weights" config/config.yaml; then
    echo "❌ Early gem configuration not found in config.yaml"
    exit 1
fi

echo "✅ Early gem hunting configuration found:"
echo "🔄 Optimized scoring weights:"
echo "   📅 Age: 40% - Ultra-early detection priority"
echo "   📈 Price Change: 25% - Early momentum signals"  
echo "   🐋 Concentration: 20% - Whale accumulation"
echo "   💧 Liquidity: 5% - Reduced for early gems"
echo "   📊 Volume: 10% - Basic activity threshold"
echo ""
echo "🎯 Early gem thresholds:"
echo "   High conviction: 35.0 (optimized for early opportunities)"
echo "   Min candidate: 25.0 (more permissive entry)"
echo ""

# Backup current config and create early gem version
cp config/config.yaml config/config.yaml.backup

# Use sed to temporarily replace scoring_weights with early_gem_scoring_weights
sed 's/scoring_weights:/original_scoring_weights:/g' config/config.yaml | \
sed 's/early_gem_scoring_weights:/scoring_weights:/g' | \
sed 's/cross_platform:/original_cross_platform:/g' | \
sed 's/early_gem_hunting:/cross_platform:/g' > config/config_early_gem.yaml

# Replace the original with early gem version
cp config/config_early_gem.yaml config/config.yaml

echo "🚀 Starting early gem hunting session..."
echo "⏰ Optimized for 0-6 hour tokens with maximum early detection bonuses"
echo "💎 Focus: Stage 0 detection, whale accumulation, social formation"
echo "====================================="

# Run the detector with early gem optimizations
python run_6hour_20min_detector.py --debug

# Cleanup - restore original config
echo ""
echo "🧹 Restoring original configuration..."
mv config/config.yaml.backup config/config.yaml
rm -f config/config_early_gem.yaml

echo "✅ Early gem hunting session completed!"
echo "📊 Check logs for detected opportunities"
