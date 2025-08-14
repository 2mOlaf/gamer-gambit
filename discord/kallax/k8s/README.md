# Kallax Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Kallax Discord bot.

## Quick Start

### 1. Setup Secrets (Required First!)
```bash
# Use the setup script (recommended)
./setup-secrets.ps1  # Windows
./setup-secrets.sh   # Linux/macOS

# Edit the generated secrets.yaml with your credentials
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
├── base/                          # Base Kubernetes manifests (for CI/CD)
│   ├── deployment.yaml           # Main deployment configuration
│   ├── service.yaml              # Kubernetes service
│   ├── namespace.yaml            # Namespace definition
│   └── kustomization.yaml        # Kustomization config
├── environments/                  # Environment-specific configs
│   └── test/
│       └── kustomization.yaml   # Test environment overrides
├── secrets.template.yaml         # Template for creating secrets
├── secrets.yaml                  # 🔒 Your working secrets (git-ignored)
├── setup-secrets.ps1            # Windows setup script
├── setup-secrets.sh             # Linux setup script
├── deploy-secrets.ps1           # Deploy secrets to K8s
├── deploy.ps1                   # Manual deployment script
├── deploy.sh                    # Manual deployment script (Linux)
├── deployment-local.yaml        # Local deployment variant
├── pvc-commands.md              # PVC management commands
├── archive/                     # Historical files (reference only)
└── SECRETS-README.md            # Secrets management guide
```

## Prerequisites

Before deployment will work:

1. **Core Infrastructure**: MetalLB, Ingress, Storage (from ansuz-k8s repo)
2. **GitHub Runner**: Self-hosted runner deployed and online
3. **Secrets**: Discord tokens and API keys configured
4. **Container Registry**: Access to GitHub Container Registry

## Environments

### Production (`gamer-gambit` namespace)
- **Trigger**: Push to `main` branch
- **Secrets**: `kallax-config`, `kallax-api-keys`
- **Image Tag**: `latest`

### Test (`gamer-gambit-test` namespace)  
- **Trigger**: Push to `test` branch
- **Secrets**: `kallax-test-config`, `kallax-test-api-keys`
- **Image Tag**: `test`

## Verification

```bash
# Check deployment status
kubectl get pods -n gamer-gambit
kubectl get pods -n gamer-gambit-test

# View logs
kubectl logs -n gamer-gambit deployment/kallax --tail=20
kubectl logs -n gamer-gambit-test deployment/test-kallax --tail=20

# Test bot functionality
# - Bot should appear online in Discord
# - Commands like `!search wingspan` should work
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

See [../../../docs/TROUBLESHOOTING.md](../../../docs/TROUBLESHOOTING.md) for detailed troubleshooting.

## Secret Management

**⚠️ SECURITY WARNING**: Never commit `secrets.yaml` to Git!

- Use `secrets.template.yaml` as a template
- Edit locally and apply with kubectl
- Secrets are git-ignored and never committed

See [SECRETS-README.md](SECRETS-README.md) for detailed instructions.

## Archive

The `archive/` directory contains historical deployment files that are no longer used but kept for reference. The current deployment uses:

- **Base manifests** in `base/` directory
- **Kustomization** for environment-specific configurations  
- **GitHub Actions** for automated CI/CD deployment

---

**Next Steps**: Once deployed successfully, see [../../../docs/OPERATIONS.md](../../../docs/OPERATIONS.md) for daily operational tasks.
