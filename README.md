# Gamer Gambit - Discord Gaming Community Platform

A collection of Discord bots and tools for gaming communities, with integrated BoardGameGeek, Steam, and Xbox support.

## 🎯 Project Overview

| Component | Status | Description |
|-----------|--------|-------------|
| **Kallax Bot** | ✅ Production | Discord bot for board gaming communities with BGG integration |
| **Infrastructure** | ✅ Production | Kubernetes deployments and CI/CD pipelines |
| **Jarvfjallet Bot** | 🚧 Planned | Future general gaming bot |

## 📁 Repository Structure

```
gamer-gambit/
├── discord/
│   ├── kallax/                    # Kallax Discord bot (Python)
│   │   ├── bot.py                 # Main bot application
│   │   ├── k8s/                   # Kubernetes manifests
│   │   └── docs/                  # Bot-specific documentation
│   └── shared/                    # Shared Discord infrastructure
├── docs/                          # Project-wide documentation
├── .github/workflows/             # CI/CD pipelines
└── README.md                      # This file
```

## 🚀 Quick Start (New Deployment)

### Prerequisites
Before any automation will work, you **must** have:

1. **Kubernetes Cluster** with:
   - LoadBalancer support (MetalLB or cloud provider)
   - Ingress controller
   - Persistent storage
   - GitHub Actions self-hosted runner

2. **External Dependencies**:
   - DNS entries for your cluster services
   - Discord Developer Application created
   - API keys for Steam/Xbox (optional)

### Day Zero Setup

1. **Set up infrastructure** (see [ansuz-k8s repository](https://gitea.gradin.lan/olafg/ansuz-k8s))
2. **Configure secrets**:
   ```bash
   cd discord/kallax/k8s
   ./setup-secrets.ps1  # Windows
   ./setup-secrets.sh   # Linux
   ```
3. **Deploy applications** via GitHub Actions or manually

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[Operations Guide](docs/OPERATIONS.md)** - Day-to-day operational tasks
- **[Security Guide](SECURITY.md)** - Security best practices
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🤖 Bots

### Kallax - Board Gaming Bot
- **Purpose**: BoardGameGeek integration for Discord communities
- **Features**: Game search, user profiles, collections, play tracking
- **Documentation**: [discord/kallax/README.md](discord/kallax/README.md)
- **Status**: Production ready with full CI/CD

## 🏗️ Infrastructure

- **Platform**: Kubernetes with GitHub Actions CI/CD
- **Registry**: GitHub Container Registry (ghcr.io)
- **Environments**: Production (`main` branch) and Test (`test` branch)
- **Secrets**: Kubernetes secrets with template system

## 🛠️ For Developers

### Local Development
```bash
cd discord/kallax
cp .env.example .env
# Edit .env with your credentials
pip install -r requirements.txt
python bot.py
```

### Deployment
Push to branches triggers automatic deployment:
- `main` → Production environment
- `test` → Test environment

## 🆘 Support

1. **Check the docs** in the `docs/` directory
2. **Review logs** with operational commands in `docs/OPERATIONS.md`
3. **Follow troubleshooting** guide for common issues

## 🔗 Related Projects

- **[ansuz-k8s](https://gitea.gradin.lan/olafg/ansuz-k8s)** - Core Kubernetes infrastructure
- **[GitHub Actions Runner](discord/shared/github-runner/)** - Self-hosted CI/CD runner

---

**Note**: This is the master project containing Discord applications. Core infrastructure components like MetalLB, Ingress, and storage are maintained in the separate `ansuz-k8s` repository.
