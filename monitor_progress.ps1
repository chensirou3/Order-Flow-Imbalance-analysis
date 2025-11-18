# OFI Analysis Progress Monitor with Percentage, Speed, and ETA
param([int]$Interval = 15)

$script:startTime = Get-Date
$script:lastCheckTime = $null
$script:lastCompletedTasks = 0
$script:speedHistory = @()

function Get-AnalysisProgress {
    # Get log content
    $logContent = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && cat analysis_output.log 2>/dev/null"

    # Parse total tasks
    $totalTasks = 48
    if ($logContent -match "总配置数:\s*(\d+)") {
        $totalTasks = [int]$matches[1]
    }

    # Count completed tasks - look for result file saves
    $completedCount = 0
    $saveMatches = [regex]::Matches($logContent, "保存结果|Saved results|✅")
    $completedCount = $saveMatches.Count

    # Get current processing info from last lines
    $lastLines = $logContent -split "`n" | Select-Object -Last 30
    $lastText = $lastLines -join "`n"

    $currentSymbol = "Unknown"
    $currentPeriod = "Unknown"
    $currentStage = "Processing..."

    if ($lastText -match "处理品种:\s*(\w+)") { $currentSymbol = $matches[1] }
    if ($lastText -match "时间周期:\s*(\w+)") { $currentPeriod = $matches[1] }
    if ($lastText -match "\[(\d+)/\d+\]\s*([^\r\n]+)") { $currentStage = $matches[2].Trim() }

    # Get process info
    $processInfo = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep 'python3.*run_full' | grep -v grep"
    $cpuUsage = 0
    $memUsage = 0
    $processTime = "0:00"
    $isRunning = $false

    if ($processInfo -and $processInfo.Length -gt 10) {
        $isRunning = $true
        $parts = $processInfo -split '\s+' | Where-Object { $_ -ne "" }
        if ($parts.Count -gt 10) {
            $cpuUsage = $parts[2]
            $memUsage = $parts[3]
            $processTime = $parts[9]
        }
    }

    return @{
        TotalTasks = $totalTasks
        CompletedTasks = $completedCount
        CurrentSymbol = $currentSymbol
        CurrentPeriod = $currentPeriod
        CurrentStage = $currentStage
        CpuUsage = $cpuUsage
        MemUsage = $memUsage
        ProcessTime = $processTime
        IsRunning = $isRunning
    }
}

function Format-TimeSpan {
    param([TimeSpan]$ts)
    if ($ts.TotalHours -ge 1) {
        return "{0}h {1}m {2}s" -f $ts.Hours, $ts.Minutes, $ts.Seconds
    } elseif ($ts.TotalMinutes -ge 1) {
        return "{0}m {1}s" -f $ts.Minutes, $ts.Seconds
    } else {
        return "{0}s" -f $ts.Seconds
    }
}

function Draw-ProgressBar {
    param([double]$Percentage, [int]$Width = 50)
    
    $filled = [Math]::Floor($Width * $Percentage / 100)
    $empty = $Width - $filled
    
    $bar = ""
    $bar += "█" * $filled
    $bar += "░" * $empty
    
    return $bar
}

while ($true) {
    $currentTime = Get-Date
    $progress = Get-AnalysisProgress

    # Calculate percentage
    $percentage = if ($progress.TotalTasks -gt 0) {
        [Math]::Round(($progress.CompletedTasks / $progress.TotalTasks) * 100, 1)
    } else { 0 }

    # Calculate speed and ETA
    $speed = 0
    $speedText = "计算中..."
    $eta = "计算中..."
    $etaText = "计算中..."

    if ($script:lastCheckTime -and $progress.CompletedTasks -gt $script:lastCompletedTasks) {
        $timeDiff = ($currentTime - $script:lastCheckTime).TotalMinutes
        $taskDiff = $progress.CompletedTasks - $script:lastCompletedTasks

        if ($timeDiff -gt 0 -and $taskDiff -gt 0) {
            $speed = $taskDiff / $timeDiff

            # Add to history
            $script:speedHistory += $speed

            # Keep only last 5 records
            if ($script:speedHistory.Count -gt 5) {
                $script:speedHistory = $script:speedHistory[-5..-1]
            }

            # Calculate average speed
            $avgSpeed = ($script:speedHistory | Measure-Object -Average).Average

            if ($avgSpeed -gt 0) {
                $speedText = "{0:F2} 任务/分钟" -f $avgSpeed

                $remainingTasks = $progress.TotalTasks - $progress.CompletedTasks
                $etaMinutes = $remainingTasks / $avgSpeed
                $etaTime = $currentTime.AddMinutes($etaMinutes)
                $eta = $etaTime
                $etaText = $etaTime.ToString("HH:mm:ss")

                $remainingTime = [TimeSpan]::FromMinutes($etaMinutes)
                if ($remainingTime.TotalHours -ge 1) {
                    $etaText += " (剩余 {0:F0}小时{1:F0}分钟)" -f $remainingTime.TotalHours, $remainingTime.Minutes
                } else {
                    $etaText += " (剩余 {0:F0}分钟)" -f $remainingTime.TotalMinutes
                }
            }
        }
    }

    $script:lastCheckTime = $currentTime
    $script:lastCompletedTasks = $progress.CompletedTasks
    
    # Display
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║           OFI 分析任务实时监控 - 服务器端                                 ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Status
    if ($progress.IsRunning) {
        Write-Host "  状态: " -NoNewline -ForegroundColor Yellow
        Write-Host "✅ 运行中" -ForegroundColor Green
    } else {
        Write-Host "  状态: " -NoNewline -ForegroundColor Yellow
        Write-Host "❌ 未运行" -ForegroundColor Red
    }
    
    Write-Host "  监控时间: $($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    Write-Host ""
    
    # Progress
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  📊 总体进度" -ForegroundColor Cyan
    Write-Host ""
    
    $progressBar = Draw-ProgressBar -Percentage $percentage -Width 60
    Write-Host "  $progressBar" -ForegroundColor Green
    Write-Host ""
    Write-Host "  完成: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.CompletedTasks) / $($progress.TotalTasks) 任务" -ForegroundColor White
    Write-Host "  进度: " -NoNewline -ForegroundColor Yellow
    Write-Host "$percentage%" -ForegroundColor White
    Write-Host ""
    
    # Speed and ETA
    Write-Host "  ⚡ 速度: " -NoNewline -ForegroundColor Yellow
    Write-Host "$speedText" -ForegroundColor White

    Write-Host "  ⏰ 预计完成: " -NoNewline -ForegroundColor Yellow
    Write-Host "$etaText" -ForegroundColor White
    Write-Host ""
    
    # Current task
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  🔄 当前任务" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  品种: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.CurrentSymbol)" -ForegroundColor White
    Write-Host "  周期: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.CurrentPeriod)" -ForegroundColor White
    Write-Host "  阶段: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.CurrentStage)" -ForegroundColor White
    Write-Host ""
    
    # System resources
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  💻 系统资源" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  CPU: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.CpuUsage)%" -ForegroundColor White
    Write-Host "  内存: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.MemUsage)%" -ForegroundColor White
    Write-Host "  运行时间: " -NoNewline -ForegroundColor Yellow
    Write-Host "$($progress.ProcessTime)" -ForegroundColor White
    Write-Host ""
    
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  下次更新: $Interval 秒后 | 按 Ctrl+C 退出" -ForegroundColor DarkGray
    Write-Host ""
    
    Start-Sleep -Seconds $Interval
}

