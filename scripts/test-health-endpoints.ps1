#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test all health endpoints via the k8s.dork.life ingress setup

.DESCRIPTION
    This script tests all the health endpoints exposed through the ingress controller
    to verify that the routing is working correctly.

.PARAMETER IngressIP
    The IP address of the ingress controller (default: 192.168.1.211)

.EXAMPLE
    ./test-health-endpoints.ps1
    
.EXAMPLE
    ./test-health-endpoints.ps1 -IngressIP "192.168.1.211"
#>

param(
    [string]$IngressIP = "192.168.1.211"
)

# ANSI color codes for better output
$Green = "`e[32m"
$Red = "`e[31m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

Write-HostName "${Blue}🎮 Testing Gamer Gambit Health Endpoints${Reset}" -ForegroundColor Blue
Write-HostName "=" * 50

# Define health endpoints to test
$endpoints = @(
    @{
        Name = "Jarvfjallet Health"
        URL = "http://jarvfjallet.k8s.dork.life/health"
        HostName = "jarvfjallet.k8s.dork.life"
    },
    @{
        Name = "Jarvfjallet Metrics"
        URL = "http://jarvfjallet.k8s.dork.life/metrics"
        HostName = "jarvfjallet.k8s.dork.life"
    },
    @{
        Name = "Kallax Health (Dev)"
        URL = "http://kallax.k8s.dork.life/health"
        HostName = "kallax.k8s.dork.life"
    },
    @{
        Name = "Kallax Metrics (Dev)"
        URL = "http://kallax.k8s.dork.life/metrics"
        HostName = "kallax.k8s.dork.life"
    },
    @{
        Name = "Kallax Status (Dev)"
        URL = "http://kallax.k8s.dork.life/status"
        HostName = "kallax.k8s.dork.life"
    },
    @{
        Name = "Prod Kallax Health"
        URL = "http://prod-kallax.k8s.dork.life/health"
        HostName = "prod-kallax.k8s.dork.life"
    },
    @{
        Name = "Prod Kallax Metrics"
        URL = "http://prod-kallax.k8s.dork.life/metrics"
        HostName = "prod-kallax.k8s.dork.life"
    },
    @{
        Name = "Prod Kallax Status"
        URL = "http://prod-kallax.k8s.dork.life/status"
        HostName = "prod-kallax.k8s.dork.life"
    },
    @{
        Name = "Health Dashboard"
        URL = "http://health.k8s.dork.life/"
        HostName = "health.k8s.dork.life"
    }
)

# Test function
function Test-HealthEndpoint {
    param(
        [string]$Name,
        [string]$URL,
        [string]$HostName,
        [string]$IngressIP
    )
    
    Write-HostName "`n${Yellow}Testing: ${Name}${Reset}" -ForegroundColor Yellow
    Write-HostName "URL: $URL"
    
    try {
        # Use curl-like behavior with Invoke-WebRequest
        # Add HostName header to simulate proper DNS routing
        $headers = @{ "Host" = $HostName }
        
        # Replace HostNamename in URL with ingress IP for testing
        $testURL = $URL -replace $HostName, $IngressIP
        
        Write-HostName "Actual request: $testURL (HostName: $HostName)"
        
        $response = Invoke-WebRequest -Uri $testURL -Headers $headers -TimeoutSec 10 -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-HostName "${Green}✅ SUCCESS${Reset} - Status: $($response.StatusCode)" -ForegroundColor Green
            
            # Show content preview for smaller responses
            $content = $response.Content
            if ($content.Length -lt 500 -and $content -match "^\{") {
                # Looks like JSON, format it nicely
                try {
                    $jsonObj = $content | ConvertFrom-Json
                    Write-HostName "${Blue}Response Preview:${Reset}" -ForegroundColor Blue
                    $jsonObj | ConvertTo-Json -Depth 3 | Write-HostName
                } catch {
                    Write-HostName "${Blue}Response Preview:${Reset} $($content.Substring(0, [Math]::Min(200, $content.Length)))" -ForegroundColor Blue
                }
            } elseif ($content.Length -lt 500) {
                Write-HostName "${Blue}Response Preview:${Reset} $($content.Substring(0, [Math]::Min(200, $content.Length)))" -ForegroundColor Blue
            } else {
                Write-HostName "${Blue}Response Size:${Reset} $($content.Length) bytes" -ForegroundColor Blue
            }
        } else {
            Write-HostName "${Red}❌ FAILED${Reset} - Status: $($response.StatusCode)" -ForegroundColor Red
        }
        
        return $true
    } catch {
        Write-HostName "${Red}❌ ERROR${Reset} - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Run tests
$successCount = 0
$totalCount = $endpoints.Count

Write-HostName "`n${Blue}Ingress Controller IP:${Reset} $IngressIP"
Write-HostName "${Blue}Total Endpoints:${Reset} $totalCount"

foreach ($endpoint in $endpoints) {
    if (Test-HealthEndpoint -Name $endpoint.Name -URL $endpoint.URL -HostName $endpoint.HostName -IngressIP $IngressIP) {
        $successCount++
    }
    Start-Sleep -Milliseconds 500  # Brief pause between requests
}

# Summary
Write-HostName "`n" + "=" * 50
Write-HostName "${Blue}📊 SUMMARY${Reset}" -ForegroundColor Blue
Write-HostName "Successful: ${Green}$successCount${Reset}/$totalCount" -ForegroundColor Green
Write-HostName "Failed: ${Red}$($totalCount - $successCount)${Reset}/$totalCount" -ForegroundColor Red

if ($successCount -eq $totalCount) {
    Write-HostName "`n${Green}🎉 All health endpoints are working correctly!${Reset}" -ForegroundColor Green
    Write-HostName "${Green}✅ Your k8s.dork.life ingress setup is successful!${Reset}" -ForegroundColor Green
} else {
    Write-HostName "`n${Yellow}⚠️  Some endpoints had issues. Check the logs above for details.${Reset}" -ForegroundColor Yellow
}

# DNS Setup Information
Write-HostName "`n${Blue}📋 DNS Setup Information:${Reset}" -ForegroundColor Blue
Write-HostName "To make these URLs work without specifying the IP address:"
Write-HostName "1. Ensure *.k8s.dork.life resolves to $IngressIP"
Write-HostName "2. Or add these entries to your local /etc/HostNames (or C:\Windows\System32\drivers\etc\HostNames):"
Write-HostName ""
foreach ($endpoint in $endpoints) {
    Write-HostName "$IngressIP`t$($endpoint.HostName)"
}
Write-HostName ""
Write-HostName "${Blue}🌐 Access URLs:${Reset}" -ForegroundColor Blue
Write-HostName "Health Dashboard: ${Green}http://health.k8s.dork.life/${Reset}" -ForegroundColor Green
Write-HostName "Jarvfjallet Health: ${Green}http://jarvfjallet.k8s.dork.life/health${Reset}" -ForegroundColor Green
Write-HostName "Kallax Health (Dev): ${Green}http://kallax.k8s.dork.life/health${Reset}" -ForegroundColor Green
Write-HostName "Prod Kallax Health: ${Green}http://prod-kallax.k8s.dork.life/health${Reset}" -ForegroundColor Green
