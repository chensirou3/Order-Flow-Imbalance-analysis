"""Test that all modules can be imported successfully.

This is a simple sanity check to ensure the project structure is correct.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test importing all modules."""
    print("Testing module imports...")
    print()
    
    tests = []
    
    # Test config loader
    try:
        from src.config_loader import get_config, get_project_root, resolve_path
        print("✓ src.config_loader")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.config_loader: {e}")
        tests.append(False)
    
    # Test data modules
    try:
        from src.data.tick_loader import load_and_clean_ticks, detect_tick_mode
        print("✓ src.data.tick_loader")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.data.tick_loader: {e}")
        tests.append(False)
    
    try:
        from src.data.tick_to_bars import ticks_to_bars
        print("✓ src.data.tick_to_bars")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.data.tick_to_bars: {e}")
        tests.append(False)
    
    try:
        from src.data.bars_with_ofi_builder import build_bars_with_ofi
        print("✓ src.data.bars_with_ofi_builder")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.data.bars_with_ofi_builder: {e}")
        tests.append(False)
    
    # Test factor modules
    try:
        from src.factors.ofi import (
            add_mid_price,
            label_tick_directions,
            compute_ofi_bars,
            standardize_ofi
        )
        print("✓ src.factors.ofi")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.factors.ofi: {e}")
        tests.append(False)
    
    # Test utils
    try:
        from src.utils.stats_utils import mean_std_t, simple_ols
        print("✓ src.utils.stats_utils")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.utils.stats_utils: {e}")
        tests.append(False)
    
    # Test research modules
    try:
        from src.research.ofi_single_factor import (
            add_future_returns,
            sanity_check_ofi,
            analyze_ofi_single_factor,
            run_ofi_single_factor_for_symbol
        )
        print("✓ src.research.ofi_single_factor")
        tests.append(True)
    except Exception as e:
        print(f"✗ src.research.ofi_single_factor: {e}")
        tests.append(False)
    
    print()
    print("=" * 60)
    
    if all(tests):
        print("✓ All modules imported successfully!")
        print("=" * 60)
        return True
    else:
        print(f"✗ {sum(not t for t in tests)} module(s) failed to import")
        print("=" * 60)
        return False


def test_config():
    """Test loading configuration."""
    print()
    print("Testing configuration loading...")
    print()
    
    try:
        from src.config_loader import get_config
        config = get_config()
        
        print("✓ Configuration loaded successfully")
        print()
        print("Configuration summary:")
        print(f"  Symbols: {config.get('symbols', [])}")
        print(f"  Bar size: {config.get('ofi', {}).get('bar_size', 'N/A')}")
        print(f"  OFI window: {config.get('ofi', {}).get('zscore_window', 'N/A')}")
        print(f"  Horizons: {config.get('analysis', {}).get('horizons', [])}")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        print()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("OFI Factor Project - Module Import Test")
    print("=" * 60)
    print()
    
    import_ok = test_imports()
    config_ok = test_config()
    
    if import_ok and config_ok:
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Place tick data in data/ticks/")
        print("  2. Run: python scripts/build_bars_with_ofi.py")
        print("  3. Run: python scripts/run_ofi_single_factor.py")
        print()
        print("Or generate sample data first:")
        print("  python scripts/generate_sample_data.py")
        return 0
    else:
        print("=" * 60)
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

