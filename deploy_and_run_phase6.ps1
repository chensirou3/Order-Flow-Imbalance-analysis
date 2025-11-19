# Deploy and run Phase 6 in one step

param(
    [string]$modules = "all"
)

Write-Host "=" * 80
Write-Host "Deploy and Run Phase 6"
Write-Host "=" * 80
Write-Host ""

# Step 1: Deploy
Write-Host "Step 1: Deploying code..."
.\deploy_phase6.ps1

Write-Host ""
Write-Host "Waiting 2 seconds..."
Start-Sleep -Seconds 2

# Step 2: Start
Write-Host ""
Write-Host "Step 2: Starting Phase 6..."
.\start_phase6.ps1 -modules $modules

Write-Host ""
Write-Host "Waiting 5 seconds for startup..."
Start-Sleep -Seconds 5

# Step 3: Monitor
Write-Host ""
Write-Host "Step 3: Checking status..."
.\monitor_phase6.ps1

