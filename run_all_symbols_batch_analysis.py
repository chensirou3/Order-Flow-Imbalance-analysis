"""
所有品种分批分析脚本 - 按年份分批处理

按顺序处理所有品种：BTCUSD -> ETHUSD -> EURUSD -> USDJPY -> XAGUSD -> XAUUSD
每个品种按年份分批，避免内存问题。
"""

import sys
from pathlib import Path
import pandas as pd
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent if '__file__' in globals() else Path.cwd()
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
            
            if len(ticks) == 0:
                print(f"    ⚠ 警告: 该时间段无数据，跳过")
                continue
            
            # [2/4] 计算OFI
            print(f"  [2/4] 计算OFI...")
            ticks = add_mid_price(ticks)
            ticks = label_tick_directions(ticks)
            ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
            ofi_bars = standardize_ofi(ofi_bars, window=200)
            print(f"    ✓ 生成 {len(ofi_bars):,} 个K线")
            
            # [3/4] 添加未来收益
            print(f"  [3/4] 计算未来收益...")
            horizons = [2, 5, 10]
            ofi_bars = add_future_returns(ofi_bars, horizons=horizons)
            print(f"    ✓ 添加 {len(horizons)} 个时间跨度")
            
            # [4/4] 保存批次结果
            print(f"  [4/4] 保存批次结果...")
            batch_file = results_dir / f"{symbol}_{bar_size}_{batch_name}_bars_with_ofi.csv"
            ofi_bars.to_csv(batch_file)
            print(f"    ✓ 保存到: {batch_file.name}")
            
            batch_results.append({
                'symbol': symbol,
                'bar_size': bar_size,
                'batch': batch_name,
                'start_date': start_date,
                'end_date': end_date,
                'n_ticks': len(ticks),
                'n_bars': len(ofi_bars),
                'file': batch_file.name
            })
            
        except Exception as e:
            print(f"    ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return batch_results


def merge_batches(symbol, bar_size, batch_files, results_dir):
    """合并多个批次的结果"""
    print(f"\n合并 {symbol} {bar_size} 的所有批次...")
    
    all_data = []
    for batch_file in batch_files:
        file_path = results_dir / batch_file
        if file_path.exists():
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            all_data.append(df)
            print(f"  ✓ 加载: {batch_file} ({len(df)} bars)")
    
    if not all_data:
        print(f"  ⚠ 没有找到批次文件")
        return None
    
    # 合并并排序
    merged = pd.concat(all_data, axis=0)
    merged = merged.sort_index()
    
    # 重新计算OFI_z（使用全部数据）
    print(f"  重新计算OFI_z（使用全部数据）...")
    merged = standardize_ofi(merged, window=200)
    
    # 重新计算未来收益
    print(f"  重新计算未来收益...")
    merged = add_future_returns(merged, horizons=[2, 5, 10])
    
    # 保存合并结果
    merged_file = results_dir / f"{symbol}_{bar_size}_merged_bars_with_ofi.csv"
    merged.to_csv(merged_file)
    print(f"  ✓ 保存合并结果: {merged_file.name} ({len(merged)} bars)")
    
    return merged


def process_symbol(symbol, bar_sizes, ticks_dir, results_dir, batches):
    """处理单个品种的所有批次"""
    print(f"\n{'#'*80}")
    print(f"# 开始处理品种: {symbol}")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")
    
    symbol_start_time = time.time()
    all_batch_results = []
    
    # 运行所有批次
    for batch_name, start_date, end_date in batches:
        batch_results = run_single_batch(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            bar_sizes=bar_sizes,
            ticks_dir=ticks_dir,
            results_dir=results_dir,
            batch_name=batch_name
        )
        all_batch_results.extend(batch_results)
    
    # 保存批次摘要
    if all_batch_results:
        summary_df = pd.DataFrame(all_batch_results)
        summary_file = results_dir / f"{symbol}_batch_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"\n✓ {symbol} 批次摘要保存到: {summary_file}")

    # 合并每个时间周期的所有批次
    print(f"\n{'='*80}")
    print(f"合并 {symbol} 的批次结果")
    print(f"{'='*80}")

    for bar_size in bar_sizes:
        batch_files = [r['file'] for r in all_batch_results if r['bar_size'] == bar_size]
        if batch_files:
            merge_batches(symbol, bar_size, batch_files, results_dir)

    symbol_elapsed = time.time() - symbol_start_time
    print(f"\n{'#'*80}")
    print(f"# {symbol} 处理完成！")
    print(f"# 耗时: {symbol_elapsed/60:.1f} 分钟")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}\n")

    return all_batch_results


