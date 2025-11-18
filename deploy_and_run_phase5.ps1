# Deploy and run Phase 5 parameter sweep

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Phase 5: Deploy and Run Parameter Sweep"
Write-Host "=" * 80

# Step 1: Deploy
Write-Host "`nStep 1: Deploying code to server..."
Write-Host "-" * 80
& .\deploy_phase5.ps1

# Step 2: Start
Write-Host "`n`nStep 2: Starting parameter sweep..."
Write-Host "-" * 80
& .\start_phase5.ps1

# Step 3: Initial monitor
Write-Host "`n`nStep 3: Initial status check..."
Write-Host "-" * 80
Start-Sleep -Seconds 5
& .\monitor_phase5.ps1

Write-Host "`n" + "=" * 80
Write-Host "Deployment and startup complete!"
Write-Host "=" * 80
Write-Host "`nThe parameter sweep is now running on the server."
Write-Host "Use .\monitor_phase5.ps1 to check progress."
Write-Host "`nExpected runtime: 5-15 minutes for default configuration"
Write-Host "(2 symbols x 3 timeframes x 36 param combos = 216 tests)"

