# Shared Discord Infrastructure

This directory contains shared infrastructure components used by all Discord bots in this project.

## Components

### GitHub Actions Runner
- **Location**: `github-runner/`
- **Purpose**: Self-hosted GitHub Actions runner for CI/CD
- **Deployment**: Runs in Kubernetes cluster with Docker-in-Docker support

## Quick Setup

### Deploy GitHub Runner
```bash
cd github-runner
# Get runner token from GitHub repository settings
./deploy-runner.ps1 -Token "YOUR_RUNNER_TOKEN"
```

### Verify Runner Status
```bash
kubectl get pods -l app=gamer-gambit-runner
kubectl logs -l app=gamer-gambit-runner --tail=20
```

## Management

### Restart Runner
```bash
kubectl rollout restart deployment/gamer-gambit-runner
```

### Update Runner Token
```bash
cd github-runner
./update-runner-token.ps1 -NewToken "NEW_TOKEN"
kubectl apply -f deployment.yaml
```

## Requirements

- Kubernetes cluster with Docker support
- GitHub repository with Actions enabled
- Runner registration token from GitHub

---

**Note**: This infrastructure is shared across all Discord bots in the project. Changes here affect all automated deployments.
