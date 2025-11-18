"""
Cryptocurrency Full Analysis - BTCUSD & ETHUSD
Using all historical data and all time periods (5min to 1D)
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
from src.factors.ofi import add_mid_price, label_tick_directions, compute_ofi_bars, standardize_ofi
from src.research.ofi_single_factor import add_future_returns, sanity_check_ofi, analyze_ofi_single_factor


def main():
    print("=" * 80)
    print("Cryptocurrency OFI Full Analysis - BTCUSD & ETHUSD")
    print("=" * 80)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    # Only analyze crypto
    crypto_symbols = ["BTCUSD", "ETHUSD"]
    bar_sizes = config['bar_settings']['bar_sizes']
    ticks_dir = project_root / config['data_paths']['ticks_dir']
    results_dir = project_root / config['results_paths']['bars_with_ofi_dir']
    
    # Use all available data
    start_date = config['data'].get('start_date')
    end_date = config['data'].get('end_date')
    
    print(f"\nConfiguration:")
    print(f"  Symbols: {', '.join(crypto_symbols)}")
    print(f"  Time periods: {', '.join(bar_sizes)}")
    print(f"  Date range: {start_date or 'ALL'} to {end_date or 'LATEST'}")
    
    # Get analysis parameters
    horizons = config['analysis']['horizons']
    quantile_low = config['analysis']['quantile_low']
    quantile_high = config['analysis']['quantile_high']
    n_bins = config['analysis']['n_bins']
    zscore_window = config['ofi']['zscore_window']
    
    total_configs = len(crypto_symbols) * len(bar_sizes)
    current_config = 0
    
    print(f"\nTotal configs: {total_configs}")
    print(f"Estimated time: 2-4 hours")
    print(f"\nStarting analysis...\n")
    
    overall_start = time.time()
    
    # Track statistics
    stats = {
        'total_ticks': 0,
        'total_bars': 0,
        'successful_configs': 0,
        'failed_configs': 0
    }
    
    for symbol in crypto_symbols:
        print(f"\n{'='*80}")
        print(f"Processing: {symbol}")
        print(f"{'='*80}")
        
        symbol_start = time.time()
        
        try:
            # Load ticks once per symbol
            print(f"  [1/4] Loading tick data...")
            load_start = time.time()
            ticks = load_partitioned_parquet_ticks(
                symbol=symbol,
                ticks_dir=ticks_dir,
                start_date=start_date,
                end_date=end_date
            )
            load_time = time.time() - load_start
            stats['total_ticks'] += len(ticks)
            
            print(f"        OK: Loaded {len(ticks):,} ticks ({load_time:.1f}s)")
            print(f"        Date range: {ticks.index[0]} to {ticks.index[-1]}")
            
            # Add mid price and label directions
            print(f"  [2/4] Computing mid price and tick directions...")
            ticks = add_mid_price(ticks)
            ticks = label_tick_directions(ticks)
            print(f"        OK: Done")
            
            # Process each bar size
            print(f"  [3/4] Processing time periods...")
            
            for bar_size in bar_sizes:
                current_config += 1
                print(f"\n    [{current_config}/{total_configs}] {symbol} - {bar_size}")
                
                try:
                    # Compute OFI bars
                    print(f"      - Aggregating to {bar_size} bars and computing OFI...")
                    bar_start = time.time()
                    ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
                    ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
                    bar_time = time.time() - bar_start
                    stats['total_bars'] += len(ofi_bars)
                    
                    print(f"        OK: Generated {len(ofi_bars):,} bars ({bar_time:.1f}s)")
                    
                    # Add future returns
                    ofi_bars = add_future_returns(ofi_bars, horizons=horizons)
                    
                    # Save bars with OFI
                    output_file = results_dir / f"{symbol}_{bar_size}_bars_with_ofi.csv"
                    ofi_bars.to_csv(output_file)
                    print(f"        OK: Saved {output_file.name}")
                    
                    # Run analysis
                    print(f"      - Running analysis...")
                    analysis_start = time.time()
                    
                    # Sanity check
                    sanity_check_ofi(
                        df=ofi_bars,
                        symbol=f"{symbol}_{bar_size}",
                        results_dir=results_dir
                    )
                    
                    # Single factor analysis
                    analyze_ofi_single_factor(
                        df=ofi_bars,
                        symbol=f"{symbol}_{bar_size}",
                        horizons=horizons,
                        results_dir=results_dir,
                        quantile_low=quantile_low,
                        quantile_high=quantile_high,
                        n_bins=n_bins
                    )
                    
                    analysis_time = time.time() - analysis_start
                    print(f"        OK: Analysis done ({analysis_time:.1f}s)")
                    
                    # Show quick stats
                    ofi_coverage = (ofi_bars['OFI_z'].notna().sum() / len(ofi_bars)) * 100
                    print(f"        Stats: OFI coverage {ofi_coverage:.1f}%")
                    
                    stats['successful_configs'] += 1
                    
                except Exception as e:
                    print(f"        ERROR: {e}")
                    stats['failed_configs'] += 1
                    continue
            
            symbol_time = time.time() - symbol_start
            print(f"\n  {symbol} completed (time: {symbol_time/60:.1f} min)")
            
        except Exception as e:
            print(f"  ERROR: {symbol} failed: {e}")
            continue
    
    overall_time = time.time() - overall_start
    
    print(f"\n{'='*80}")
    print(f"Cryptocurrency Analysis Complete!")
    print(f"{'='*80}")
    print(f"\nStatistics:")
    print(f"  Total time: {overall_time/60:.1f} min ({overall_time/3600:.2f} hours)")
    print(f"  Total ticks: {stats['total_ticks']:,}")
    print(f"  Total bars: {stats['total_bars']:,}")
    print(f"  Successful: {stats['successful_configs']}/{total_configs}")
    print(f"  Failed: {stats['failed_configs']}/{total_configs}")
    
    print(f"\nNext steps:")
    print(f"  1. Generate summary: python scripts/generate_summary_report.py")
    print(f"  2. Create visualizations: python scripts/visualize_results.py")


if __name__ == "__main__":
    main()

