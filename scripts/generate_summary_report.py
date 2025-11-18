"""Generate a summary report of all OFI analysis results."""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_project_root


def main():
    project_root = get_project_root()
    results_dir = project_root / "results"
    single_factor_dir = results_dir / "single_factor"
    
    # Collect all single-factor analysis files
    sf_files = list(single_factor_dir.glob("ofi_R1_single_factor_*.csv"))
    bin_files = list(single_factor_dir.glob("ofi_R1_bins_*.csv"))
    
    print(f"Found {len(sf_files)} single-factor analysis files")
    print(f"Found {len(bin_files)} bin analysis files")
    
    # Parse results
    all_results = []
    
    for sf_file in sorted(sf_files):
        # Extract symbol and bar_size from filename
        # Format: ofi_R1_single_factor_SYMBOL_BARSIZE.csv
        parts = sf_file.stem.split('_')
        if len(parts) >= 5:
            symbol = parts[4]
            bar_size = parts[5] if len(parts) > 5 else '4H'
        else:
            continue
        
        # Load data
        df = pd.read_csv(sf_file)
        
        # Extract key metrics for each horizon
        for horizon in df['horizon'].unique():
            horizon_data = df[df['horizon'] == horizon]
            
            high_ofi = horizon_data[horizon_data['group'] == 'high_ofi'].iloc[0]
            low_ofi = horizon_data[horizon_data['group'] == 'low_ofi'].iloc[0]
            
            all_results.append({
                'symbol': symbol,
                'bar_size': bar_size,
                'horizon': horizon,
                'high_ofi_mean': high_ofi['mean_ret'],
                'high_ofi_t_stat': high_ofi['t_stat'],
                'low_ofi_mean': low_ofi['mean_ret'],
                'low_ofi_t_stat': low_ofi['t_stat'],
                'spread': high_ofi['mean_ret'] - low_ofi['mean_ret'],
                'ols_beta': high_ofi['ols_beta'],
                'ols_t_stat': high_ofi['ols_t_stat'],
            })
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(all_results)
    
    # Save full summary
    summary_file = results_dir / "OFI_FULL_SUMMARY.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSaved full summary to {summary_file}")
    
    # Create markdown report
    report_file = results_dir / "OFI_ANALYSIS_SUMMARY.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# OFI因子分析 - 全品种全周期汇总报告\n\n")
        f.write(f"**生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary statistics
        f.write("## 分析覆盖范围\n\n")
        f.write(f"- **品种数量**: {summary_df['symbol'].nunique()}\n")
        f.write(f"- **时间周期**: {sorted(summary_df['bar_size'].unique())}\n")
        f.write(f"- **预测时间跨度**: {sorted(summary_df['horizon'].unique())}\n")
        f.write(f"- **总分析数**: {len(summary_df)}\n\n")
        
        # Best performers by spread (high_ofi - low_ofi)
        f.write("## Top 20: 最大收益差异 (高OFI - 低OFI)\n\n")
        top_spread = summary_df.nlargest(20, 'spread')
        f.write("| 排名 | 品种 | 周期 | Horizon | 高OFI收益 | 低OFI收益 | 收益差 | t统计量(高) | OLS Beta |\n")
        f.write("|------|------|------|---------|-----------|-----------|--------|-------------|----------|\n")
        for i, row in enumerate(top_spread.itertuples(), 1):
            f.write(f"| {i} | {row.symbol} | {row.bar_size} | {row.horizon} | "
                   f"{row.high_ofi_mean*100:.3f}% | {row.low_ofi_mean*100:.3f}% | "
                   f"{row.spread*100:.3f}% | {row.high_ofi_t_stat:.2f} | {row.ols_beta*100:.4f}% |\n")
        f.write("\n")
        
        # Best t-statistics
        f.write("## Top 20: 最显著的统计结果 (按t统计量)\n\n")
        top_t = summary_df.nlargest(20, 'high_ofi_t_stat')
        f.write("| 排名 | 品种 | 周期 | Horizon | 高OFI收益 | t统计量 | OLS t值 |\n")
        f.write("|------|------|------|---------|-----------|---------|----------|\n")
        for i, row in enumerate(top_t.itertuples(), 1):
            f.write(f"| {i} | {row.symbol} | {row.bar_size} | {row.horizon} | "
                   f"{row.high_ofi_mean*100:.3f}% | {row.high_ofi_t_stat:.2f} | {row.ols_t_stat:.2f} |\n")
        f.write("\n")
        
        # By symbol summary
        f.write("## 各品种表现汇总\n\n")
        for symbol in sorted(summary_df['symbol'].unique()):
            symbol_data = summary_df[summary_df['symbol'] == symbol]
            
            f.write(f"### {symbol}\n\n")
            
            # Best result for this symbol
            best = symbol_data.nlargest(1, 'spread').iloc[0]
            f.write(f"**最佳配置**: {best['bar_size']} 周期, Horizon={best['horizon']}\n")
            f.write(f"- 高OFI收益: {best['high_ofi_mean']*100:.3f}%\n")
            f.write(f"- 低OFI收益: {best['low_ofi_mean']*100:.3f}%\n")
            f.write(f"- 收益差: {best['spread']*100:.3f}%\n")
            f.write(f"- t统计量: {best['high_ofi_t_stat']:.2f}\n")
            f.write(f"- OLS Beta: {best['ols_beta']*100:.4f}%\n\n")
            
            # Summary table for this symbol
            f.write(f"**所有配置结果**:\n\n")
            f.write("| 周期 | Horizon | 收益差 | t统计量 |\n")
            f.write("|------|---------|--------|----------|\n")
            for _, row in symbol_data.sort_values(['bar_size', 'horizon']).iterrows():
                f.write(f"| {row['bar_size']} | {row['horizon']} | "
                       f"{row['spread']*100:.3f}% | {row['high_ofi_t_stat']:.2f} |\n")
            f.write("\n")
    
    print(f"Saved markdown report to {report_file}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("OFI ANALYSIS SUMMARY")
    print("="*80)
    print(f"\nAnalyzed:")
    print(f"  - {summary_df['symbol'].nunique()} symbols")
    print(f"  - {summary_df['bar_size'].nunique()} time periods")
    print(f"  - {summary_df['horizon'].nunique()} horizons")
    print(f"  - {len(summary_df)} total configurations")
    
    print(f"\nTop 5 configurations by spread:")
    top5 = summary_df.nlargest(5, 'spread')
    for i, row in enumerate(top5.itertuples(), 1):
        print(f"  {i}. {row.symbol:8s} {row.bar_size:4s} H={row.horizon:2d} "
              f"spread={row.spread*100:6.3f}% t={row.high_ofi_t_stat:5.2f}")
    
    print(f"\nReports saved:")
    print(f"  - {summary_file}")
    print(f"  - {report_file}")


if __name__ == "__main__":
    main()

