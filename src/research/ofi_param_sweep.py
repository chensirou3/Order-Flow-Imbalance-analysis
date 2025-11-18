"""
Phase 5: Parameter Optimization & Cost Overlay

This module coordinates:
1. Running trade-path simulations for a grid of parameters
2. Applying cost scenarios to each set of trades
3. Computing performance metrics per (symbol, timeframe, param_combo, cost_scenario)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm

from ..config_loader import get_config
from ..trading.trade_path_simulator import TradePathConfig, simulate_ofi_trade_paths_for_df
from ..utils.cost_utils import CostScenario, apply_cost_scenario_to_trades


@dataclass(frozen=True)
class ParamCombo:
    """
    Represents one parameter combination for testing.
    
    Attributes:
        entry_q_high: High quantile threshold (e.g., 0.8)
        entry_q_low: Low quantile threshold (e.g., 0.2)
        hmax_bars: Maximum holding period in bars
        tp_R: Optional static take profit in R-multiples (None = no TP)
    """
    entry_q_high: float
    entry_q_low: float
    hmax_bars: int
    tp_R: Optional[float]
    
    def to_id(self) -> str:
        """
        Return a unique string identifier.
        
        Examples:
            "qh0.80_ql0.20_hmax150_tpNone"
            "qh0.85_ql0.15_hmax100_tp2.0"
        """
        tp_str = f"tp{self.tp_R}" if self.tp_R is not None else "tpNone"
        return f"qh{self.entry_q_high:.2f}_ql{self.entry_q_low:.2f}_hmax{self.hmax_bars}_{tp_str}"
    
    def __repr__(self) -> str:
        return self.to_id()


def generate_param_combos_from_config(cfg) -> List[ParamCombo]:
    """
    Read ofi_param_sweep settings from config and build a list of ParamCombo objects.

    Args:
        cfg: Config dict with ofi_param_sweep section

    Returns:
        List of ParamCombo objects representing all combinations
    """
    sweep_cfg = cfg['ofi_param_sweep']

    combos = []
    for q_high, q_low in sweep_cfg['ofi_quantile_sets']:
        for hmax in sweep_cfg['hmax_candidates']:
            for tp_R in sweep_cfg['tp_R_levels']:
                combos.append(ParamCombo(
                    entry_q_high=q_high,
                    entry_q_low=q_low,
                    hmax_bars=hmax,
                    tp_R=tp_R
                ))

    return combos


def compute_performance_metrics(
    trades_df: pd.DataFrame,
    cost_scenarios: List[CostScenario]
) -> Dict:
    """
    Compute performance metrics for a set of trades under different cost scenarios.
    
    Args:
        trades_df: DataFrame with gross trade results
        cost_scenarios: List of CostScenario objects
    
    Returns:
        Dictionary with metrics for gross and each cost scenario
    """
    if trades_df.empty:
        metrics = {
            'n_trades': 0,
            'n_long': 0,
            'n_short': 0,
        }
        # Add placeholders for each cost scenario
        for scenario in cost_scenarios:
            metrics[f'mean_final_R_net_{scenario.name}'] = np.nan
            metrics[f'sharpe_R_net_{scenario.name}'] = np.nan
        return metrics
    
    # Apply cost scenarios
    trades_with_costs = trades_df.copy()
    for scenario in cost_scenarios:
        trades_with_costs = apply_cost_scenario_to_trades(trades_with_costs, scenario)
    
    # Basic counts
    metrics = {
        'n_trades': len(trades_df),
        'n_long': (trades_df['direction'] == 1).sum(),
        'n_short': (trades_df['direction'] == -1).sum(),
    }
    
    # Gross metrics
    metrics['mean_final_R_gross'] = trades_df['final_R'].mean()
    metrics['median_final_R_gross'] = trades_df['final_R'].median()
    metrics['std_final_R_gross'] = trades_df['final_R'].std()
    metrics['sharpe_R_gross'] = (
        trades_df['final_R'].mean() / trades_df['final_R'].std()
        if trades_df['final_R'].std() > 0 else 0
    )
    metrics['win_rate_gross'] = (trades_df['final_R'] > 0).mean()
    
    # Net metrics for each cost scenario
    for scenario in cost_scenarios:
        net_col = f'final_R_net_{scenario.name}'
        cost_col = f'cost_R_{scenario.name}'
        
        metrics[f'mean_cost_R_{scenario.name}'] = trades_with_costs[cost_col].mean()
        metrics[f'mean_final_R_net_{scenario.name}'] = trades_with_costs[net_col].mean()
        metrics[f'median_final_R_net_{scenario.name}'] = trades_with_costs[net_col].median()
        metrics[f'std_final_R_net_{scenario.name}'] = trades_with_costs[net_col].std()
        metrics[f'sharpe_R_net_{scenario.name}'] = (
            trades_with_costs[net_col].mean() / trades_with_costs[net_col].std()
            if trades_with_costs[net_col].std() > 0 else 0
        )
        metrics[f'win_rate_net_{scenario.name}'] = (trades_with_costs[net_col] > 0).mean()
    
    # MFE/MAE statistics
    metrics['median_MFE_R'] = trades_df['MFE_R'].median()
    metrics['p75_MFE_R'] = trades_df['MFE_R'].quantile(0.75)
    metrics['p90_MFE_R'] = trades_df['MFE_R'].quantile(0.90)
    metrics['median_MAE_R'] = trades_df['MAE_R'].median()

    # Time statistics
    metrics['median_bars_held'] = trades_df['bars_held'].median()
    metrics['mean_bars_held'] = trades_df['bars_held'].mean()

    # Exit reason distribution
    metrics['pct_stop'] = (trades_df['exit_reason'] == 'stop').mean()
    metrics['pct_tp_hit'] = (trades_df['exit_reason'] == 'tp_hit').mean()
    metrics['pct_hmax'] = (trades_df['exit_reason'] == 'hmax').mean()
    metrics['pct_end_of_data'] = (trades_df['exit_reason'] == 'end_of_data').mean()

    return metrics


def run_param_sweep_for_symbol_tf(
    symbol: str,
    timeframe: str,
    combos: List[ParamCombo],
    cost_scenarios: List[CostScenario],
    config
) -> pd.DataFrame:
    """
    Run parameter sweep for a given (symbol, timeframe) pair.

    For each ParamCombo:
    1. Build TradePathConfig
    2. Run simulate_ofi_trade_paths_for_df() to get gross trades
    3. For each cost scenario, apply costs and compute metrics
    4. Store one row per (symbol, timeframe, ParamCombo, cost_scenario)

    Args:
        symbol: Symbol name (e.g., "BTCUSD")
        timeframe: Timeframe (e.g., "8H")
        combos: List of ParamCombo objects to test
        cost_scenarios: List of CostScenario objects
        config: Config dict

    Returns:
        DataFrame with one row per parameter combination
    """
    # Load base bar+OFI data
    bars_pattern = config['ofi_param_sweep']['paths']['bars_with_ofi_pattern']
    bars_path = bars_pattern.format(symbol=symbol, tf=timeframe)

    print(f"\n{'='*80}")
    print(f"Processing {symbol} {timeframe}")
    print(f"Loading data from: {bars_path}")

    try:
        df = pd.read_csv(bars_path, index_col=0, parse_dates=True)
        print(f"Loaded {len(df)} bars")
    except FileNotFoundError:
        print(f"WARNING: File not found: {bars_path}")
        return pd.DataFrame()

    # Get base config settings
    base_cfg = config['ofi_trade_path']

    results = []

    for combo in tqdm(combos, desc=f"{symbol} {timeframe}", leave=False):
        # Build TradePathConfig for this combo
        cfg = TradePathConfig(
            entry_mode=base_cfg['entry_mode'],
            entry_q_high=combo.entry_q_high,
            entry_q_low=combo.entry_q_low,
            atr_period=base_cfg['atr_period'],
            atr_method=base_cfg['atr_method'],
            hmax_bars=combo.hmax_bars,
            tp_R=combo.tp_R,
            position_size=base_cfg['fixed_position_size'],
            save_paths=False
        )

        # Run simulation
        try:
            trades_df = simulate_ofi_trade_paths_for_df(symbol, timeframe, df, cfg)
        except Exception as e:
            print(f"ERROR in simulation for {combo}: {e}")
            continue

        # Compute metrics
        metrics = compute_performance_metrics(trades_df, cost_scenarios)

        # Build result row
        row = {
            'symbol': symbol,
            'timeframe': timeframe,
            'param_combo_id': combo.to_id(),
            'entry_q_high': combo.entry_q_high,
            'entry_q_low': combo.entry_q_low,
            'hmax_bars': combo.hmax_bars,
            'tp_R': combo.tp_R if combo.tp_R is not None else np.nan,
        }
        row.update(metrics)

        results.append(row)

    return pd.DataFrame(results)


def run_phase5_param_sweep(config_path: Path) -> None:
    """
    High-level runner for Phase 5 parameter sweep.

    Steps:
    1. Load config
    2. Build CostScenario objects from config
    3. Build ParamCombo list from config
    4. For each symbol/timeframe:
       - Run parameter sweep
       - Save per-(symbol,timeframe) CSV
    5. Concatenate all results into global DataFrame
    6. Save global results and rankings

    Args:
        config_path: Path to config/settings.yaml
    """
    print("="*80)
    print("Phase 5: Parameter Optimization & Cost Overlay")
    print("="*80)

    # Load config
    config = get_config(config_path)
    sweep_cfg = config['ofi_param_sweep']

    # Build cost scenarios
    cost_scenarios = [
        CostScenario(name=sc['name'], per_side_rate=sc['per_side_rate'])
        for sc in sweep_cfg['cost_scenarios']
    ]
    print(f"\nCost scenarios: {cost_scenarios}")

    # Build parameter combinations
    combos = generate_param_combos_from_config(config)
    print(f"\nParameter combinations: {len(combos)}")
    print(f"  - OFI quantile sets: {sweep_cfg['ofi_quantile_sets']}")
    print(f"  - Hmax candidates: {sweep_cfg['hmax_candidates']}")
    print(f"  - TP_R levels: {sweep_cfg['tp_R_levels']}")

    # Create output directory
    output_dir = Path(sweep_cfg['paths']['sweep_results_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    # Run sweep for each symbol/timeframe
    all_results = []

    for symbol in sweep_cfg['symbols']:
        for timeframe in sweep_cfg['timeframes']:
            # Run sweep
            results_df = run_param_sweep_for_symbol_tf(
                symbol, timeframe, combos, cost_scenarios, config
            )

            if results_df.empty:
                print(f"WARNING: No results for {symbol} {timeframe}")
                continue

            # Save per-(symbol,timeframe) results
            output_file = output_dir / f"ofi_param_sweep_{symbol}_{timeframe}.csv"
            results_df.to_csv(output_file, index=False)
            print(f"Saved: {output_file} ({len(results_df)} rows)")

            all_results.append(results_df)

    if not all_results:
        print("\nERROR: No results generated!")
        return

    # Concatenate all results
    global_df = pd.concat(all_results, ignore_index=True)

    # Save global results
    global_file = output_dir / "ofi_param_sweep_all_configs.csv"
    global_df.to_csv(global_file, index=False)
    print(f"\n{'='*80}")
    print(f"Saved global results: {global_file}")
    print(f"Total rows: {len(global_df)}")

    # Create rankings
    print(f"\n{'='*80}")
    print("Creating rankings...")

    # Sort by different metrics
    rankings = []

    for scenario in cost_scenarios:
        net_col = f'mean_final_R_net_{scenario.name}'
        sharpe_col = f'sharpe_R_net_{scenario.name}'

        # Rank by net expectancy
        ranked = global_df.sort_values(net_col, ascending=False).copy()
        ranked[f'rank_by_{net_col}'] = range(1, len(ranked) + 1)

        # Rank by Sharpe
        ranked_sharpe = global_df.sort_values(sharpe_col, ascending=False).copy()
        ranked[f'rank_by_{sharpe_col}'] = range(1, len(ranked_sharpe) + 1)

        rankings.append(ranked)

    # Save rankings
    ranking_file = output_dir / "ofi_param_sweep_ranking.csv"

    # Use the first cost scenario's ranking as the main ranking
    main_ranking = rankings[0] if rankings else global_df
    main_ranking.to_csv(ranking_file, index=False)
    print(f"Saved rankings: {ranking_file}")

    # Print top 10 by high_cost net expectancy
    if cost_scenarios:
        high_cost_scenario = [s for s in cost_scenarios if 'high' in s.name.lower()]
        if high_cost_scenario:
            net_col = f'mean_final_R_net_{high_cost_scenario[0].name}'
            top10 = global_df.nlargest(10, net_col)

            print(f"\n{'='*80}")
            print(f"Top 10 by {net_col}:")
            print("="*80)

            display_cols = [
                'symbol', 'timeframe', 'param_combo_id', 'n_trades',
                net_col, f'sharpe_R_net_{high_cost_scenario[0].name}',
                'median_MFE_R', 'pct_tp_hit', 'pct_stop'
            ]

            print(top10[display_cols].to_string(index=False))

    print(f"\n{'='*80}")
    print("Phase 5 parameter sweep complete!")
    print("="*80)

