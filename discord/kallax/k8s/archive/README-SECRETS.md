# Secret Management

## Files in this directory:
- `secret.yaml` - Your actual secrets (GIT-IGNORED)
- `secret.template.yaml` - Template with placeholders  
- `deploy-secrets.ps1` - Deployment script

## Setup:
1. Edit secret.yaml with your actual credentials
2. Run: ./deploy-secrets.ps1 -Environment test
3. Deploy your bot code

## Getting API Keys:
- Steam: https://steamcommunity.com/dev/apikey  
- Xbox: https://xbl.io/ (requires account)
- Discord: https://discord.com/developers/applications

⚠️ NEVER commit secret.yaml to Git!
