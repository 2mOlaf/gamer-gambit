# 🔒 Security Guidelines

## Overview
This repository contains Discord bot applications that require sensitive credentials. This document outlines security best practices and setup procedures.

## ⚠️ NEVER COMMIT CREDENTIALS

**The following files should NEVER be committed to version control:**
- `auth.json` - Contains Discord bot tokens
- `local.settings.json` - May contain API keys
- `.env` files - Environment variables with secrets
- Any file containing tokens, passwords, or API keys

## 🔧 Setup Instructions

### For Node.js Bots

1. **Copy the template:**
   ```bash
   cp node/auth.json.example node/auth.json
   cp discord/jarvfjallet/node/auth.json.example discord/jarvfjallet/node/auth.json
   ```

2. **Add your bot token:**
   Edit the `auth.json` files and replace `YOUR_DISCORD_BOT_TOKEN_HERE` with your actual Discord bot token.

3. **Verify .gitignore:**
   Ensure these files are ignored by git:
   ```bash
   git check-ignore auth.json  # Should return the filename
   ```

### For Python Bot (Kallax)

The Kallax bot uses environment variables and Kubernetes secrets for security:

1. **Local Development:**
   ```bash
   cp discord/kallax/.env.example discord/kallax/.env
   # Edit .env file with your credentials
   ```

2. **Kubernetes Deployment:**
   ```bash
   cd discord/kallax/k8s
   powershell -ExecutionPolicy Bypass -File .\update-secrets.ps1 "YOUR_DISCORD_TOKEN"
   ```

## 🛡️ Security Best Practices

### Bot Token Security
- **Regenerate tokens** if ever exposed publicly
- **Use environment variables** for production deployments
- **Rotate tokens** periodically
- **Monitor bot activity** for unauthorized access

### Repository Security
- **Review commits** before pushing
- **Use pre-commit hooks** to scan for credentials
- **Enable branch protection** on main branches
- **Regular security audits** of dependencies

### Discord Bot Permissions
- **Principle of least privilege** - only grant necessary permissions
- **Regular audit** of bot permissions across servers
- **Monitor OAuth scopes** used by the bot

## 🚨 If Credentials are Compromised

1. **Immediately revoke the token:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Select your application
   - Navigate to "Bot" section
   - Click "Reset Token"

2. **Generate new token:**
   - Copy the new token immediately
   - Update your local configuration files
   - Update Kubernetes secrets if applicable

3. **Review access logs:**
   - Check Discord audit logs
   - Monitor for unauthorized bot activity
   - Review server permissions

4. **Update deployment:**
   - Deploy with new token
   - Verify bot functionality
   - Monitor for issues

## 📋 Security Checklist

- [ ] All credential files are in `.gitignore`
- [ ] No hardcoded tokens in source code
- [ ] Environment variables used for sensitive data
- [ ] Kubernetes secrets properly configured
- [ ] Bot permissions follow least privilege principle
- [ ] Regular token rotation schedule established
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented

## 🔗 Useful Links

- [Discord Bot Token Security](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)
- [Git Secrets Prevention](https://github.com/awslabs/git-secrets)
- [Kubernetes Secrets Management](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Environment Variables Best Practices](https://12factor.net/config)

## 📞 Reporting Security Issues

If you discover a security vulnerability in this project, please report it privately by creating an issue with the "security" label. Do not disclose the vulnerability publicly until it has been addressed.
