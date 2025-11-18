# 部署并运行交易路径分析
# 用法: .\deploy_and_run_trade_path.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  OFI Trade Path Analysis - Deploy & Run (Phase 4)             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 服务器信息
$server = "ubuntu@49.51.244.154"
$keyFile = "mishi/lianxi.pem"
$remoteDir = "Order-Flow-Imbalance-analysis"

# 步骤1: 上传新代码
Write-Host "Step 1: Uploading new code to server..." -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray

$filesToUpload = @(
    "config/settings.yaml",
    "src/trading/__init__.py",
    "src/trading/ofi_signals.py",
    "src/trading/trade_path_simulator.py",
    "src/research/ofi_trade_path_analysis.py",
    "scripts/run_ofi_trade_path.py",
    "run_trade_path_analysis_server.py"
)

foreach ($file in $filesToUpload) {
    Write-Host "  Uploading: $file" -ForegroundColor Gray
    
    # 创建远程目录
    $remoteFile = "$remoteDir/$file"
    $remoteFileDir = Split-Path -Parent $remoteFile
    ssh.exe -i $keyFile $server "mkdir -p $remoteFileDir"
    
    # 上传文件
    scp -i $keyFile $file "${server}:~/$remoteFile"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Success" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ All files uploaded successfully!" -ForegroundColor Green
Write-Host ""

# 步骤2: 验证文件
Write-Host "Step 2: Verifying uploaded files..." -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray

ssh.exe -i $keyFile $server "cd $remoteDir && ls -lh src/trading/*.py src/research/ofi_trade_path_analysis.py run_trade_path_analysis_server.py"

Write-Host ""

# 步骤3: 检查Python环境
Write-Host "Step 3: Checking Python environment..." -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray

ssh.exe -i $keyFile $server "python3 --version"
ssh.exe -i $keyFile $server "python3 -c 'import pandas, numpy, yaml; print(\"Required packages OK\")'"

Write-Host ""

# 步骤4: 启动分析
Write-Host "Step 4: Starting trade path analysis..." -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

Write-Host "  Starting analysis in background..." -ForegroundColor Cyan
Write-Host "  Log file: $remoteDir/trade_path_analysis.log" -ForegroundColor Gray
Write-Host ""

# 使用nohup在后台运行
$runCommand = "cd $remoteDir && nohup python3 run_trade_path_analysis_server.py > trade_path_analysis.log 2>&1 &"
ssh.exe -i $keyFile $server $runCommand

Start-Sleep -Seconds 2

# 检查进程
Write-Host "  Checking if process started..." -ForegroundColor Cyan
$processCheck = ssh.exe -i $keyFile $server "ps aux | grep 'run_trade_path_analysis_server.py' | grep -v grep"

if ($processCheck) {
    Write-Host ""
    Write-Host "✅ Analysis started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Process info:" -ForegroundColor Yellow
    Write-Host $processCheck -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "⚠️  Process may not have started. Checking log..." -ForegroundColor Yellow
    ssh.exe -i $keyFile $server "tail -20 $remoteDir/trade_path_analysis.log"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# 显示初始日志
Write-Host "Initial log output:" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray
ssh.exe -i $keyFile $server "tail -30 $remoteDir/trade_path_analysis.log"
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# 步骤5: 监控说明
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Analysis is now running on the server!                        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Monitor progress with:" -ForegroundColor Yellow
Write-Host "  .\monitor_trade_path.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or watch log in real-time:" -ForegroundColor Yellow
Write-Host "  ssh.exe -i $keyFile $server `"tail -f $remoteDir/trade_path_analysis.log`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected completion time: ~30-60 minutes" -ForegroundColor Gray
Write-Host "  (4 symbols x 8 timeframes = 32 configurations)" -ForegroundColor Gray
Write-Host ""

