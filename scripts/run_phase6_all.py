"""
Phase 6 Combined Runner

Run all Phase 6 submodules:
- 6A: Long vs Short leg + Regime analysis
- 6B: OFI × ManipScore joint signals
- 6C: Strategy spec generation
"""

import sys
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.ofi_long_short_regime import run_phase6A_long_short_regime
from src.research.ofi_manipscore_joint import run_phase6B_ofi_ms_joint
from src.research.strategy_spec_generator import run_phase6C_strategy_spec_generation


def main():
    """Main runner for Phase 6."""
    parser = argparse.ArgumentParser(description="Run Phase 6 analysis modules")
    parser.add_argument(
        '--modules',
        nargs='+',
        choices=['6A', '6B', '6C', 'all'],
        default=['all'],
        help='Which modules to run (default: all)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/settings.yaml',
        help='Path to config file'
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    
    modules_to_run = args.modules
    if 'all' in modules_to_run:
        modules_to_run = ['6A', '6B', '6C']
    
    print("=" * 80)
    print("Phase 6: Advanced Analysis & Strategy Spec Generation")
    print("=" * 80)
    print()
    print(f"Config: {config_path}")
    print(f"Modules to run: {', '.join(modules_to_run)}")
    print()
    print("=" * 80)
    print()
    
    # Run selected modules
    if '6A' in modules_to_run:
        try:
            run_phase6A_long_short_regime(config_path)
            print()
        except Exception as e:
            print(f"ERROR in Phase 6A: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    if '6B' in modules_to_run:
        try:
            run_phase6B_ofi_ms_joint(config_path)
            print()
        except Exception as e:
            print(f"ERROR in Phase 6B: {e}")
            print("  (This is expected if ManipScore data is not available)")
            import traceback
            traceback.print_exc()
            print()
    
    if '6C' in modules_to_run:
        try:
            run_phase6C_strategy_spec_generation(config_path)
            print()
        except Exception as e:
            print(f"ERROR in Phase 6C: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 80)
    print("Phase 6 Complete!")
    print("=" * 80)
    print()
    print("Output directories:")
    print("  - results/long_short/       (Phase 6A)")
    print("  - results/joint/             (Phase 6B)")
    print("  - docs/strategy_specs/       (Phase 6C)")
    print()


if __name__ == "__main__":
    main()

