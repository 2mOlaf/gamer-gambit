# PVC Management Quick Reference

## Finding Your PVC Path

### 1. Get PVC to PV mapping:
```bash
kubectl get pvc kallax-data -n gamer-gambit -o jsonpath='{.spec.volumeName}'
```

### 2. Get NFS path from PV:
```bash
# Get PV name first
PV_NAME=$(kubectl get pvc kallax-data -n gamer-gambit -o jsonpath='{.spec.volumeName}')

# Get NFS details
kubectl get pv $PV_NAME -o jsonpath='{.spec.nfs.server}:{.spec.nfs.path}'
```

### 3. One-liner to get full path:
```bash
kubectl get pv $(kubectl get pvc kallax-data -n gamer-gambit -o jsonpath='{.spec.volumeName}') -o jsonpath='{.spec.nfs.server}:{.spec.nfs.path}'
```

## Safe Data Access Methods

### Method 1: Via Running Pod (Safest)
```bash
# Access the running Kallax pod
kubectl exec -n gamer-gambit -it deployment/kallax -- /bin/bash
cd /app/data
ls -la

# View database with sqlite3
kubectl exec -n gamer-gambit -it deployment/kallax -- sqlite3 /app/data/kallax.db ".tables"
```

### Method 2: Debug Pod (Recommended for maintenance)
```bash
# Create a debug pod with the same PVC mounted
kubectl run debug-kallax -n gamer-gambit --image=alpine --rm -it --restart=Never \
  --overrides='{
    "spec": {
      "containers": [{
        "name": "debug",
        "image": "alpine",
        "command": ["sleep", "3600"],
        "volumeMounts": [{
          "name": "kallax-data",
          "mountPath": "/data"
        }]
      }],
      "volumes": [{
        "name": "kallax-data",
        "persistentVolumeClaim": {
          "claimName": "kallax-data"
        }
      }]
    }
  }' -- sh

# Inside the debug pod:
cd /data
ls -la
```

### Method 3: Direct NFS Access (Use with Caution)
```bash
# Only use when the pod is stopped!
# 1. Scale down the deployment first
kubectl scale deployment kallax -n gamer-gambit --replicas=0

# 2. Get the NFS path
NFS_PATH=$(kubectl get pv $(kubectl get pvc kallax-data -n gamer-gambit -o jsonpath='{.spec.volumeName}') -o jsonpath='{.spec.nfs.server}:{.spec.nfs.path}')

# 3. Mount locally (Linux/WSL)
sudo mkdir -p /mnt/kallax-data
sudo mount -t nfs $NFS_PATH /mnt/kallax-data

# 4. Access the data
cd /mnt/kallax-data
ls -la

# 5. When done, unmount and scale back up
sudo umount /mnt/kallax-data
kubectl scale deployment kallax -n gamer-gambit --replicas=1
```

### Method 4: Windows Direct Access
```powershell
# Get the path using the PowerShell script
.\find-pvc-path.ps1

# Use the Windows UNC path shown in the output
# Example: \\mimisbrunnr.gradin.lan\volume2\k8s-pvc\pvc-abc123-def4-5678-9012-345678901234
```

## Common Operations

### Backup Database
```bash
# Via pod
kubectl exec -n gamer-gambit deployment/kallax -- sqlite3 /app/data/kallax.db ".backup /app/data/kallax-backup-$(date +%Y%m%d).db"

# Copy backup out of pod
kubectl cp gamer-gambit/kallax-pod:/app/data/kallax-backup-20250809.db ./kallax-backup.db
```

### View Database Schema
```bash
kubectl exec -n gamer-gambit -it deployment/kallax -- sqlite3 /app/data/kallax.db ".schema"
```

### Monitor Database Size
```bash
kubectl exec -n gamer-gambit deployment/kallax -- du -sh /app/data/
```

### View Logs with Database Events
```bash
kubectl logs -n gamer-gambit deployment/kallax -f | grep -i database
```

## Best Practices

### ✅ Safe Practices
- **Always use pod access** for routine operations
- **Use debug pods** for maintenance tasks
- **Scale down deployments** before direct NFS access
- **Take backups** before making changes
- **Test changes** in a debug pod first

### ❌ Dangerous Practices
- **Never edit files directly** while pods are running
- **Don't mount NFS directly** without stopping the app
- **Avoid concurrent access** from multiple sources
- **Don't delete PVCs** without backing up data

## Troubleshooting

### PVC Won't Bind
```bash
# Check storage classes
kubectl get storageclass

# Check PV status
kubectl get pv

# Describe PVC for events
kubectl describe pvc kallax-data -n gamer-gambit
```

### Pod Won't Start (Volume Issues)
```bash
# Check pod events
kubectl describe pod -n gamer-gambit -l app=kallax

# Check if PVC exists and is bound
kubectl get pvc -n gamer-gambit

# Test NFS connectivity
kubectl run nfs-test --image=alpine --rm -it --restart=Never -- \
  sh -c "apk add nfs-utils && showmount -e mimisbrunnr.gradin.lan"
```

### Database Corruption
```bash
# Check database integrity
kubectl exec -n gamer-gambit -it deployment/kallax -- \
  sqlite3 /app/data/kallax.db "PRAGMA integrity_check;"

# Vacuum database
kubectl exec -n gamer-gambit -it deployment/kallax -- \
  sqlite3 /app/data/kallax.db "VACUUM;"
```
