# Monitor Phase 6 progress on server

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host ("=" * 80)
Write-Host "Phase 6 Monitor"
Write-Host ("=" * 80)
Write-Host ""

# Show latest log entries
Write-Host ("[Latest Log Entries]")
Write-Host ("-" * 80)
ssh.exe -i $KEY $SERVER "tail -100 $REMOTE_DIR/phase6.log"

Write-Host ""
Write-Host ("=" * 80)
Write-Host ("[Checking Completion Status]")
Write-Host ("=" * 80)
ssh.exe -i $KEY $SERVER "tail -20 $REMOTE_DIR/phase6.log | grep -E '(complete|Complete|ERROR)' || echo 'Still running...'"

Write-Host ""
Write-Host ("=" * 80)
Write-Host ("[Output Files]")
Write-Host ("=" * 80)
ssh.exe -i $KEY $SERVER "ls -lh $REMOTE_DIR/results/long_short/ 2>/dev/null || echo 'No long_short results yet'"
ssh.exe -i $KEY $SERVER "ls -lh $REMOTE_DIR/results/joint/ 2>/dev/null || echo 'No joint results yet'"
ssh.exe -i $KEY $SERVER "ls -lh $REMOTE_DIR/docs/strategy_specs/ 2>/dev/null || echo 'No strategy specs yet'"

Write-Host ""
Write-Host ("=" * 80)
Write-Host ("[Process Status]")
Write-Host ("=" * 80)
ssh.exe -i $KEY $SERVER "ps aux | grep 'run_phase6' | grep -v grep || echo 'Process not running'"

Write-Host ""
Write-Host ("=" * 80)
Write-Host ("[Resource Usage]")
Write-Host ("=" * 80)
ssh.exe -i $KEY $SERVER "free -h"
ssh.exe -i $KEY $SERVER "df -h /"

Write-Host ""
Write-Host ("=" * 80)
Write-Host "Monitor complete. Press Ctrl+C to exit or wait for auto-refresh..."
Write-Host ("=" * 80)

