# Jarvfjallet Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Jarvfjallet Discord bot.

## Quick Start

### 1. Setup Secrets (Required First!)
```bash
# Copy the template and edit with your tokens
cp secrets.template.yaml secrets.yaml
# Edit secrets.yaml with your actual Discord bot tokens
kubectl apply -f secrets.yaml
```

### 2. Deploy to Production
```bash
# Automatic via GitHub Actions (recommended)
git push origin main

# Manual deployment
kubectl apply -k base/
```

### 3. Deploy to Test Environment
```bash
# Automatic via GitHub Actions (recommended) 
git push origin test

# Manual deployment
kubectl apply -k environments/test/
```

## File Structure

```
k8s/
├── base/                          # Base Kubernetes manifests
│   ├── deployment.yaml           # Main deployment configuration
│   ├── service.yaml              # Kubernetes service
│   ├── namespace.yaml            # Namespace definition
│   ├── pvc.yaml                  # Persistent volume claim
│   └── kustomization.yaml        # Kustomization config
├── environments/                  # Environment-specific configs
│   ├── production/
│   │   └── kustomization.yaml   # Production overrides
│   └── test/
│       ├── kustomization.yaml   # Test environment overrides
│       └── test-namespace.yaml  # Test namespace
├── secrets.template.yaml         # Template for creating secrets
└── secrets.yaml                  # 🔒 Your working secrets (git-ignored)
```

## Prerequisites

Before deployment will work:

1. **Core Infrastructure**: MetalLB, Ingress, Storage (from ansuz-k8s repo)
2. **GitHub Runner**: Self-hosted runner deployed and online
3. **Secrets**: Discord tokens configured
4. **Container Registry**: Access to GitHub Container Registry

## Environments

### Production (`gamer-gambit` namespace)
- **Trigger**: Push to `main` branch
- **Secrets**: `jarvfjallet-config`
- **Image Tag**: `main`
- **PVC**: `jarvfjallet-data` (1Gi)

### Test (`gamer-gambit-test` namespace)  
- **Trigger**: Push to `test` branch
- **Secrets**: `jarvfjallet-config` (test namespace)
- **Image Tag**: `test`
- **PVC**: `test-jarvfjallet-data` (1Gi)

## Bot Configuration

The bot requires these environment variables in the secrets:

```yaml
DISCORD_TOKEN: "your_discord_bot_token"
DISCORD_GUILD_ID: "your_guild_id" (optional)
DATABASE_PATH: "/app/data/jarvfjallet.db"
COMMAND_PREFIX: "!"
```

## Data Migration

The bot will automatically import existing JSON data:

1. **First deployment**: Place `itch_pak.json` in the persistent volume
2. **Automatic import**: Bot detects and imports on startup
3. **SQLite conversion**: JSON data converted to SQLite database
4. **Data preservation**: All user assignments preserved

## Verification

```bash
# Check deployment status
kubectl get pods -n gamer-gambit
kubectl get pods -n gamer-gambit-test

# View logs
kubectl logs -n gamer-gambit deployment/jarvfjallet --tail=20
kubectl logs -n gamer-gambit-test deployment/test-jarvfjallet --tail=20

# Check health endpoint (if exposed)
kubectl port-forward -n gamer-gambit deployment/jarvfjallet 8080:8080
curl http://localhost:8080/health

# Test bot functionality
# - Bot should appear online in Discord
# - Commands like `/hit` should work
# - `/gameinfo` should show database stats
```

## Troubleshooting

### Common Issues

1. **"secret not found"**
   - Apply secrets first: `kubectl apply -f secrets.yaml`

2. **"runner offline"** 
   - Check GitHub Actions runner status
   - Restart runner if needed

3. **"image pull backoff"**
   - Verify GitHub Container Registry access
   - Check image name and tag

4. **"database empty"**
   - Place `itch_pak.json` in persistent volume
   - Check logs for import errors

5. **"commands not syncing"**
   - Set DISCORD_GUILD_ID for instant sync
   - Wait up to 1 hour for global sync

### Data Recovery

If you need to restore from the original JSON files:

```bash
# Copy JSON to persistent volume
kubectl cp itch_pak.json gamer-gambit/jarvfjallet-pod:/app/data/
# Restart bot to trigger import
kubectl rollout restart deployment/jarvfjallet -n gamer-gambit
```

### Monitoring

The bot provides several monitoring endpoints:

- `/health` - Basic health check with bot status
- `/metrics` - Detailed metrics including game statistics

## Secret Management

**⚠️ SECURITY WARNING**: Never commit `secrets.yaml` to Git!

- Use `secrets.template.yaml` as a template
- Edit locally and apply with kubectl
- Secrets are git-ignored and never committed

## Resource Usage

The Jarvfjallet bot is lightweight:

- **CPU**: 50m request, 200m limit
- **Memory**: 128Mi request, 256Mi limit
- **Storage**: 1Gi persistent volume for database

## Updates

The bot follows the same update pattern as Kallax:

1. **Code changes**: Push to appropriate branch
2. **Automatic build**: GitHub Actions handles container build
3. **Deployment**: Kubernetes pod restart with new image
4. **Verification**: Health checks ensure successful deployment

---

**Next Steps**: Once deployed successfully, see the main [README.md](../README.md) for command usage and features.
