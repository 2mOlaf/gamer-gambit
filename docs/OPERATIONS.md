# Operations Guide

Daily operational tasks and commands for managing the Gamer Gambit Discord bots.

## 📊 Health Monitoring

### Quick Status Check
```bash
# Check all environments at once
kubectl get pods -A -l app=kallax
kubectl get pods -A -l app=kallax-test

# Detailed view
kubectl get pods,svc,ingress -n gamer-gambit
kubectl get pods,svc,ingress -n gamer-gambit-test
```

### Bot Health Verification
```bash
# Check if bots are responding (built-in health checks)
kubectl get pods -n gamer-gambit -l app=kallax -o wide
kubectl logs -n gamer-gambit deployment/kallax --tail=5

# Test environment
kubectl get pods -n gamer-gambit-test -l app=kallax-test -o wide  
kubectl logs -n gamer-gambit-test deployment/test-kallax --tail=5
```

## 🔧 Common Operations

### Restart Deployments
```bash
# Production
kubectl rollout restart deployment/kallax -n gamer-gambit
kubectl rollout status deployment/kallax -n gamer-gambit --timeout=300s

# Test
kubectl rollout restart deployment/test-kallax -n gamer-gambit-test  
kubectl rollout status deployment/test-kallax -n gamer-gambit-test --timeout=300s
```

### View Logs
```bash
# Follow live logs
kubectl logs -n gamer-gambit deployment/kallax -f

# Get recent logs with timestamps
kubectl logs -n gamer-gambit deployment/kallax --tail=50 --timestamps

# Search logs for errors
kubectl logs -n gamer-gambit deployment/kallax --tail=200 | grep -i error
```

### Scale Deployments
```bash
# Scale up (not typically needed for Discord bots)
kubectl scale deployment/kallax --replicas=2 -n gamer-gambit

# Scale down for maintenance
kubectl scale deployment/kallax --replicas=0 -n gamer-gambit

# Scale back to normal
kubectl scale deployment/kallax --replicas=1 -n gamer-gambit
```

## 🔐 Secrets Management

### View Current Secrets
```bash
# List secrets
kubectl get secrets -n gamer-gambit
kubectl get secrets -n gamer-gambit-test

# Describe secrets (shows keys but not values)
kubectl describe secret kallax-config -n gamer-gambit
```

### Update Secrets
```bash
# After editing your local secrets.yaml
kubectl apply -f discord/kallax/k8s/secrets.yaml

# Restart deployments to pick up changes
kubectl rollout restart deployment/kallax -n gamer-gambit
kubectl rollout restart deployment/test-kallax -n gamer-gambit-test
```

### Emergency Token Rotation
```bash
# 1. Update Discord bot token in Developer Portal
# 2. Update your local secrets.yaml file
# 3. Apply new secrets
kubectl apply -f discord/kallax/k8s/secrets.yaml

# 4. Restart bot immediately
kubectl rollout restart deployment/kallax -n gamer-gambit
```

## 📈 Performance Monitoring

### Resource Usage
```bash
# Current resource consumption
kubectl top pods -n gamer-gambit
kubectl top pods -n gamer-gambit-test

# Detailed resource requests/limits
kubectl describe pod -n gamer-gambit -l app=kallax | grep -A5 -B5 Resources
```

### Database Health
```bash
# Check persistent volume status
kubectl get pvc -n gamer-gambit
kubectl get pv | grep gamer-gambit

# Database size and health
kubectl exec -n gamer-gambit deployment/kallax -- ls -la /app/data/
kubectl exec -n gamer-gambit deployment/kallax -- du -sh /app/data/kallax.db
```

## 🚀 Deployment Operations

### Manual Image Updates
```bash
# Update to specific image version
kubectl set image deployment/kallax kallax=ghcr.io/2molaf/kallax-discord-bot:v1.2.3 -n gamer-gambit

# Update to latest from registry
kubectl set image deployment/kallax kallax=ghcr.io/2molaf/kallax-discord-bot:latest -n gamer-gambit

# Verify update
kubectl rollout status deployment/kallax -n gamer-gambit
```

### Rollback Operations
```bash
# View rollout history
kubectl rollout history deployment/kallax -n gamer-gambit

# Rollback to previous version
kubectl rollout undo deployment/kallax -n gamer-gambit

# Rollback to specific revision
kubectl rollout undo deployment/kallax -n gamer-gambit --to-revision=5
```

