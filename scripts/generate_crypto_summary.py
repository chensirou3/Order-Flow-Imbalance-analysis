"""
Generate summary report for cryptocurrency OFI analysis
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config, get_project_root


def main():
    print("=" * 80)
    print("Generating Cryptocurrency OFI Summary Report")
    print("=" * 80)
    
    config = get_config()
    project_root = get_project_root()
    results_dir = project_root / "results"
    
    # Crypto symbols and periods
    crypto_symbols = ["BTCUSD", "ETHUSD"]
    bar_sizes = config['bar_settings']['bar_sizes']
    
    # Collect all results
    all_results = []
    
    for symbol in crypto_symbols:
        for bar_size in bar_sizes:
            # Try to load single factor results
            file_path = results_dir / f"ofi_R1_single_factor_{symbol}_{bar_size}.csv"
            
            # Also try in single_factor subdirectory
            if not file_path.exists():
                file_path = results_dir / "single_factor" / f"ofi_R1_single_factor_{symbol}_{bar_size}.csv"
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    
                    # Extract high vs low OFI results
                    for horizon in df['horizon'].unique():
                        horizon_data = df[df['horizon'] == horizon]
                        
                        high_ofi = horizon_data[horizon_data['group'] == 'high_ofi'].iloc[0]
                        low_ofi = horizon_data[horizon_data['group'] == 'low_ofi'].iloc[0]
                        
                        spread = high_ofi['mean_ret'] - low_ofi['mean_ret']
                        
                        all_results.append({
                            'symbol': symbol,
                            'period': bar_size,
                            'horizon': int(horizon),
                            'high_ofi_ret': high_ofi['mean_ret'],
                            'low_ofi_ret': low_ofi['mean_ret'],
                            'spread': spread,
                            'high_ofi_tstat': high_ofi['t_stat'],
                            'low_ofi_tstat': low_ofi['t_stat'],
                            'high_ofi_N': int(high_ofi['N']),
                            'low_ofi_N': int(low_ofi['N'])
                        })
                        
                    print(f"  Loaded: {symbol} {bar_size}")
                except Exception as e:
                    print(f"  Error loading {symbol} {bar_size}: {e}")
            else:
                print(f"  Not found: {symbol} {bar_size}")
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(all_results)
    
    # Sort by spread (descending)
    summary_df = summary_df.sort_values('spread', ascending=False)
    
    # Save full summary
    output_file = results_dir / "CRYPTO_OFI_SUMMARY.csv"
    summary_df.to_csv(output_file, index=False)
    print(f"\nSaved full summary to: {output_file}")
    
    # Create markdown report
    md_lines = []
    md_lines.append("# Cryptocurrency OFI Factor Analysis Summary")
    md_lines.append("")
    md_lines.append("## Overview")
    md_lines.append("")
    md_lines.append(f"- **Symbols**: BTCUSD, ETHUSD")
    md_lines.append(f"- **Time Periods**: {', '.join(bar_sizes)}")
    md_lines.append(f"- **Total Configurations**: {len(summary_df) // 3}")
    md_lines.append(f"- **Data Range**: 2017-2025 (8 years)")
    md_lines.append("")
    
    # Top 10 configurations
    md_lines.append("## Top 10 Configurations (by Spread)")
    md_lines.append("")
    md_lines.append("| Rank | Symbol | Period | Horizon | High OFI | Low OFI | Spread | t-stat (High) |")
    md_lines.append("|------|--------|--------|---------|----------|---------|--------|---------------|")
    
    for i, row in summary_df.head(10).iterrows():
        md_lines.append(
            f"| {len(md_lines)-6} | {row['symbol']} | {row['period']} | {row['horizon']} | "
            f"{row['high_ofi_ret']:.4%} | {row['low_ofi_ret']:.4%} | "
            f"**{row['spread']:.4%}** | {row['high_ofi_tstat']:.2f} |"
        )
    
    md_lines.append("")
    
    # By symbol
    md_lines.append("## Results by Symbol")
    md_lines.append("")
    
    for symbol in crypto_symbols:
        md_lines.append(f"### {symbol}")
        md_lines.append("")
        
        symbol_data = summary_df[summary_df['symbol'] == symbol].head(5)
        
        md_lines.append("| Period | Horizon | High OFI | Low OFI | Spread | t-stat |")
        md_lines.append("|--------|---------|----------|---------|--------|--------|")
        
        for i, row in symbol_data.iterrows():
            md_lines.append(
                f"| {row['period']} | {row['horizon']} | {row['high_ofi_ret']:.4%} | "
                f"{row['low_ofi_ret']:.4%} | **{row['spread']:.4%}** | {row['high_ofi_tstat']:.2f} |"
            )
        
        md_lines.append("")
    
    # By period
    md_lines.append("## Results by Time Period")
    md_lines.append("")
    
    for period in ['5min', '15min', '30min', '1H', '4H', '1D']:
        period_data = summary_df[summary_df['period'] == period]
        if len(period_data) > 0:
            md_lines.append(f"### {period}")
            md_lines.append("")
            
            md_lines.append("| Symbol | Horizon | High OFI | Low OFI | Spread | t-stat |")
            md_lines.append("|--------|---------|----------|---------|--------|--------|")
            
            for i, row in period_data.head(6).iterrows():
                md_lines.append(
                    f"| {row['symbol']} | {row['horizon']} | {row['high_ofi_ret']:.4%} | "
                    f"{row['low_ofi_ret']:.4%} | **{row['spread']:.4%}** | {row['high_ofi_tstat']:.2f} |"
                )
            
            md_lines.append("")
    
    # Save markdown report
    md_file = results_dir / "CRYPTO_OFI_SUMMARY.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f"Saved markdown report to: {md_file}")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"\nTotal configurations analyzed: {len(summary_df) // 3}")
    print(f"Average spread: {summary_df['spread'].mean():.4%}")
    print(f"Max spread: {summary_df['spread'].max():.4%}")
    print(f"Min spread: {summary_df['spread'].min():.4%}")
    
    print("\nTop 3 configurations:")
    for i, row in summary_df.head(3).iterrows():
        print(f"  {i+1}. {row['symbol']} {row['period']} H={row['horizon']}: "
              f"Spread={row['spread']:.4%}, t-stat={row['high_ofi_tstat']:.2f}")


if __name__ == "__main__":
    main()

