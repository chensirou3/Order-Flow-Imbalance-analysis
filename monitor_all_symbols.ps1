# Monitor All Symbols Batch Analysis Progress

param(
    [int]$Interval = 60  # Update interval in seconds
)

$symbols = @{
    'BTCUSD' = @{ total = 40; log = 'btc_batch_output.log' }
    'ETHUSD' = @{ total = 40; log = 'ETHUSD_batch_output.log' }
    'EURUSD' = @{ total = 48; log = 'EURUSD_batch_output.log' }
    'USDJPY' = @{ total = 48; log = 'USDJPY_batch_output.log' }
    'XAGUSD' = @{ total = 48; log = 'XAGUSD_batch_output.log' }
    'XAUUSD' = @{ total = 48; log = 'XAUUSD_batch_output.log' }
}

while ($true) {
    $now = Get-Date
    
    Clear-Host
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  所有品种分批分析进度监控" -ForegroundColor Cyan
    Write-Host "  时间: $($now.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $totalCompleted = 0
    $totalTasks = 0
    
    foreach ($symbol in $symbols.Keys | Sort-Object) {
        $info = $symbols[$symbol]
        $logFile = $info.log
        $total = $info.total
        $totalTasks += $total
        
        Write-Host "[$symbol]" -ForegroundColor Yellow
        
        # 检查日志文件是否存在
        $cmd = "cd Order-Flow-Imbalance-analysis; test -f $logFile && grep -c '保存到:' $logFile 2>/dev/null || echo 0"
        $completedStr = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd
        $completed = 0
        try { $completed = [int]$completedStr.Trim() } catch { }
        
        $totalCompleted += $completed
        $pct = if ($total -gt 0) { [Math]::Round(($completed * 100.0 / $total), 1) } else { 0 }
        
        # 状态
        if ($completed -eq 0) {
            Write-Host "  状态: 等待中" -ForegroundColor Gray
        } elseif ($completed -eq $total) {
            Write-Host "  状态: 已完成" -ForegroundColor Green
        } else {
            Write-Host "  状态: 进行中" -ForegroundColor Cyan
        }
        
        Write-Host "  进度: $completed / $total ($pct%)" -ForegroundColor White
        
        # 进度条
        $barWidth = 40
        $filled = [Math]::Floor($barWidth * $pct / 100)
        $empty = $barWidth - $filled
        $bar = ""
        for ($i = 0; $i -lt $filled; $i++) { $bar += "█" }
        for ($i = 0; $i -lt $empty; $i++) { $bar += "░" }
        Write-Host "  $bar" -ForegroundColor Green
        Write-Host ""
    }
    
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host ""
    
    # 总体进度
    $overallPct = if ($totalTasks -gt 0) { [Math]::Round(($totalCompleted * 100.0 / $totalTasks), 1) } else { 0 }
    Write-Host "[总体进度]" -ForegroundColor Yellow
    Write-Host "  完成: $totalCompleted / $totalTasks 任务 ($overallPct%)" -ForegroundColor White
    
    $barWidth = 60
    $filled = [Math]::Floor($barWidth * $overallPct / 100)
    $empty = $barWidth - $filled
    $bar = ""
    for ($i = 0; $i -lt $filled; $i++) { $bar += "█" }
    for ($i = 0; $i -lt $empty; $i++) { $bar += "░" }
    Write-Host "  $bar" -ForegroundColor Cyan
    Write-Host ""
    
    # 当前活动
    Write-Host "[当前活动]" -ForegroundColor Yellow
    $cmd2 = "cd Order-Flow-Imbalance-analysis; tail -5 all_symbols_sequential.log 2>/dev/null || echo '无日志'"
    $activity = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd2
    if ($activity) {
        foreach ($line in $activity) {
            Write-Host "  $line" -ForegroundColor Gray
        }
    }
    Write-Host ""
    
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "下次更新: $Interval 秒后 (按 Ctrl+C 停止)" -ForegroundColor DarkGray
    Write-Host ""
    
    # 如果全部完成，退出
    if ($totalCompleted -eq $totalTasks) {
        Write-Host ""
        Write-Host "✅ 所有品种分析已完成！" -ForegroundColor Green
        Write-Host ""
        
        # 显示结果文件
        Write-Host "结果文件:" -ForegroundColor Yellow
        ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && ls -lh results/*_merged_bars_with_ofi.csv 2>/dev/null | wc -l"
        Write-Host ""
        break
    }
    
    Start-Sleep -Seconds $Interval
}

