# PowerShell script to update GitHub runner token
param(
    [Parameter(Mandatory=$true)]
    [string]$NewToken
)

$scriptPath = $PSScriptRoot
$deploymentFile = Join-Path $scriptPath "github-runner-deployment.yaml"

if (-not (Test-Path $deploymentFile)) {
    Write-Error "Could not find deployment file at: $deploymentFile"
    exit 1
}

Write-Host "Found deployment file: $deploymentFile"

# Read all content
$content = Get-Content $deploymentFile

# Find and replace the token
$updated = $false
for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i] -like "*- name: RUNNER_TOKEN*") {
        # Next line should have the value
        if ($i + 1 -lt $content.Count) {
            $valueLine = $content[$i + 1]
            if ($valueLine -like "*value:*") {
                # Extract current token for display
                $currentToken = ($valueLine -split '"')[1]
                Write-Host "Replacing token: $currentToken -> $NewToken"
                
                # Replace with new token, preserving indentation
                $indent = $valueLine.Substring(0, $valueLine.IndexOf('value:'))
                $content[$i + 1] = "${indent}value: `"$NewToken`""
                $updated = $true
                break
            }
        }
    }
}

if (-not $updated) {
    Write-Error "Could not find RUNNER_TOKEN value to update"
    exit 1
}

# Write back to file
$content | Set-Content $deploymentFile

Write-Host "Successfully updated runner token!"
Write-Host "Now run: kubectl apply -f $deploymentFile"
