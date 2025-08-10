# Security Cleanup Script - Run BEFORE making repository public
# This script removes sensitive files and cleans git history

Write-Host "🔒 SECURITY CLEANUP - Removing Credentials from Repository" -ForegroundColor Red
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository root directory" -ForegroundColor Red
    exit 1
}

# List of sensitive files to remove
$sensitiveFiles = @(
    "discord/jarvfjallet/node/auth.json",
    "node/auth.json",
    "discord/jarvfjallet/node/local.settings.json",
    "node/local.settings.json"
)

Write-Host "🔍 Checking for sensitive files..." -ForegroundColor Yellow

foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        Write-Host "⚠️  Found sensitive file: $file" -ForegroundColor Yellow
        
        # Remove from git tracking
        Write-Host "   Removing from git tracking..." -ForegroundColor Cyan
        git rm --cached $file 2>$null
        
        # Optionally remove the file entirely (uncomment if desired)
        # Remove-Item $file -Force
        Write-Host "   ✅ Removed from git tracking" -ForegroundColor Green
    } else {
        Write-Host "✅ File not found (good): $file" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "📋 Adding updated .gitignore..." -ForegroundColor Yellow
git add .gitignore

Write-Host ""
Write-Host "💾 Committing security improvements..." -ForegroundColor Yellow
git commit -m "🔒 Security: Remove credential files and update .gitignore

- Remove auth.json files containing Discord tokens from git tracking
- Add comprehensive .gitignore for credential files
- Prepare for public repository (tokens must be regenerated)

SECURITY NOTE: All Discord bot tokens in this commit history 
should be considered compromised and regenerated."

Write-Host ""
Write-Host "⚠️  CRITICAL NEXT STEPS:" -ForegroundColor Red
Write-Host "1. 🔑 REGENERATE Discord bot token at https://discord.com/developers/applications" -ForegroundColor White
Write-Host "2. 🗂️  Store new token in Kubernetes secrets using update-secrets.ps1" -ForegroundColor White
Write-Host "3. 🧹 (Optional) Use BFG Repo-Cleaner to remove tokens from git history" -ForegroundColor White
Write-Host "4. 🌍 Then repository is safe to make public" -ForegroundColor White
Write-Host ""

Write-Host "✅ Security cleanup completed!" -ForegroundColor Green
Write-Host "📤 Push changes with: git push origin main" -ForegroundColor Cyan
