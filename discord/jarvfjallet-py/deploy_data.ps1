# Jarvfjallet Production Data Deployment Script
# This script ensures the production environment has the necessary JSON data

Write-Host "🚀 Jarvfjallet Production Data Deployment" -ForegroundColor Green

# Check if we're running in the correct directory
if (!(Test-Path "k8s/base/deployment.yaml")) {
    Write-Host "❌ Please run this script from the jarvfjallet-py directory" -ForegroundColor Red
    exit 1
}

# Check if the JSON file exists
$jsonFile = "../itch_pak_from_test.json"
if (!(Test-Path $jsonFile)) {
    Write-Host "❌ Source JSON file not found: $jsonFile" -ForegroundColor Red
    Write-Host "Please ensure itch_pak_from_test.json exists in the parent directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Found source JSON file: $jsonFile" -ForegroundColor Green

# Copy to the Kubernetes persistent volume
$namespaceProd = "gamer-gambit"
$namespaceTest = "gamer-gambit-test"

Write-Host "🔄 Copying JSON data to production persistent volume..." -ForegroundColor Yellow

# Get the pod name for production
$podName = kubectl get pods -n $namespaceProd -l app=jarvfjallet -o jsonpath="{.items[0].metadata.name}"

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($podName)) {
    Write-Host "❌ Could not find production pod. Is the bot deployed?" -ForegroundColor Red
    Write-Host "Try: kubectl get pods -n $namespaceProd -l app=jarvfjallet" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 Found production pod: $podName" -ForegroundColor Green

# Copy the JSON file to the pod
Write-Host "📂 Copying JSON file to production pod..." -ForegroundColor Yellow
kubectl cp $jsonFile "${namespaceProd}/${podName}:/app/data/itch_pak.json"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ JSON file copied successfully!" -ForegroundColor Green
    
    # Restart the pod to trigger data import
    Write-Host "♻️ Restarting pod to trigger data import..." -ForegroundColor Yellow
    kubectl rollout restart deployment/jarvfjallet -n $namespaceProd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment restarted successfully!" -ForegroundColor Green
        Write-Host "🔍 Check logs with: kubectl logs -n $namespaceProd deployment/jarvfjallet --tail=20" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Failed to restart deployment" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to copy JSON file" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Data deployment complete!" -ForegroundColor Green
Write-Host "The bot should now import the game data on startup." -ForegroundColor Cyan
