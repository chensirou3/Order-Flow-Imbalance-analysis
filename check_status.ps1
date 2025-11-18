# Quick status check for all symbols

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  All Symbols Analysis Progress" -ForegroundColor Cyan
Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check BTCUSD
Write-Host "[BTCUSD]" -ForegroundColor Yellow
$cmd1 = "cd Order-Flow-Imbalance-analysis; grep -c 'BTCUSD_' btc_batch_output.log 2>/dev/null | head -1"
$btc = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd1
Write-Host "  Completed: $btc / 40" -ForegroundColor White
Write-Host ""

# Check ETHUSD
Write-Host "[ETHUSD]" -ForegroundColor Yellow
$cmd2 = "cd Order-Flow-Imbalance-analysis; test -f ETHUSD_batch_output.log && grep -c 'ETHUSD_' ETHUSD_batch_output.log 2>/dev/null || echo 0"
$eth = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd2
Write-Host "  Completed: $eth / 40" -ForegroundColor White
Write-Host ""

# Check EURUSD
Write-Host "[EURUSD]" -ForegroundColor Yellow
$cmd3 = "cd Order-Flow-Imbalance-analysis; test -f EURUSD_batch_output.log && grep -c 'EURUSD_' EURUSD_batch_output.log 2>/dev/null || echo 0"
$eur = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd3
Write-Host "  Completed: $eur / 48" -ForegroundColor White
Write-Host ""

# Check USDJPY
Write-Host "[USDJPY]" -ForegroundColor Yellow
$cmd4 = "cd Order-Flow-Imbalance-analysis; test -f USDJPY_batch_output.log && grep -c 'USDJPY_' USDJPY_batch_output.log 2>/dev/null || echo 0"
$jpy = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd4
Write-Host "  Completed: $jpy / 48" -ForegroundColor White
Write-Host ""

# Check XAGUSD
Write-Host "[XAGUSD]" -ForegroundColor Yellow
$cmd5 = "cd Order-Flow-Imbalance-analysis; test -f XAGUSD_batch_output.log && grep -c 'XAGUSD_' XAGUSD_batch_output.log 2>/dev/null || echo 0"
$xag = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd5
Write-Host "  Completed: $xag / 48" -ForegroundColor White
Write-Host ""

# Check XAUUSD
Write-Host "[XAUUSD]" -ForegroundColor Yellow
$cmd6 = "cd Order-Flow-Imbalance-analysis; test -f XAUUSD_batch_output.log && grep -c 'XAUUSD_' XAUUSD_batch_output.log 2>/dev/null || echo 0"
$xau = ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 $cmd6
Write-Host "  Completed: $xau / 48" -ForegroundColor White
Write-Host ""

Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

# Current activity
Write-Host "[Current Activity]" -ForegroundColor Yellow
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cd Order-Flow-Imbalance-analysis && tail -10 all_symbols_sequential.log 2>/dev/null"
Write-Host ""

Write-Host "================================================================" -ForegroundColor DarkGray
Write-Host ""

