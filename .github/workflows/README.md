# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for automated deployment of the Gamer Gambit Discord bots.

## 🤖 Self-Hosted Runner

The workflows use a self-hosted GitHub Actions runner deployed on your Kubernetes cluster:
- **Runner Name**: `gamer-gambit-k8s-runner`
- **Labels**: `[self-hosted, kubernetes, discord-bot]`
- **Location**: Kubernetes cluster (bypassing NFS mount issues)

## 📋 Available Workflows

### 1. Kallax Discord Bot CI/CD (`kallax-deploy.yml`)
**Status**: ✅ Active and Ready

**Triggers**:
- Push to `main` branch → Production deployment
- Push to `develop` branch → Test deployment  
- Pull requests → Test deployment
- Manual trigger via `workflow_dispatch`

**Pipeline Stages**:
1. **Build & Test**
   - Python 3.11 setup
   - Dependency installation and caching
   - Code linting with flake8
   - Bot validation
   - Docker image build and push to GHCR

2. **Deploy to Production** (main branch)
   - Kubernetes deployment update
   - Image rollout with verification
   - Health checks and logging

3. **Deploy to Test** (develop branch/PRs)
   - Test namespace setup
   - Isolated test deployment
   - Integration testing

**Image Registry**: `ghcr.io/2molaf/kallax-discord-bot`

### 2. Jarvfjallet Discord Bot CI/CD (`jarvfjallet-deploy.yml.disabled`)
**Status**: 🚧 Skeleton Only (Disabled)

**Current State**: 
- File has `.disabled` extension to prevent execution
- Contains placeholder structure for Node.js bot
- Build validation only (no Docker/K8s deployment yet)

**To Enable**:
1. Rename file from `.yml.disabled` to `.yml`
2. Create Dockerfile for Jarvfjallet
3. Create Kubernetes manifests
4. Remove `if: false` conditions from deployment jobs

## 🔄 Workflow Behavior

### Branch Strategy
- `main` → Production environment (`gamer-gambit` namespace)
- `develop` → Test environment (`gamer-gambit-test` namespace)
- Pull requests → Temporary test deployments

### Docker Images
- Built and pushed to GitHub Container Registry (GHCR)
- Tagged with branch name, commit SHA, and `latest` for main
- Cached layers for faster builds

### Kubernetes Deployment
- Uses existing K8s manifests in `discord/kallax/k8s/`
- Updates deployment images via `kubectl set image`
- Waits for rollout completion with timeouts
- Automatic cleanup of PR test environments

## 🚀 Getting Started

### Prerequisites
✅ Self-hosted runner is deployed and active
✅ Kubectl access to your cluster configured on runner
✅ GitHub Container Registry permissions configured

### First Deployment
1. Make changes to Kallax bot code in `discord/kallax/`
2. Commit and push to `main` or `develop` branch
3. Monitor workflow progress in GitHub Actions tab
4. Check deployment status with: `kubectl get pods -n gamer-gambit`

### Manual Deployment
You can trigger deployments manually:
1. Go to Actions tab in GitHub
2. Select "Kallax Discord Bot CI/CD"
3. Click "Run workflow"
4. Choose environment (production/test)

### Enabling Jarvfjallet
When ready to deploy Jarvfjallet:
1. Create `discord/jarvfjallet/Dockerfile`
2. Create Kubernetes manifests in `discord/jarvfjallet/k8s/`
3. Rename `jarvfjallet-deploy.yml.disabled` to `jarvfjallet-deploy.yml`
4. Remove `if: false` from deployment jobs
5. Push changes to trigger first build

## 🔍 Monitoring & Debugging

### View Workflow Status
- GitHub repository → Actions tab
- Real-time logs and status updates
- Deployment summaries in workflow runs

### Check Runner Status
```bash
kubectl get pods -l app=gamer-gambit-runner
kubectl logs -l app=gamer-gambit-runner
```

### Monitor Bot Deployments
```bash
# Production
kubectl get pods -n gamer-gambit -l app=kallax
kubectl logs -n gamer-gambit deployment/kallax --tail=50

# Test  
kubectl get pods -n gamer-gambit-test -l app=test-kallax
kubectl logs -n gamer-gambit-test deployment/test-kallax --tail=50
```

## 🔧 Configuration

### Required Secrets
The workflows use these automatically available secrets:
- `GITHUB_TOKEN` - For GHCR authentication (auto-provided)

### Environment Variables
Configured in the Kubernetes secret `kallax-config`:
- `DISCORD_TOKEN`
- `DATABASE_PATH`
- `BGG_API_BASE_URL`
- `COMMAND_PREFIX`

### Customization
- Modify triggers in workflow `on:` sections
- Adjust resource limits in Kubernetes manifests
- Update Docker build contexts and tags
- Configure additional test steps or validation

## 💡 Benefits

✅ **Automated**: Push code → automatic build & deploy
✅ **Isolated**: Separate test and production environments  
✅ **Reliable**: Health checks and rollout verification
✅ **Efficient**: Docker layer caching and dependency caching
✅ **Flexible**: Manual triggers and environment selection
✅ **Monitored**: Comprehensive logging and status reporting
