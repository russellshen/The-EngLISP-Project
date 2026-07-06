# verify_docker.ps1
# EngLISP Local Docker Container Verification Script
# This script builds the local Docker image, runs the server on port 8000, 
# performs a health check query, and then cleanly shuts the container down.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "1. Building local Docker image (englisp-server)..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
$token = $env:PRIVATE_ASSETS_TOKEN
if (-not $token) {
    $token = $env:GITHUB_TOKEN
}

if ($token) {
    Write-Host "Found build token. Injecting into build..." -ForegroundColor Yellow
    docker build --build-arg PRIVATE_ASSETS_TOKEN=$token -t englisp-server .
} else {
    Write-Host "No build token found. Building with fallback sample dictionary assets..." -ForegroundColor Yellow
    docker build -t englisp-server .
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed. Please make sure Docker Desktop is running."
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "2. Launching temporary container..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
# Run container in background mapping port 8000
$containerId = (docker run -d -p 8000:8000 englisp-server).Trim()

if (-not $containerId) {
    Write-Error "Failed to start the Docker container."
}

Write-Host "Container started with ID: $containerId" -ForegroundColor Green
Write-Host "Waiting 5 seconds for the Gunicorn server to boot..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "3. Performing HTTP API health check..." -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    
    # Query /api/auth/me (returns stripe_enabled and other metadata)
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" -Method Get
    
    Write-Host "Response received successfully!" -ForegroundColor Green
    Write-Host "Authentication State: $($response.authenticated)" -ForegroundColor Yellow
    Write-Host "Stripe Enabled Status: $($response.stripe_enabled)" -ForegroundColor Yellow
    Write-Host "Server Tier: $($response.tier)" -ForegroundColor Yellow
    
    Write-Host "`n[SUCCESS] Local Docker container built and verified successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`n[ERROR] Health check failed to connect to the server." -ForegroundColor Red
    Write-Error $_
}
finally {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "4. Cleaning up container ($containerId)..." -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    docker stop $containerId | Out-Null
    docker rm $containerId | Out-Null
    Write-Host "Cleanup complete." -ForegroundColor Green
}
