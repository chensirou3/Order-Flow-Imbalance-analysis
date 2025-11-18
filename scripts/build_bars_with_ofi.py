"""Build 4H bars with OFI factor from tick data.

This script:
1. Reads configuration from config/settings.yaml
2. For each symbol:
   - Loads tick data from data/ticks/{symbol}_ticks_*.csv
   - Builds 4H OHLCV bars
   - Computes OFI_raw and OFI_z
   - Saves to results/{symbol}_4h_bars_with_ofi.csv
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, resolve_path
from src.data.bars_with_ofi_builder import build_bars_with_ofi


def main():
    """Main entry point for building bars with OFI."""
    print("=" * 80)
    print("Building 4H Bars with OFI Factor")
    print("=" * 80)
    print()
    
    # Load config
    config = get_config()
    
    symbols = config['symbols']
    ticks_dir = resolve_path(config['data_paths']['ticks_dir'])
    bars_with_ofi_dir = resolve_path(config['results_paths']['bars_with_ofi_dir'])
    bar_size = config['ofi']['bar_size']
    ofi_window = config['ofi']['zscore_window']
    
    print(f"Configuration:")
    print(f"  Symbols: {symbols}")
    print(f"  Ticks directory: {ticks_dir}")
    print(f"  Output directory: {bars_with_ofi_dir}")
    print(f"  Bar size: {bar_size}")
    print(f"  OFI z-score window: {ofi_window}")
    print()
    
    # Create output directory
    bars_with_ofi_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each symbol
    for symbol in symbols:
        print("-" * 80)
        print(f"Processing {symbol}")
        print("-" * 80)
        
        # Find tick data file
        # Look for files matching pattern: {symbol}_ticks*.csv
        tick_files = list(ticks_dir.glob(f"{symbol}_ticks*.csv"))
        
        if not tick_files:
            print(f"[{symbol}] ERROR: No tick data found in {ticks_dir}")
            print(f"[{symbol}] Expected file pattern: {symbol}_ticks*.csv")
            print(f"[{symbol}] Skipping...")
            print()
            continue
        
        if len(tick_files) > 1:
            print(f"[{symbol}] WARNING: Multiple tick files found:")
            for f in tick_files:
                print(f"  - {f.name}")
            print(f"[{symbol}] Using: {tick_files[0].name}")
        
        ticks_path = tick_files[0]
        
        # Output path
        bars_out_path = bars_with_ofi_dir / f"{symbol}_4h_bars_with_ofi.csv"
        
        try:
            # Build bars with OFI
            result = build_bars_with_ofi(
                symbol=symbol,
                ticks_path=ticks_path,
                bar_size=bar_size,
                bars_out_path=bars_out_path,
                ofi_window=ofi_window,
            )
            
            print(f"[{symbol}] SUCCESS: Created {len(result):,} bars")
            print()
            
        except Exception as e:
            print(f"[{symbol}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()
            continue
    
    print("=" * 80)
    print("Build complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

