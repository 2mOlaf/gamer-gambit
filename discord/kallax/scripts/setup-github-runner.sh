#!/bin/bash
# GitHub Self-Hosted Runner Setup for Kallax CI/CD

# This script sets up a GitHub Actions self-hosted runner
# that has access to your Kubernetes cluster

echo "🏃 Setting up GitHub Actions Self-Hosted Runner..."

# Prerequisites check
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Test Kubernetes access
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot access Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Runner configuration
GITHUB_OWNER="2mOlaf"
GITHUB_REPO="gamer-gambit"
RUNNER_NAME="hostname-kallax-runner"

echo "🔧 Configuring runner for $GITHUB_OWNER/$GITHUB_REPO"
echo "Runner name: $RUNNER_NAME"

# Download and configure runner
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Note: You'll need to get the runner token from:
# https://github.com/$GITHUB_OWNER/$GITHUB_REPO/settings/actions/runners/new

echo ""
echo "🎯 Next steps:"
echo "1. Go to: https://github.com/$GITHUB_OWNER/$GITHUB_REPO/settings/actions/runners/new"
echo "2. Copy the token and run:"
echo "   ./config.sh --url https://github.com/$GITHUB_OWNER/$GITHUB_REPO --token YOUR_TOKEN --name $RUNNER_NAME"
echo "3. Install as a service:"
echo "   sudo ./svc.sh install"
echo "   sudo ./svc.sh start"
echo ""
echo "The runner will then be able to deploy to your Kubernetes cluster!"
