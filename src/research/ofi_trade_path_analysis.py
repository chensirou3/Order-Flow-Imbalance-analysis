"""
Phase 4.3 & 4.4: Trade Path Analysis and Cross-Asset Summary

Analyze trade paths for each symbol/timeframe and create cross-asset rankings.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.trading.ofi_signals import prepare_trading_data
from src.trading.trade_path_simulator import simulate_trade_paths, analyze_trade_statistics


def analyze_single_config(
    symbol: str,
    timeframe: str,
    data_file: Path,
    config: Dict,
    save_trades: bool = True,
    output_dir: Path = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Analyze trade paths for a single symbol/timeframe configuration.
    
    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., 'BTCUSD')
    timeframe : str
        Timeframe (e.g., '1H', '1D')
    data_file : Path
        Path to bars_with_ofi CSV file
    config : Dict
        Configuration dictionary with trade_path parameters
    save_trades : bool
        Whether to save individual trade results
    output_dir : Path
        Output directory for trade files
    
    Returns
    -------
    Tuple[pd.DataFrame, Dict]
        (trade_df, statistics_dict)
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {symbol} {timeframe}")
    print(f"{'='*80}")
    
    # Load data
    print(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    print(f"  Loaded {len(df)} bars")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    
    # Check required columns
    required_cols = ['open', 'high', 'low', 'close', 'OFI_z']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Prepare trading data (add signals and ATR)
    print(f"Generating signals...")
    df = prepare_trading_data(
        df,
        entry_mode=config['entry_mode'],
        entry_q_high=config['entry_q_high'],
        entry_q_low=config['entry_q_low'],
        atr_period=config['atr_period'],
        atr_method=config['atr_method']
    )
    
    n_long_signals = (df['signal'] == 1).sum()
    n_short_signals = (df['signal'] == -1).sum()
    print(f"  Long signals: {n_long_signals}")
    print(f"  Short signals: {n_short_signals}")
    print(f"  Total signals: {n_long_signals + n_short_signals}")
    
    # Simulate trades
    print(f"Simulating trades...")
    trade_df = simulate_trade_paths(
        df,
        hmax_bars=config['hmax_bars'],
        position_size=config['fixed_position_size'],
        save_paths=config['save_paths']
    )
    
    if len(trade_df) == 0:
        print(f"  ⚠️  No trades generated!")
        return pd.DataFrame(), {}
    
    print(f"  Generated {len(trade_df)} trades")
    
    # Compute statistics
    print(f"Computing statistics...")
    stats = analyze_trade_statistics(trade_df)
    
    # Add metadata
    stats['symbol'] = symbol
    stats['timeframe'] = timeframe
    stats['data_bars'] = len(df)
    stats['date_start'] = df.index.min()
    stats['date_end'] = df.index.max()
    
    # Print summary
    print(f"\n  Summary:")
    print(f"    Trades: {stats['n_trades']} (Long: {stats['n_long']}, Short: {stats['n_short']})")
    print(f"    Mean R: {stats['mean_r']:.3f}")
    print(f"    Win Rate: {stats['win_rate']:.1%}")
    print(f"    Expectancy R: {stats['expectancy_r']:.3f}")
    print(f"    Sharpe R: {stats['sharpe_r']:.3f}")
    print(f"    Mean MFE_R: {stats['mean_mfe_r']:.3f}")
    print(f"    Mean MAE_R: {stats['mean_mae_r']:.3f}")
    print(f"    Mean Bars Held: {stats['mean_bars_held']:.1f}")
    
    # Save trades if requested
    if save_trades and output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        trade_file = output_dir / f"{symbol}_{timeframe}_trades.csv"
        trade_df.to_csv(trade_file, index=False)
        print(f"  Saved trades to: {trade_file}")
    
    return trade_df, stats


def analyze_all_configs(
    symbols: List[str],
    timeframes: List[str],
    config: Dict,
    results_dir: Path,
    output_dir: Path
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze all symbol/timeframe combinations.
    
    Parameters
    ----------
    symbols : List[str]
        List of symbols to analyze
    timeframes : List[str]
        List of timeframes to analyze
    config : Dict
        Configuration dictionary
    results_dir : Path
        Directory containing bars_with_ofi files
    output_dir : Path
        Output directory for results
    
    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (all_trades_df, summary_stats_df)
    """
    all_stats = []
    all_trades = []
    
    total_configs = len(symbols) * len(timeframes)
    current = 0
    
    for symbol in symbols:
        for timeframe in timeframes:
            current += 1
            print(f"\n[{current}/{total_configs}] Processing {symbol} {timeframe}...")
            
            # Construct data file path
            data_file = results_dir / f"{symbol}_{timeframe}_merged_bars_with_ofi.csv"
            
            if not data_file.exists():
                print(f"  ⚠️  File not found: {data_file}")
                continue
            
            try:
                # Analyze this configuration
                trade_df, stats = analyze_single_config(
                    symbol=symbol,
                    timeframe=timeframe,
                    data_file=data_file,
                    config=config,
                    save_trades=True,
                    output_dir=output_dir / 'individual_trades'
                )
                
                if len(trade_df) > 0:
                    # Add metadata to trades
                    trade_df['symbol'] = symbol
                    trade_df['timeframe'] = timeframe
                    all_trades.append(trade_df)
                    all_stats.append(stats)
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol} {timeframe}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Combine results
    if len(all_stats) == 0:
        print("\n⚠️  No successful analyses!")
        return pd.DataFrame(), pd.DataFrame()
    
    summary_df = pd.DataFrame(all_stats)
    
    if len(all_trades) > 0:
        trades_df = pd.concat(all_trades, ignore_index=True)
    else:
        trades_df = pd.DataFrame()
    
    return trades_df, summary_df


