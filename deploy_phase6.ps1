# Deploy Phase 6 code to server

$SERVER = "ubuntu@49.51.244.154"
$KEY = "mishi/lianxi.pem"
$REMOTE_DIR = "Order-Flow-Imbalance-analysis"

Write-Host "=" * 80
Write-Host "Deploying Phase 6 to server..."
Write-Host "=" * 80
Write-Host ""

# Upload config
Write-Host "Uploading config..."
scp -i $KEY config/settings.yaml ${SERVER}:~/${REMOTE_DIR}/config/

# Upload Phase 6 modules
Write-Host "Uploading Phase 6 modules..."
scp -i $KEY src/research/ofi_long_short_regime.py ${SERVER}:~/${REMOTE_DIR}/src/research/
scp -i $KEY src/research/ofi_manipscore_joint.py ${SERVER}:~/${REMOTE_DIR}/src/research/
scp -i $KEY src/research/strategy_spec_generator.py ${SERVER}:~/${REMOTE_DIR}/src/research/

# Upload runner script
Write-Host "Uploading runner script..."
scp -i $KEY scripts/run_phase6_all.py ${SERVER}:~/${REMOTE_DIR}/scripts/

Write-Host ""
Write-Host "=" * 80
Write-Host "Deployment complete!"
Write-Host "=" * 80

