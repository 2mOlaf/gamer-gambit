#!/usr/bin/env pwsh
# Deploy Test Environment for Kallax Bot

param(
    [Parameter(Mandatory=$false)]
    [string]$TestDiscordToken,
    
    [Parameter(Mandatory=$false)]
    [string]$TestGuildId,
    
    [Parameter(Mandatory=$false)]
    [string]$Branch = "develop"
)

Write-Host "🧪 Deploying Kallax Test Environment" -ForegroundColor Green
Write-Host "Branch: $Branch" -ForegroundColor Cyan

# Create test namespace
Write-Host "📦 Creating test namespace..." -ForegroundColor Yellow
kubectl create namespace gamer-gambit-test --dry-run=client -o yaml | kubectl apply -f -

# Get tokens if not provided
if (-not $TestDiscordToken) {
    $TestDiscordToken = Read-Host "Enter Test Discord Bot Token"
}

if (-not $TestGuildId) {
    $TestGuildId = Read-Host "Enter Test Discord Guild ID (optional)"
}

# Create test secrets
Write-Host "🔐 Creating test secrets..." -ForegroundColor Yellow
$secretContent = @\"
apiVersion: v1
kind: Secret
metadata:
  name: kallax-test-config
  namespace: gamer-gambit-test
  labels:
    app: kallax-test
    environment: test
type: Opaque
stringData:
  DISCORD_TOKEN: "$TestDiscordToken"
  DISCORD_GUILD_ID: "$TestGuildId"
  DATABASE_PATH: "/app/data/kallax-test.db"
  BGG_API_BASE_URL: "https://boardgamegeek.com/xmlapi2"
  COMMAND_PREFIX: "!test"
  DEFAULT_WEEKLY_STATS_CHANNEL: "test-game-stats"
  ENVIRONMENT: "test"
  GITHUB_BRANCH: "$Branch"
  LOG_LEVEL: "DEBUG"
\"@

$secretContent | kubectl apply -f -

# Deploy using kustomize
Write-Host "🚀 Deploying test environment..." -ForegroundColor Yellow
kubectl apply -k k8s/environments/test/

Write-Host "⏳ Waiting for deployment..." -ForegroundColor Yellow
kubectl rollout status deployment/test-kallax -n gamer-gambit-test --timeout=300s

Write-Host "✅ Test environment deployed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Status:" -ForegroundColor Cyan
kubectl get pods -n gamer-gambit-test -l app=kallax-test

Write-Host ""
Write-Host "🔍 To check logs:" -ForegroundColor Cyan
Write-Host "  kubectl logs -n gamer-gambit-test deployment/test-kallax -f" -ForegroundColor White

Write-Host ""
Write-Host "🏥 Health check (after port-forward):" -ForegroundColor Cyan
Write-Host "  kubectl port-forward -n gamer-gambit-test svc/test-kallax-service 8081:8080" -ForegroundColor White
Write-Host "  curl http://localhost:8081/health" -ForegroundColor White
