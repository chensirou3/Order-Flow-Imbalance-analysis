# Monitor OFI Analysis on Server
param([int]$Interval = 30)

$startTime = Get-Date
$iteration = 0

while ($true) {
    $iteration++
    $elapsed = (Get-Date) - $startTime
    
    Clear-Host
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "       OFI Analysis Monitor - Server Side" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor Start: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
    Write-Host "Elapsed Time:  $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Yellow
    Write-Host "Check Count:   #$iteration" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
    Write-Host ""
    
    # Check process status
    Write-Host "[1] Process Status:" -ForegroundColor Green
    $processInfo = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep 'python3.*run_full' | grep -v grep"
    if ($processInfo) {
        $parts = $processInfo -split '\s+'
        $cpu = $parts[2]
        $mem = $parts[3]
        $time = $parts[9]
        Write-Host "    CPU: $cpu%  |  Memory: $mem%  |  Time: $time" -ForegroundColor White
    } else {
        Write-Host "    Process NOT running!" -ForegroundColor Red
    }
    Write-Host ""
    
    # Check results count
    Write-Host "[2] Results Generated:" -ForegroundColor Green
    $resultsCount = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && find results -name '*.csv' -newer analysis_output.log 2>/dev/null | wc -l"
    $totalResults = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && find results -name '*.csv' 2>/dev/null | wc -l"
    Write-Host "    New results: $resultsCount  |  Total results: $totalResults" -ForegroundColor White
    Write-Host ""
    
    # Get latest log output
    Write-Host "[3] Latest Log Output (last 20 lines):" -ForegroundColor Green
    $logOutput = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && tail -20 analysis_output.log 2>/dev/null"
    
    if ($logOutput) {
        $logOutput -split "`n" | ForEach-Object {
            $line = $_
            if ($line -match "Processing|Analyzing|Running") {
                Write-Host "    $_" -ForegroundColor Cyan
            }
            elseif ($line -match "completed|success|finished|✅") {
                Write-Host "    $_" -ForegroundColor Green
            }
            elseif ($line -match "error|failed|Error|❌") {
                Write-Host "    $_" -ForegroundColor Red
            }
            elseif ($line -match "symbol=|period=|horizon=") {
                Write-Host "    $_" -ForegroundColor Yellow
            }
            else {
                Write-Host "    $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "    No log output yet..." -ForegroundColor DarkGray
    }
    
    Write-Host ""
    Write-Host "----------------------------------------------------------------" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next update in $Interval seconds | Press Ctrl+C to exit" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Tip: To view full log, run:" -ForegroundColor DarkCyan
    Write-Host "  ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 'tail -f Order-Flow-Imbalance-analysis/analysis_output.log'" -ForegroundColor DarkCyan
    
    Start-Sleep -Seconds $Interval
}

