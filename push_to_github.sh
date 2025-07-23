#!/bin/bash

# GitHub Push Script for Virtuoso Gem Hunter
# Replace 'your-username' with your actual GitHub username

echo "🚀 Pushing Virtuoso Gem Hunter to GitHub..."

# Add GitHub remote (replace with your username)
git remote add origin https://github.com/your-username/virtuoso-gem-hunter.git

# Verify remote was added
echo "📍 Remote added:"
git remote -v

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin main

echo "✅ Push complete! Your repository is now on GitHub."
echo "🔗 Visit: https://github.com/your-username/virtuoso-gem-hunter"