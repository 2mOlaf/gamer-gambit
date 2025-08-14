#!/bin/bash
# Deploy Kallax Discord Bot to Kubernetes
# Usage: ./deploy.sh [discord_token] [guild_id]

set -e

DISCORD_TOKEN="$1"
GUILD_ID="$2"

echo "🎲 Deploying Kallax Discord Bot to Kubernetes..."
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl and ensure it's in your PATH."
    exit 1
fi
echo "✅ kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Check your kubeconfig."
    exit 1
fi
echo "✅ Connected to Kubernetes cluster"

# Get Discord token if not provided
if [ -z "$DISCORD_TOKEN" ]; then
    read -p "Enter Discord Bot Token: " DISCORD_TOKEN
fi

if [ -z "$DISCORD_TOKEN" ]; then
    echo "❌ Discord token is required"
    exit 1
fi

# Get Guild ID if not provided
if [ -z "$GUILD_ID" ]; then
    read -p "Enter Discord Guild ID (optional, press Enter to skip): " GUILD_ID
fi

echo ""
echo "📦 Creating namespace..."
kubectl apply -f namespace.yaml

echo ""
echo "🔐 Creating secrets..."

# Create secret with actual values
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: kallax-config
  namespace: gamer-gambit
  labels:
    app: kallax
    component: config
type: Opaque
stringData:
  DISCORD_TOKEN: "$DISCORD_TOKEN"
  DISCORD_GUILD_ID: "$GUILD_ID"
  DATABASE_PATH: "/app/data/kallax.db"
  BGG_API_BASE_URL: "https://boardgamegeek.com/xmlapi2"
  COMMAND_PREFIX: "!"
  DEFAULT_WEEKLY_STATS_CHANNEL: "weekly-game-stats"
---
apiVersion: v1
kind: Secret
metadata:
  name: kallax-api-keys
  namespace: gamer-gambit
  labels:
    app: kallax
    component: api-keys
type: Opaque
stringData:
  STEAM_API_KEY: ""
  XBOX_API_KEY: ""
EOF

echo ""
echo "🚀 Deploying application..."
# Use deployment with integrated PVC that uses cluster's default storage
kubectl apply -f deployment-with-cluster-storage.yaml

echo ""
echo "🔍 Creating service..."
kubectl apply -f service.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To check the status:"
echo "  kubectl get pods -n gamer-gambit"
echo "  kubectl logs -n gamer-gambit deployment/kallax -f"
echo ""
echo "To update the bot:"
echo "  kubectl rollout restart deployment/kallax -n gamer-gambit"
echo ""
echo "To delete the deployment:"
echo "  kubectl delete namespace gamer-gambit"
