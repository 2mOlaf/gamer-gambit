# Manual Deployment Script for Jarvfjallet Bot
# Usage: ./deploy.ps1 [production|test]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("production", "test")]
    [string]$Environment = "production"
)

Write-Host "🚀 Deploying Jarvfjallet Bot to $Environment environment..." -ForegroundColor Green

# Check if kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ kubectl not found. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# Check if secrets exist
if (-not (Test-Path "secrets.yaml")) {
    Write-Host "❌ secrets.yaml not found. Please create it from secrets.template.yaml first." -ForegroundColor Red
    Write-Host "   1. Copy secrets.template.yaml to secrets.yaml" -ForegroundColor Yellow
    Write-Host "   2. Edit secrets.yaml with your actual Discord tokens" -ForegroundColor Yellow
    Write-Host "   3. Run: kubectl apply -f secrets.yaml" -ForegroundColor Yellow
    exit 1
}

try {
    if ($Environment -eq "production") {
        Write-Host "📦 Deploying to production (gamer-gambit namespace)..." -ForegroundColor Cyan
        kubectl apply -k environments/production/
        
        Write-Host "⏳ Waiting for deployment to be ready..." -ForegroundColor Yellow
        kubectl rollout status deployment/jarvfjallet -n gamer-gambit --timeout=300s
        
        Write-Host "✅ Verifying production deployment..." -ForegroundColor Green
        kubectl get pods -n gamer-gambit -l app=jarvfjallet
        
    } elseif ($Environment -eq "test") {
        Write-Host "🧪 Deploying to test (gamer-gambit-test namespace)..." -ForegroundColor Cyan
        kubectl apply -k environments/test/
        
        Write-Host "⏳ Waiting for deployment to be ready..." -ForegroundColor Yellow
        kubectl rollout status deployment/test-jarvfjallet -n gamer-gambit-test --timeout=300s
        
        Write-Host "✅ Verifying test deployment..." -ForegroundColor Green
        kubectl get pods -n gamer-gambit-test -l app=jarvfjallet
    }
    
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "🔍 Check logs with:" -ForegroundColor Cyan
    
    if ($Environment -eq "production") {
        Write-Host "   kubectl logs -n gamer-gambit deployment/jarvfjallet --tail=20 -f" -ForegroundColor Gray
    } else {
        Write-Host "   kubectl logs -n gamer-gambit-test deployment/test-jarvfjallet --tail=20 -f" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
