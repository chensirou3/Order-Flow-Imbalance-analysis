# Start Phase 4 analysis on server
# Usage: .\start_phase4.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Starting Phase 4 Analysis on Server" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Server info
$server = "ubuntu@49.51.244.154"
$keyFile = "mishi/lianxi.pem"
$remoteDir = "Order-Flow-Imbalance-analysis"

# Check Python environment
Write-Host "Checking Python environment..." -ForegroundColor Yellow
ssh.exe -i $keyFile $server "python3 --version"
ssh.exe -i $keyFile $server "python3 -c 'import pandas, numpy, yaml; print(`"Required packages OK`")'"

Write-Host ""

# Start analysis in background
Write-Host "Starting analysis in background..." -ForegroundColor Yellow
Write-Host "  Log file: $remoteDir/trade_path_analysis.log" -ForegroundColor Gray
Write-Host ""

$runCommand = "cd $remoteDir && nohup python3 run_trade_path_analysis_server.py > trade_path_analysis.log 2>&1 &"
ssh.exe -i $keyFile $server $runCommand

Start-Sleep -Seconds 2

# Check if process started
Write-Host "Checking if process started..." -ForegroundColor Yellow
$processCheck = ssh.exe -i $keyFile $server "ps aux | grep 'run_trade_path_analysis_server.py' | grep -v grep"

if ($processCheck) {
    Write-Host ""
    Write-Host "Analysis started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Process info:" -ForegroundColor Yellow
    Write-Host $processCheck -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Process may not have started. Checking log..." -ForegroundColor Yellow
    ssh.exe -i $keyFile $server "tail -20 $remoteDir/trade_path_analysis.log"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# Show initial log
Write-Host "Initial log output:" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor DarkGray
ssh.exe -i $keyFile $server "tail -30 $remoteDir/trade_path_analysis.log"
Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# Instructions
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Analysis is now running on the server!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Monitor progress with:" -ForegroundColor Yellow
Write-Host "  .\monitor_trade_path.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected completion time: 30-60 minutes" -ForegroundColor Gray
Write-Host "  (32 configurations: 4 symbols x 8 timeframes)" -ForegroundColor Gray
Write-Host ""

