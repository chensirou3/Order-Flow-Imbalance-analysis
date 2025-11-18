"""
合并BTCUSD的批次文件
"""

import pandas as pd
from pathlib import Path
import numpy as np


def standardize_ofi(df, window=200):
    """标准化OFI"""
    if 'OFI' not in df.columns:
        return df

    # 使用滚动窗口计算均值和标准差
    ofi_mean = df['OFI'].rolling(window=window, min_periods=1).mean()
    ofi_std = df['OFI'].rolling(window=window, min_periods=1).std()

    # 标准化
    df['OFI_z'] = (df['OFI'] - ofi_mean) / ofi_std.replace(0, 1)

    return df


def add_future_returns(df, horizons=[2, 5, 10]):
    """添加未来收益"""
    if 'close' not in df.columns:
        return df

    for h in horizons:
        # 计算未来h期的收益率
        df[f'fut_ret_{h}'] = df['close'].pct_change(h).shift(-h)

    return df


def merge_batches(symbol, bar_size, results_dir):
    """合并指定品种和时间周期的所有批次文件"""
    
    # 查找所有批次文件
    pattern = f"{symbol}_{bar_size}_*_bars_with_ofi.csv"
    batch_files = sorted(results_dir.glob(pattern))
    
    if not batch_files:
        print(f"  ✗ 没有找到批次文件: {pattern}")
        return False
    
    print(f"  找到 {len(batch_files)} 个批次文件")
    
    # 读取并合并
    all_data = []
    for batch_file in batch_files:
        print(f"    读取: {batch_file.name}")
        df = pd.read_csv(batch_file, index_col=0, parse_dates=True)
        all_data.append(df)
    
    # 合并
    print(f"  合并数据...")
    merged = pd.concat(all_data, axis=0)
    merged = merged.sort_index()
    
    print(f"  总行数: {len(merged):,}")
    print(f"  日期范围: {merged.index.min()} 到 {merged.index.max()}")
    
    # 重新计算OFI_z（使用全部数据的统计量）
    print(f"  重新计算OFI_z...")
    merged = standardize_ofi(merged, window=200)
    
    # 重新计算未来收益（确保跨批次边界的连续性）
    print(f"  重新计算未来收益...")
    merged = add_future_returns(merged, horizons=[2, 5, 10])
    
    # 保存
    merged_file = results_dir / f"{symbol}_{bar_size}_merged_bars_with_ofi.csv"
    print(f"  保存到: {merged_file.name}")
    merged.to_csv(merged_file)
    
    return True


def main():
    results_dir = Path('results')
    
    if not results_dir.exists():
        print("❌ results/ 目录不存在")
        return
    
    symbol = 'BTCUSD'
    bar_sizes = ['5min', '15min', '30min', '1H', '2H', '4H', '8H', '1D']
    
    print(f"\n{'='*80}")
    print(f"合并 {symbol} 的批次文件")
    print(f"{'='*80}\n")
    
    success_count = 0
    for bar_size in bar_sizes:
        print(f"处理时间周期: {bar_size}")
        print("-" * 60)
        
        if merge_batches(symbol, bar_size, results_dir):
            success_count += 1
            print(f"  ✓ 完成\n")
        else:
            print(f"  ✗ 失败\n")
    
    print(f"{'='*80}")
    print(f"✅ 完成！成功合并 {success_count}/{len(bar_sizes)} 个时间周期")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

