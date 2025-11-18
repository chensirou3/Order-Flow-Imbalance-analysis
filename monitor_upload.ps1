# 实时监控数据上传进度
$targetSize = 12.11
$targetFiles = 25094
$startTime = Get-Date

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  数据上传实时监控" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "目标: $targetSize GB / $targetFiles 文件" -ForegroundColor Yellow
Write-Host "开始时间: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Yellow
Write-Host ""

$iteration = 0
while ($true) {
    $iteration++
    $currentTime = Get-Date
    $elapsed = ($currentTime - $startTime).TotalMinutes
    
    # 获取服务器数据
    try {
        $result = ssh -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && du -sm data/ticks 2>/dev/null && find data/ticks -name '*.parquet' 2>/dev/null | wc -l" 2>$null
        
        if ($result) {
            $lines = $result -split "`n"
            $sizeMB = [int]($lines[0] -replace '\D+','')
            $sizeGB = [math]::Round($sizeMB / 1024, 2)
            $files = [int]$lines[1].Trim()
            
            # 计算进度
            $sizePercent = [math]::Round(($sizeGB / $targetSize) * 100, 1)
            $filesPercent = [math]::Round(($files / $targetFiles) * 100, 1)
            
            # 计算速度和预计时间
            if ($elapsed -gt 0) {
                $speedMBPerMin = $sizeMB / $elapsed
                $speedMBPerSec = [math]::Round($speedMBPerMin / 60, 2)
                $remainingMB = ($targetSize * 1024) - $sizeMB
                $etaMinutes = if ($speedMBPerMin -gt 0) { [math]::Round($remainingMB / $speedMBPerMin, 1) } else { 0 }
            } else {
                $speedMBPerSec = 0
                $etaMinutes = 0
            }
            
            # 清屏并显示
            Clear-Host
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "  数据上传实时监控 #$iteration" -ForegroundColor Cyan
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host ""
            
            Write-Host "当前时间: $($currentTime.ToString('HH:mm:ss'))" -ForegroundColor White
            Write-Host "已运行: $([math]::Round($elapsed, 1)) 分钟" -ForegroundColor White
            Write-Host ""
            
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            Write-Host "  数据大小进度" -ForegroundColor Yellow
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            
            $barLength = 40
            $filledLength = [math]::Floor($barLength * $sizePercent / 100)
            $bar = "█" * $filledLength + "░" * ($barLength - $filledLength)
            
            Write-Host "  $bar" -ForegroundColor Green
            Write-Host "  $sizeGB GB / $targetSize GB ($sizePercent%)" -ForegroundColor White
            Write-Host ""
            
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            Write-Host "  文件数量进度" -ForegroundColor Yellow
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            
            $filledLength2 = [math]::Floor($barLength * $filesPercent / 100)
            $bar2 = "█" * $filledLength2 + "░" * ($barLength - $filledLength2)
            
            Write-Host "  $bar2" -ForegroundColor Cyan
            Write-Host "  $files / $targetFiles 文件 ($filesPercent%)" -ForegroundColor White
            Write-Host ""
            
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            Write-Host "  上传统计" -ForegroundColor Yellow
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
            Write-Host "  上传速度: $speedMBPerSec MB/s" -ForegroundColor White
            Write-Host "  预计剩余: $etaMinutes 分钟" -ForegroundColor White
            
            if ($etaMinutes -gt 0) {
                $etaTime = $currentTime.AddMinutes($etaMinutes)
                Write-Host "  预计完成: $($etaTime.ToString('HH:mm:ss'))" -ForegroundColor White
            }
            Write-Host ""
            
            # 检查是否完成
            if ($files -ge $targetFiles -and $sizeGB -ge ($targetSize * 0.95)) {
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "  ✅ 上传完成！" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "总耗时: $([math]::Round($elapsed, 1)) 分钟" -ForegroundColor Yellow
                Write-Host "最终大小: $sizeGB GB" -ForegroundColor Yellow
                Write-Host "最终文件数: $files" -ForegroundColor Yellow
                break
            }
            
            Write-Host "按 Ctrl+C 停止监控" -ForegroundColor DarkGray
            Write-Host "下次更新: 10秒后..." -ForegroundColor DarkGray
            
        } else {
            Write-Host "⚠️  无法连接到服务器，10秒后重试..." -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️  连接错误: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "监控结束。" -ForegroundColor Cyan

