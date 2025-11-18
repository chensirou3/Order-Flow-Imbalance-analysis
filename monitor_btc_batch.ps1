# Monitor BTC Batch Analysis Progress

param(
    [int]$Interval = 30  # Update interval in seconds
)

$totalBatches = 5
$totalPeriods = 8
$totalTasks = $totalBatches * $totalPeriods  # 5 batches × 8 periods = 40 tasks

$speeds = @()
$lastCompleted = 0
$lastTime = $null

while ($true) {
    $now = Get-Date
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  BTCUSD Batch Analysis Progress Monitor" -ForegroundColor Cyan
    Write-Host "  Time: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if process is running
    Write-Host "[Process Status]" -ForegroundColor Yellow
    $proc = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep 'python3.*run_btc' | grep -v grep"
    if ($proc) {
        Write-Host "  Status: RUNNING" -ForegroundColor Green
        $parts = $proc -split '\s+' | Where-Object { $_ }
        if ($parts.Count -gt 10) {
            Write-Host "  CPU: $($parts[2])%  Memory: $($parts[3])%  Time: $($parts[9])" -ForegroundColor White
        }
    } else {
        Write-Host "  Status: NOT RUNNING" -ForegroundColor Red
    }
    Write-Host ""
    
    # Count completed tasks (look for saved markers)
    Write-Host "[Progress Analysis]" -ForegroundColor Yellow
    $cmd2 = "cd Order-Flow-Imbalance-analysis; grep -c '保存到:' btc_batch_output.log 2>/dev/null || echo 0"
    $completedStr = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd2
    $completed = 0
    try { $completed = [int]$completedStr.Trim() } catch { }
    
    $pct = if ($totalTasks -gt 0) { [Math]::Round(($completed * 100.0 / $totalTasks), 1) } else { 0 }
    
    Write-Host "  Total Tasks: $totalTasks (5 batches × 8 periods)" -ForegroundColor White
    Write-Host "  Completed: $completed" -ForegroundColor White
    Write-Host "  Progress: $pct%" -ForegroundColor Cyan
    Write-Host ""
    
    # Progress bar
    $barWidth = 60
    $filled = [Math]::Floor($barWidth * $pct / 100)
    $empty = $barWidth - $filled
    $bar = ""
    for ($i = 0; $i -lt $filled; $i++) { $bar += "█" }
    for ($i = 0; $i -lt $empty; $i++) { $bar += "░" }
    Write-Host "  $bar" -ForegroundColor Green
    Write-Host ""
    
    # Calculate speed
    if ($lastTime -and $completed -gt $lastCompleted) {
        $elapsed = ($now - $lastTime).TotalMinutes
        if ($elapsed -gt 0) {
            $speed = ($completed - $lastCompleted) / $elapsed
            $speeds += $speed
            if ($speeds.Count -gt 5) {
                $speeds = $speeds[-5..-1]
            }
        }
    }
    
    # Calculate ETA
    if ($speeds.Count -gt 0) {
        $avgSpeed = ($speeds | Measure-Object -Average).Average
        Write-Host "  Speed: $([Math]::Round($avgSpeed, 2)) tasks/min" -ForegroundColor Cyan
        
        if ($avgSpeed -gt 0) {
            $remaining = $totalTasks - $completed
            $etaMinutes = $remaining / $avgSpeed
            $etaTime = $now.AddMinutes($etaMinutes)
            
            $hours = [Math]::Floor($etaMinutes / 60)
            $mins = [Math]::Floor($etaMinutes % 60)
            
            Write-Host "  Remaining: $remaining tasks" -ForegroundColor White
            Write-Host "  ETA: $hours h $mins min (around $($etaTime.ToString('HH:mm')))" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Speed: Calculating..." -ForegroundColor Gray
        Write-Host "  ETA: Calculating..." -ForegroundColor Gray
    }
    Write-Host ""
    
    # Current batch info
    Write-Host "[Current Activity]" -ForegroundColor Yellow
    $cmd1 = "cd Order-Flow-Imbalance-analysis; tail -20 btc_batch_output.log"
    $recentLog = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd1
    $currentInfo = $recentLog | Select-Object -Last 5
    if ($currentInfo) {
        foreach ($line in $currentInfo) {
            Write-Host "  $line" -ForegroundColor Gray
        }
    }
    Write-Host ""

    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "Next update in $Interval seconds (Press Ctrl+C to stop)" -ForegroundColor DarkGray
    Write-Host ""
    
    # Update tracking variables
    $lastCompleted = $completed
    $lastTime = $now
    
    # Wait
    Start-Sleep -Seconds $Interval
}