def main():
    print("="*80)
    print("所有品种分批分析脚本")
    print("="*80)

    # 配置
    config = get_config()
    project_root = get_project_root()

    symbols = config['symbols']
    bar_sizes = config['bar_settings']['bar_sizes']
    ticks_dir = project_root / config['data_paths']['ticks_dir']
    results_dir = project_root / config['results_paths']['bars_with_ofi_dir']
    results_dir.mkdir(parents=True, exist_ok=True)

    # 定义批次（按年份分批）
    # 加密货币: 2017-2025
    crypto_batches = [
        ('2017-2018', '2017-01-01', '2018-12-31'),
        ('2019-2020', '2019-01-01', '2020-12-31'),
        ('2021-2022', '2021-01-01', '2022-12-31'),
        ('2023-2024', '2023-01-01', '2024-12-31'),
        ('2025', '2025-01-01', '2025-12-31'),
    ]

    # 外汇和贵金属: 2010-2025
    forex_batches = [
        ('2010-2012', '2010-01-01', '2012-12-31'),
        ('2013-2015', '2013-01-01', '2015-12-31'),
        ('2016-2018', '2016-01-01', '2018-12-31'),
        ('2019-2021', '2019-01-01', '2021-12-31'),
        ('2022-2024', '2022-01-01', '2024-12-31'),
        ('2025', '2025-01-01', '2025-12-31'),
    ]

    # 为每个品种定义批次
    symbol_batches = {
        'BTCUSD': crypto_batches,
        'ETHUSD': crypto_batches,
        'EURUSD': forex_batches,
        'USDJPY': forex_batches,
        'XAGUSD': forex_batches,
        'XAUUSD': forex_batches,
    }

    print(f"\n配置信息:")
    print(f"  品种: {', '.join(symbols)}")
    print(f"  时间周期: {', '.join(bar_sizes)}")
    print(f"  数据目录: {ticks_dir}")
    print(f"  结果目录: {results_dir}")

    # 计算总任务数
    total_tasks = 0
    for symbol in symbols:
        batches = symbol_batches.get(symbol, crypto_batches)
        total_tasks += len(batches) * len(bar_sizes)
    print(f"  总任务数: {total_tasks}")

    # 按顺序处理每个品种
    overall_start_time = time.time()
    all_results = {}

    for i, symbol in enumerate(symbols, 1):
        print(f"\n\n")
        print(f"{'*'*80}")
        print(f"* 进度: {i}/{len(symbols)} - 处理品种 {symbol}")
        print(f"{'*'*80}")

        batches = symbol_batches.get(symbol, crypto_batches)
        results = process_symbol(symbol, bar_sizes, ticks_dir, results_dir, batches)
        all_results[symbol] = results

    # 生成总体摘要
    overall_elapsed = time.time() - overall_start_time
    print(f"\n\n")
    print(f"{'='*80}")
    print(f"✅ 所有品种处理完成！")
    print(f"{'='*80}")
    print(f"\n总耗时: {overall_elapsed/3600:.2f} 小时")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 保存总体摘要
    all_summary = []
    for symbol, results in all_results.items():
        all_summary.extend(results)

    if all_summary:
        overall_summary = pd.DataFrame(all_summary)
        summary_file = results_dir / "all_symbols_batch_summary.csv"
        overall_summary.to_csv(summary_file, index=False)
        print(f"\n总体摘要保存到: {summary_file}")

        # 打印统计
        print(f"\n统计信息:")
        print(f"  总批次数: {len(overall_summary)}")
        print(f"  总K线数: {overall_summary['n_bars'].sum():,}")
        print(f"  总Tick数: {overall_summary['n_ticks'].sum():,}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()


