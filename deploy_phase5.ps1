# Deploy Phase 5 code to server and run parameter sweep

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Deploying Phase 5 to server..."
Write-Host "=" * 80

# Create remote directories
Write-Host "`nCreating remote directories..."
ssh.exe -i $KEY $SERVER "mkdir -p $REMOTE_DIR/src/utils"
ssh.exe -i $KEY $SERVER "mkdir -p $REMOTE_DIR/src/research"
ssh.exe -i $KEY $SERVER "mkdir -p $REMOTE_DIR/src/trading"
ssh.exe -i $KEY $SERVER "mkdir -p $REMOTE_DIR/scripts"
ssh.exe -i $KEY $SERVER "mkdir -p $REMOTE_DIR/results/param_sweep"

# Upload Phase 5 files
Write-Host "`nUploading Phase 5 files..."

# Config
Write-Host "  - config/settings.yaml"
scp -i $KEY config/settings.yaml ${SERVER}:~/$REMOTE_DIR/config/

# Utils
Write-Host "  - src/utils/cost_utils.py"
scp -i $KEY src/utils/cost_utils.py ${SERVER}:~/$REMOTE_DIR/src/utils/

# Trading (updated simulator)
Write-Host "  - src/trading/trade_path_simulator.py"
scp -i $KEY src/trading/trade_path_simulator.py ${SERVER}:~/$REMOTE_DIR/src/trading/

# Research
Write-Host "  - src/research/ofi_param_sweep.py"
scp -i $KEY src/research/ofi_param_sweep.py ${SERVER}:~/$REMOTE_DIR/src/research/

# Scripts
Write-Host "  - scripts/run_ofi_param_sweep.py"
scp -i $KEY scripts/run_ofi_param_sweep.py ${SERVER}:~/$REMOTE_DIR/scripts/

# Documentation
Write-Host "  - PHASE5_PARAM_OPTIMIZATION.md"
scp -i $KEY PHASE5_PARAM_OPTIMIZATION.md ${SERVER}:~/$REMOTE_DIR/

Write-Host "  - PHASE5_QUICKSTART.md"
scp -i $KEY PHASE5_QUICKSTART.md ${SERVER}:~/$REMOTE_DIR/

Write-Host "`n" + "=" * 80
Write-Host "Phase 5 deployment complete!"
Write-Host "=" * 80

Write-Host "`nTo run Phase 5 on the server:"
Write-Host "  ssh -i $KEY $SERVER"
Write-Host "  cd $REMOTE_DIR"
Write-Host "  nohup python3 scripts/run_ofi_param_sweep.py > phase5_sweep.log 2>&1 &"
Write-Host "`nTo monitor progress:"
Write-Host "  ssh -i $KEY $SERVER 'tail -f $REMOTE_DIR/phase5_sweep.log'"

