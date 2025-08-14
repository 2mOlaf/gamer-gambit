# 🚀 Quick Fix for Deployment Failures

## The Main Issue
Your GitHub Actions are failing because **the required Kubernetes secrets don't exist yet**. The bot deployment expects these secrets but can't find them.

## 🔧 Quick Fix (2 minutes)

### Step 1: Create Your Secrets File
```bash
# On your Kubernetes server/workstation
cd discord/kallax/k8s
cp secrets.template.yaml secrets.yaml
```

### Step 2: Edit With Your Real Credentials
Edit `secrets.yaml` and replace these placeholders:
- `YOUR_PRODUCTION_DISCORD_BOT_TOKEN_HERE` - Get from Discord Developer Portal
- `YOUR_TEST_DISCORD_BOT_TOKEN_HERE` - Same token or create a separate test bot
- `YOUR_DISCORD_GUILD_ID_HERE` - Your Discord server ID
- `YOUR_STEAM_API_KEY_HERE` - Get from https://steamcommunity.com/dev/apikey

### Step 3: Apply to Kubernetes
```bash
kubectl apply -f secrets.yaml
```

### Step 4: Verify Secrets Exist
```bash
# Check production secrets
kubectl get secrets -n gamer-gambit

# Check test secrets  
kubectl get secrets -n gamer-gambit-test
```

You should see:
```
kallax-config       Opaque   6      1m
kallax-api-keys     Opaque   2      1m
```

### Step 5: Retry Your GitHub Action
Go to GitHub Actions and re-run the failed workflow.

## ✅ What This Fixes

- ❌ `secret "kallax-config" not found` → ✅ Secrets exist
- ❌ `secret "kallax-test-config" not found` → ✅ Test secrets exist  
- ❌ Pod startup failures → ✅ Bot can access environment variables
- ❌ Deployment timeouts → ✅ Faster startup with proper config

## 🔐 Security Notes

- The `secrets.yaml` file is git-ignored and will **NEVER** be committed
- Only the template file is committed to Git
- Keep your actual secrets file local and secure

## 🆘 Still Failing?

Check these common issues:

1. **Self-hosted runners offline**: Verify your GitHub runners are online
2. **Wrong namespace**: Make sure namespaces `gamer-gambit` and `gamer-gambit-test` exist
3. **Missing PVC**: Check if `kallax-data` PersistentVolumeClaim exists:
   ```bash
   kubectl get pvc -n gamer-gambit
   kubectl get pvc -n gamer-gambit-test
   ```

## 📞 Quick Validation Commands

```bash
# Test if your secrets are working
kubectl get pods -n gamer-gambit-test
kubectl describe pod <pod-name> -n gamer-gambit-test
kubectl logs -n gamer-gambit-test deployment/test-kallax
```

---

**TL;DR**: Copy the template, add your tokens, apply with kubectl. That's it! 🎉
