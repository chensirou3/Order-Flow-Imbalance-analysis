# Start Phase 6 on server

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Starting Phase 6 on server..."
Write-Host "=" * 80
Write-Host ""

# Parse arguments
param(
    [string]$modules = "all"
)

Write-Host "Modules to run: $modules"
Write-Host ""

# Start Phase 6 in background
$cmd = "cd $REMOTE_DIR && nohup python3 scripts/run_phase6_all.py --modules $modules > phase6.log 2>&1 &"

Write-Host "Executing: $cmd"
ssh.exe -i $KEY $SERVER $cmd

Write-Host ""
Write-Host "Phase 6 started in background!"
Write-Host "Monitor with: .\monitor_phase6.ps1"
Write-Host ""

