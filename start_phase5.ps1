# Start Phase 5 parameter sweep on server

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Starting Phase 5 parameter sweep on server..."
Write-Host "=" * 80

# Start the process in background
Write-Host "`nStarting parameter sweep..."
ssh.exe -i $KEY $SERVER "cd $REMOTE_DIR && nohup python3 scripts/run_ofi_param_sweep.py > phase5_sweep.log 2>&1 &"

Start-Sleep -Seconds 2

# Check if process started
Write-Host "`nChecking process status..."
ssh.exe -i $KEY $SERVER "ps aux | grep run_ofi_param_sweep | grep -v grep"

Write-Host "`n" + "=" * 80
Write-Host "Phase 5 started!"
Write-Host "=" * 80

Write-Host "`nTo monitor progress:"
Write-Host "  .\monitor_phase5.ps1"
Write-Host "`nOr manually:"
Write-Host "  ssh -i $KEY $SERVER 'tail -f $REMOTE_DIR/phase5_sweep.log'"

