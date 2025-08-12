# Script to monitor Kallax deployment updates
Write-Host "🔍 Current Kallax deployment status:" -ForegroundColor Cyan
kubectl get deployment kallax -n gamer-gambit

Write-Host "`n📦 Current image:" -ForegroundColor Cyan
$currentImage = kubectl get deployment kallax -n gamer-gambit -o jsonpath='{.spec.template.spec.containers[0].image}'
Write-Host $currentImage

Write-Host "`n📊 Pod status:" -ForegroundColor Cyan
kubectl get pods -n gamer-gambit -l app=kallax

Write-Host "`n🤖 Runner status:" -ForegroundColor Cyan
kubectl get pods -A -l app=gamer-gambit-runner

Write-Host "`n💡 To watch for changes, run:" -ForegroundColor Yellow
Write-Host "kubectl get deployment kallax -n gamer-gambit -w"
