# Deploy Kallax Discord Bot to Kubernetes
# Usage: .\deploy.ps1 [discord_token] [guild_id]

param(
    [Parameter(Mandatory=$false)]
    [string]$DiscordToken,
    
    [Parameter(Mandatory=$false)]
    [string]$GuildId
)

Write-Host "🎲 Deploying Kallax Discord Bot to Kubernetes..." -ForegroundColor Green
Write-Host ""

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
    Write-Host "✅ kubectl found" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl not found. Please install kubectl and ensure it's in your PATH." -ForegroundColor Red
    exit 1
}

# Check cluster connection
try {
    kubectl cluster-info | Out-Null
    Write-Host "✅ Connected to Kubernetes cluster" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to Kubernetes cluster. Check your kubeconfig." -ForegroundColor Red
    exit 1
}

# Get Discord token if not provided
if (-not $DiscordToken) {
    $DiscordToken = Read-Host "Enter Discord Bot Token"
}

if (-not $DiscordToken) {
    Write-Host "❌ Discord token is required" -ForegroundColor Red
    exit 1
}

# Get Guild ID if provided
if (-not $GuildId) {
    $GuildId = Read-Host "Enter Discord Guild ID (optional, press Enter to skip)"
}

Write-Host ""
Write-Host "📦 Creating namespace..." -ForegroundColor Yellow
kubectl apply -f namespace.yaml

Write-Host ""
Write-Host "🔐 Creating secrets..." -ForegroundColor Yellow

# Create temporary secret file with actual values
$secretContent = @"
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
  DISCORD_TOKEN: "$DiscordToken"
  DISCORD_GUILD_ID: "$GuildId"
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
"@

$secretContent | kubectl apply -f -

Write-Host ""
Write-Host "🚀 Deploying application..." -ForegroundColor Yellow
# Use deployment with integrated PVC that uses cluster's default storage
kubectl apply -f deployment-with-cluster-storage.yaml

Write-Host ""
Write-Host "🔍 Creating service..." -ForegroundColor Yellow
kubectl apply -f service.yaml

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To check the status:" -ForegroundColor Cyan
Write-Host "  kubectl get pods -n gamer-gambit" -ForegroundColor White
Write-Host "  kubectl logs -n gamer-gambit deployment/kallax -f" -ForegroundColor White
Write-Host ""
Write-Host "To update the bot:" -ForegroundColor Cyan
Write-Host "  kubectl rollout restart deployment/kallax -n gamer-gambit" -ForegroundColor White
Write-Host ""
Write-Host "To delete the deployment:" -ForegroundColor Cyan
Write-Host "  kubectl delete namespace gamer-gambit" -ForegroundColor White
