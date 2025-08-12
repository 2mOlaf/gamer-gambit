# Discord Bots Infrastructure Management

This directory contains the infrastructure configuration and management scripts for the Discord bots in this repository.

## Files Overview

### Kubernetes Deployments
- **github-runner-deployment.yaml** - GitHub Actions self-hosted runner deployment for CI/CD
- **Bot-specific deployments** are located in each bot's directory (e.g., kallax/k8s/)

### Management Scripts

#### update-runner-token.ps1
Updates the GitHub runner registration token in the deployment YAML.

**Usage:**
PowerShell
# Get new token from: https://github.com/2mOlaf/gamer-gambit/settings/actions/runners
.\update-runner-token.ps1 -NewToken "YOUR_NEW_TOKEN_HERE"

# Then apply the updated deployment:
kubectl apply -f github-runner-deployment.yaml


#### manage-runner.ps1
Comprehensive GitHub runner management.

**Usage:**
PowerShell
# Check runner status (default)
.\manage-runner.ps1
.\manage-runner.ps1 -Action status

# View recent runner logs
.\manage-runner.ps1 -Action logs

# Restart the runner deployment
.\manage-runner.ps1 -Action restart

# Apply the deployment file
.\manage-runner.ps1 -Action apply


#### check-kallax-deployment.ps1
Monitor the Kallax bot deployment status and image versions.

**Usage:**
PowerShell
.\check-kallax-deployment.ps1


## GitHub Runner Setup

The self-hosted GitHub Actions runner enables automated CI/CD for the Discord bots. It runs in Kubernetes with Docker-in-Docker (DinD) support.

### Initial Setup

1. **Get a registration token:**
   - Go to: https://github.com/2mOlaf/gamer-gambit/settings/actions/runners
   - Click "New self-hosted runner"
   - Copy the token from the configuration command

2. **Update the deployment:**
   PowerShell
   .\update-runner-token.ps1 -NewToken "YOUR_TOKEN"
   

3. **Deploy the runner:**
   PowerShell
   kubectl apply -f github-runner-deployment.yaml
   

4. **Verify it's working:**
   PowerShell
   .\manage-runner.ps1 -Action status
   

### Troubleshooting

If the runner is in CrashLoopBackOff:
1. Check if the token has expired
2. Get a new token and update the deployment
3. Restart the runner deployment

PowerShell
# Quick restart process
.\update-runner-token.ps1 -NewToken "NEW_TOKEN"
.\manage-runner.ps1 -Action restart


## Next Steps for Getting Your Pipeline Running

**You're all set up!** Here's what to do:

1. **Get a fresh GitHub runner token** from your repository settings
2. **Run the token update script** with your new token
3. **Deploy the runner** and watch your CI/CD pipeline execute automatically

Your commit to main branch is waiting to be processed once the runner comes online!
