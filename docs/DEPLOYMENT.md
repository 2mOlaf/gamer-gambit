# Deployment Guide

## Prerequisites (CRITICAL)

**⚠️ These steps MUST be completed before any CI/CD will work:**

### 1. Core Infrastructure Setup
Deploy to your Kubernetes cluster using the [ansuz-k8s repository](https://gitea.gradin.lan/olafg/ansuz-k8s):

```bash
# Infrastructure components
kubectl apply -f infrastructure/metallb/
kubectl apply -f infrastructure/ingress/  
kubectl apply -f infrastructure/storage/
```

Required components:
- **MetalLB**: LoadBalancer IP pool
- **Ingress Controller**: External access
- **Persistent Storage**: Database persistence

### 2. GitHub Actions Runner
Deploy the self-hosted runner to your cluster:

```bash
# Get runner token from: https://github.com/YOUR_ORG/gamer-gambit/settings/actions/runners
cd discord/shared/github-runner/
./deploy-runner.ps1 -Token "YOUR_RUNNER_TOKEN"
```

**Verify runner is online** in GitHub before proceeding.

### 3. Create Required Secrets
Before any deployment can succeed:

```bash
cd discord/kallax/k8s
./setup-secrets.ps1  # Windows
./setup-secrets.sh   # Linux
```

Edit the generated `secrets.yaml` with your credentials and apply:
```bash
kubectl apply -f secrets.yaml
```

### 4. Container Registry Access
Ensure your cluster can pull from GitHub Container Registry:

```bash
# Verify registry access
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_TOKEN
```

## Deployment Methods

### Method 1: Automated (GitHub Actions)

**Production Deployment:**
```bash
git push origin main
```

**Test Deployment:**
```bash
git push origin test
```

Monitor at: `https://github.com/YOUR_ORG/gamer-gambit/actions`

### Method 2: Manual Deployment

For direct control or troubleshooting:

```bash
# Production
kubectl apply -k discord/kallax/k8s/base/
kubectl set image deployment/kallax kallax=ghcr.io/YOUR_ORG/kallax-discord-bot:latest -n gamer-gambit

# Test
kubectl apply -k discord/kallax/k8s/environments/test/
kubectl set image deployment/test-kallax test-kallax=ghcr.io/YOUR_ORG/kallax-discord-bot:test -n gamer-gambit-test
```

## Verification

### Check Deployment Status
```bash
# Production
kubectl get pods -n gamer-gambit
kubectl logs -n gamer-gambit deployment/kallax --tail=20

# Test  
kubectl get pods -n gamer-gambit-test
kubectl logs -n gamer-gambit-test deployment/test-kallax --tail=20
```

### Verify Bot Functionality
In Discord:
- Bot appears online
- Slash commands are available
- `!search wingspan` returns results

## Common Deployment Failures

### 1. "secret not found"
**Cause**: Missing Kubernetes secrets
**Fix**: Complete step 3 in Prerequisites

### 2. "runner offline"  
**Cause**: GitHub Actions runner not deployed
**Fix**: Complete step 2 in Prerequisites

### 3. "image pull backoff"
**Cause**: Container registry access issues
**Fix**: Verify GitHub Container Registry authentication

### 4. "pod pending"
**Cause**: Missing persistent storage or node resources
**Fix**: Verify infrastructure setup (step 1)

## Environment Details

### Production Environment
- **Namespace**: `gamer-gambit`
- **Secrets**: `kallax-config`, `kallax-api-keys`
- **Branch**: `main`
- **Registry Tag**: `latest`

### Test Environment  
- **Namespace**: `gamer-gambit-test`
- **Secrets**: `kallax-test-config`, `kallax-test-api-keys` 
- **Branch**: `test`
- **Registry Tag**: `test`

## Rollback Procedures

### Rollback Production
```bash
kubectl rollout undo deployment/kallax -n gamer-gambit
kubectl rollout status deployment/kallax -n gamer-gambit
```

### Rollback to Specific Version
```bash
# List rollout history
kubectl rollout history deployment/kallax -n gamer-gambit

# Rollback to specific revision
kubectl rollout undo deployment/kallax -n gamer-gambit --to-revision=2
```

## Security Considerations

- Secrets are stored as Kubernetes secrets (base64 encoded)
- Container images are scanned by GitHub
- Network policies restrict pod communication
- RBAC limits deployment permissions

## Next Steps

After successful deployment:
1. Set up monitoring (Prometheus/Grafana)
2. Configure backup procedures
3. Implement resource quotas
4. Set up alerting for failures

---

**Remember**: Infrastructure must be set up first! No amount of application deployment will work without the prerequisite infrastructure components.
