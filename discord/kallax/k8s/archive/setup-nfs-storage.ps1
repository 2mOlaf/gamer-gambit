# Setup NFS Storage Classes for Kubernetes Cluster
# This script creates general-purpose NFS storage classes that can be used by any workload

Write-Host "🗄️ Setting up NFS Storage Classes for Kubernetes..." -ForegroundColor Green
Write-Host ""

# Check if kubectl is available
try {
    kubectl version --client --short | Out-Null
    Write-Host "✅ kubectl found" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl not found. Please install kubectl and ensure it's in your PATH." -ForegroundColor Red
    exit 1
}

# Check cluster connection
try {
    kubectl cluster-info | Out-Null
    Write-Host "✅ Connected to Kubernetes cluster" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to Kubernetes cluster. Check your kubeconfig." -ForegroundColor Red
    exit 1
}

# Check if NFS CSI driver is available
Write-Host ""
Write-Host "🔍 Checking for NFS CSI driver..." -ForegroundColor Yellow
$nfsDriver = kubectl get csidrivers nfs.csi.k8s.io 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ NFS CSI driver (nfs.csi.k8s.io) not found in cluster" -ForegroundColor Red
    Write-Host "Please install the NFS CSI driver first:" -ForegroundColor Yellow
    Write-Host "  helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts" -ForegroundColor White
    Write-Host "  helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system" -ForegroundColor White
    exit 1
}
Write-Host "✅ NFS CSI driver found" -ForegroundColor Green

# Prompt for NFS server details
Write-Host ""
$nfsServer = Read-Host "Enter NFS server hostname/IP (default: mimisbrunnr.gradin.lan)"
if (-not $nfsServer) {
    $nfsServer = "mimisbrunnr.gradin.lan"
}

$storageShare = Read-Host "Enter NFS share path for general storage (default: /k8s-storage)"
if (-not $storageShare) {
    $storageShare = "/k8s-storage"
}

$persistentShare = Read-Host "Enter NFS share path for persistent storage (default: /k8s-persistent)"
if (-not $persistentShare) {
    $persistentShare = "/k8s-persistent"
}

# Create storage classes
Write-Host ""
Write-Host "📦 Creating NFS Storage Classes..." -ForegroundColor Yellow

$storageClassContent = @"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-general
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: nfs.csi.k8s.io
parameters:
  server: $nfsServer
  share: $storageShare
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-retain
provisioner: nfs.csi.k8s.io
parameters:
  server: $nfsServer
  share: $persistentShare
reclaimPolicy: Retain
volumeBindingMode: Immediate
allowVolumeExpansion: true
"@

$storageClassContent | kubectl apply -f -

Write-Host ""
Write-Host "✅ NFS Storage Classes created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Storage Classes:" -ForegroundColor Cyan
kubectl get storageclasses

Write-Host ""
Write-Host "Usage Examples:" -ForegroundColor Cyan
Write-Host "  # For temporary data (deleted with PVC):" -ForegroundColor White
Write-Host "  storageClassName: nfs-general" -ForegroundColor White
Write-Host ""
Write-Host "  # For persistent data (retained after PVC deletion):" -ForegroundColor White
Write-Host "  storageClassName: nfs-retain" -ForegroundColor White
Write-Host ""
Write-Host "Note: Ensure the NFS shares exist on your server:" -ForegroundColor Yellow
Write-Host "  $storageShare" -ForegroundColor White
Write-Host "  $persistentShare" -ForegroundColor White
