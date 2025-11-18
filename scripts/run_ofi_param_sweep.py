"""
Phase 5: Parameter Optimization & Cost Overlay

CLI script to run parameter sweep for top configurations.

Usage:
    python scripts/run_ofi_param_sweep.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.research.ofi_param_sweep import run_phase5_param_sweep


if __name__ == "__main__":
    config_path = project_root / "config" / "settings.yaml"
    
    print(f"Using config: {config_path}")
    print()
    
    run_phase5_param_sweep(config_path)

