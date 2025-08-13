# Kallax Discord Bot - Secrets Setup Script (PowerShell)
# ========================================================
# This script helps you create the secrets.yaml file and apply it to Kubernetes

$ErrorActionPreference = "Stop"

$K8sDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SecretsTemplate = Join-Path $K8sDir "secrets.template.yaml"
$SecretsFile = Join-Path $K8sDir "secrets.yaml"

Write-Host "🔐 Kallax Discord Bot Secrets Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host

# Check if template exists
if (-not (Test-Path $SecretsTemplate)) {
    Write-Host "❌ Error: secrets.template.yaml not found in $K8sDir" -ForegroundColor Red
    exit 1
}

# Check if secrets.yaml already exists
if (Test-Path $SecretsFile) {
    Write-Host "⚠️  Warning: secrets.yaml already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "❌ Cancelled" -ForegroundColor Red
        exit 1
    }
}

# Copy template to secrets.yaml
Write-Host "📋 Creating secrets.yaml from template..." -ForegroundColor Blue
Copy-Item $SecretsTemplate $SecretsFile

Write-Host "✅ Created $SecretsFile" -ForegroundColor Green
Write-Host
Write-Host "🔧 Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit $SecretsFile and replace all placeholder values with your actual credentials"
Write-Host "2. Apply the secrets with: kubectl apply -f `"$SecretsFile`""
Write-Host "3. Verify with: kubectl get secrets -n gamer-gambit"
Write-Host "4. NEVER commit the secrets.yaml file to Git!"
Write-Host
Write-Host "📝 You need to obtain the following credentials:" -ForegroundColor Magenta
Write-Host "   • Discord Bot Token: https://discord.com/developers/applications"
Write-Host "   • Steam API Key: https://steamcommunity.com/dev/apikey"
Write-Host "   • Xbox API Key: Xbox Developer Portal"
Write-Host
Write-Host "⚠️  SECURITY REMINDER: The secrets.yaml file is git-ignored and should NEVER be committed!" -ForegroundColor Red
