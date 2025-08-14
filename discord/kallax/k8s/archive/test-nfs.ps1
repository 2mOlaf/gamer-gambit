# Test NFS connectivity and setup for Kubernetes
# This script helps diagnose NFS issues and verify setup

param(
    [Parameter(Mandatory=$false)]
    [string]$NfsServer = "mimisbrunnr.gradin.lan"
)

Write-Host "🧪 Testing NFS Setup for Kubernetes..." -ForegroundColor Green
Write-Host ""

# Test 1: Check if NFS server is reachable
Write-Host "1. Testing NFS server connectivity..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $NfsServer -Count 2 -Quiet
    if ($ping) {
        Write-Host "   ✅ NFS server $NfsServer is reachable" -ForegroundColor Green
    } else {
        Write-Host "   ❌ NFS server $NfsServer is not reachable" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Failed to ping NFS server: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Check NFS exports from within cluster
Write-Host ""
Write-Host "2. Checking NFS exports from Kubernetes cluster..." -ForegroundColor Yellow
$testPod = @"
apiVersion: v1
kind: Pod
metadata:
  name: nfs-test-pod
  namespace: default
spec:
  restartPolicy: Never
  containers:
  - name: nfs-test
    image: alpine:latest
    command:
    - sh
    - -c
    - |
      apk add --no-cache nfs-utils
      echo "Testing NFS exports on $NfsServer..."
      showmount -e $NfsServer
      echo "---"
      echo "Testing NFS mount (if exports exist)..."
      mkdir -p /test-mount
      # Try to mount if any exports exist
      if showmount -e $NfsServer | grep -q '/'; then
        export_path=`$(showmount -e $NfsServer | tail -1 | awk '{print $$1}')
        echo "Attempting to mount $$export_path..."
        mount -t nfs $NfsServer:$$export_path /test-mount || echo "Mount failed"
        ls -la /test-mount || echo "Directory listing failed"
        umount /test-mount 2>/dev/null || true
      else
        echo "No NFS exports found"
      fi
"@

Write-Host "   Creating test pod..." -ForegroundColor Cyan
$testPod | kubectl apply -f -

# Wait for pod to complete
Write-Host "   Waiting for test to complete..." -ForegroundColor Cyan
$timeout = 60
$elapsed = 0
do {
    Start-Sleep 2
    $elapsed += 2
    $podStatus = kubectl get pod nfs-test-pod -o jsonpath='{.status.phase}' 2>$null
} while ($podStatus -eq "Pending" -and $elapsed -lt $timeout)

if ($podStatus -eq "Succeeded" -or $podStatus -eq "Failed") {
    Write-Host "   📋 Test results:" -ForegroundColor Cyan
    kubectl logs nfs-test-pod
} else {
    Write-Host "   ⏰ Test timed out or failed to start" -ForegroundColor Yellow
    kubectl logs nfs-test-pod 2>$null
}

# Cleanup
kubectl delete pod nfs-test-pod --ignore-not-found=true 2>$null

# Test 3: Check if NFS CSI driver is installed
Write-Host ""
Write-Host "3. Checking NFS CSI driver..." -ForegroundColor Yellow
$csiDriver = kubectl get csidrivers nfs.csi.k8s.io 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ NFS CSI driver is installed" -ForegroundColor Green
    kubectl get csidrivers nfs.csi.k8s.io
} else {
    Write-Host "   ❌ NFS CSI driver not found" -ForegroundColor Red
    Write-Host "   Install with: helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system" -ForegroundColor Yellow
}

# Test 4: Check storage classes
Write-Host ""
Write-Host "4. Checking storage classes..." -ForegroundColor Yellow
$storageClasses = kubectl get storageclasses 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "   📋 Available storage classes:" -ForegroundColor Cyan
    kubectl get storageclasses
} else {
    Write-Host "   ❌ No storage classes found" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔧 Recommendations:" -ForegroundColor Cyan
Write-Host ""
Write-Host "If no NFS exports were found, you need to:" -ForegroundColor Yellow
Write-Host "1. Configure NFS server on $NfsServer" -ForegroundColor White
Write-Host "2. Create NFS shares (e.g., /k8s-storage, /k8s-persistent)" -ForegroundColor White
Write-Host "3. Ensure shares are exported with proper permissions" -ForegroundColor White
Write-Host ""
Write-Host "Example NFS server configuration (/etc/exports):" -ForegroundColor Yellow
Write-Host "/k8s-storage *(rw,sync,no_subtree_check,no_root_squash)" -ForegroundColor White
Write-Host "/k8s-persistent *(rw,sync,no_subtree_check,no_root_squash)" -ForegroundColor White
Write-Host ""
Write-Host "After configuring NFS server, run:" -ForegroundColor Yellow
Write-Host "  .\setup-nfs-storage.ps1" -ForegroundColor White
