# Troubleshooting Guide

Common issues and their solutions for the Gamer Gambit Discord bots.

## 🚨 Critical Issues

### Bot Not Responding in Discord

**Symptoms:**
- Bot appears offline in Discord
- Commands don't work
- No response to mentions

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n gamer-gambit

# Check logs for errors
kubectl logs -n gamer-gambit deployment/kallax --tail=50

# Verify secrets exist
kubectl get secrets -n gamer-gambit
```

**Common Causes & Fixes:**

1. **Invalid Discord Token**
   ```bash
   # Update token in secrets.yaml and apply
   kubectl apply -f discord/kallax/k8s/secrets.yaml
   kubectl rollout restart deployment/kallax -n gamer-gambit
   ```

2. **Pod CrashLoopBackOff**
   ```bash
   # Check what's causing the crash
   kubectl describe pod -n gamer-gambit -l app=kallax
   kubectl logs -n gamer-gambit -l app=kallax --previous
   ```

3. **Resource Limits Exceeded**
   ```bash
   # Check resource usage
   kubectl top pods -n gamer-gambit
   # Increase limits in deployment.yaml if needed
   ```

### Deployment Failures

**Symptoms:**
- GitHub Actions fail
- Pods stuck in Pending state
- Image pull failures

**Common Causes & Fixes:**

1. **Missing Secrets**
   ```
   Error: secret "kallax-config" not found
   ```
   **Fix**: Apply secrets first:
   ```bash
   cd discord/kallax/k8s
   kubectl apply -f secrets.yaml
   ```

2. **Runner Offline**
   ```
   Error: No self-hosted runners online
   ```
   **Fix**: Restart GitHub runner:
   ```bash
   kubectl get pods -l app=gamer-gambit-runner
   kubectl rollout restart deployment/gamer-gambit-runner
   ```

3. **Image Pull Failures**
   ```
   Error: Failed to pull image "ghcr.io/..."
   ```
   **Fix**: Check registry authentication:
   ```bash
   docker login ghcr.io -u YOUR_USERNAME -p YOUR_TOKEN
   ```

### Database Issues

**Symptoms:**
- Bot starts but can't save data
- Commands work but don't persist
- Database connection errors

**Diagnosis:**
```bash
# Check persistent volume
kubectl get pvc -n gamer-gambit
kubectl describe pvc kallax-data -n gamer-gambit

# Check database file
kubectl exec -n gamer-gambit deployment/kallax -- ls -la /app/data/
```

**Fixes:**
```bash
# If PVC is not bound
kubectl describe pv | grep gamer-gambit

# Check storage class
kubectl get storageclass

# Recreate PVC if needed (DATA LOSS WARNING)
kubectl delete pvc kallax-data -n gamer-gambit
kubectl apply -f discord/kallax/k8s/base/
```

## ⚠️ Common Errors

### "ModuleNotFoundError" in Logs

**Error:**
```
ModuleNotFoundError: No module named 'discord'
```

**Cause**: Dependencies not installed in container

**Fix**: Rebuild container image:
```bash
# Trigger rebuild via GitHub Actions
git commit --allow-empty -m "Rebuild container"
git push origin test  # or main
```

### "Permission denied" for Database

**Error:**
```
sqlite3.OperationalError: unable to open database file
```

**Cause**: File permissions or missing directory

**Fix:**
```bash
# Check pod filesystem
kubectl exec -n gamer-gambit deployment/kallax -- ls -la /app/
kubectl exec -n gamer-gambit deployment/kallax -- mkdir -p /app/data
kubectl rollout restart deployment/kallax -n gamer-gambit
```

### BGG API Timeouts

**Error:**
```
aiohttp.client_exceptions.ServerTimeoutError
```

**Cause**: BoardGameGeek API is slow/overloaded

**Fix**: Usually resolves itself, but can:
```bash
# Restart bot to reset connections
kubectl rollout restart deployment/kallax -n gamer-gambit

# Check if BGG is accessible
kubectl exec -n gamer-gambit deployment/kallax -- curl -I https://boardgamegeek.com
```

### Discord Rate Limiting

**Error:**
```
discord.errors.HTTPException: 429 Too Many Requests
```

**Cause**: Bot is making too many API calls

**Fix**: Rate limiting is built-in, usually self-resolves. If persistent:
```bash
# Check for loops in logs
kubectl logs -n gamer-gambit deployment/kallax --tail=100 | grep -i rate

