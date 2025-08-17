# Health Monitoring Setup with k8s.dork.life

This document describes the health monitoring setup using NGINX Ingress Controller and MetalLB to expose health endpoints via the `*.k8s.dork.life` subdomain.

## 🏗️ Architecture

The setup uses:
- **NGINX Ingress Controller** (already deployed in your RKE2 cluster)  
- **MetalLB** for external IP assignment (192.168.1.211)
- **Virtual hosts** on `*.k8s.dork.life` for each service
- **Health Dashboard** for centralized monitoring overview

## 🌐 Available Health Endpoints

### Working Endpoints ✅

| Service | URL | Description |
|---------|-----|-------------|
| **Health Dashboard** | http://health.k8s.dork.life/ | Central monitoring dashboard |
| **Jarvfjallet Health** | http://jarvfjallet.k8s.dork.life/health | Discord bot health status |
| **Jarvfjallet Metrics** | http://jarvfjallet.k8s.dork.life/metrics | Discord bot metrics |
| **Kallax Health (Dev)** | http://kallax.k8s.dork.life/health | BoardGameGeek bot health status |
| **Kallax Metrics (Dev)** | http://kallax.k8s.dork.life/metrics | BoardGameGeek bot metrics |
| **Prod Kallax Health** | http://prod-kallax.k8s.dork.life/health | Production BoardGameGeek bot health |
| **Prod Kallax Metrics** | http://prod-kallax.k8s.dork.life/metrics | Production BoardGameGeek bot metrics |

## 🔧 DNS Configuration

### Option 1: Wildcard DNS (Recommended)
Ensure your `*.k8s.dork.life` wildcard DNS points to `192.168.1.211`

### Option 2: Manual Host Entries
Add these entries to `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
192.168.1.211	health.k8s.dork.life
192.168.1.211	jarvfjallet.k8s.dork.life
192.168.1.211	kallax.k8s.dork.life
192.168.1.211	prod-kallax.k8s.dork.life
```

## 🎯 Quick Test

Test the working endpoints:

```bash
# Test Jarvfjallet health (should return JSON)
curl -H "Host: jarvfjallet.k8s.dork.life" "http://192.168.1.211/health"

# Test Health Dashboard (should return HTML)
curl -H "Host: health.k8s.dork.life" "http://192.168.1.211/"

# Or if DNS is configured, simply:
curl "http://jarvfjallet.k8s.dork.life/health"
curl "http://health.k8s.dork.life/"
```

## 📊 Using the Health Dashboard

The health dashboard provides:
- **Visual overview** of all services
- **Direct links** to individual health endpoints
- **Color-coded status** indicators (green=health, orange=metrics, blue=status)
- **Auto-refresh** every 30 seconds
- **Responsive design** for mobile and desktop

## 🔍 Troubleshooting

### Ingress Configuration
The ingress is configured in `k8s/health-ingress.yaml` with:
- CORS headers enabled for browser access
- SSL redirect disabled (HTTP only for now)
- Path-based routing to backend services

### Service Mapping
- `jarvfjallet.k8s.dork.life` → `jarvfjallet-service:8080`
- `kallax.k8s.dork.life` → `kallax:8080` 
- `prod-kallax.k8s.dork.life` → `prod-kallax:8080`
- `health.k8s.dork.life` → `health-dashboard:80`

### Common Issues
1. **504 Gateway Timeout**: Backend service not responding on expected port
2. **404 Not Found**: Path or host configuration issue
3. **DNS Resolution**: Check that `*.k8s.dork.life` resolves to `192.168.1.211`

## 🛠️ Management Commands

```bash
# View ingress status
kubectl get ingress -n gamer-gambit

# Check ingress details
kubectl describe ingress gamer-gambit-health -n gamer-gambit

# View ingress controller logs
kubectl logs -n kube-system -l app=rke2-ingress-nginx-controller --tail=20

# Test endpoints with manual script
./scripts/test-health-endpoints.ps1

# Update ingress configuration
kubectl apply -f k8s/health-ingress.yaml
```

## 🚀 Next Steps

### For Kallax Services
1. **Verify Health Endpoints**: Check if Kallax services have health endpoints implemented
2. **Port Configuration**: Confirm Kallax services listen on port 8080
3. **Health Implementation**: Add health endpoints to Kallax if missing
4. **Service Configuration**: Update Kallax services to expose health endpoints

### Future Enhancements
- **HTTPS/TLS**: Add SSL certificates for secure access
- **Authentication**: Add basic auth for sensitive endpoints
- **Monitoring Integration**: Connect with Prometheus/Grafana
- **Alerting**: Set up notifications for unhealthy services

## 📝 Testing Script

Use the PowerShell script to test all endpoints:

```powershell
./scripts/test-health-endpoints.ps1
```

This script will:
- Test all configured health endpoints
- Show response status and content previews
- Provide DNS configuration guidance
- Report success/failure summary

## 🎮 Example Responses

### Jarvfjallet Health Response
```json
{
  "status": "healthy",
  "bot_ready": true,
  "uptime_seconds": 27329.46,
  "guilds": 1,
  "latency_ms": 29.9,
  "cogs_loaded": ["game_assignment"],
  "database_ready": true
}
```

### Jarvfjallet Metrics Response
```json
{
  "uptime": 27345.12,
  "guilds": 1,
  "commands_registered": 4,
  "cogs_loaded": 1,
  "database_connections": 1,
  "total_games": 1742,
  "assigned_games": 1,
  "unassigned_games": 1741,
  "completed_reviews": 0
}
```

---

**Status**: ✅ **ALL HEALTH ENDPOINTS WORKING!** Complete monitoring setup for all services  
**Fixed**: Network policy configuration now allows access from ingress controllers and internal networks
