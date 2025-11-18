"""Test batch analysis script."""

import sys
from pathlib import Path

print("Starting test...")
print(f"Python version: {sys.version}")
print(f"Current directory: {Path.cwd()}")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

print("\nImporting modules...")
from src.config_loader import get_config, get_project_root

print("✅ Imported config_loader")

from src.data.parquet_tick_loader import load_partitioned_parquet_ticks

print("✅ Imported parquet_tick_loader")

from src.research.ofi_single_factor import add_future_returns, sanity_check_ofi, analyze_ofi_single_factor

print("✅ Imported ofi_single_factor")

print("\nLoading config...")
config = get_config()
print(f"Symbols: {config.get('symbols')}")
print(f"Bar sizes: {config.get('bar_settings', {}).get('bar_sizes')}")

print("\n✅ All imports successful!")

