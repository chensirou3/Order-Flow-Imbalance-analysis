"""
加密货币完整分析 - BTCUSD & ETHUSD

使用全部历史数据和所有时间周期（5min到1D）
"""

import sys
from pathlib import Path
import time

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
from src.factors.ofi import add_mid_price, label_tick_directions, compute_ofi_bars, standardize_ofi
from src.research.ofi_single_factor import add_future_returns, sanity_check_ofi, analyze_ofi_single_factor


def main():
    print("=" * 80)
    print("Crypto Full Analysis - BTCUSD & ETHUSD")
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
    print(f"  Data dir: {ticks_dir}")
    print(f"  Results dir: {results_dir}")
    
    # Get analysis parameters
    horizons = config['analysis']['horizons']
    quantile_low = config['analysis']['quantile_low']
    quantile_high = config['analysis']['quantile_high']
    n_bins = config['analysis']['n_bins']
    zscore_window = config['ofi']['zscore_window']
    
    total_configs = len(crypto_symbols) * len(bar_sizes)
    current_config = 0
    
    print(f"\n总配置数: {total_configs}")
    print(f"预计耗时: 2-4小时")
    print(f"\n开始处理...\n")
    
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
        print(f"处理品种: {symbol}")
        print(f"{'='*80}")
        
        symbol_start = time.time()
        
        try:
            # Load ticks once per symbol
            print(f"  [1/4] 加载tick数据...")
            load_start = time.time()
            ticks = load_partitioned_parquet_ticks(
                symbol=symbol,
                ticks_dir=ticks_dir,
                start_date=start_date,
                end_date=end_date
            )
            load_time = time.time() - load_start
            stats['total_ticks'] += len(ticks)
            
            print(f"        ✓ 加载完成: {len(ticks):,} 条tick ({load_time:.1f}秒)")
            print(f"        📅 时间范围: {ticks.index[0]} 到 {ticks.index[-1]}")
            
            # Add mid price and label directions
            print(f"  [2/4] 计算中间价和tick方向...")
            ticks = add_mid_price(ticks)
            ticks = label_tick_directions(ticks)
            print(f"        ✓ 完成")
            
            # Process each bar size
            print(f"  [3/4] 处理各个时间周期...")
            
            for bar_size in bar_sizes:
                current_config += 1
                print(f"\n    [{current_config}/{total_configs}] {symbol} - {bar_size}")
                
                try:
                    # Compute OFI bars
                    print(f"      - 聚合到{bar_size}K线并计算OFI...")
                    bar_start = time.time()
                    ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
                    ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
                    bar_time = time.time() - bar_start
                    stats['total_bars'] += len(ofi_bars)
                    
                    print(f"        ✓ 生成 {len(ofi_bars):,} 根K线 ({bar_time:.1f}秒)")
                    
                    # Add future returns
                    ofi_bars = add_future_returns(ofi_bars, horizons=horizons)
                    
                    # Save bars with OFI
                    output_file = results_dir / f"{symbol}_{bar_size}_bars_with_ofi.csv"
                    ofi_bars.to_csv(output_file)
                    print(f"        ✓ 保存: {output_file.name}")
                    
                    # Run analysis
                    print(f"      - 运行分析...")
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
                    print(f"        ✓ 分析完成 ({analysis_time:.1f}秒)")
                    
                    # Show quick stats
                    ofi_coverage = (ofi_bars['OFI_z'].notna().sum() / len(ofi_bars)) * 100
                    print(f"        📊 OFI覆盖率: {ofi_coverage:.1f}%")
                    
                    stats['successful_configs'] += 1
                    
                except Exception as e:
                    print(f"        ✗ 错误: {e}")
                    stats['failed_configs'] += 1
                    import traceback
                    traceback.print_exc()
                    continue
            
            symbol_time = time.time() - symbol_start
            print(f"\n  {symbol} 完成 (总耗时: {symbol_time/60:.1f}分钟)")
            
        except Exception as e:
            print(f"  ✗ {symbol} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    overall_time = time.time() - overall_start
    
    print(f"\n{'='*80}")
    print(f"加密货币分析完成！")
    print(f"{'='*80}")
    print(f"\n统计信息:")
    print(f"  总耗时: {overall_time/60:.1f} 分钟 ({overall_time/3600:.2f} 小时)")
    print(f"  处理tick数: {stats['total_ticks']:,}")
    print(f"  生成K线数: {stats['total_bars']:,}")
    print(f"  成功配置: {stats['successful_configs']}/{total_configs}")
    print(f"  失败配置: {stats['failed_configs']}/{total_configs}")
    
    print(f"\n下一步:")
    print(f"  1. 运行汇总报告: python scripts/generate_summary_report.py")
    print(f"  2. 生成可视化: python scripts/visualize_results.py")
    print(f"  3. 查看结果: notepad results\\OFI_ANALYSIS_SUMMARY.md")


if __name__ == "__main__":
    main()

