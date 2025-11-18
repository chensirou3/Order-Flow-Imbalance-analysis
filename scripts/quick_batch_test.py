"""Quick batch test - process BTCUSD with all time periods."""

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
    print("="*80)
    print("QUICK BATCH TEST: BTCUSD × All Time Periods")
    print("="*80)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    symbol = 'BTCUSD'
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
    print(f"  Symbol: {symbol}")
    print(f"  Bar sizes: {bar_sizes}")
    print(f"  Date range: {start_date} to {end_date}")
    
    # Load ticks once
    print(f"\n{'='*80}")
    print(f"Loading tick data for {symbol}...")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    ticks = load_partitioned_parquet_ticks(
        symbol=symbol,
        ticks_dir=ticks_dir,
        start_date=start_date,
        end_date=end_date,
    )
    load_time = datetime.now() - start_time
    print(f"Loaded {len(ticks):,} ticks in {load_time}")
    
    # Prepare ticks
    print("Preparing ticks...")
    ticks = add_mid_price(ticks)
    ticks = label_tick_directions(ticks)
    
    # Process each bar size
    results = []
    for i, bar_size in enumerate(bar_sizes, 1):
        print(f"\n{'-'*80}")
        print(f"Task {i}/{len(bar_sizes)}: {symbol} - {bar_size}")
        print(f"{'-'*80}")
        
        try:
            task_start = datetime.now()
            
            # Compute OFI bars
            print(f"  [1/6] Computing OFI bars...")
            ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
            ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
            print(f"        Created {len(ofi_bars):,} OFI bars")
            
            # Build OHLCV bars
            print(f"  [2/6] Building OHLCV bars...")
            bars = ticks_to_bars(ticks, bar_size=bar_size)
            print(f"        Created {len(bars):,} OHLCV bars")
            
            # Merge
            print(f"  [3/6] Merging bars and OFI...")
            bars_with_ofi = bars.join(ofi_bars[['OFI_raw', 'OFI_z']], how='left')
            
            # Save
            output_file = output_dir / f"{symbol}_{bar_size}_bars_with_ofi.csv"
            bars_with_ofi.to_csv(output_file)
            print(f"        Saved to {output_file.name}")
            
            # Add future returns
            print(f"  [4/6] Adding future returns...")
            bars_with_ofi = add_future_returns(bars_with_ofi, horizons=horizons)
            
            # Sanity check
            print(f"  [5/6] Running sanity check...")
            sanity_check_ofi(bars_with_ofi, symbol=f"{symbol}_{bar_size}", results_dir=sanity_dir)
            
            # Single-factor analysis
            print(f"  [6/6] Running single-factor analysis...")
            analyze_ofi_single_factor(
                bars_with_ofi,
                symbol=f"{symbol}_{bar_size}",
                horizons=horizons,
                results_dir=single_factor_dir,
                quantile_low=quantile_low,
                quantile_high=quantile_high,
                n_bins=n_bins
            )
            
            task_time = datetime.now() - task_start
            print(f"  ✅ SUCCESS in {task_time}")
            
            results.append({
                'bar_size': bar_size,
                'status': 'success',
                'n_bars': len(bars_with_ofi),
                'time': task_time
            })
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'bar_size': bar_size,
                'status': 'failed',
                'error': str(e)
            })
    
    # Summary
    total_time = datetime.now() - start_time
    
    print("\n" + "="*80)
    print("QUICK BATCH TEST COMPLETE")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    
    print(f"\nSummary:")
    print(f"  Total tasks: {len(bar_sizes)}")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {len(bar_sizes) - success_count}")
    print(f"  Total time: {total_time}")
    
    print(f"\nResults:")
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        if result['status'] == 'success':
            print(f"  {status_icon} {result['bar_size']:4s} - {result['n_bars']:,} bars in {result['time']}")
        else:
            print(f"  {status_icon} {result['bar_size']:4s} - {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()

