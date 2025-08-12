# PowerShell script to update GitHub runner token
param(
    [Parameter(Mandatory=$true)]
    [string]$NewToken
)

# Get the script directory and find the deployment file
$scriptPath = $PSScriptRoot
$deploymentFile = Join-Path $scriptPath "github-runner-deployment.yaml"

# Check if file exists
if (-not (Test-Path $deploymentFile)) {
    Write-Error "Could not find deployment file at: $deploymentFile"
    Write-Host "Script is in: $scriptPath"
    Write-Host "Looking for file: $deploymentFile"
    exit 1
}

Write-Host "Found deployment file: $deploymentFile"

# Read current content
$content = Get-Content $deploymentFile

# Simple replacement of the known old token
$oldToken = "ACYMZHUBVLCSFOVD5EDQ4RLITFLOS"
$updatedContent = $content -replace $oldToken, $NewToken

# Write back to file
$updatedContent | Set-Content $deploymentFile

Write-Host "Updated runner token in deployment file"
Write-Host "Now run: kubectl apply -f $deploymentFile"
Write-Host "Check runner status: kubectl get pods -l app=gamer-gambit-runner"
