"""
测试短周期（5分钟、15分钟、30分钟）的OFI分析

这个脚本用于快速测试短周期是否能正常工作
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
    print("测试短周期OFI分析 (5min, 15min, 30min)")
    print("=" * 80)
    
    # Load configuration
    config = get_config()
    project_root = get_project_root()
    
    # Test with BTCUSD only, limited date range
    test_symbol = "BTCUSD"
    test_periods = ["5min", "15min", "30min"]
    
    # Use a limited date range for quick testing
    start_date = "2024-01-01"  # 只测试2024年的数据
    end_date = "2024-12-31"
    
    ticks_dir = project_root / config['data_paths']['ticks_dir']
    results_dir = project_root / config['results_paths']['bars_with_ofi_dir']
    
    print(f"\n测试配置:")
    print(f"  品种: {test_symbol}")
    print(f"  时间周期: {', '.join(test_periods)}")
    print(f"  数据范围: {start_date} 到 {end_date}")
    
    # Get analysis parameters
    horizons = config['analysis']['horizons']
    quantile_low = config['analysis']['quantile_low']
    quantile_high = config['analysis']['quantile_high']
    n_bins = config['analysis']['n_bins']
    zscore_window = config['ofi']['zscore_window']
    
    print(f"\n开始测试...\n")
    
    overall_start = time.time()
    
    try:
        # Load ticks
        print(f"[1/3] 加载tick数据...")
        load_start = time.time()
        ticks = load_partitioned_parquet_ticks(
            symbol=test_symbol,
            ticks_dir=ticks_dir,
            start_date=start_date,
            end_date=end_date
        )
        load_time = time.time() - load_start
        print(f"      ✓ 加载完成: {len(ticks):,} 条tick ({load_time:.1f}秒)")
        
        # Add mid price and label directions
        print(f"[2/3] 计算中间价和tick方向...")
        ticks = add_mid_price(ticks)
        ticks = label_tick_directions(ticks)
        print(f"      ✓ 完成")
        
        # Process each bar size
        print(f"[3/3] 测试各个时间周期...")
        
        for bar_size in test_periods:
            print(f"\n  测试 {bar_size}:")
            
            try:
                # Compute OFI bars
                print(f"    - 聚合到{bar_size}K线并计算OFI...")
                bar_start = time.time()
                ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
                ofi_bars = standardize_ofi(ofi_bars, window=zscore_window)
                bar_time = time.time() - bar_start
                
                print(f"      ✓ 生成 {len(ofi_bars):,} 根K线 ({bar_time:.1f}秒)")
                
                # Check if we have enough bars
                if len(ofi_bars) < zscore_window + max(horizons) + 10:
                    print(f"      ⚠️  警告: K线数量较少 ({len(ofi_bars)}根)，可能影响分析质量")
                
                # Add future returns
                ofi_bars = add_future_returns(ofi_bars, horizons=horizons)
                
                # Save bars with OFI
                output_file = results_dir / f"{test_symbol}_{bar_size}_bars_with_ofi.csv"
                ofi_bars.to_csv(output_file)
                print(f"      ✓ 保存: {output_file.name}")
                
                # Run analysis
                print(f"    - 运行分析...")
                analysis_start = time.time()
                
                # Sanity check
                sanity_check_ofi(
                    df=ofi_bars,
                    symbol=f"{test_symbol}_{bar_size}",
                    results_dir=results_dir
                )
                
                # Single factor analysis
                analyze_ofi_single_factor(
                    df=ofi_bars,
                    symbol=f"{test_symbol}_{bar_size}",
                    horizons=horizons,
                    results_dir=results_dir,
                    quantile_low=quantile_low,
                    quantile_high=quantile_high,
                    n_bins=n_bins
                )
                
                analysis_time = time.time() - analysis_start
                print(f"      ✓ 分析完成 ({analysis_time:.1f}秒)")
                
                # Show quick stats
                ofi_coverage = (ofi_bars['OFI_z'].notna().sum() / len(ofi_bars)) * 100
                print(f"      📊 OFI覆盖率: {ofi_coverage:.1f}%")
                print(f"      📊 OFI_z范围: [{ofi_bars['OFI_z'].min():.2f}, {ofi_bars['OFI_z'].max():.2f}]")
                
            except Exception as e:
                print(f"      ✗ 错误: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        overall_time = time.time() - overall_start
        
        print(f"\n{'='*80}")
        print(f"测试完成！")
        print(f"{'='*80}")
        print(f"总耗时: {overall_time:.1f} 秒")
        print(f"\n生成的文件:")
        for bar_size in test_periods:
            print(f"  - results/{test_symbol}_{bar_size}_bars_with_ofi.csv")
            print(f"  - results/sanity/ofi_R0_sanity_{test_symbol}_{bar_size}.md")
            print(f"  - results/single_factor/ofi_R1_single_factor_{test_symbol}_{bar_size}.csv")
        
        print(f"\n✅ 短周期测试成功！可以运行完整的批量分析了。")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

