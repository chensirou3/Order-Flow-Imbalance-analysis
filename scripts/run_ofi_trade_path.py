"""
Phase 4: OFI Trade Path Analysis

Main script to run trade path simulation and analysis for all crypto and metal symbols.

Usage:
    python scripts/run_ofi_trade_path.py
"""

import sys
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.research.ofi_trade_path_analysis import (
    analyze_all_configs,
    create_rankings,
    generate_summary_report
)


def main():
    """Main execution function."""
    
    print("="*80)
    print("OFI Trade Path Analysis - Phase 4")
    print("="*80)
    print()
    
    # Load configuration
    config_file = project_root / 'config' / 'settings.yaml'
    print(f"Loading configuration from: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Extract parameters
    symbols = config['trade_path_symbols']  # Only crypto and metals
    timeframes = config['timeframes']
    trade_path_config = config['ofi_trade_path']
    
    print(f"\nSymbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"Entry mode: {trade_path_config['entry_mode']}")
    print(f"Entry thresholds: Q_low={trade_path_config['entry_q_low']}, Q_high={trade_path_config['entry_q_high']}")
    print(f"ATR period: {trade_path_config['atr_period']}")
    print(f"Hmax bars: {trade_path_config['hmax_bars']}")
    print()
    
    # Setup paths
    results_dir = project_root / config['paths']['results_dir']
    output_dir = project_root / config['paths']['trade_path_dir']
    summary_dir = project_root / config['paths']['trade_summary_dir']
    
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Summary directory: {summary_dir}")
    print()
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis for all configurations
    print("="*80)
    print("Starting analysis...")
    print("="*80)
    
    all_trades_df, summary_df = analyze_all_configs(
        symbols=symbols,
        timeframes=timeframes,
        config=trade_path_config,
        results_dir=results_dir,
        output_dir=output_dir
    )
    
    # Save results
    print("\n" + "="*80)
    print("Saving results...")
    print("="*80)
    
    if len(summary_df) > 0:
        # Save summary statistics
        summary_file = summary_dir / 'trade_path_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"✅ Summary statistics saved to: {summary_file}")
        
        # Create and save rankings
        ranked_df = create_rankings(summary_df)
        ranked_file = summary_dir / 'trade_path_rankings.csv'
        ranked_df.to_csv(ranked_file, index=False)
        print(f"✅ Rankings saved to: {ranked_file}")
        
        # Generate markdown report
        report_file = summary_dir / 'trade_path_report.md'
        generate_summary_report(summary_df, report_file)
        
        # Print top 5 configurations
        print("\n" + "="*80)
        print("Top 5 Configurations by Expectancy R:")
        print("="*80)
        
        top5 = ranked_df.nsmallest(5, 'rank_expectancy')
        for idx, row in top5.iterrows():
            print(f"\n{int(row['rank_expectancy'])}. {row['symbol']} {row['timeframe']}")
            print(f"   Trades: {int(row['n_trades'])}")
            print(f"   Expectancy R: {row['expectancy_r']:.3f}")
            print(f"   Win Rate: {row['win_rate']:.1%}")
            print(f"   Sharpe R: {row['sharpe_r']:.3f}")
            print(f"   Mean MFE_R: {row['mean_mfe_r']:.3f}")
            print(f"   Mean MAE_R: {row['mean_mae_r']:.3f}")
            print(f"   Mean Bars Held: {row['mean_bars_held']:.1f}")
    
    if len(all_trades_df) > 0:
        # Save all trades
        all_trades_file = output_dir / 'all_trades.csv'
        all_trades_df.to_csv(all_trades_file, index=False)
        print(f"\n✅ All trades saved to: {all_trades_file}")
        print(f"   Total trades: {len(all_trades_df)}")
    
    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80)
    print()
    
    # Print summary by symbol
    if len(summary_df) > 0:
        print("\nPerformance by Symbol:")
        print("-" * 80)
        by_symbol = summary_df.groupby('symbol').agg({
            'n_trades': 'sum',
            'expectancy_r': 'mean',
            'win_rate': 'mean',
            'sharpe_r': 'mean'
        }).sort_values('expectancy_r', ascending=False)
        
        for symbol, row in by_symbol.iterrows():
            print(f"{symbol:10s} | Trades: {int(row['n_trades']):5d} | "
                  f"Exp R: {row['expectancy_r']:6.3f} | "
                  f"Win%: {row['win_rate']:5.1%} | "
                  f"Sharpe: {row['sharpe_r']:6.3f}")
        print()


if __name__ == '__main__':
    main()

