"""Batch analysis for all symbols and all time periods.

This script runs the complete OFI analysis pipeline for:
- All configured symbols
- All configured bar sizes (time periods)

Usage:
    python scripts/batch_analysis_all.py

Author: OFI Research Project
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
from src.data.tick_to_bars import ticks_to_bars
from src.factors.ofi import add_mid_price, label_tick_directions, compute_ofi_bars, standardize_ofi
from src.research.ofi_single_factor import (
    add_future_returns,
    sanity_check_ofi,
    analyze_ofi_single_factor
)


def process_symbol_period(
    symbol: str,
    bar_size: str,
    ticks_dir: Path,
    output_dir: Path,
    sanity_dir: Path,
    single_factor_dir: Path,
    zscore_window: int,
    horizons: list,
    quantile_low: float,
    quantile_high: float,
    n_bins: int,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Process one symbol with one bar size.
    
    Returns:
        dict with status and metrics
    """
    result = {
        'symbol': symbol,
        'bar_size': bar_size,
        'status': 'failed',
        'n_ticks': 0,
        'n_bars': 0,
        'error': None
    }
    
    try:
        print(f"\n{'='*70}")
        print(f"Processing {symbol} - {bar_size}")
        print(f"{'='*70}")
        
        # Load tick data (cache if already loaded for this symbol)
        print(f"[{symbol}] Loading tick data...")
        ticks = load_partitioned_parquet_ticks(
            symbol=symbol,
            ticks_dir=ticks_dir,
            start_date=start_date,
            end_date=end_date,
        )
        result['n_ticks'] = len(ticks)
        
        # Add mid price
        print(f"[{symbol}] Adding mid price...")
        ticks = add_mid_price(ticks)
        
        # Label tick directions
        print(f"[{symbol}] Labeling tick directions...")
        ticks = label_tick_directions(ticks)
        
        # Compute OFI bars
        print(f"[{symbol}] Computing OFI bars for {bar_size}...")
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
        result['n_bars'] = len(bars_with_ofi)
        
        # Save bars with OFI
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{symbol}_{bar_size}_bars_with_ofi.csv"
        bars_with_ofi.to_csv(output_file)
        print(f"[{symbol}] Saved to {output_file}")
        
        # Add future returns
        print(f"[{symbol}] Adding future returns for horizons {horizons}...")
        bars_with_ofi = add_future_returns(bars_with_ofi, horizons=horizons)
        
        # Run sanity check
        print(f"[{symbol}] Running sanity check...")
        sanity_dir.mkdir(parents=True, exist_ok=True)
        # Create a subdirectory for this bar size
        sanity_output_dir = sanity_dir / bar_size
        sanity_output_dir.mkdir(parents=True, exist_ok=True)
        sanity_check_ofi(bars_with_ofi, symbol=f"{symbol}_{bar_size}", results_dir=sanity_output_dir.parent)

        # Run single-factor analysis (includes bin analysis)
        print(f"[{symbol}] Running single-factor analysis...")
        single_factor_dir.mkdir(parents=True, exist_ok=True)
        # Create a subdirectory for this bar size
        sf_output_dir = single_factor_dir / bar_size
        sf_output_dir.mkdir(parents=True, exist_ok=True)
        analyze_ofi_single_factor(
            bars_with_ofi,
            symbol=f"{symbol}_{bar_size}",
            horizons=horizons,
            results_dir=sf_output_dir.parent,
            quantile_low=quantile_low,
            quantile_high=quantile_high,
            n_bins=n_bins
        )
        
        print(f"[{symbol}] ✅ SUCCESS: {bar_size} analysis complete!")
        result['status'] = 'success'
        
    except Exception as e:
        print(f"\n[{symbol}] ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
    
    return result


def main():
    """Main entry point."""
    start_time = datetime.now()
    
    print("="*70)
    print("BATCH ANALYSIS: All Symbols × All Time Periods")
    print("="*70)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    # Get parameters
    symbols = config.get('symbols', ['BTCUSD'])
    bar_sizes = config.get('bar_settings', {}).get('bar_sizes', ['4H'])
    ticks_dir = project_root / "data" / "ticks"
    output_dir = project_root / "results"
    sanity_dir = project_root / "results" / "sanity"
    single_factor_dir = project_root / "results" / "single_factor"
    
    zscore_window = config.get('ofi', {}).get('zscore_window', 200)
    horizons = config.get('analysis', {}).get('horizons', [2, 5, 10])
    quantile_low = config.get('analysis', {}).get('quantile_low', 0.10)
    quantile_high = config.get('analysis', {}).get('quantile_high', 0.90)
    n_bins = config.get('analysis', {}).get('n_bins', 5)
    
    start_date = config.get('data', {}).get('start_date', None)
    end_date = config.get('data', {}).get('end_date', None)
    
    print(f"\nConfiguration:")
    print(f"  Symbols: {symbols}")
    print(f"  Bar sizes: {bar_sizes}")
    print(f"  Horizons: {horizons}")
    print(f"  OFI z-score window: {zscore_window}")
    print(f"  Quantile thresholds: low={quantile_low}, high={quantile_high}")
    print(f"  Number of bins: {n_bins}")
    if start_date:
        print(f"  Start date: {start_date}")
    if end_date:
        print(f"  End date: {end_date}")
    
    total_tasks = len(symbols) * len(bar_sizes)
    print(f"\nTotal tasks: {total_tasks} ({len(symbols)} symbols × {len(bar_sizes)} periods)")
    
    # Process all combinations
    results = []
    task_num = 0
    
    for symbol in symbols:
        for bar_size in bar_sizes:
            task_num += 1
            print(f"\n{'#'*70}")
            print(f"Task {task_num}/{total_tasks}: {symbol} - {bar_size}")
            print(f"{'#'*70}")
            
            result = process_symbol_period(
                symbol=symbol,
                bar_size=bar_size,
                ticks_dir=ticks_dir,
                output_dir=output_dir,
                sanity_dir=sanity_dir,
                single_factor_dir=single_factor_dir,
                zscore_window=zscore_window,
                horizons=horizons,
                quantile_low=quantile_low,
                quantile_high=quantile_high,
                n_bins=n_bins,
                start_date=start_date,
                end_date=end_date,
            )
            results.append(result)
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("BATCH ANALYSIS COMPLETE")
    print("="*70)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\nSummary:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  Duration: {duration}")
    
    print(f"\nResults by symbol and period:")
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"  {status_icon} {result['symbol']:8s} {result['bar_size']:4s} - "
              f"{result['n_ticks']:,} ticks → {result['n_bars']:,} bars")
        if result['error']:
            print(f"      Error: {result['error']}")
    
    print(f"\nResults saved to:")
    print(f"  - {output_dir}/*_bars_with_ofi.csv")
    print(f"  - {sanity_dir}/ofi_R0_sanity_*.md")
    print(f"  - {single_factor_dir}/ofi_R1_*.csv")


if __name__ == "__main__":
    main()

