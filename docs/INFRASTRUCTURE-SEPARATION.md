# Infrastructure Separation Guide

This document outlines the proper separation between application-specific infrastructure (gamer-gambit repo) and general Kubernetes infrastructure (ansuz-k8s repo).

## Current State

### gamer-gambit Repository (✅ Correct)
- **Discord bots**: Kallax bot application code
- **Bot-specific K8s manifests**: Deployments, services, secrets for Discord bots
- **GitHub Actions workflows**: CI/CD for applications
- **GitHub Actions runner**: Self-hosted runner for this project's CI/CD
- **Application documentation**: Bot usage, features, deployment guides

### ansuz-k8s Repository (✅ Correct)
- **Core infrastructure**: MetalLB, Ingress Controller, Storage
- **Cluster-wide components**: Networking, security, monitoring
- **Infrastructure documentation**: Cluster setup, troubleshooting

## Recommendations

### ✅ Keep in gamer-gambit
These are application-specific and should stay:

```
gamer-gambit/
├── discord/
│   ├── kallax/                   # Bot application code
│   │   ├── k8s/                  # Bot-specific K8s manifests
│   │   │   ├── base/            # Base deployment configs
│   │   │   ├── environments/    # Environment-specific configs
│   │   │   └── secrets.template.yaml
│   └── shared/
│       └── github-runner/       # CI/CD runner for this project
├── .github/workflows/           # CI/CD pipelines for bots
└── docs/                        # Application documentation
```

### 🔄 Consider for ansuz-k8s
Only if they become reusable across multiple projects:

- **Monitoring stack** (Prometheus, Grafana) - if monitoring multiple applications
- **Backup solutions** - if backing up multiple applications
- **Service mesh** - if implementing cross-application communication
- **Certificate management** - if managing certs for multiple apps

### ❌ Don't Move to ansuz-k8s
These are too application-specific:

- Discord bot code and containers
- Bot-specific secrets and configurations
- Application CI/CD workflows
- Bot-specific documentation

## Decision Matrix

| Component | Stay in gamer-gambit | Move to ansuz-k8s | Criteria |
|-----------|---------------------|-------------------|----------|
| Kallax bot code | ✅ | ❌ | Application-specific |
| Bot K8s manifests | ✅ | ❌ | Application-specific |
| Bot secrets templates | ✅ | ❌ | Application-specific |
| GitHub Actions workflows | ✅ | ❌ | Project-specific CI/CD |
| GitHub runner | ✅ | ❌ | Project-specific CI/CD |
| MetalLB config | ❌ | ✅ | Cluster-wide infrastructure |
| Ingress controller | ❌ | ✅ | Cluster-wide infrastructure |
| Storage classes | ❌ | ✅ | Cluster-wide infrastructure |
| Monitoring (if shared) | ❌ | ✅ | Multi-application |

## Benefits of Current Separation

### gamer-gambit Repository
- **Self-contained**: Everything needed to deploy Discord bots
- **Version control**: Bot code and deployment configs versioned together
- **CI/CD isolation**: Changes only affect Discord bot deployments
- **Team boundaries**: Discord bot developers have full control

### ansuz-k8s Repository  
- **Infrastructure focus**: Core cluster components only
- **Stability**: Changes are infrequent and well-planned
- **Reusability**: Infrastructure can support multiple application projects
- **Security**: Infrastructure changes require different approval process

## Future Considerations

### If Adding More Applications
```
ansuz-k8s/           # Core infrastructure
├── infrastructure/ 
│   ├── metallb/
│   ├── ingress/
│   └── storage/
└── monitoring/      # If monitoring multiple apps

gamer-gambit/        # Discord gaming applications
├── discord/
└── docs/

other-project/       # Future application project
├── application-code/
├── k8s/
└── docs/
```

### Shared Services Pattern
If you develop multiple application projects, consider:

- **Shared monitoring**: Move to ansuz-k8s
- **Shared ingress rules**: Keep application-specific
- **Shared secrets management**: External tools (Vault, etc.)
- **Shared storage**: Infrastructure in ansuz-k8s, PVCs in applications

## Recommendations Summary

**✅ Current separation is correct** - keep as is!

The gamer-gambit repository properly contains:
- Application code
- Application-specific infrastructure
- Project-specific CI/CD
- Application documentation

The ansuz-k8s repository properly contains:
- Cluster-wide infrastructure
- Core networking and storage
- Infrastructure documentation

This separation follows Kubernetes best practices and maintains clear boundaries between infrastructure and applications.
