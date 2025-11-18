# Monitor Phase 5 parameter sweep progress

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Phase 5 Parameter Sweep Monitor"
Write-Host "=" * 80

# Show latest log entries
Write-Host "`n[Latest Log Entries]"
Write-Host "-" * 80
ssh.exe -i $KEY $SERVER "tail -50 $REMOTE_DIR/phase5_sweep.log"

# Check for completion
Write-Host "`n" + "=" * 80
Write-Host "[Checking Completion Status]"
Write-Host "=" * 80
ssh.exe -i $KEY $SERVER "grep -i 'complete' $REMOTE_DIR/phase5_sweep.log | tail -5"

# Check output files
Write-Host "`n" + "=" * 80
Write-Host "[Output Files]"
Write-Host "=" * 80
ssh.exe -i $KEY $SERVER "ls -lh $REMOTE_DIR/results/param_sweep/*.csv 2>/dev/null || echo 'No output files yet'"

# Show process status
Write-Host "`n" + "=" * 80
Write-Host "[Process Status]"
Write-Host "=" * 80
ssh.exe -i $KEY $SERVER "ps aux | grep run_ofi_param_sweep | grep -v grep || echo 'Process not running'"

# Show resource usage
Write-Host "`n" + "=" * 80
Write-Host "[Resource Usage]"
Write-Host "=" * 80
ssh.exe -i $KEY $SERVER "free -h | head -2"
ssh.exe -i $KEY $SERVER "df -h | grep -E '(Filesystem|/$)'"

Write-Host "`n" + "=" * 80
Write-Host "Monitor complete. Press Ctrl+C to exit or wait for auto-refresh..."
Write-Host "=" * 80

