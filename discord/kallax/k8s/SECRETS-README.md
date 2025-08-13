# Secrets Management for Kallax Discord Bot

This document explains how to securely manage secrets for the Kallax Discord Bot deployment on Kubernetes.

## 🔐 Security Approach

- **Templates Only in Git**: Only template files are committed to the repository
- **Local Secrets**: Actual secrets are stored locally and never committed
- **Gitignore Protection**: Multiple layers of gitignore rules prevent accidental commits
- **Kubernetes Secrets**: All sensitive data is stored as Kubernetes secrets

## 📁 File Structure

```
k8s/
├── secrets.template.yaml  ✅ Committed to Git (template only)
├── secrets.yaml          ❌ NEVER committed (contains real secrets)
├── setup-secrets.sh      ✅ Setup script for Linux/macOS
└── setup-secrets.ps1     ✅ Setup script for Windows
```

## 🚀 Quick Setup

### Option 1: Using Setup Script (Recommended)

**Windows (PowerShell):**
```powershell
cd discord/kallax/k8s
.\setup-secrets.ps1
```

**Linux/macOS (Bash):**
```bash
cd discord/kallax/k8s
chmod +x setup-secrets.sh
./setup-secrets.sh
```

### Option 2: Manual Setup

1. Copy the template:
   ```bash
   cp secrets.template.yaml secrets.yaml
   ```

2. Edit `secrets.yaml` and replace all placeholder values with your actual credentials
3. Apply to Kubernetes:
   ```bash
   kubectl apply -f secrets.yaml
   ```

## 🎯 Required Credentials

### Discord Bot Configuration
- **DISCORD_TOKEN**: Your bot token from Discord Developer Portal
- **DISCORD_GUILD_ID**: Your Discord server ID (optional, for faster command sync)

### Platform API Keys
- **STEAM_API_KEY**: From https://steamcommunity.com/dev/apikey
- **XBOX_API_KEY**: From Xbox Developer Portal

### Where to Get Credentials

1. **Discord Bot Token**:
   - Go to https://discord.com/developers/applications
   - Select your bot application
   - Go to "Bot" section
   - Copy the token

2. **Steam API Key**:
   - Go to https://steamcommunity.com/dev/apikey
   - Register for a key (free)
   - Use any domain name for development

3. **Xbox API Key**:
   - Register at Xbox Developer Portal
   - Create an application
   - Get API credentials

## 🔧 Deployment Verification

After applying secrets, verify they exist:

```bash
# Check production secrets
kubectl get secrets -n gamer-gambit
kubectl describe secret kallax-config -n gamer-gambit
kubectl describe secret kallax-api-keys -n gamer-gambit

# Check test secrets
kubectl get secrets -n gamer-gambit-test
kubectl describe secret kallax-test-config -n gamer-gambit-test
kubectl describe secret kallax-test-api-keys -n gamer-gambit-test
```

## 🛡️ Security Best Practices

### ✅ DO:
- Use the setup scripts to create secrets.yaml
- Keep secrets.yaml local only
- Use separate test credentials when possible
- Regularly rotate your API keys
- Use `kubectl` to verify secret creation

### ❌ DON'T:
- Commit secrets.yaml to Git
- Share your secrets.yaml file
- Use production credentials in test environments
- Store secrets in plain text files
- Share API keys in chat or email

## 🔄 Updating Secrets

To update existing secrets:

1. Edit your local `secrets.yaml` file
2. Apply the changes:
   ```bash
   kubectl apply -f secrets.yaml
   ```
3. Restart the deployment to pick up new values:
   ```bash
   kubectl rollout restart deployment/kallax -n gamer-gambit
   kubectl rollout restart deployment/test-kallax -n gamer-gambit-test
   ```

## 🚨 Emergency Procedures

### If Secrets Are Accidentally Committed:

1. **Immediately rotate all exposed credentials**:
   - Generate new Discord bot token
   - Generate new API keys
   
2. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch discord/kallax/k8s/secrets.yaml' --prune-empty --tag-name-filter cat -- --all
   git push --force --all
   ```

3. **Update .gitignore** (already done in this setup)

4. **Apply new secrets** with rotated credentials

## 📞 Troubleshooting

### Secret Not Found Error
```
Error: secret "kallax-config" not found
```
**Solution**: Apply your secrets.yaml file first: `kubectl apply -f secrets.yaml`

### Pod Crashing Due to Missing Env Vars
Check if secrets exist and have correct keys:
```bash
kubectl get secret kallax-config -n gamer-gambit -o yaml
```

### Template File Missing
If `secrets.template.yaml` is missing, it means the repository setup is incomplete.

---

**Remember**: The security of your bot depends on keeping these secrets safe. Never commit real credentials to Git!
