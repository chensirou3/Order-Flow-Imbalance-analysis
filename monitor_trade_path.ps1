# 监控交易路径分析进度
# 用法: .\monitor_trade_path.ps1

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  OFI Trade Path Analysis - Progress Monitor" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 服务器信息
$server = "ubuntu@49.51.244.154"
$keyFile = "mishi/lianxi.pem"
$logFile = "Order-Flow-Imbalance-analysis/trade_path_analysis.log"

Write-Host "Connecting to server..." -ForegroundColor Yellow
Write-Host "Server: $server" -ForegroundColor Gray
Write-Host "Log file: $logFile" -ForegroundColor Gray
Write-Host ""

# 检查进程
Write-Host "Checking Python process..." -ForegroundColor Yellow
ssh.exe -i $keyFile $server "ps aux | grep 'run_trade_path_analysis_server.py' | grep -v grep"
Write-Host ""

# 显示最新日志
Write-Host "Latest log entries (last 30 lines):" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray
ssh.exe -i $keyFile $server "tail -30 $logFile"
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# 统计信息
Write-Host "Analysis Statistics:" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

# 总配置数
$totalConfigs = ssh.exe -i $keyFile $server "grep -c 'Progress:' $logFile 2>/dev/null"
if ($totalConfigs) {
    Write-Host "  Total progress entries: $totalConfigs" -ForegroundColor Green
}

# 成功数
$successCount = ssh.exe -i $keyFile $server "grep -c '✅ Success' $logFile 2>/dev/null"
if ($successCount) {
    Write-Host "  Successful analyses: $successCount" -ForegroundColor Green
}

# 错误数
$errorCount = ssh.exe -i $keyFile $server "grep -c '❌ Error' $logFile 2>/dev/null"
if ($errorCount) {
    Write-Host "  Errors: $errorCount" -ForegroundColor Red
}

# 警告数
$warningCount = ssh.exe -i $keyFile $server "grep -c '⚠️' $logFile 2>/dev/null"
if ($warningCount) {
    Write-Host "  Warnings: $warningCount" -ForegroundColor Yellow
}

Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# 检查输出文件
Write-Host "Checking output files..." -ForegroundColor Yellow
ssh.exe -i $keyFile $server "ls -lh Order-Flow-Imbalance-analysis/results/trade_summaries/*.csv 2>/dev/null | tail -5"
Write-Host ""

# 内存使用
Write-Host "Server resource usage:" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
ssh.exe -i $keyFile $server "free -h | head -2"
Write-Host ""
ssh.exe -i $keyFile $server "top -bn1 | grep 'Cpu(s)' | head -1"
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Monitor Commands:" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Watch log in real-time:" -ForegroundColor White
Write-Host "    ssh.exe -i $keyFile $server 'tail -f $logFile'" -ForegroundColor Gray
Write-Host ""
Write-Host "  Check process:" -ForegroundColor White
Write-Host "    ssh.exe -i $keyFile $server 'ps aux | grep python3'" -ForegroundColor Gray
Write-Host ""
Write-Host "  Download results:" -ForegroundColor White
Write-Host "    scp -i $keyFile -r ${server}:~/Order-Flow-Imbalance-analysis/results/trade_summaries ." -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

