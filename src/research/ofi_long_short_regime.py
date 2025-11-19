"""
Phase 6A: Long vs Short Leg Decomposition + Regime Analysis

Analyze OFI trade performance separately for:
1. Long vs Short legs
2. Different market regimes (trend, volatility)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import get_config


def compute_trade_metrics(trades_df: pd.DataFrame) -> Dict:
    """
    Compute performance metrics for a subset of trades.

    Parameters
    ----------
    trades_df : pd.DataFrame
        Trade data with columns: final_r, mfe_r, mae_r, t_mfe, exit_reason

    Returns
    -------
    Dict
        Performance metrics
    """
    if len(trades_df) == 0:
        return {
            'n_trades': 0,
            'mean_final_R_gross': np.nan,
            'sharpe_R_gross': np.nan,
            'median_MFE_R': np.nan,
            'p75_MFE_R': np.nan,
            'p90_MFE_R': np.nan,
            'median_MAE_R': np.nan,
            'median_t_MFE': np.nan,
            'pct_stop': np.nan,
            'pct_tp_hit': np.nan,
            'pct_hmax': np.nan,
            'pct_end_of_data': np.nan
        }

    # Basic metrics (use lowercase column names from Phase 4)
    n_trades = len(trades_df)
    mean_final_R = trades_df['final_r'].mean()
    std_final_R = trades_df['final_r'].std()
    sharpe_R = mean_final_R / std_final_R if std_final_R > 0 else np.nan

    # MFE/MAE metrics (use lowercase column names)
    median_MFE_R = trades_df['mfe_r'].median()
    p75_MFE_R = trades_df['mfe_r'].quantile(0.75)
    p90_MFE_R = trades_df['mfe_r'].quantile(0.90)
    median_MAE_R = trades_df['mae_r'].median()
    median_t_MFE = trades_df['t_mfe'].median()
    
    # Exit reason distribution
    exit_counts = trades_df['exit_reason'].value_counts()
    total = len(trades_df)
    pct_stop = exit_counts.get('stop', 0) / total
    pct_tp_hit = exit_counts.get('tp_hit', 0) / total
    pct_hmax = exit_counts.get('hmax', 0) / total
    pct_end_of_data = exit_counts.get('end_of_data', 0) / total
    
    return {
        'n_trades': n_trades,
        'mean_final_R_gross': mean_final_R,
        'sharpe_R_gross': sharpe_R,
        'median_MFE_R': median_MFE_R,
        'p75_MFE_R': p75_MFE_R,
        'p90_MFE_R': p90_MFE_R,
        'median_MAE_R': median_MAE_R,
        'median_t_MFE': median_t_MFE,
        'pct_stop': pct_stop,
        'pct_tp_hit': pct_tp_hit,
        'pct_hmax': pct_hmax,
        'pct_end_of_data': pct_end_of_data
    }


def analyze_long_short_legs(
    symbol: str,
    timeframe: str,
    trades_path: Path
) -> pd.DataFrame:
    """
    Analyze long vs short leg performance for a single symbol/timeframe.
    
    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    trades_path : Path
        Path to trade CSV file
    
    Returns
    -------
    pd.DataFrame
        Summary with long/short metrics
    """
    # Load trades
    if not trades_path.exists():
        print(f"  WARNING: Trade file not found: {trades_path}")
        return pd.DataFrame()
    
    trades_df = pd.read_csv(trades_path)
    
    if len(trades_df) == 0:
        print(f"  WARNING: No trades found in {trades_path}")
        return pd.DataFrame()
    
    # Split by direction
    long_trades = trades_df[trades_df['direction'] == 1]
    short_trades = trades_df[trades_df['direction'] == -1]
    
    # Compute metrics for each leg
    long_metrics = compute_trade_metrics(long_trades)
    short_metrics = compute_trade_metrics(short_trades)
    
    # Build summary
    summary = []
    for leg, metrics in [('long', long_metrics), ('short', short_metrics)]:
        row = {
            'symbol': symbol,
            'timeframe': timeframe,
            'leg': leg,
            **metrics
        }
        summary.append(row)
    
    return pd.DataFrame(summary)


def compute_regime_indicators(
    bars_df: pd.DataFrame,
    trend_ma_period: int = 200,
    vol_measure: str = "atr",
    high_vol_q: float = 0.7,
    low_vol_q: float = 0.3
) -> pd.DataFrame:
    """
    Compute trend and volatility regime indicators.

    Parameters
    ----------
    bars_df : pd.DataFrame
        Bar data with OHLC
    trend_ma_period : int
        MA period for trend regime
    vol_measure : str
        "atr" or "true_range_std"
    high_vol_q : float
        High volatility quantile threshold
    low_vol_q : float
        Low volatility quantile threshold

    Returns
    -------
    pd.DataFrame
        Bars with added regime columns
    """
    df = bars_df.copy()

    # Trend regime: close vs MA
    df['ma'] = df['close'].rolling(window=trend_ma_period).mean()
    df['trend_state'] = np.where(df['close'] > df['ma'], 'above_ma', 'below_ma')

    # Volatility regime
    if vol_measure == "atr":
        # Use ATR if available, otherwise compute it
        if 'ATR' not in df.columns:
            # Compute True Range
            df['prev_close'] = df['close'].shift(1)
            df['tr'] = df[['high', 'low', 'prev_close']].apply(
                lambda x: max(x['high'] - x['low'],
                            abs(x['high'] - x['prev_close']),
                            abs(x['low'] - x['prev_close'])),
                axis=1
            )
            df['vol_measure'] = df['tr'].rolling(window=20).mean()
            df = df.drop(columns=['prev_close', 'tr'])
        else:
            df['vol_measure'] = df['ATR']
    else:  # true_range_std
        df['prev_close'] = df['close'].shift(1)
        df['tr'] = df[['high', 'low', 'prev_close']].apply(
            lambda x: max(x['high'] - x['low'],
                        abs(x['high'] - x['prev_close']),
                        abs(x['low'] - x['prev_close'])),
            axis=1
        )
        df['vol_measure'] = df['tr'].rolling(window=20).std()
        df = df.drop(columns=['prev_close', 'tr'])

    # Compute volatility quantiles
    q_high = df['vol_measure'].quantile(high_vol_q)
    q_low = df['vol_measure'].quantile(low_vol_q)

    df['vol_regime'] = 'medium_vol'
    df.loc[df['vol_measure'] >= q_high, 'vol_regime'] = 'high_vol'
    df.loc[df['vol_measure'] <= q_low, 'vol_regime'] = 'low_vol'

    return df


def merge_trades_with_regimes(
    trades_df: pd.DataFrame,
    bars_with_regimes: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge trade data with regime information at entry time.

    Parameters
    ----------
    trades_df : pd.DataFrame
        Trade data with entry_time
    bars_with_regimes : pd.DataFrame
        Bar data with regime columns (indexed by timestamp)

    Returns
    -------
    pd.DataFrame
        Trades with regime columns added
    """
    # Ensure bars_with_regimes has timestamp index
    if 'timestamp' in bars_with_regimes.columns:
        bars_with_regimes = bars_with_regimes.set_index('timestamp')

    # Convert entry_time to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(trades_df['entry_time']):
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])

    # Merge on entry_time
    trades_with_regimes = trades_df.merge(
        bars_with_regimes[['trend_state', 'vol_regime']],
        left_on='entry_time',
        right_index=True,
        how='left'
    )

    return trades_with_regimes


