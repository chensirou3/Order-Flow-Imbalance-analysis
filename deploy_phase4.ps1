# Deploy Phase 4 code to server
# Usage: .\deploy_phase4.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  OFI Trade Path Analysis - Deploy Phase 4" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Server info
$server = "ubuntu@49.51.244.154"
$keyFile = "mishi/lianxi.pem"
$remoteDir = "Order-Flow-Imbalance-analysis"

# Files to upload
$filesToUpload = @(
    "config/settings.yaml",
    "src/trading/__init__.py",
    "src/trading/ofi_signals.py",
    "src/trading/trade_path_simulator.py",
    "src/research/ofi_trade_path_analysis.py",
    "scripts/run_ofi_trade_path.py",
    "run_trade_path_analysis_server.py"
)

Write-Host "Creating remote directories..." -ForegroundColor Yellow
ssh.exe -i $keyFile $server "mkdir -p $remoteDir/src/trading $remoteDir/src/research $remoteDir/scripts"
Write-Host ""

Write-Host "Uploading files to server..." -ForegroundColor Yellow
Write-Host ""

foreach ($file in $filesToUpload) {
    Write-Host "  Uploading: $file" -ForegroundColor Gray

    # Upload file
    $remoteFile = "$remoteDir/$file"
    scp -i $keyFile $file "${server}:~/$remoteFile"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    OK" -ForegroundColor Green
    } else {
        Write-Host "    FAILED" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "All files uploaded successfully!" -ForegroundColor Green
Write-Host ""

# Verify files
Write-Host "Verifying uploaded files..." -ForegroundColor Yellow
ssh.exe -i $keyFile $server "cd $remoteDir && ls -lh src/trading/*.py src/research/ofi_trade_path_analysis.py run_trade_path_analysis_server.py"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start analysis: .\start_phase4.ps1" -ForegroundColor Cyan
Write-Host "  2. Monitor progress: .\monitor_trade_path.ps1" -ForegroundColor Cyan
Write-Host ""

