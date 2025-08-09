# Find NFS paths for Kubernetes PVCs
# Usage: .\find-pvc-path.ps1 [namespace] [pvc-name]

param(
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "gamer-gambit",
    
    [Parameter(Mandatory=$false)]
    [string]$PvcName = "kallax-data"
)

Write-Host "🔍 Finding NFS path for PVC..." -ForegroundColor Green
Write-Host ""

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
} catch {
    Write-Host "❌ kubectl not found" -ForegroundColor Red
    exit 1
}

# Get PVC details
Write-Host "📋 PVC Information:" -ForegroundColor Yellow
$pvcInfo = kubectl get pvc $PvcName -n $Namespace -o json 2>$null | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ PVC '$PvcName' not found in namespace '$Namespace'" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available PVCs in namespace:" -ForegroundColor Yellow
    kubectl get pvc -n $Namespace
    exit 1
}

$pvName = $pvcInfo.spec.volumeName
$pvcStatus = $pvcInfo.status.phase
$storageClass = $pvcInfo.spec.storageClassName

Write-Host "  PVC Name: $PvcName" -ForegroundColor White
Write-Host "  Namespace: $Namespace" -ForegroundColor White
Write-Host "  Status: $pvcStatus" -ForegroundColor White
Write-Host "  Storage Class: $storageClass" -ForegroundColor White
Write-Host "  Bound PV: $pvName" -ForegroundColor White

if ($pvcStatus -ne "Bound") {
    Write-Host "❌ PVC is not bound to a PV" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📁 Persistent Volume Details:" -ForegroundColor Yellow

# Get PV details
$pvInfo = kubectl get pv $pvName -o json | ConvertFrom-Json
$nfsServer = $pvInfo.spec.nfs.server
$nfsPath = $pvInfo.spec.nfs.path

Write-Host "  PV Name: $pvName" -ForegroundColor White
Write-Host "  NFS Server: $nfsServer" -ForegroundColor White
Write-Host "  NFS Path: $nfsPath" -ForegroundColor White

Write-Host ""
Write-Host "🎯 Direct Access Information:" -ForegroundColor Green
Write-Host "  Full NFS Path: $nfsServer`:$nfsPath" -ForegroundColor Cyan
Write-Host "  Local Mount: \\$nfsServer$($nfsPath.Replace('/','\'))" -ForegroundColor Cyan

Write-Host ""
Write-Host "📊 Usage in Pods:" -ForegroundColor Yellow

# Find pods using this PVC
$pods = kubectl get pods -n $Namespace -o json | ConvertFrom-Json
$usingPods = @()

foreach ($pod in $pods.items) {
    if ($pod.spec.volumes) {
        foreach ($volume in $pod.spec.volumes) {
            if ($volume.persistentVolumeClaim -and $volume.persistentVolumeClaim.claimName -eq $PvcName) {
                $usingPods += @{
                    Name = $pod.metadata.name
                    Status = $pod.status.phase
                    Volume = $volume.name
                }
            }
        }
    }
}

if ($usingPods.Count -gt 0) {
    Write-Host "  Used by pods:" -ForegroundColor White
    foreach ($pod in $usingPods) {
        Write-Host "    - $($pod.Name) ($($pod.Status))" -ForegroundColor White
    }
} else {
    Write-Host "  No pods currently using this PVC" -ForegroundColor White
}

Write-Host ""
Write-Host "🛠️ Access Methods:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Via Pod (Recommended):" -ForegroundColor Yellow
Write-Host "   kubectl exec -n $Namespace -it deployment/kallax -- /bin/bash" -ForegroundColor White
Write-Host "   cd /app/data" -ForegroundColor White
Write-Host ""
Write-Host "2. Direct NFS Access:" -ForegroundColor Yellow
Write-Host "   ⚠️  Use with caution - can cause data corruption if pod is running" -ForegroundColor Red
Write-Host "   Windows: \\$nfsServer$($nfsPath.Replace('/','\'))" -ForegroundColor White
Write-Host "   Linux:   mount -t nfs $nfsServer`:$nfsPath /mnt/pvc" -ForegroundColor White
Write-Host ""
Write-Host "3. Kubernetes Debug Pod:" -ForegroundColor Yellow
Write-Host "   kubectl run debug-pod --image=alpine --rm -it --restart=Never --" -ForegroundColor White
Write-Host "   overrides='{\"spec\":{\"containers\":[{\"name\":\"debug\",\"image\":\"alpine\",\"command\":[\"sleep\",\"3600\"],\"volumeMounts\":[{\"name\":\"data\",\"mountPath\":\"/data\"}]}],\"volumes\":[{\"name\":\"data\",\"persistentVolumeClaim\":{\"claimName\":\"$PvcName\"}}]}}'" -ForegroundColor White

Write-Host ""
Write-Host "📝 Best Practices:" -ForegroundColor Green
Write-Host "• Always access via pod when possible" -ForegroundColor White
Write-Host "• Stop the application before direct NFS access" -ForegroundColor White  
Write-Host "• Use debug pods for safe data inspection" -ForegroundColor White
Write-Host "• Backup before making direct changes" -ForegroundColor White