def analyze_regime_performance(
    symbol: str,
    timeframe: str,
    trades_path: Path,
    bars_path: Path,
    config: Dict
) -> pd.DataFrame:
    """
    Analyze trade performance across different regimes.

    Parameters
    ----------
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    trades_path : Path
        Path to trade CSV
    bars_path : Path
        Path to bars with OFI CSV
    config : Dict
        Configuration dict

    Returns
    -------
    pd.DataFrame
        Regime-specific performance summary
    """
    # Load trades
    if not trades_path.exists():
        print(f"  WARNING: Trade file not found: {trades_path}")
        return pd.DataFrame()

    trades_df = pd.read_csv(trades_path, parse_dates=['entry_time', 'exit_time'])

    if len(trades_df) == 0:
        print(f"  WARNING: No trades found")
        return pd.DataFrame()

    # Load bars
    if not bars_path.exists():
        print(f"  WARNING: Bars file not found: {bars_path}")
        return pd.DataFrame()

    bars_df = pd.read_csv(bars_path, index_col=0, parse_dates=True)

    # Compute regime indicators
    regime_cfg = config['phase6']['long_short_regime']
    bars_with_regimes = compute_regime_indicators(
        bars_df,
        trend_ma_period=regime_cfg['trend']['ma_period'],
        vol_measure=regime_cfg['volatility']['vol_measure'],
        high_vol_q=regime_cfg['volatility']['high_vol_quantile'],
        low_vol_q=regime_cfg['volatility']['low_vol_quantile']
    )

    # Merge trades with regimes
    trades_with_regimes = merge_trades_with_regimes(trades_df, bars_with_regimes)

    # Analyze by regime combinations
    summary = []

    # Overall (no regime filter)
    overall_metrics = compute_trade_metrics(trades_with_regimes)
    summary.append({
        'symbol': symbol,
        'timeframe': timeframe,
        'leg': 'all',
        'trend_regime': 'all',
        'vol_regime': 'all',
        **overall_metrics
    })

    # By leg
    for leg_name, direction in [('long', 1), ('short', -1)]:
        leg_trades = trades_with_regimes[trades_with_regimes['direction'] == direction]
        leg_metrics = compute_trade_metrics(leg_trades)
        summary.append({
            'symbol': symbol,
            'timeframe': timeframe,
            'leg': leg_name,
            'trend_regime': 'all',
            'vol_regime': 'all',
            **leg_metrics
        })

    # By trend regime
    for trend_state in ['above_ma', 'below_ma']:
        trend_trades = trades_with_regimes[trades_with_regimes['trend_state'] == trend_state]
        trend_metrics = compute_trade_metrics(trend_trades)
        summary.append({
            'symbol': symbol,
            'timeframe': timeframe,
            'leg': 'all',
            'trend_regime': trend_state,
            'vol_regime': 'all',
            **trend_metrics
        })

    # By volatility regime
    for vol_state in ['high_vol', 'medium_vol', 'low_vol']:
        vol_trades = trades_with_regimes[trades_with_regimes['vol_regime'] == vol_state]
        vol_metrics = compute_trade_metrics(vol_trades)
        summary.append({
            'symbol': symbol,
            'timeframe': timeframe,
            'leg': 'all',
            'trend_regime': 'all',
            'vol_regime': vol_state,
            **vol_metrics
        })

    # By leg × trend regime
    for leg_name, direction in [('long', 1), ('short', -1)]:
        for trend_state in ['above_ma', 'below_ma']:
            subset = trades_with_regimes[
                (trades_with_regimes['direction'] == direction) &
                (trades_with_regimes['trend_state'] == trend_state)
            ]
            metrics = compute_trade_metrics(subset)
            summary.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'leg': leg_name,
                'trend_regime': trend_state,
                'vol_regime': 'all',
                **metrics
            })

    # By leg × volatility regime
    for leg_name, direction in [('long', 1), ('short', -1)]:
        for vol_state in ['high_vol', 'medium_vol', 'low_vol']:
            subset = trades_with_regimes[
                (trades_with_regimes['direction'] == direction) &
                (trades_with_regimes['vol_regime'] == vol_state)
            ]
            metrics = compute_trade_metrics(subset)
            summary.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'leg': leg_name,
                'trend_regime': 'all',
                'vol_regime': vol_state,
                **metrics
            })

    return pd.DataFrame(summary)


