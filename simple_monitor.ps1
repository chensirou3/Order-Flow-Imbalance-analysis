# Simple Analysis Monitor
param([int]$Interval = 20)

$startTime = Get-Date
$count = 0

while ($true) {
    $count++
    $elapsed = (Get-Date) - $startTime
    
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  OFI Analysis Monitor" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Start Time: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Yellow
    Write-Host "Elapsed: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Yellow
    Write-Host "Check #$count" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    
    # Get log output
    $log = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && tail -40 analysis_output.log 2>/dev/null"
    
    if ($log) {
        Write-Host "Latest Output:" -ForegroundColor Green
        Write-Host ""
        $log -split "`n" | Select-Object -Last 30 | ForEach-Object {
            Write-Host "  $_"
        }
    }
    else {
        Write-Host "Waiting for analysis to start..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host "Next update in $Interval seconds (Ctrl+C to exit)" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $Interval
}

