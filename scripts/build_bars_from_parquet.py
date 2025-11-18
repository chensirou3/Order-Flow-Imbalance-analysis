"""Build 4H bars with OFI from partitioned Parquet tick data.

This script loads tick data from partitioned Parquet files and builds bars with OFI.

Usage:
    python scripts/build_bars_from_parquet.py

Author: OFI Research Project
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root, resolve_path
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
from src.data.tick_to_bars import ticks_to_bars
from src.factors.ofi import add_mid_price, label_tick_directions, compute_ofi_bars, standardize_ofi


def build_bars_with_ofi_from_parquet(
    symbol: str,
    ticks_dir: Path,
    output_dir: Path,
    bar_size: str = "4H",
    zscore_window: int = 200,
    start_date: str = None,
    end_date: str = None,
) -> None:
    """Build bars with OFI from partitioned Parquet data.
    
    Args:
        symbol: Trading symbol
        ticks_dir: Directory containing partitioned parquet data
        output_dir: Directory to save results
        bar_size: Bar size (e.g., '4H', '1H')
        zscore_window: Window for OFI z-score calculation
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    """
    print(f"\n{'-'*58}")
    print(f"Processing {symbol}")
    print(f"{'-'*58}")
    
    # Load tick data
    print(f"[{symbol}] Loading tick data from partitioned Parquet...")
    ticks = load_partitioned_parquet_ticks(
        symbol=symbol,
        ticks_dir=ticks_dir,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Add mid price
    print(f"[{symbol}] Adding mid price...")
    ticks = add_mid_price(ticks)
    
    # Label tick directions
    print(f"[{symbol}] Labeling tick directions...")
    ticks = label_tick_directions(ticks)
    
    # Compute OFI bars
    print(f"[{symbol}] Computing OFI bars...")
    ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
    print(f"[{symbol}] Created {len(ofi_bars)} OFI bars")
    
    # Standardize OFI
    print(f"[{symbol}] Standardizing OFI (window={zscore_window})...")
    ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
    
    # Build OHLCV bars
    print(f"[{symbol}] Building OHLCV bars...")
    bars = ticks_to_bars(ticks, bar_size=bar_size)
    print(f"[{symbol}] Created {len(bars)} OHLCV bars")
    
    # Merge bars and OFI
    print(f"[{symbol}] Merging bars and OFI...")
    bars_with_ofi = bars.join(ofi_bars[['OFI_raw', 'OFI_z']], how='left')
    
    print(f"[{symbol}] Final dataset: {len(bars_with_ofi)} bars")
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{symbol}_4h_bars_with_ofi.csv"
    bars_with_ofi.to_csv(output_file)
    print(f"[{symbol}] Saved to {output_file}")
    print(f"[{symbol}] SUCCESS: Created {len(bars_with_ofi)} bars")


def main():
    """Main entry point."""
    print("=" * 58)
    print("Building 4H Bars with OFI from Parquet Data")
    print("=" * 58)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    # Get parameters
    symbols = config.get('symbols', ['BTCUSD', 'XAUUSD'])
    ticks_dir = project_root / "data" / "ticks"
    output_dir = project_root / "results"
    bar_size = config.get('ofi', {}).get('bar_size', '4H')
    zscore_window = config.get('ofi', {}).get('zscore_window', 200)
    
    # Optional date range (can be added to config if needed)
    start_date = config.get('data', {}).get('start_date', None)
    end_date = config.get('data', {}).get('end_date', None)
    
    print()
    print("Configuration:")
    print(f"  Symbols: {symbols}")
    print(f"  Ticks directory: {ticks_dir}")
    print(f"  Output directory: {output_dir}")
    print(f"  Bar size: {bar_size}")
    print(f"  OFI z-score window: {zscore_window}")
    if start_date:
        print(f"  Start date: {start_date}")
    if end_date:
        print(f"  End date: {end_date}")
    
    # Process each symbol
    for symbol in symbols:
        try:
            build_bars_with_ofi_from_parquet(
                symbol=symbol,
                ticks_dir=ticks_dir,
                output_dir=output_dir,
                bar_size=bar_size,
                zscore_window=zscore_window,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            print(f"\n[{symbol}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print()
    print("=" * 58)
    print("Build complete!")
    print("=" * 58)
    print()
    print("Next step:")
    print("  python scripts/run_ofi_single_factor.py")


if __name__ == "__main__":
    main()

