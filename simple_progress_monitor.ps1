# Simple OFI Analysis Progress Monitor
param([int]$Interval = 20)

$startTime = Get-Date
$lastCompleted = 0
$lastCheckTime = $null
$speedHistory = @()

while ($true) {
    $now = Get-Date
    $elapsed = $now - $startTime
    
    Clear-Host
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "     OFI Analysis Progress Monitor (Server: 49.51.244.154)     " -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor Time: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    Write-Host "Elapsed: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Gray
    Write-Host ""
    
    # Check if process is running
    Write-Host "[ 1. Process Status ]" -ForegroundColor Yellow
    $processCheck = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep 'python3.*run_full' | grep -v grep"
    
    if ($processCheck -and $processCheck.Length -gt 20) {
        $procParts = $processCheck -split '\s+' | Where-Object { $_ -ne "" }
        Write-Host "  Status: " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
        Write-Host "  CPU: $($procParts[2])%  |  Memory: $($procParts[3])%  |  Time: $($procParts[9])" -ForegroundColor White
    } else {
        Write-Host "  Status: " -NoNewline
        Write-Host "NOT RUNNING" -ForegroundColor Red
    }
    Write-Host ""
    
    # Get progress
    Write-Host "[ 2. Analysis Progress ]" -ForegroundColor Yellow
    
    # Count completed tasks
    $completedStr = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && grep -c '保存结果' analysis_output.log 2>/dev/null || echo 0"
    $completed = 0
    if ($completedStr -match '^\d+$') {
        $completed = [int]$completedStr
    }
    
    $total = 48
    $percentage = [Math]::Round(($completed / $total) * 100, 1)
    
    # Draw progress bar
    $barWidth = 50
    $filledCount = [Math]::Floor($barWidth * $percentage / 100)
    $emptyCount = $barWidth - $filledCount
    $progressBar = ("█" * $filledCount) + ("░" * $emptyCount)
    
    Write-Host "  $progressBar" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Progress: $percentage%  ($completed / $total tasks)" -ForegroundColor White
    Write-Host ""
    
    # Calculate speed and ETA
    if ($lastCheckTime -and $completed -gt $lastCompleted) {
        $timeDiff = ($now - $lastCheckTime).TotalMinutes
        $taskDiff = $completed - $lastCompleted
        
        if ($timeDiff -gt 0) {
            $currentSpeed = $taskDiff / $timeDiff
            $speedHistory += $currentSpeed
            
            if ($speedHistory.Count -gt 5) {
                $speedHistory = $speedHistory[-5..-1]
            }
        }
    }
    
    if ($speedHistory.Count -gt 0) {
        $avgSpeed = ($speedHistory | Measure-Object -Average).Average
        $speedText = "$([Math]::Round($avgSpeed, 2)) tasks/min"
        Write-Host "  Speed: $speedText" -ForegroundColor Cyan

        $remaining = $total - $completed
        if ($avgSpeed -gt 0) {
            $etaMinutes = $remaining / $avgSpeed
            $etaTime = $now.AddMinutes($etaMinutes)
            $etaTimeStr = $etaTime.ToString('HH:mm:ss')

            if ($etaMinutes -ge 60) {
                $hours = [Math]::Floor($etaMinutes / 60)
                $mins = [Math]::Floor($etaMinutes % 60)
                $remainingText = "(in $hours h $mins min)"
            } else {
                $remainingText = "(in $([Math]::Floor($etaMinutes)) min)"
            }

            Write-Host "  ETA: $etaTimeStr $remainingText" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  Speed: Calculating..." -ForegroundColor Gray
        Write-Host "  ETA: Calculating..." -ForegroundColor Gray
    }
    
    $lastCompleted = $completed
    $lastCheckTime = $now
    Write-Host ""
    
    # Current task info
    Write-Host "[ 3. Current Task ]" -ForegroundColor Yellow
    $logCmd = 'cd Order-Flow-Imbalance-analysis; tail -30 analysis_output.log'
    $logLines = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $logCmd

    $currentSymbol = "Unknown"
    $currentStage = "Unknown"

    foreach ($line in $logLines) {
        if ($line -match "Symbol:\s*(\w+)") {
            $currentSymbol = $matches[1]
        }
        if ($line -match "\[(\d+)/(\d+)\]") {
            $currentStage = "[$($matches[1])/$($matches[2])]"
        }
    }

    Write-Host "  Symbol: $currentSymbol" -ForegroundColor White
    Write-Host "  Stage: $currentStage" -ForegroundColor White
    Write-Host ""

    # Latest log
    Write-Host "[ 4. Latest Log (last 10 lines) ]" -ForegroundColor Yellow
    $logLines | Select-Object -Last 10 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "Next update in $Interval seconds | Press Ctrl+C to exit" -ForegroundColor DarkGray
    Write-Host ""
    
    Start-Sleep -Seconds $Interval
}