# Restart if needed
kubectl rollout restart deployment/kallax -n gamer-gambit
```

## 🔧 GitHub Actions Issues

### Workflow Not Triggering

**Symptoms:**
- Push to main/test doesn't trigger workflow
- No runs appear in Actions tab

**Checks:**
1. **Path filters**: Ensure changes are in `discord/kallax/**` or workflow files
2. **Branch protection**: Check branch rules aren't blocking
3. **Runner status**: Verify self-hosted runner is online

**Fix:**
```bash
# Manual trigger
git commit --allow-empty -m "Trigger workflow"
git push origin test

# Check runner logs
kubectl logs -l app=gamer-gambit-runner --tail=20
```

### Build Failures

**Common build errors:**

1. **Python Import Errors**
   ```
   ImportError: No module named 'utils.database'
   ```
   **Fix**: Check file structure and Python path

2. **Docker Build Fails**
   ```
   Error building image
   ```
   **Fix**: Check Dockerfile syntax and base image availability

3. **Registry Push Fails**
   ```
   Error pushing to ghcr.io
   ```
   **Fix**: Verify GitHub token permissions

### Deployment Timeouts

**Error:**
```
Error: deployment rollout timeout
```

**Causes:**
- Pod taking too long to start
- Health checks failing
- Resource constraints

**Fix:**
```bash
# Check pod events
kubectl get events -n gamer-gambit --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl describe pod -n gamer-gambit -l app=kallax

# Manual intervention
kubectl rollout restart deployment/kallax -n gamer-gambit
```

## 🐛 Debug Commands

### Comprehensive Health Check
```bash
#!/bin/bash
echo "=== Gamer Gambit Health Check ==="

echo "1. Pod Status:"
kubectl get pods -n gamer-gambit -o wide

echo "2. Recent Logs:"
kubectl logs -n gamer-gambit deployment/kallax --tail=10

echo "3. Secrets:"
kubectl get secrets -n gamer-gambit

echo "4. Storage:"
kubectl get pvc -n gamer-gambit

echo "5. Services:"
kubectl get svc -n gamer-gambit

echo "6. GitHub Runner:"
kubectl get pods -l app=gamer-gambit-runner
```

### Deep Debugging
```bash
# Get into bot container for debugging
kubectl exec -it -n gamer-gambit deployment/kallax -- /bin/bash

# Inside container, check:
python -c "import discord; print('Discord.py version:', discord.__version__)"
python -c "import os; print('Token set:', bool(os.getenv('DISCORD_TOKEN')))"
ls -la /app/data/
cat /app/requirements.txt
```

### Network Debugging
```bash
# Test external connectivity
kubectl exec -n gamer-gambit deployment/kallax -- nslookup discord.com
kubectl exec -n gamer-gambit deployment/kallax -- curl -sI https://discord.com/api/v10/gateway
kubectl exec -n gamer-gambit deployment/kallax -- curl -sI https://boardgamegeek.com/xmlapi2/search
```

## 📋 Issue Resolution Checklist

When troubleshooting any issue:

1. **Identify the scope**:
   - [ ] Is it affecting production, test, or both?
   - [ ] Is it a new issue or recurring?
   - [ ] When did it start?

2. **Gather information**:
   - [ ] Pod status and logs
   - [ ] Recent changes (Git commits)
   - [ ] Resource usage
   - [ ] External dependencies status

3. **Try quick fixes**:
   - [ ] Restart deployment
   - [ ] Check secrets
   - [ ] Verify network connectivity
   - [ ] Review recent logs

4. **Escalate if needed**:
   - [ ] Rollback to previous version
   - [ ] Scale down to investigate
   - [ ] Contact external service support

## 🔍 Log Analysis

### Important Log Patterns

**Startup Success:**
```
✅ Bot modules imported successfully
Logged in as Kallax#1234
Ready! Logged in as Kallax
```

**Connection Issues:**
```
discord.errors.LoginFailure
aiohttp.client_exceptions.ClientConnectorError
```

**Database Issues:**
```
sqlite3.OperationalError
Database connection failed
```

**Memory Issues:**
```
MemoryError
OOMKilled
```

### Log Commands
```bash
# Follow logs with context
kubectl logs -n gamer-gambit deployment/kallax -f --tail=20

# Search for errors
kubectl logs -n gamer-gambit deployment/kallax --since=1h | grep -i "error\|exception\|failed"

# Export logs for analysis
kubectl logs -n gamer-gambit deployment/kallax --since=24h > debug.log
```

---

**Remember**: Most issues are resolved by restarting deployments and ensuring secrets are properly configured. When in doubt, check the basics first!
