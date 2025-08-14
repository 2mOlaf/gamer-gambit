# Kubernetes Deployment for Kallax Discord Bot

This directory contains Kubernetes manifests to deploy the Kallax Discord bot to your Kubernetes cluster in the `gamer-gambit` namespace.

## Quick Start

### Windows (PowerShell)
```powershell
cd k8s
.\deploy.ps1
```

### Linux/Mac (Bash)
```bash
cd k8s
chmod +x deploy.sh
./deploy.sh
```

The script will prompt you for your Discord bot token and optionally your guild ID.

## Manual Deployment

If you prefer to deploy manually:

1. **Create namespace:**
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. **Configure secrets:**
   Edit `secret.yaml` with your Discord bot token and other configuration, then:
   ```bash
   kubectl apply -f secret.yaml
   ```

3. **Create storage:**
   ```bash
   kubectl apply -f pvc.yaml
   ```

4. **Deploy the bot:**
   ```bash
   kubectl apply -f deployment-local.yaml
   kubectl apply -f service.yaml
   ```

## File Overview

- **`namespace.yaml`** - Creates the `gamer-gambit` namespace
- **`secret.yaml`** - Template for bot configuration (Discord token, etc.)
- **`pvc.yaml`** - Persistent volume claim for database storage
- **`deployment-local.yaml`** - Main deployment using local filesystem
- **`deployment.yaml`** - Alternative deployment using Git (requires setup)
- **`service.yaml`** - Service for potential monitoring
- **`deploy.ps1`** - Automated PowerShell deployment script  
- **`deploy.sh`** - Automated Bash deployment script

## Deployment Options

### Option 1: Local Files (Recommended)
Uses `deployment-local.yaml` which mounts the source code directly from NFS (`mimisbrunnr.gradin.lan`). This allows the bot to access live code changes and ensures persistence across pod restarts.

### Option 2: Git Repository
Uses `deployment.yaml` with an init container that clones from a Git repository. Requires setting up a Git repo and modifying the deployment YAML.

## Configuration

The bot is configured via Kubernetes secrets:

### Required Configuration (`kallax-config` secret):
- `DISCORD_TOKEN` - Your Discord bot token
- `DATABASE_PATH` - Path to SQLite database (default: `/app/data/kallax.db`)
- `BGG_API_BASE_URL` - BoardGameGeek API URL
- `COMMAND_PREFIX` - Bot command prefix (default: `!`)

### Optional Configuration (`kallax-api-keys` secret):
- `DISCORD_GUILD_ID` - Specific guild ID for bot
- `STEAM_API_KEY` - Steam API key for Steam integration
- `XBOX_API_KEY` - Xbox API key for Xbox integration

## Resource Requirements

- **Memory**: 256Mi requested, 512Mi limit
- **CPU**: 100m requested, 500m limit
- **Storage**: 1Gi persistent volume for database

## Monitoring

### Check deployment status:
```bash
kubectl get pods -n gamer-gambit
kubectl get deployments -n gamer-gambit
```

### View logs:
```bash
kubectl logs -n gamer-gambit deployment/kallax -f
```

### Check events:
```bash
kubectl get events -n gamer-gambit --sort-by=.metadata.creationTimestamp
```

## Updating the Bot

### Restart deployment (picks up code changes):
```bash
kubectl rollout restart deployment/kallax -n gamer-gambit
```

### Update configuration:
```bash
# Edit and reapply secrets
kubectl apply -f secret.yaml
# Restart to pick up changes
kubectl rollout restart deployment/kallax -n gamer-gambit
```

## Troubleshooting

### Pod not starting:
1. Check pod status: `kubectl describe pod -n gamer-gambit <pod-name>`
2. Check logs: `kubectl logs -n gamer-gambit <pod-name>`
3. Verify secrets exist: `kubectl get secrets -n gamer-gambit`

### Bot not responding:
1. Verify Discord token is correct
2. Check bot has proper permissions in Discord server
3. Ensure bot is online in Discord server member list

### Database issues:
1. Check PVC is bound: `kubectl get pvc -n gamer-gambit`
2. Verify volume mounts: `kubectl describe pod -n gamer-gambit <pod-name>`

### Network issues:
1. Check if bot can reach Discord: `kubectl exec -n gamer-gambit <pod-name> -- curl -I https://discord.com`
2. Check BGG API access: `kubectl exec -n gamer-gambit <pod-name> -- curl -I https://boardgamegeek.com`

## Cleanup

### Delete everything:
```bash
kubectl delete namespace gamer-gambit
```

### Delete specific components:
```bash
kubectl delete deployment kallax -n gamer-gambit
kubectl delete pvc kallax-data -n gamer-gambit
kubectl delete secret kallax-config kallax-api-keys -n gamer-gambit
```

## Production Considerations

1. **Secrets Management**: Consider using external secret management (Vault, etc.)
2. **Monitoring**: Add proper monitoring with Prometheus/Grafana
3. **Backup**: Implement database backup strategy
4. **Resource Limits**: Adjust resource limits based on usage
5. **Node Affinity**: Pin to specific nodes if needed
6. **Image Security**: Consider building custom Docker image instead of using init container

## Security Notes

- Secrets are stored in Kubernetes secret objects (base64 encoded, not encrypted by default)
- Consider enabling encryption at rest for your cluster
- Use RBAC to restrict access to the `gamer-gambit` namespace
- Regularly rotate Discord bot tokens and API keys
