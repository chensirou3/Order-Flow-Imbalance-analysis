# 实时监控分析进度
param(
    [int]$IntervalSeconds = 30
)

$host.UI.RawUI.WindowTitle = "OFI Analysis Monitor"

function Get-ProgressBar {
    param([double]$Percent, [int]$Width = 50)
    $filled = [math]::Floor($Percent / 100 * $Width)
    $empty = $Width - $filled
    return ("█" * $filled) + ("░" * $empty)
}

function Show-Header {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          OFI 全品种全周期历史数据分析 - 实时监控                  ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

$startTime = Get-Date
$iteration = 0

while ($true) {
    $iteration++
    $currentTime = Get-Date
    $elapsed = $currentTime - $startTime
    
    Show-Header
    
    Write-Host "⏰ 开始时间: " -NoNewline -ForegroundColor Yellow
    Write-Host $startTime.ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "⏱️  运行时长: " -NoNewline -ForegroundColor Yellow
    Write-Host ("{0:D2}:{1:D2}:{2:D2}" -f $elapsed.Hours, $elapsed.Minutes, $elapsed.Seconds)
    Write-Host "🔄 检查次数: " -NoNewline -ForegroundColor Yellow
    Write-Host $iteration
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    
    # 获取日志最后50行
    $logOutput = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && tail -50 analysis_output.log 2>/dev/null"
    
    if ($logOutput) {
        # 分析日志内容
        $lines = $logOutput -split "`n"
        
        # 查找关键信息
        $currentSymbol = ""
        $currentPeriod = ""
        $currentHorizon = ""
        $completedCount = 0
        $errorCount = 0
        
        foreach ($line in $lines) {
            if ($line -match "Processing.*symbol=(\w+)") {
                $currentSymbol = $matches[1]
            }
            if ($line -match "period=(\w+)") {
                $currentPeriod = $matches[1]
            }
            if ($line -match "horizon=(\d+)") {
                $currentHorizon = $matches[1]
            }
            if ($line -match "✅|completed|finished|success") {
                $completedCount++
            }
            if ($line -match "❌|error|failed|Error|ERROR") {
                $errorCount++
            }
        }
        
        # 显示当前状态
        Write-Host "📊 当前进度:" -ForegroundColor Green
        Write-Host ""
        
        if ($currentSymbol) {
            Write-Host "  品种: " -NoNewline -ForegroundColor Cyan
            Write-Host $currentSymbol -ForegroundColor White
        }
        if ($currentPeriod) {
            Write-Host "  周期: " -NoNewline -ForegroundColor Cyan
            Write-Host $currentPeriod -ForegroundColor White
        }
        if ($currentHorizon) {
            Write-Host "  Horizon: " -NoNewline -ForegroundColor Cyan
            Write-Host $currentHorizon -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "  ✅ 完成任务: " -NoNewline -ForegroundColor Green
        Write-Host $completedCount
        Write-Host "  ❌ 错误数量: " -NoNewline -ForegroundColor Red
        Write-Host $errorCount
        Write-Host ""
        
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📝 最新日志 (最后10行):" -ForegroundColor Yellow
        Write-Host ""
        
        # 显示最后10行
        $lastLines = $lines | Select-Object -Last 10
        foreach ($line in $lastLines) {
            if ($line -match "✅|success|completed") {
                Write-Host "  $line" -ForegroundColor Green
            }
            elseif ($line -match "❌|error|failed|Error") {
                Write-Host "  $line" -ForegroundColor Red
            }
            elseif ($line -match "Processing|Running|Analyzing") {
                Write-Host "  $line" -ForegroundColor Cyan
            }
            else {
                Write-Host "  $line" -ForegroundColor Gray
            }
        }
    }
    else {
        Write-Host "⏳ 等待分析启动..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   分析进程可能正在初始化，请稍候..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⏭️  下次更新: $IntervalSeconds 秒后 | 按 Ctrl+C 退出监控" -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $IntervalSeconds
}

