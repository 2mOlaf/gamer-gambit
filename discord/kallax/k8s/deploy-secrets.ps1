#!/usr/bin/env pwsh
# Secure Secret Deployment Script
# Usage: ./deploy-secrets.ps1 [-Environment test|prod]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("test", "prod")]
    [string]$Environment = "test"
)

$secretFile = "secret.yaml"

if (-not (Test-Path $secretFile)) {
    Write-Host "❌ Error: $secretFile not found!" -ForegroundColor Red
    Write-Host "💡 Copy from template: cp secret.template.yaml secret.yaml" -ForegroundColor Yellow
    Write-Host "💡 Then edit secret.yaml with your actual credentials" -ForegroundColor Yellow
    exit 1
}

# Check for placeholder values
$content = Get-Content $secretFile -Raw
if ($content -match "PUT_YOUR_.*_HERE") {
    Write-Host "⚠️  Warning: Found placeholder values in secret.yaml" -ForegroundColor Yellow
    Write-Host "   Please replace all PUT_YOUR_*_HERE values with actual credentials" -ForegroundColor White
    Write-Host ""
}

Write-Host "🔐 Deploying secrets to $Environment environment..." -ForegroundColor Green
Write-Host ""

try {
    # Create namespace if needed
    if ($Environment -eq "test") {
        kubectl create namespace gamer-gambit-test --dry-run=client -o yaml | kubectl apply -f -
    } else {
        kubectl create namespace gamer-gambit --dry-run=client -o yaml | kubectl apply -f -
    }
    
    # Apply secrets
    kubectl apply -f $secretFile
    
    Write-Host "✅ Secrets deployed successfully!" -ForegroundColor Green
    
    # Show what was deployed
    if ($Environment -eq "test") {
        Write-Host ""
        Write-Host "📊 Test Environment Secrets:" -ForegroundColor Cyan
        kubectl get secrets -n gamer-gambit-test
    } else {
        Write-Host ""
        Write-Host "📊 Production Environment Secrets:" -ForegroundColor Cyan  
        kubectl get secrets -n gamer-gambit
    }
    
    Write-Host ""
    Write-Host "🚀 Ready to deploy your bot!" -ForegroundColor Green
    Write-Host "   Next: git checkout test && git merge dev/... && git push origin test" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error deploying secrets: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
