# Secrets Setup Script for Jarvfjallet Bot
# This script helps create the secrets.yaml file from the template

Write-Host "🔐 Setting up Jarvfjallet Bot secrets..." -ForegroundColor Green

# Check if template exists
if (-not (Test-Path "secrets.template.yaml")) {
    Write-Host "❌ secrets.template.yaml not found in current directory." -ForegroundColor Red
    Write-Host "   Please run this script from the k8s directory." -ForegroundColor Yellow
    exit 1
}

# Check if secrets.yaml already exists
if (Test-Path "secrets.yaml") {
    Write-Host "⚠️  secrets.yaml already exists." -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "🚫 Setup cancelled." -ForegroundColor Gray
        exit 0
    }
}

# Copy template
Copy-Item "secrets.template.yaml" "secrets.yaml"
Write-Host "✅ Created secrets.yaml from template." -ForegroundColor Green

# Verify gitignore protection
if (Test-Path ".gitignore") {
    $gitignoreContent = Get-Content ".gitignore" -Raw
    if ($gitignoreContent -like "*secrets.yaml*") {
        Write-Host "✅ secrets.yaml is protected by .gitignore" -ForegroundColor Green
    } else {
        Write-Host "⚠️  WARNING: secrets.yaml may not be protected by .gitignore!" -ForegroundColor Yellow
    }
}

# Check git status
try {
    $gitStatus = git status --porcelain 2>$null | Select-String "secrets.yaml"
    if ($gitStatus) {
        Write-Host "🚨 WARNING: secrets.yaml appears in git status!" -ForegroundColor Red
        Write-Host "   This file should be ignored by git for security." -ForegroundColor Yellow
    } else {
        Write-Host "✅ secrets.yaml is properly ignored by git" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️  Could not check git status (not in a git repository)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit secrets.yaml with your actual Discord bot tokens:" -ForegroundColor White
Write-Host "   - Replace 'your_production_discord_token_here' with your production bot token" -ForegroundColor Gray
Write-Host "   - Replace 'your_test_discord_token_here' with your test bot token" -ForegroundColor Gray
Write-Host "   - Replace 'your_guild_id_here' with your Discord server ID (optional)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Apply the secrets to Kubernetes:" -ForegroundColor White
Write-Host "   kubectl apply -f secrets.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Deploy the bot:" -ForegroundColor White
Write-Host "   .\deploy.ps1 production" -ForegroundColor Gray
Write-Host "   .\deploy.ps1 test" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 For more information, see SECRETS-README.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛡️  SECURITY REMINDERS:" -ForegroundColor Red
Write-Host "   • Never commit secrets.yaml to git!" -ForegroundColor Yellow
Write-Host "   • Don't share secrets.yaml files" -ForegroundColor Yellow
Write-Host "   • Use separate tokens for test/production" -ForegroundColor Yellow
Write-Host "   • Rotate your bot tokens regularly" -ForegroundColor Yellow
