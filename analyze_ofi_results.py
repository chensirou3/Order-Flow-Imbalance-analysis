"""
分析OFI因子结果
生成总结报告
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def analyze_single_file(file_path):
    """分析单个文件"""
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    
    # 基本统计
    stats = {
        'file': file_path.name,
        'rows': len(df),
        'start_date': df.index.min(),
        'end_date': df.index.max(),
        'days': (df.index.max() - df.index.min()).days,
    }
    
    # OFI统计
    if 'OFI_z' in df.columns:
        stats['ofi_z_mean'] = df['OFI_z'].mean()
        stats['ofi_z_std'] = df['OFI_z'].std()
        stats['ofi_z_min'] = df['OFI_z'].min()
        stats['ofi_z_max'] = df['OFI_z'].max()
    
    # 未来收益统计
    for horizon in [2, 5, 10]:
        col = f'fut_ret_{horizon}'
        if col in df.columns:
            # 去除NaN
            returns = df[col].dropna()
            if len(returns) > 0:
                stats[f'fut_ret_{horizon}_mean'] = returns.mean()
                stats[f'fut_ret_{horizon}_std'] = returns.std()
                stats[f'fut_ret_{horizon}_sharpe'] = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
    
    # OFI与未来收益的相关性
    if 'OFI_z' in df.columns:
        for horizon in [2, 5, 10]:
            col = f'fut_ret_{horizon}'
            if col in df.columns:
                corr = df[['OFI_z', col]].corr().iloc[0, 1]
                stats[f'corr_ofi_ret_{horizon}'] = corr
    
    # 分组分析：按OFI_z分5组
    if 'OFI_z' in df.columns and 'fut_ret_10' in df.columns:
        df_clean = df[['OFI_z', 'fut_ret_10']].dropna()
        if len(df_clean) > 0:
            df_clean['ofi_quintile'] = pd.qcut(df_clean['OFI_z'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
            quintile_returns = df_clean.groupby('ofi_quintile')['fut_ret_10'].mean()
            
            if len(quintile_returns) >= 2:
                stats['q5_minus_q1'] = quintile_returns.iloc[-1] - quintile_returns.iloc[0]
                stats['q5_return'] = quintile_returns.iloc[-1]
                stats['q1_return'] = quintile_returns.iloc[0]
    
    return stats


def main():
    results_dir = Path('results')
    
    if not results_dir.exists():
        print("❌ results/ 目录不存在")
        return
    
    # 获取所有合并文件
    merged_files = list(results_dir.glob('*_merged_bars_with_ofi.csv'))
    
    if not merged_files:
        print("❌ 没有找到合并文件")
        return
    
    print(f"\n找到 {len(merged_files)} 个合并文件")
    print("="*80)
    
    # 分析所有文件
    all_stats = []
    for file_path in sorted(merged_files):
        print(f"分析: {file_path.name}...")
        try:
            stats = analyze_single_file(file_path)
            all_stats.append(stats)
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    # 转换为DataFrame
    df_stats = pd.DataFrame(all_stats)
    
    # 解析文件名
    df_stats['symbol'] = df_stats['file'].str.split('_').str[0]
    df_stats['timeframe'] = df_stats['file'].str.split('_').str[1]
    
    # 保存详细统计
    output_file = results_dir / 'analysis_summary.csv'
    df_stats.to_csv(output_file, index=False)
    print(f"\n✓ 详细统计保存到: {output_file}")
    
    # 生成总结报告
    print("\n" + "="*80)
    print("OFI因子分析总结报告")
    print("="*80)
    
    # 按品种汇总
    print("\n【按品种汇总】")
    print("-"*80)
    for symbol in df_stats['symbol'].unique():
        symbol_data = df_stats[df_stats['symbol'] == symbol]
        print(f"\n{symbol}:")
        print(f"  时间周期数: {len(symbol_data)}")
        print(f"  数据行数: {symbol_data['rows'].sum():,}")
        print(f"  日期范围: {symbol_data['start_date'].min()} 到 {symbol_data['end_date'].max()}")
        
        # 最佳表现的时间周期
        if 'q5_minus_q1' in symbol_data.columns:
            best_tf = symbol_data.nlargest(1, 'q5_minus_q1')
            if len(best_tf) > 0:
                print(f"  最佳时间周期: {best_tf.iloc[0]['timeframe']}")
                print(f"    Q5-Q1收益差: {best_tf.iloc[0]['q5_minus_q1']:.4%}")
                print(f"    OFI相关性: {best_tf.iloc[0]['corr_ofi_ret_10']:.4f}")
    
    # 整体统计
    print("\n【整体统计】")
    print("-"*80)
    print(f"总文件数: {len(df_stats)}")
    print(f"总数据行数: {df_stats['rows'].sum():,}")
    print(f"平均OFI_z标准差: {df_stats['ofi_z_std'].mean():.4f}")
    
    if 'corr_ofi_ret_10' in df_stats.columns:
        print(f"\nOFI与未来收益相关性 (Horizon=10):")
        print(f"  平均相关性: {df_stats['corr_ofi_ret_10'].mean():.4f}")
        print(f"  最大相关性: {df_stats['corr_ofi_ret_10'].max():.4f}")
        print(f"  最小相关性: {df_stats['corr_ofi_ret_10'].min():.4f}")
    
    if 'q5_minus_q1' in df_stats.columns:
        print(f"\nQ5-Q1收益差 (Horizon=10):")
        print(f"  平均: {df_stats['q5_minus_q1'].mean():.4%}")
        print(f"  最大: {df_stats['q5_minus_q1'].max():.4%}")
        print(f"  最小: {df_stats['q5_minus_q1'].min():.4%}")
        
        # 显示表现最好的配置
        print(f"\n【表现最好的10个配置】")
        print("-"*80)
        top10 = df_stats.nlargest(10, 'q5_minus_q1')[['symbol', 'timeframe', 'q5_minus_q1', 'corr_ofi_ret_10', 'rows']]
        print(top10.to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80)


if __name__ == '__main__':
    main()

