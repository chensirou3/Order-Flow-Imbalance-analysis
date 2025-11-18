# Quick check of all symbols progress

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  所有品种分析进度快速检查" -ForegroundColor Cyan
Write-Host "  时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 定义品种和任务数
$symbols = @(
    @{ name = 'BTCUSD'; total = 40; log = 'btc_batch_output.log' },
    @{ name = 'ETHUSD'; total = 40; log = 'ETHUSD_batch_output.log' },
    @{ name = 'EURUSD'; total = 48; log = 'EURUSD_batch_output.log' },
    @{ name = 'USDJPY'; total = 48; log = 'USDJPY_batch_output.log' },
    @{ name = 'XAGUSD'; total = 48; log = 'XAGUSD_batch_output.log' },
    @{ name = 'XAUUSD'; total = 48; log = 'XAUUSD_batch_output.log' }
)

$totalCompleted = 0
$totalTasks = 0

foreach ($s in $symbols) {
    $symbol = $s.name
    $total = $s.total
    $logFile = $s.log
    $totalTasks += $total
    
    # 检查完成数
    $cmd = "cd Order-Flow-Imbalance-analysis; test -f $logFile && grep -c '保存到:' $logFile 2>/dev/null || echo 0"
    $completedStr = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd
    $completed = 0
    try { $completed = [int]$completedStr.Trim() } catch { }
    
    $totalCompleted += $completed
    $pct = if ($total -gt 0) { [Math]::Round(($completed * 100.0 / $total), 1) } else { 0 }
    
    # 显示
    Write-Host "[$symbol]" -ForegroundColor Yellow -NoNewline
    Write-Host "  $completed / $total ($pct%)" -ForegroundColor White
    
    # 进度条
    $barWidth = 30
    $filled = [Math]::Floor($barWidth * $pct / 100)
    $empty = $barWidth - $filled
    $bar = "  "
    for ($i = 0; $i -lt $filled; $i++) { $bar += "#" }
    for ($i = 0; $i -lt $empty; $i++) { $bar += "-" }
    
    if ($completed -eq 0) {
        Write-Host $bar -ForegroundColor DarkGray
    } elseif ($completed -eq $total) {
        Write-Host $bar -ForegroundColor Green
    } else {
        Write-Host $bar -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# 总体进度
$overallPct = if ($totalTasks -gt 0) { [Math]::Round(($totalCompleted * 100.0 / $totalTasks), 1) } else { 0 }
Write-Host "[Overall Progress]" -ForegroundColor Yellow
Write-Host "  $totalCompleted / $totalTasks tasks ($overallPct%)" -ForegroundColor White

$barWidth = 60
$filled = [Math]::Floor($barWidth * $overallPct / 100)
$empty = $barWidth - $filled
$bar = "  "
for ($i = 0; $i -lt $filled; $i++) { $bar += "#" }
for ($i = 0; $i -lt $empty; $i++) { $bar += "-" }
Write-Host $bar -ForegroundColor Cyan

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# 当前活动
Write-Host "[Current Activity]" -ForegroundColor Yellow
$cmd2 = "cd Order-Flow-Imbalance-analysis; tail -8 all_symbols_sequential.log 2>/dev/null"
$activity = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd2
if ($activity) {
    foreach ($line in $activity) {
        Write-Host "  $line" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