def create_rankings(summary_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create rankings based on various metrics.

    Parameters
    ----------
    summary_df : pd.DataFrame
        Summary statistics from analyze_all_configs

    Returns
    -------
    pd.DataFrame
        Ranked configurations
    """
    if len(summary_df) == 0:
        return pd.DataFrame()

    # Create a copy for ranking
    ranked = summary_df.copy()

    # Sort by expectancy_r (descending)
    ranked = ranked.sort_values('expectancy_r', ascending=False)

    # Add rank column
    ranked['rank_expectancy'] = range(1, len(ranked) + 1)

    # Also rank by Sharpe
    ranked['rank_sharpe'] = ranked['sharpe_r'].rank(ascending=False, method='min')

    # Rank by win rate
    ranked['rank_winrate'] = ranked['win_rate'].rank(ascending=False, method='min')

    # Composite score (simple average of ranks)
    ranked['composite_rank'] = (
        ranked['rank_expectancy'] +
        ranked['rank_sharpe'] +
        ranked['rank_winrate']
    ) / 3

    return ranked


def generate_summary_report(
    summary_df: pd.DataFrame,
    output_file: Path
) -> None:
    """
    Generate a markdown summary report.

    Parameters
    ----------
    summary_df : pd.DataFrame
        Summary statistics
    output_file : Path
        Output markdown file path
    """
    if len(summary_df) == 0:
        print("No data to generate report!")
        return

    # Create rankings
    ranked = create_rankings(summary_df)

    # Generate report
    lines = []
    lines.append("# OFI Trade Path Analysis - Summary Report")
    lines.append("")
    lines.append(f"**Generated**: {pd.Timestamp.now()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overall statistics
    lines.append("## Overall Statistics")
    lines.append("")
    lines.append(f"- **Total Configurations**: {len(summary_df)}")
    lines.append(f"- **Total Trades**: {summary_df['n_trades'].sum():.0f}")
    lines.append(f"- **Average Trades per Config**: {summary_df['n_trades'].mean():.1f}")
    lines.append("")

    # Top 10 by Expectancy
    lines.append("## Top 10 Configurations by Expectancy (R)")
    lines.append("")
    lines.append("| Rank | Symbol | Timeframe | Trades | Expectancy R | Win Rate | Sharpe R | Mean MFE_R | Mean Bars |")
    lines.append("|------|--------|-----------|--------|--------------|----------|----------|------------|-----------|")

    top10_exp = ranked.nsmallest(10, 'rank_expectancy')
    for idx, row in top10_exp.iterrows():
        lines.append(
            f"| {int(row['rank_expectancy'])} | {row['symbol']} | {row['timeframe']} | "
            f"{int(row['n_trades'])} | {row['expectancy_r']:.3f} | {row['win_rate']:.1%} | "
            f"{row['sharpe_r']:.3f} | {row['mean_mfe_r']:.3f} | {row['mean_bars_held']:.1f} |"
        )
    lines.append("")

    # Top 10 by Sharpe
    lines.append("## Top 10 Configurations by Sharpe Ratio")
    lines.append("")
    lines.append("| Rank | Symbol | Timeframe | Trades | Sharpe R | Expectancy R | Win Rate | Mean MFE_R |")
    lines.append("|------|--------|-----------|--------|----------|--------------|----------|------------|")

    top10_sharpe = ranked.nsmallest(10, 'rank_sharpe')
    for idx, row in top10_sharpe.iterrows():
        lines.append(
            f"| {int(row['rank_sharpe'])} | {row['symbol']} | {row['timeframe']} | "
            f"{int(row['n_trades'])} | {row['sharpe_r']:.3f} | {row['expectancy_r']:.3f} | "
            f"{row['win_rate']:.1%} | {row['mean_mfe_r']:.3f} |"
        )
    lines.append("")

    # By symbol summary
    lines.append("## Performance by Symbol")
    lines.append("")
    lines.append("| Symbol | Configs | Total Trades | Avg Expectancy R | Avg Win Rate | Avg Sharpe R |")
    lines.append("|--------|---------|--------------|------------------|--------------|--------------|")

    by_symbol = summary_df.groupby('symbol').agg({
        'timeframe': 'count',
        'n_trades': 'sum',
        'expectancy_r': 'mean',
        'win_rate': 'mean',
        'sharpe_r': 'mean'
    }).sort_values('expectancy_r', ascending=False)

    for symbol, row in by_symbol.iterrows():
        lines.append(
            f"| {symbol} | {int(row['timeframe'])} | {int(row['n_trades'])} | "
            f"{row['expectancy_r']:.3f} | {row['win_rate']:.1%} | {row['sharpe_r']:.3f} |"
        )
    lines.append("")

    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n✅ Summary report saved to: {output_file}")
