"""Simplified batch analysis for all symbols and time periods.

Usage:
    python scripts/run_batch_analysis.py
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
from src.research.ofi_single_factor import add_future_returns, sanity_check_ofi, analyze_ofi_single_factor


def main():
    start_time = datetime.now()
    
    print("="*80)
    print("BATCH ANALYSIS: All Symbols × All Time Periods")
    print("="*80)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    symbols = config.get('symbols', ['BTCUSD'])
    bar_sizes = config.get('bar_settings', {}).get('bar_sizes', ['4H'])
    ticks_dir = project_root / "data" / "ticks"
    output_dir = project_root / "results"
    sanity_dir = output_dir / "sanity"
    single_factor_dir = output_dir / "single_factor"
    
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
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Total tasks: {len(symbols)} × {len(bar_sizes)} = {len(symbols) * len(bar_sizes)}")
    
    results = []
    task_num = 0
    total_tasks = len(symbols) * len(bar_sizes)
    
    # Cache loaded ticks by symbol to avoid reloading
    ticks_cache = {}
    
    for symbol in symbols:
        # Load ticks once per symbol
        print(f"\n{'='*80}")
        print(f"Loading tick data for {symbol}...")
        print(f"{'='*80}")
        
        try:
            ticks = load_partitioned_parquet_ticks(
                symbol=symbol,
                ticks_dir=ticks_dir,
                start_date=start_date,
                end_date=end_date,
            )
            
            # Prepare ticks
            ticks = add_mid_price(ticks)
            ticks = label_tick_directions(ticks)
            ticks_cache[symbol] = ticks
            
        except Exception as e:
            print(f"❌ Failed to load {symbol}: {e}")
            # Skip all bar sizes for this symbol
            for bar_size in bar_sizes:
                task_num += 1
                results.append({
                    'symbol': symbol,
                    'bar_size': bar_size,
                    'status': 'failed',
                    'error': f'Failed to load ticks: {e}'
                })
            continue
        
        # Process each bar size
        for bar_size in bar_sizes:
            task_num += 1
            print(f"\n{'-'*80}")
            print(f"Task {task_num}/{total_tasks}: {symbol} - {bar_size}")
            print(f"{'-'*80}")
            
            try:
                ticks = ticks_cache[symbol]
                
                # Compute OFI bars
                print(f"  Computing OFI bars...")
                ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
                ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
                print(f"  Created {len(ofi_bars)} OFI bars")
                
                # Build OHLCV bars
                print(f"  Building OHLCV bars...")
                bars = ticks_to_bars(ticks, bar_size=bar_size)
                
                # Merge
                bars_with_ofi = bars.join(ofi_bars[['OFI_raw', 'OFI_z']], how='left')
                
                # Save
                output_file = output_dir / f"{symbol}_{bar_size}_bars_with_ofi.csv"
                bars_with_ofi.to_csv(output_file)
                print(f"  Saved to {output_file}")
                
                # Add future returns
                print(f"  Adding future returns...")
                bars_with_ofi = add_future_returns(bars_with_ofi, horizons=horizons)
                
                # Sanity check
                print(f"  Running sanity check...")
                sanity_check_ofi(bars_with_ofi, symbol=f"{symbol}_{bar_size}", results_dir=sanity_dir)
                
                # Single-factor analysis
                print(f"  Running single-factor analysis...")
                analyze_ofi_single_factor(
                    bars_with_ofi,
                    symbol=f"{symbol}_{bar_size}",
                    horizons=horizons,
                    results_dir=single_factor_dir,
                    quantile_low=quantile_low,
                    quantile_high=quantile_high,
                    n_bins=n_bins
                )
                
                print(f"  ✅ SUCCESS")
                results.append({
                    'symbol': symbol,
                    'bar_size': bar_size,
                    'status': 'success',
                    'n_bars': len(bars_with_ofi),
                    'error': None
                })
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    'symbol': symbol,
                    'bar_size': bar_size,
                    'status': 'failed',
                    'error': str(e)
                })
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("BATCH ANALYSIS COMPLETE")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"\nSummary:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"  Duration: {duration}")
    
    print(f"\nResults:")
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        n_bars = result.get('n_bars', 0)
        print(f"  {status_icon} {result['symbol']:8s} {result['bar_size']:4s} - {n_bars:,} bars")
        if result['error']:
            print(f"      Error: {result['error']}")


if __name__ == "__main__":
    main()

