# PowerShell script to manage GitHub runner deployment
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('status', 'restart', 'logs', 'apply')]
    [string]$Action = 'status'
)

$deploymentFile = Join-Path $PSScriptRoot "github-runner-deployment.yaml"

switch ($Action) {
    'status' {
        Write-Host "=== GitHub Runner Status ===" -ForegroundColor Cyan
        kubectl get pods -l app=gamer-gambit-runner
        Write-Host "
=== Recent Events ===" -ForegroundColor Cyan
        kubectl get events --field-selector involvedObject.name=gamer-gambit-runner --sort-by='.lastTimestamp' | Select-Object -Last 5
    }
    'restart' {
        Write-Host "Restarting GitHub runner..." -ForegroundColor Yellow
        kubectl delete deployment gamer-gambit-runner 2>$null
        Start-Sleep -Seconds 5
        kubectl apply -f $deploymentFile
        Write-Host "Runner deployment restarted" -ForegroundColor Green
    }
    'logs' {
        Write-Host "=== Runner Logs ===" -ForegroundColor Cyan
        $pod = kubectl get pods -l app=gamer-gambit-runner -o jsonpath='{.items[0].metadata.name}' 2>$null
        if ($pod) {
            kubectl logs $pod -c runner --tail=50
        } else {
            Write-Host "No runner pod found" -ForegroundColor Red
        }
    }
    'apply' {
        Write-Host "Applying runner deployment..." -ForegroundColor Yellow
        kubectl apply -f $deploymentFile
        Write-Host "Deployment applied" -ForegroundColor Green
    }
}