def run_phase6A_long_short_regime(config_path: Path) -> None:
    """
    Phase 6A main runner: Long/Short decomposition + Regime analysis.

    Parameters
    ----------
    config_path : Path
        Path to config YAML file
    """
    print("=" * 80)
    print("Phase 6A: Long vs Short Leg + Regime Analysis")
    print("=" * 80)
    print()

    # Load config
    config = get_config(str(config_path))
    phase6_cfg = config['phase6']['long_short_regime']

    symbols = phase6_cfg['symbols']
    timeframes = phase6_cfg['timeframes']

    # Create output directory
    output_dir = Path(phase6_cfg['paths']['long_short_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"Output directory: {output_dir}")
    print()

    all_long_short = []
    all_regime = []

    # Process each symbol/timeframe
    for symbol in symbols:
        for tf in timeframes:
            print(f"Processing {symbol} {tf}...")

            # Paths
            trades_pattern = phase6_cfg['paths']['trade_paths_pattern']
            bars_pattern = phase6_cfg['paths']['bars_with_ofi_pattern']

            trades_path = Path(trades_pattern.format(symbol=symbol, tf=tf))
            bars_path = Path(bars_pattern.format(symbol=symbol, tf=tf))

            # Long/Short analysis
            print(f"  Analyzing long/short legs...")
            long_short_summary = analyze_long_short_legs(symbol, tf, trades_path)

            if not long_short_summary.empty:
                # Save per-symbol/timeframe
                out_file = output_dir / f"ofi_long_short_summary_{symbol}_{tf}.csv"
                long_short_summary.to_csv(out_file, index=False)
                print(f"  Saved: {out_file}")

                all_long_short.append(long_short_summary)

            # Regime analysis
            print(f"  Analyzing regimes...")
            regime_summary = analyze_regime_performance(symbol, tf, trades_path, bars_path, config)

            if not regime_summary.empty:
                # Save per-symbol/timeframe
                out_file = output_dir / f"ofi_regime_summary_{symbol}_{tf}.csv"
                regime_summary.to_csv(out_file, index=False)
                print(f"  Saved: {out_file}")

                all_regime.append(regime_summary)

            print()

    # Concatenate all results
    if all_long_short:
        combined_long_short = pd.concat(all_long_short, ignore_index=True)
        out_file = output_dir / "ofi_long_short_all.csv"
        combined_long_short.to_csv(out_file, index=False)
        print(f"Saved combined long/short summary: {out_file}")
        print(f"  Total rows: {len(combined_long_short)}")

    if all_regime:
        combined_regime = pd.concat(all_regime, ignore_index=True)
        out_file = output_dir / "ofi_long_short_regime_all.csv"
        combined_regime.to_csv(out_file, index=False)
        print(f"Saved combined regime summary: {out_file}")
        print(f"  Total rows: {len(combined_regime)}")

    print()
    print("=" * 80)
    print("Phase 6A complete!")
    print("=" * 80)


if __name__ == "__main__":
    config_path = Path("config/settings.yaml")
    run_phase6A_long_short_regime(config_path)

