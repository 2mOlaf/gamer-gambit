#!/bin/bash
# Secrets Setup Script for Jarvfjallet Bot
# This script helps create the secrets.yaml file from the template

echo "🔐 Setting up Jarvfjallet Bot secrets..."

# Check if template exists
if [ ! -f "secrets.template.yaml" ]; then
    echo "❌ secrets.template.yaml not found in current directory."
    echo "   Please run this script from the k8s directory."
    exit 1
fi

# Check if secrets.yaml already exists
if [ -f "secrets.yaml" ]; then
    echo "⚠️  secrets.yaml already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "🚫 Setup cancelled."
        exit 0
    fi
fi

# Copy template
cp secrets.template.yaml secrets.yaml
echo "✅ Created secrets.yaml from template."

# Verify gitignore protection
if [ -f ".gitignore" ]; then
    if grep -q "secrets.yaml" .gitignore; then
        echo "✅ secrets.yaml is protected by .gitignore"
    else
        echo "⚠️  WARNING: secrets.yaml may not be protected by .gitignore!"
    fi
fi

# Check git status
if command -v git &> /dev/null; then
    if git status --porcelain 2>/dev/null | grep -q "secrets.yaml"; then
        echo "🚨 WARNING: secrets.yaml appears in git status!"
        echo "   This file should be ignored by git for security."
    else
        echo "✅ secrets.yaml is properly ignored by git"
    fi
else
    echo "ℹ️  Could not check git status (git not found)"
fi

echo ""
echo "📝 Next steps:"
echo "1. Edit secrets.yaml with your actual Discord bot tokens:"
echo "   - Replace 'your_production_discord_token_here' with your production bot token"
echo "   - Replace 'your_test_discord_token_here' with your test bot token"
echo "   - Replace 'your_guild_id_here' with your Discord server ID (optional)"
echo ""
echo "2. Apply the secrets to Kubernetes:"
echo "   kubectl apply -f secrets.yaml"
echo ""
echo "3. Deploy the bot:"
echo "   ./deploy.ps1 production"
echo "   ./deploy.ps1 test"
echo ""
echo "📖 For more information, see SECRETS-README.md"
echo ""
echo "🛡️  SECURITY REMINDERS:"
echo "   • Never commit secrets.yaml to git!"
echo "   • Don't share secrets.yaml files"
echo "   • Use separate tokens for test/production"  
echo "   • Rotate your bot tokens regularly"
