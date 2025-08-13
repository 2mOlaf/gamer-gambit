#!/bin/bash

# Kallax Discord Bot - Secrets Setup Script
# ==========================================
# This script helps you create the secrets.yaml file and apply it to Kubernetes

set -e

K8S_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_TEMPLATE="$K8S_DIR/secrets.template.yaml"
SECRETS_FILE="$K8S_DIR/secrets.yaml"

echo "🔐 Kallax Discord Bot Secrets Setup"
echo "===================================="
echo

# Check if template exists
if [ ! -f "$SECRETS_TEMPLATE" ]; then
    echo "❌ Error: secrets.template.yaml not found in $K8S_DIR"
    exit 1
fi

# Check if secrets.yaml already exists
if [ -f "$SECRETS_FILE" ]; then
    echo "⚠️  Warning: secrets.yaml already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 1
    fi
fi

# Copy template to secrets.yaml
echo "📋 Creating secrets.yaml from template..."
cp "$SECRETS_TEMPLATE" "$SECRETS_FILE"

echo "✅ Created $SECRETS_FILE"
echo
echo "🔧 Next steps:"
echo "1. Edit $SECRETS_FILE and replace all placeholder values with your actual credentials"
echo "2. Apply the secrets with: kubectl apply -f $SECRETS_FILE"
echo "3. Verify with: kubectl get secrets -n gamer-gambit"
echo "4. NEVER commit the secrets.yaml file to Git!"
echo
echo "📝 You need to obtain the following credentials:"
echo "   • Discord Bot Token: https://discord.com/developers/applications"
echo "   • Steam API Key: https://steamcommunity.com/dev/apikey"
echo "   • Xbox API Key: Xbox Developer Portal"
echo
echo "⚠️  SECURITY REMINDER: The secrets.yaml file is git-ignored and should NEVER be committed!"