## 🧹 Maintenance Tasks

### Cleanup Old Resources
```bash
# Clean up failed pods
kubectl delete pods -n gamer-gambit --field-selector=status.phase=Failed

# Clean up completed jobs
kubectl delete jobs -n gamer-gambit --field-selector=status.successful=1

# Cleanup test environment after testing
kubectl delete namespace gamer-gambit-test
```

### Database Backup (Manual)
```bash
# Copy database to local machine
kubectl cp gamer-gambit/kallax-pod:/app/data/kallax.db ./kallax-backup-$(date +%Y%m%d).db

# Verify backup
ls -la kallax-backup-*.db
```

### Log Archival
```bash
# Export recent logs for analysis
kubectl logs -n gamer-gambit deployment/kallax --since=24h > kallax-logs-$(date +%Y%m%d).log

# Compress old logs
gzip kallax-logs-*.log
```

## 🔍 Troubleshooting Commands

### Pod Issues
```bash
# Get detailed pod information
kubectl describe pod -n gamer-gambit -l app=kallax

# Check events in namespace
kubectl get events -n gamer-gambit --sort-by=.metadata.creationTimestamp

# Debug networking
kubectl exec -n gamer-gambit deployment/kallax -- nslookup discord.com
kubectl exec -n gamer-gambit deployment/kallax -- curl -s https://api.github.com
```

### GitHub Actions Integration
```bash
# Check runner status
kubectl get pods -l app=gamer-gambit-runner
kubectl logs -l app=gamer-gambit-runner --tail=20

# Restart runner if needed
kubectl rollout restart deployment/gamer-gambit-runner
```

### Secret Validation
```bash
# Verify secrets are properly mounted
kubectl exec -n gamer-gambit deployment/kallax -- env | grep DISCORD
kubectl exec -n gamer-gambit deployment/kallax -- ls -la /app/data/

# Test bot connectivity
kubectl exec -n gamer-gambit deployment/kallax -- python -c "
import os
print('Discord Token:', 'SET' if os.getenv('DISCORD_TOKEN') else 'MISSING')
print('Database Path:', os.getenv('DATABASE_PATH'))
"
```

## 📋 Daily Checklist

### Morning Health Check
- [ ] Check bot status: `kubectl get pods -n gamer-gambit`
- [ ] Review overnight logs: `kubectl logs -n gamer-gambit deployment/kallax --since=8h`
- [ ] Verify GitHub Actions: Check repository Actions tab
- [ ] Test bot responsiveness in Discord

### Weekly Tasks
- [ ] Review resource usage: `kubectl top pods -n gamer-gambit`
- [ ] Check disk usage: Database size trends
- [ ] Review and archive logs
- [ ] Verify backup procedures

### Monthly Tasks
- [ ] Review and rotate API keys
- [ ] Update dependencies (Dependabot PRs)
- [ ] Performance analysis
- [ ] Infrastructure updates coordination

## 🚨 Emergency Procedures

### Bot Completely Down
```bash
# 1. Check pod status
kubectl get pods -n gamer-gambit

# 2. Check recent logs
kubectl logs -n gamer-gambit deployment/kallax --tail=50

# 3. Restart deployment
kubectl rollout restart deployment/kallax -n gamer-gambit

# 4. If still failing, check secrets and resources
kubectl describe pod -n gamer-gambit -l app=kallax
```

### Secrets Compromised
```bash
# 1. Immediately rotate Discord bot token
# 2. Update local secrets.yaml
# 3. Apply new secrets
kubectl apply -f discord/kallax/k8s/secrets.yaml

# 4. Restart bot
kubectl rollout restart deployment/kallax -n gamer-gambit

# 5. Monitor logs for successful startup
kubectl logs -n gamer-gambit deployment/kallax -f
```

---

**Pro Tip**: Set up aliases for common commands in your shell profile:
```bash
alias kgp='kubectl get pods'
alias kgp-prod='kubectl get pods -n gamer-gambit'
alias kgp-test='kubectl get pods -n gamer-gambit-test'
alias klogs-kallax='kubectl logs -n gamer-gambit deployment/kallax'
```
