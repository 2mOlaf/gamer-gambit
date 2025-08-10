# Update Kallax Discord Bot Secrets
# Usage: .\update-secrets.ps1 <discord_token> [guild_id]

param(
    [Parameter(Mandatory=$true)]
    [string]$DiscordToken,
    
    [Parameter(Mandatory=$false)]
    [string]$GuildId = ""
)

Write-Host "🔐 Updating Kallax Bot Secrets..." -ForegroundColor Green
Write-Host ""

# Validate Discord token format (basic check)
if (-not $DiscordToken.StartsWith("MTI") -and $DiscordToken.Length -lt 50) {
    Write-Host "⚠️  Warning: Discord token format looks unusual. Please verify it's correct." -ForegroundColor Yellow
}

# Create secret content
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

# Apply the secret
try {
    $secretContent | kubectl apply -f -
    Write-Host "✅ Secrets updated successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Restart the deployment to pick up new secrets
    Write-Host "🔄 Restarting bot deployment..." -ForegroundColor Yellow
    kubectl rollout restart deployment/kallax -n gamer-gambit
    
    Write-Host ""
    Write-Host "📊 Checking deployment status..." -ForegroundColor Cyan
    kubectl get pods -n gamer-gambit
    
    Write-Host ""
    Write-Host "🎉 Bot deployment updated!" -ForegroundColor Green
    Write-Host "   • OAuth Scopes Required: bot + applications.commands" -ForegroundColor White
    Write-Host "   • Slash commands now use gg- prefix" -ForegroundColor White
    Write-Host "   • Available commands: /gg-hello, /gg-test" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 To check logs:" -ForegroundColor Cyan
    Write-Host "   kubectl logs -n gamer-gambit deployment/kallax -f" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error updating secrets: $($_.Exception.Message)" -ForegroundColor Red
}
