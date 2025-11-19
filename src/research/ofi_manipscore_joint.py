"""
Phase 6B: OFI × ManipScore Joint Signal Design & Diagnostics

Combine OFI and ManipScore factors to create joint trading signals.
Test different signal combinations and compare with OFI-only strategies.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum
import sys
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import get_config
from src.trading.trade_path_simulator import (
    TradePathConfig,
    simulate_trade_paths
)
from src.utils.cost_utils import CostScenario, apply_cost_scenario_to_trades


class JointStrategy(Enum):
    """Joint signal strategy types."""
    BOTH_TREND = "J1_both_trend"           # OFI+MS both strong, direction = sign(OFI_z)
    BOTH_REVERSAL = "J2_both_reversal"     # OFI+MS both strong, direction = -sign(OFI_z)
    MS_ONLY_TREND = "J3_ms_only_trend"     # MS strong only, direction = sign(OFI_z)
    OFI_ONLY_TREND = "J4_ofi_only_trend"   # OFI strong only, direction = sign(OFI_z)


def join_ofi_and_manipscore(
    symbol: str,
    timeframe: str,
    bars_ofi_path: Path,
    bars_ms_pattern: str
) -> Optional[pd.DataFrame]:
    """
    Join OFI and ManipScore bar data on timestamp.
    
    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    bars_ofi_path : Path
        Path to bars with OFI
    bars_ms_pattern : str
        Pattern for ManipScore bars path
    
    Returns
    -------
    Optional[pd.DataFrame]
        Joined DataFrame or None if ManipScore file not found
    """
    # Load OFI bars
    if not bars_ofi_path.exists():
        print(f"  WARNING: OFI bars not found: {bars_ofi_path}")
        return None
    
    bars_ofi = pd.read_csv(bars_ofi_path, index_col=0, parse_dates=True)
    
    # Try to load ManipScore bars
    bars_ms_path = Path(bars_ms_pattern.format(symbol=symbol, tf=timeframe))
    
    if not bars_ms_path.exists():
        print(f"  WARNING: ManipScore bars not found: {bars_ms_path}")
        print(f"  Skipping {symbol} {timeframe}")
        return None
    
    bars_ms = pd.read_csv(bars_ms_path, index_col=0, parse_dates=True)
    
    # Check for ManipScore column
    if 'ManipScore' not in bars_ms.columns:
        print(f"  WARNING: ManipScore column not found in {bars_ms_path}")
        return None
    
    # Join on timestamp (inner join to keep only common timestamps)
    bars_joined = bars_ofi.join(bars_ms[['ManipScore']], how='inner')
    
    print(f"  Joined {len(bars_ofi)} OFI bars with {len(bars_ms)} MS bars")
    print(f"  Result: {len(bars_joined)} common bars")
    
    return bars_joined


def compute_joint_signal_conditions(
    bars_df: pd.DataFrame,
    ofi_abs_q: float = 0.9,
    ms_q: float = 0.9
) -> pd.DataFrame:
    """
    Compute joint signal conditions based on OFI_z and ManipScore.
    
    Parameters
    ----------
    bars_df : pd.DataFrame
        Bars with OFI_z and ManipScore
    ofi_abs_q : float
        Quantile threshold for |OFI_z|
    ms_q : float
        Quantile threshold for ManipScore
    
    Returns
    -------
    pd.DataFrame
        Bars with added condition columns
    """
    df = bars_df.copy()
    
    # Compute thresholds
    q_ofi_abs = df['OFI_z'].abs().quantile(ofi_abs_q)
    q_ms = df['ManipScore'].quantile(ms_q)
    
    print(f"  OFI_z abs quantile {ofi_abs_q}: {q_ofi_abs:.3f}")
    print(f"  ManipScore quantile {ms_q}: {q_ms:.3f}")
    
    # Define conditions
    df['cond_ofi_strong'] = df['OFI_z'].abs() >= q_ofi_abs
    df['cond_ms_strong'] = df['ManipScore'] >= q_ms
    df['cond_both'] = df['cond_ofi_strong'] & df['cond_ms_strong']
    df['cond_ofi_only'] = df['cond_ofi_strong'] & ~df['cond_ms_strong']
    df['cond_ms_only'] = df['cond_ms_strong'] & ~df['cond_ofi_strong']
    
    # Count occurrences
    print(f"  Bars with OFI strong: {df['cond_ofi_strong'].sum()}")
    print(f"  Bars with MS strong: {df['cond_ms_strong'].sum()}")
    print(f"  Bars with both strong: {df['cond_both'].sum()}")
    print(f"  Bars with OFI only: {df['cond_ofi_only'].sum()}")
    print(f"  Bars with MS only: {df['cond_ms_only'].sum()}")
    
    return df


def generate_joint_signals(
    bars_df: pd.DataFrame,
    strategy: JointStrategy
) -> pd.DataFrame:
    """
    Generate trading signals based on joint strategy.
    
    Parameters
    ----------
    bars_df : pd.DataFrame
        Bars with condition columns
    strategy : JointStrategy
        Which joint strategy to use
    
    Returns
    -------
    pd.DataFrame
        Bars with 'signal' column added
    """
    df = bars_df.copy()
    df['signal'] = 0  # Default: no signal
    
    if strategy == JointStrategy.BOTH_TREND:
        # Entry when both OFI and MS are strong, direction = sign(OFI_z)
        df.loc[df['cond_both'], 'signal'] = np.sign(df.loc[df['cond_both'], 'OFI_z'])
    
    elif strategy == JointStrategy.BOTH_REVERSAL:
        # Entry when both strong, direction = -sign(OFI_z)
        df.loc[df['cond_both'], 'signal'] = -np.sign(df.loc[df['cond_both'], 'OFI_z'])
    
    elif strategy == JointStrategy.MS_ONLY_TREND:
        # Entry when MS strong only, direction = sign(OFI_z)
        df.loc[df['cond_ms_only'], 'signal'] = np.sign(df.loc[df['cond_ms_only'], 'OFI_z'])
    
    elif strategy == JointStrategy.OFI_ONLY_TREND:
        # Entry when OFI strong only, direction = sign(OFI_z)
        df.loc[df['cond_ofi_only'], 'signal'] = np.sign(df.loc[df['cond_ofi_only'], 'OFI_z'])
    
    return df


def simulate_joint_strategy(
    symbol: str,
    timeframe: str,
    bars_with_signals: pd.DataFrame,
    strategy: JointStrategy,
    trade_config: TradePathConfig,
    cost_scenarios: List[CostScenario]
) -> Dict:
    """
    Simulate trades for a joint strategy and compute metrics.

    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    bars_with_signals : pd.DataFrame
        Bars with 'signal' column
    strategy : JointStrategy
        Strategy type
    trade_config : TradePathConfig
        Trade simulation config
    cost_scenarios : List[CostScenario]
        Cost scenarios to apply

    Returns
    -------
    Dict
        Performance metrics
    """
    # Simulate trades using existing simulator
    trades_df = simulate_trade_paths(
        bars_with_signals,
        hmax_bars=trade_config.hmax_bars,
        position_size=trade_config.position_size,
        save_paths=False,
        tp_R=trade_config.tp_R
    )

    if len(trades_df) == 0:
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'strategy': strategy.value,
            'n_trades': 0,
            'mean_final_R_gross': np.nan,
            'sharpe_R_gross': np.nan
        }

    # Compute gross metrics
    n_trades = len(trades_df)
    mean_final_R_gross = trades_df['final_R'].mean()
    std_final_R = trades_df['final_R'].std()
    sharpe_R_gross = mean_final_R_gross / std_final_R if std_final_R > 0 else np.nan

    # MFE/MAE metrics
    median_MFE_R = trades_df['MFE_R'].median()
    p75_MFE_R = trades_df['MFE_R'].quantile(0.75)
    median_MAE_R = trades_df['MAE_R'].median()

    # Exit reason distribution
    exit_counts = trades_df['exit_reason'].value_counts()
    total = len(trades_df)
    pct_stop = exit_counts.get('stop', 0) / total
    pct_tp_hit = exit_counts.get('tp_hit', 0) / total
    pct_hmax = exit_counts.get('hmax', 0) / total

    # Build result dict
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'strategy': strategy.value,
        'n_trades': n_trades,
        'mean_final_R_gross': mean_final_R_gross,
        'sharpe_R_gross': sharpe_R_gross,
        'median_MFE_R': median_MFE_R,
        'p75_MFE_R': p75_MFE_R,
        'median_MAE_R': median_MAE_R,
        'pct_stop': pct_stop,
        'pct_tp_hit': pct_tp_hit,
        'pct_hmax': pct_hmax
    }

    # Apply cost scenarios
    for scenario in cost_scenarios:
        trades_with_cost = apply_cost_scenario_to_trades(trades_df, scenario)

        if len(trades_with_cost) > 0:
            mean_net = trades_with_cost[f'final_R_net_{scenario.name}'].mean()
            std_net = trades_with_cost[f'final_R_net_{scenario.name}'].std()
            sharpe_net = mean_net / std_net if std_net > 0 else np.nan

            result[f'mean_final_R_net_{scenario.name}'] = mean_net
            result[f'sharpe_R_net_{scenario.name}'] = sharpe_net

    return result


def get_best_ofi_config_from_phase5(
    symbol: str,
    timeframe: str,
    ranking_file: Path
) -> Optional[Dict]:
    """
    Get the best OFI-only config for a symbol/timeframe from Phase 5 ranking.

    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    ranking_file : Path
        Path to Phase 5 ranking CSV

    Returns
    -------
    Optional[Dict]
        Best config parameters or None
    """
    if not ranking_file.exists():
        print(f"  WARNING: Ranking file not found: {ranking_file}")
        return None

    ranking_df = pd.read_csv(ranking_file)

    # Filter by symbol and timeframe
    subset = ranking_df[
        (ranking_df['symbol'] == symbol) &
        (ranking_df['timeframe'] == timeframe)
    ]

    if len(subset) == 0:
        print(f"  WARNING: No configs found for {symbol} {timeframe}")
        return None

    # Get top config (already sorted by ranking metric)
    best = subset.iloc[0]

    return {
        'entry_q_high': best['entry_q_high'],
        'entry_q_low': best['entry_q_low'],
        'hmax_bars': int(best['hmax_bars']),
        'tp_R': best['tp_R'] if not pd.isna(best['tp_R']) else None,
        'atr_period': int(best.get('atr_period', 20)),
        'atr_method': best.get('atr_method', 'rolling_mean')
    }


def run_phase6B_ofi_ms_joint(config_path: Path) -> None:
    """
    Phase 6B main runner: OFI × ManipScore joint signal analysis.

    Parameters
    ----------
    config_path : Path
        Path to config YAML file
    """
    print("=" * 80)
    print("Phase 6B: OFI × ManipScore Joint Signal Design")
    print("=" * 80)
    print()

    # Load config
    config = get_config(str(config_path))
    phase6_cfg = config['phase6']['ofi_manipscore_joint']

    symbols = phase6_cfg['symbols']
    timeframes = phase6_cfg['timeframes']

    # Create output directories
    output_dir = Path(phase6_cfg['paths']['joint_results_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    joined_dir = Path("results_joint")
    joined_dir.mkdir(parents=True, exist_ok=True)

    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"Output directory: {output_dir}")
    print()

    # Cost scenarios from Phase 5
    cost_scenarios = [
        CostScenario(name=cs['name'], per_side_rate=cs['per_side_rate'])
        for cs in config['ofi_param_sweep']['cost_scenarios']
    ]

    print(f"Cost scenarios: {[cs.name for cs in cost_scenarios]}")
    print()

    all_results = []

    # Process each symbol/timeframe
    for symbol in symbols:
        for tf in timeframes:
            print(f"Processing {symbol} {tf}...")
            print("-" * 80)

            # Step 1: Join OFI and ManipScore bars
            bars_ofi_pattern = phase6_cfg['paths']['bars_with_ofi_pattern']
            bars_ofi_path = Path(bars_ofi_pattern.format(symbol=symbol, tf=tf))

            bars_joined = join_ofi_and_manipscore(
                symbol, tf,
                bars_ofi_path,
                phase6_cfg['bars_with_ms_pattern']
            )

            if bars_joined is None:
                print(f"  Skipping {symbol} {tf} (no ManipScore data)")
                print()
                continue

            # Save joined bars
            joined_pattern = phase6_cfg['bars_with_ofi_ms_pattern']
            joined_path = Path(joined_pattern.format(symbol=symbol, tf=tf))
            joined_path.parent.mkdir(parents=True, exist_ok=True)
            bars_joined.to_csv(joined_path)
            print(f"  Saved joined bars: {joined_path}")

            # Step 2: Compute joint signal conditions
            bars_with_conditions = compute_joint_signal_conditions(
                bars_joined,
                ofi_abs_q=phase6_cfg['ofi_abs_q'],
                ms_q=phase6_cfg['ms_q']
            )

            # Step 3: Get best OFI config from Phase 5
            if phase6_cfg.get('use_phase5_best_config', True):
                ranking_file = Path(config['phase6']['strategy_spec']['ranking_file'])
                best_config = get_best_ofi_config_from_phase5(symbol, tf, ranking_file)

                if best_config is None:
                    print(f"  WARNING: No Phase 5 config found, using defaults")
                    best_config = {
                        'hmax_bars': 150,
                        'tp_R': None,
                        'atr_period': 20,
                        'atr_method': 'rolling_mean'
                    }

                print(f"  Using config: Hmax={best_config['hmax_bars']}, TP={best_config.get('tp_R')}")
            else:
                best_config = {
                    'hmax_bars': 150,
                    'tp_R': None,
                    'atr_period': 20,
                    'atr_method': 'rolling_mean'
                }

            # Create trade config
            trade_config = TradePathConfig(
                entry_mode='trend',  # Will be overridden by external signals
                hmax_bars=best_config['hmax_bars'],
                tp_R=best_config.get('tp_R'),
                atr_period=best_config.get('atr_period', 20),
                atr_method=best_config.get('atr_method', 'rolling_mean'),
                position_size=1.0,
                save_paths=False
            )

            # Step 4: Test each joint strategy
            for strategy in JointStrategy:
                print(f"  Testing strategy: {strategy.value}")

                # Generate signals
                bars_with_signals = generate_joint_signals(bars_with_conditions, strategy)

                n_signals = (bars_with_signals['signal'] != 0).sum()
                print(f"    Signals generated: {n_signals}")

                if n_signals == 0:
                    print(f"    Skipping (no signals)")
                    continue

                # Simulate trades
                result = simulate_joint_strategy(
                    symbol, tf,
                    bars_with_signals,
                    strategy,
                    trade_config,
                    cost_scenarios
                )

                all_results.append(result)

                print(f"    Trades: {result['n_trades']}")
                print(f"    Mean R (gross): {result['mean_final_R_gross']:.3f}")
                print(f"    Sharpe R (gross): {result['sharpe_R_gross']:.3f}")

            print()

    # Save results
    if all_results:
        results_df = pd.DataFrame(all_results)

        # Save global summary
        out_file = output_dir / "ofi_ms_joint_all.csv"
        results_df.to_csv(out_file, index=False)
        print(f"Saved global joint results: {out_file}")
        print(f"  Total rows: {len(results_df)}")

        # Save per-symbol/timeframe
        for symbol in symbols:
            for tf in timeframes:
                subset = results_df[
                    (results_df['symbol'] == symbol) &
                    (results_df['timeframe'] == tf)
                ]

                if len(subset) > 0:
                    out_file = output_dir / f"ofi_ms_joint_{symbol}_{tf}.csv"
                    subset.to_csv(out_file, index=False)
                    print(f"  Saved: {out_file}")

    print()
    print("=" * 80)
    print("Phase 6B complete!")
    print("=" * 80)


if __name__ == "__main__":
    config_path = Path("config/settings.yaml")
    run_phase6B_ofi_ms_joint(config_path)

