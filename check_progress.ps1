# Simple one-time progress check
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  OFI Analysis Progress Check" -ForegroundColor Cyan
Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if process is running
Write-Host "[1] Process Status" -ForegroundColor Yellow
$result = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep 'python3.*run_full' | grep -v grep"
if ($result) {
    Write-Host "  Status: RUNNING" -ForegroundColor Green
    $parts = $result -split '\s+' | Where-Object { $_ }
    if ($parts.Count -gt 10) {
        Write-Host "  CPU: $($parts[2])%  Memory: $($parts[3])%  Time: $($parts[9])" -ForegroundColor White
    }
} else {
    Write-Host "  Status: NOT RUNNING" -ForegroundColor Red
}
Write-Host ""

# Get log
Write-Host "[2] Latest Log (last 25 lines)" -ForegroundColor Yellow
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && tail -25 analysis_output.log"
Write-Host ""

Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "To monitor continuously, run this script in a loop:" -ForegroundColor Cyan
Write-Host "  while (\$true) { .\check_progress.ps1; Start-Sleep -Seconds 30 }" -ForegroundColor Gray
Write-Host ""

