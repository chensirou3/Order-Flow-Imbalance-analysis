"""
完成剩余的USDJPY和XAUUSD分析
使用1年批次以避免OOM问题
"""

import sys
from pathlib import Path
import pandas as pd
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
from src.factors.ofi import add_mid_price, label_tick_directions, compute_ofi_bars, standardize_ofi
from src.research.ofi_single_factor import add_future_returns


def run_single_batch(symbol, start_date, end_date, bar_sizes, ticks_dir, results_dir, batch_name):
    """运行单个批次的分析"""
    print(f"\n{'='*80}")
    print(f"批次: {batch_name}")
    print(f"品种: {symbol}")
    print(f"日期范围: {start_date} 到 {end_date}")
    print(f"{'='*80}\n")
    
    batch_results = []
    
    for bar_size in bar_sizes:
        print(f"\n处理时间周期: {bar_size}")
        print("-" * 60)
        
        try:
            # [1/4] 加载tick数据
            print(f"  [1/4] 加载tick数据...")
            start_time = time.time()
            ticks = load_partitioned_parquet_ticks(
                symbol=symbol,
                ticks_dir=ticks_dir,
                start_date=start_date,
                end_date=end_date
            )
            load_time = time.time() - start_time
            print(f"    ✓ 加载完成: {len(ticks):,} ticks ({load_time:.1f}秒)")
            
            # [2/4] 计算OFI
            print(f"  [2/4] 计算OFI...")
            ticks = add_mid_price(ticks)
            ticks = label_tick_directions(ticks)
            ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
            ofi_bars = standardize_ofi(ofi_bars, window=200)
            print(f"    ✓ 生成 {len(ofi_bars):,} 个K线")
            
            # [3/4] 添加未来收益
            print(f"  [3/4] 计算未来收益...")
            ofi_bars = add_future_returns(ofi_bars, horizons=[2, 5, 10])
            print(f"    ✓ 添加 3 个时间跨度")
            
            # [4/4] 保存批次结果
            print(f"  [4/4] 保存批次结果...")
            batch_file = results_dir / f"{symbol}_{bar_size}_{batch_name}_bars_with_ofi.csv"
            ofi_bars.to_csv(batch_file)
            print(f"    ✓ 保存到: {batch_file.name}")
            
            batch_results.append({
                'symbol': symbol,
                'batch': batch_name,
                'bar_size': bar_size,
                'num_ticks': len(ticks),
                'num_bars': len(ofi_bars),
                'file': batch_file.name
            })
            
            # 清理内存
            del ticks, ofi_bars
            
        except Exception as e:
            print(f"    ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    return batch_results


def merge_batches(symbol, bar_size, batch_files, results_dir):
    """合并所有批次"""
    print(f"\n合并 {symbol} {bar_size}...")
    
    all_data = []
    for batch_file in batch_files:
        file_path = results_dir / batch_file
        if file_path.exists():
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            all_data.append(df)
            print(f"  ✓ 加载: {batch_file} ({len(df):,} 行)")
    
    if not all_data:
        print(f"  ✗ 没有找到批次文件")
        return
    
    # 合并并排序
    merged = pd.concat(all_data, axis=0)
    merged = merged.sort_index()
    print(f"  ✓ 合并完成: {len(merged):,} 行")
    
    # 重新计算OFI_z (使用全部数据)
    merged = standardize_ofi(merged, window=200)
    print(f"  ✓ 重新计算OFI_z")
    
    # 重新计算未来收益
    merged = add_future_returns(merged, horizons=[2, 5, 10])
    print(f"  ✓ 重新计算未来收益")
    
    # 保存合并结果
    merged_file = results_dir / f"{symbol}_{bar_size}_merged_bars_with_ofi.csv"
    merged.to_csv(merged_file)
    print(f"  ✓ 保存: {merged_file.name}\n")


def main():
    # 配置
    config = get_config()
    project_root = get_project_root()
    ticks_dir = project_root / config['data_paths']['ticks_dir']
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)
    
    bar_sizes = ['5min', '15min', '30min', '1H', '2H', '4H', '8H', '1D']
    
    # USDJPY和XAUUSD使用1年批次（避免OOM）
    usdjpy_batches = [
        ('2022', '2022-01-01', '2022-12-31'),
        ('2023', '2023-01-01', '2023-12-31'),
        ('2024', '2024-01-01', '2024-12-31'),
        ('2025', '2025-01-01', '2025-12-31'),
    ]
    
    xauusd_batches = [
        ('2016', '2016-01-01', '2016-12-31'),
        ('2017', '2017-01-01', '2017-12-31'),
        ('2018', '2018-01-01', '2018-12-31'),
        ('2019', '2019-01-01', '2019-12-31'),
        ('2020', '2020-01-01', '2020-12-31'),
        ('2021', '2021-01-01', '2021-12-31'),
        ('2022', '2022-01-01', '2022-12-31'),
        ('2023', '2023-01-01', '2023-12-31'),
        ('2024', '2024-01-01', '2024-12-31'),
        ('2025', '2025-01-01', '2025-12-31'),
    ]

    print("="*80)
    print("完成剩余分析 - 使用1年批次避免OOM")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 处理USDJPY剩余批次
    print("\n" + "="*80)
    print("处理 USDJPY 剩余批次 (2022-2025)")
    print("="*80)

    usdjpy_results = []
    for batch_name, start_date, end_date in usdjpy_batches:
        results = run_single_batch(
            symbol='USDJPY',
            start_date=start_date,
            end_date=end_date,
            bar_sizes=bar_sizes,
            ticks_dir=ticks_dir,
            results_dir=results_dir,
            batch_name=batch_name
        )
        usdjpy_results.extend(results)

    # 合并USDJPY所有批次
    print("\n" + "="*80)
    print("合并 USDJPY 所有批次")
    print("="*80)

    for bar_size in bar_sizes:
        # 找到所有USDJPY批次文件
        batch_files = [
            f"USDJPY_{bar_size}_2010-2012_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2013-2015_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2016-2018_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2019-2021_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2022_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2023_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2024_bars_with_ofi.csv",
            f"USDJPY_{bar_size}_2025_bars_with_ofi.csv",
        ]
        merge_batches('USDJPY', bar_size, batch_files, results_dir)

    # 处理XAUUSD剩余批次
    print("\n" + "="*80)
    print("处理 XAUUSD 剩余批次 (2016-2025)")
    print("="*80)

    xauusd_results = []
    for batch_name, start_date, end_date in xauusd_batches:
        results = run_single_batch(
            symbol='XAUUSD',
            start_date=start_date,
            end_date=end_date,
            bar_sizes=bar_sizes,
            ticks_dir=ticks_dir,
            results_dir=results_dir,
            batch_name=batch_name
        )
        xauusd_results.extend(results)

    # 合并XAUUSD所有批次
    print("\n" + "="*80)
    print("合并 XAUUSD 所有批次")
    print("="*80)

    for bar_size in bar_sizes:
        # 找到所有XAUUSD批次文件
        batch_files = [
            f"XAUUSD_{bar_size}_2010-2012_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2013-2015_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2016_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2017_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2018_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2019_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2020_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2021_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2022_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2023_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2024_bars_with_ofi.csv",
            f"XAUUSD_{bar_size}_2025_bars_with_ofi.csv",
        ]
        merge_batches('XAUUSD', bar_size, batch_files, results_dir)

    # 保存摘要
    all_results = usdjpy_results + xauusd_results
    if all_results:
        summary_df = pd.DataFrame(all_results)
        summary_file = results_dir / 'remaining_analysis_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✓ 摘要保存到: {summary_file}")

    print("\n" + "="*80)
    print("✅ 所有分析完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == '__main__':
    main()

