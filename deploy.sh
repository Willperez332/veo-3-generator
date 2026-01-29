#!/bin/bash
# Automated deployment script for VEO 3 Generator

set -e

echo "🚀 VEO 3 Generator - Automated Deployment"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must run from veo-generator directory"
    exit 1
fi

# Step 1: Create GitHub repo
echo "📦 Step 1: Creating GitHub repository..."
echo ""
echo "Please create a GitHub repository manually:"
echo "1. Go to: https://github.com/new"
echo "2. Repository name: veo-3-generator"
echo "3. Description: Batch VEO 3 video generator"
echo "4. Visibility: Public or Private (your choice)"
echo "5. Click 'Create repository'"
echo ""
read -p "Press ENTER when you've created the repository..."

# Step 2: Get the repository URL
echo ""
read -p "Enter your GitHub username (e.g., Willperez332): " github_user
repo_url="https://github.com/${github_user}/veo-3-generator.git"

echo ""
echo "📤 Step 2: Pushing code to GitHub..."
git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"
git branch -M main
git push -u origin main

echo ""
echo "✅ Code pushed to GitHub successfully!"
echo ""
echo "🚂 Step 3: Deploy to Railway"
echo ""
echo "Now deploy on Railway:"
echo "1. Go to: https://railway.com/dashboard"
echo "2. Click 'New Project'"
echo "3. Select 'Deploy from GitHub repo'"
echo "4. Choose 'veo-3-generator'"
echo "5. Wait 2-3 minutes for build"
echo "6. Click 'Settings' → 'Generate Domain'"
echo "7. Copy the public URL"
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Share the Railway URL with your team and they're ready to go!"
