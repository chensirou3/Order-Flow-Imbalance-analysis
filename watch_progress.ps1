# Ultra-simple progress monitor
param([int]$Interval = 20)

$startTime = Get-Date
$lastCompleted = 0
$lastTime = $null
$speeds = @()

while ($true) {
    $now = Get-Date
    $elapsed = $now - $startTime
    
    Clear-Host
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  OFI Analysis Monitor - Server 49.51.244.154" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Time: $($now.ToString('HH:mm:ss'))  |  Elapsed: $($elapsed.Hours)h $($elapsed.Minutes)m" -ForegroundColor Gray
    Write-Host ""
    
    # Process status
    Write-Host "[1] Process Status" -ForegroundColor Yellow
    $proc = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep python3 | grep run_full | grep -v grep"
    if ($proc) {
        $p = $proc -split '\s+' | Where-Object { $_ }
        Write-Host "  Running: YES  |  CPU: $($p[2])%  |  MEM: $($p[3])%  |  Time: $($p[9])" -ForegroundColor Green
    } else {
        Write-Host "  Running: NO" -ForegroundColor Red
    }
    Write-Host ""
    
    # Progress
    Write-Host "[2] Progress" -ForegroundColor Yellow
    $countCmd = 'grep -c saved analysis_output.log 2>/dev/null || echo 0'
    $completedRaw = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis; $countCmd"
    $completed = 0
    try { $completed = [int]$completedRaw } catch { $completed = 0 }
    
    $total = 48
    $pct = [Math]::Round(($completed * 100.0 / $total), 1)
    
    # Bar
    $w = 50
    $f = [Math]::Floor($w * $pct / 100)
    $e = $w - $f
    $bar = ""
    for ($i = 0; $i -lt $f; $i++) { $bar += "█" }
    for ($i = 0; $i -lt $e; $i++) { $bar += "░" }
    
    Write-Host "  $bar" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Completed: $completed / $total" -ForegroundColor White
    Write-Host "  Percentage: $pct%" -ForegroundColor Cyan
    Write-Host ""
    
    # Speed and ETA
    if ($lastTime -and $completed -gt $lastCompleted) {
        $mins = ($now - $lastTime).TotalMinutes
        if ($mins -gt 0) {
            $speed = ($completed - $lastCompleted) / $mins
            $speeds += $speed
            if ($speeds.Count -gt 5) { $speeds = $speeds[-5..-1] }
        }
    }
    
    if ($speeds.Count -gt 0) {
        $avgSpeed = ($speeds | Measure-Object -Average).Average
        $speedRounded = [Math]::Round($avgSpeed, 2)
        Write-Host "  Speed: $speedRounded tasks/min" -ForegroundColor Cyan
        
        if ($avgSpeed -gt 0) {
            $remaining = $total - $completed
            $etaMins = $remaining / $avgSpeed
            $etaTime = $now.AddMinutes($etaMins)
            $etaStr = $etaTime.ToString('HH:mm:ss')
            $etaMinsRounded = [Math]::Floor($etaMins)
            
            Write-Host "  ETA: $etaStr (in $etaMinsRounded min)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  Speed: Calculating..." -ForegroundColor Gray
        Write-Host "  ETA: Calculating..." -ForegroundColor Gray
    }
    
    $lastCompleted = $completed
    $lastTime = $now
    Write-Host ""
    
    # Latest log
    Write-Host "[3] Latest Log" -ForegroundColor Yellow
    $logCmd = 'tail -12 analysis_output.log'
    $log = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis; $logCmd"
    foreach ($line in $log) {
        Write-Host "  $line" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "Next update in $Interval sec | Ctrl+C to exit" -ForegroundColor DarkGray
    Write-Host ""
    
    Start-Sleep -Seconds $Interval
}

