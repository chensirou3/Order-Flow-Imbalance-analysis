"""OFI single-factor analysis and diagnostics."""

from pathlib import Path
from typing import List
import pandas as pd
import numpy as np

from ..utils.stats_utils import mean_std_t, simple_ols
from ..config_loader import get_config, resolve_path


def add_future_returns(df: pd.DataFrame, horizons: List[int]) -> pd.DataFrame:
    """Add future return columns for multiple horizons.
    
    Args:
        df: DataFrame with 'close' column
        horizons: List of forward periods (in bars)
        
    Returns:
        DataFrame with added columns 'fut_ret_H' for each horizon H
        where fut_ret_H = close[t+H] / close[t] - 1
    """
    df = df.copy()
    
    for H in horizons:
        df[f'fut_ret_{H}'] = df['close'].shift(-H) / df['close'] - 1
    
    return df


def sanity_check_ofi(df: pd.DataFrame, symbol: str, results_dir: Path) -> None:
    """Compute basic distribution stats and correlations for OFI.
    
    Args:
        df: DataFrame with OFI columns
        symbol: Symbol name
        results_dir: Directory to save results
        
    Outputs:
        Saves a markdown summary to results_dir/ofi_R0_sanity_{symbol}.md
        
    Includes:
        - Descriptive statistics for OFI_raw and OFI_z
        - Key percentiles of OFI_z (1%, 5%, 95%, 99%)
        - Correlation between OFI_z and volume
        - Correlation between |OFI_z| and intrabar range (high-low)
    """
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / f"ofi_R0_sanity_{symbol}.md"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# OFI Sanity Check: {symbol}\n\n")
        
        # Descriptive statistics
        f.write("## Descriptive Statistics\n\n")
        f.write("### OFI_raw\n\n")
        f.write(df['OFI_raw'].describe().to_string())
        f.write("\n\n")
        
        f.write("### OFI_z\n\n")
        f.write(df['OFI_z'].describe().to_string())
        f.write("\n\n")
        
        # Key percentiles of OFI_z
        f.write("## Key Percentiles of OFI_z\n\n")
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        pct_values = df['OFI_z'].quantile([p/100 for p in percentiles])
        f.write("| Percentile | OFI_z |\n")
        f.write("|------------|-------|\n")
        for p, val in zip(percentiles, pct_values):
            f.write(f"| {p}% | {val:.4f} |\n")
        f.write("\n")
        
        # Correlations
        f.write("## Correlations\n\n")
        
        # OFI_z vs volume
        corr_vol = df[['OFI_z', 'volume']].corr().iloc[0, 1]
        f.write(f"- **OFI_z vs Volume**: {corr_vol:.4f}\n")
        
        # |OFI_z| vs intrabar range
        df_temp = df.copy()
        df_temp['abs_OFI_z'] = df_temp['OFI_z'].abs()
        df_temp['range'] = df_temp['high'] - df_temp['low']
        corr_range = df_temp[['abs_OFI_z', 'range']].corr().iloc[0, 1]
        f.write(f"- **|OFI_z| vs Intrabar Range (high-low)**: {corr_range:.4f}\n")
        
        # OFI_z vs |return|
        df_temp['abs_ret'] = ((df_temp['close'] / df_temp['open']) - 1).abs()
        corr_abs_ret = df_temp[['abs_OFI_z', 'abs_ret']].corr().iloc[0, 1]
        f.write(f"- **|OFI_z| vs |Intrabar Return|**: {corr_abs_ret:.4f}\n")
        
        f.write("\n")
        
        # Data coverage
        f.write("## Data Coverage\n\n")
        f.write(f"- Total bars: {len(df):,}\n")
        f.write(f"- Non-NaN OFI_z: {df['OFI_z'].notna().sum():,}\n")
        f.write(f"- Coverage: {df['OFI_z'].notna().sum() / len(df) * 100:.2f}%\n")
        
    print(f"[{symbol}] Sanity check saved to {output_path}")


def analyze_ofi_single_factor(
    df: pd.DataFrame,
    symbol: str,
    horizons: List[int],
    results_dir: Path,
    quantile_low: float = 0.10,
    quantile_high: float = 0.90,
    n_bins: int = 5,
) -> None:
    """Single-factor conditional return analysis for OFI_z.

    Args:
        df: DataFrame with OFI_z and future return columns
        symbol: Symbol name
        horizons: List of horizons to analyze
        results_dir: Directory to save results
        quantile_low: Low quantile threshold for OFI_z
        quantile_high: High quantile threshold for OFI_z
        n_bins: Number of bins for quantile analysis

    Outputs:
        - results_dir/ofi_R1_single_factor_{symbol}.csv: Conditional returns and regressions
        - results_dir/ofi_R1_bins_{symbol}.csv: Quantile bin analysis

    Analysis:
        For each horizon H:
        - Define high_ofi = OFI_z >= quantile_high
        - Define low_ofi = OFI_z <= quantile_low
        - Compute N, mean, std, t-stat for each group
        - Run OLS: fut_ret_H ~ OFI_z
        - Bin OFI_z into n_bins quantiles and compute mean returns
    """
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Compute quantile thresholds
    q_lo = df['OFI_z'].quantile(quantile_low)
    q_hi = df['OFI_z'].quantile(quantile_high)

    print(f"[{symbol}] OFI_z quantile thresholds: low={q_lo:.4f}, high={q_hi:.4f}")

    # Results storage
    results = []

    for H in horizons:
        fut_ret_col = f'fut_ret_{H}'

        if fut_ret_col not in df.columns:
            print(f"[{symbol}] Warning: {fut_ret_col} not found, skipping horizon {H}")
            continue

        # Define groups
        high_ofi = df['OFI_z'] >= q_hi
        low_ofi = df['OFI_z'] <= q_lo

        # High OFI_z group
        high_returns = df.loc[high_ofi, fut_ret_col]
        mean_h, std_h, t_h, n_h = mean_std_t(high_returns)

        # Low OFI_z group
        low_returns = df.loc[low_ofi, fut_ret_col]
        mean_l, std_l, t_l, n_l = mean_std_t(low_returns)

        # OLS regression
        beta, t_beta = simple_ols(df['OFI_z'], df[fut_ret_col])

        results.append({
            'horizon': H,
            'group': 'high_ofi',
            'N': n_h,
            'mean_ret': mean_h,
            'std_ret': std_h,
            't_stat': t_h,
            'ols_beta': beta,
            'ols_t_stat': t_beta,
        })

        results.append({
            'horizon': H,
            'group': 'low_ofi',
            'N': n_l,
            'mean_ret': mean_l,
            'std_ret': std_l,
            't_stat': t_l,
            'ols_beta': np.nan,  # Only report once per horizon
            'ols_t_stat': np.nan,
        })

    # Save conditional returns
    results_df = pd.DataFrame(results)
    output_path = results_dir / f"ofi_R1_single_factor_{symbol}.csv"
    results_df.to_csv(output_path, index=False)
    print(f"[{symbol}] Single-factor analysis saved to {output_path}")

    # Quantile bin analysis
    bin_results = []

    for H in horizons:
        fut_ret_col = f'fut_ret_{H}'

        if fut_ret_col not in df.columns:
            continue

        # Create bins
        df_temp = df[['OFI_z', fut_ret_col]].dropna()
        df_temp['OFI_z_bin'] = pd.qcut(df_temp['OFI_z'], q=n_bins, labels=False, duplicates='drop')

        # Compute mean return for each bin
        for bin_idx in range(n_bins):
            bin_data = df_temp[df_temp['OFI_z_bin'] == bin_idx]

            if len(bin_data) > 0:
                mean_ret = bin_data[fut_ret_col].mean()
                n_obs = len(bin_data)
                ofi_z_min = bin_data['OFI_z'].min()
                ofi_z_max = bin_data['OFI_z'].max()

                bin_results.append({
                    'horizon': H,
                    'bin': bin_idx + 1,  # 1-indexed for readability
                    'N': n_obs,
                    'OFI_z_min': ofi_z_min,
                    'OFI_z_max': ofi_z_max,
                    'mean_ret': mean_ret,
                })

    # Save bin analysis
    bin_df = pd.DataFrame(bin_results)
    bin_output_path = results_dir / f"ofi_R1_bins_{symbol}.csv"
    bin_df.to_csv(bin_output_path, index=False)
    print(f"[{symbol}] Bin analysis saved to {bin_output_path}")


def run_ofi_single_factor_for_symbol(
    symbol: str,
    config_path: Path = None,
) -> None:
    """Convenience wrapper to run full OFI single-factor analysis for a symbol.

    Args:
        symbol: Symbol name
        config_path: Path to config file (optional)

    Steps:
        1. Load config
        2. Load bars_with_ofi CSV for the symbol
        3. Add future returns for configured horizons
        4. Run sanity_check_ofi
        5. Run analyze_ofi_single_factor
    """
    # Load config
    config = get_config(config_path)

    # Get parameters
    horizons = config['analysis']['horizons']
    quantile_low = config['analysis']['quantile_low']
    quantile_high = config['analysis']['quantile_high']
    n_bins = config['analysis']['n_bins']

    # Paths
    bars_with_ofi_dir = resolve_path(config['results_paths']['bars_with_ofi_dir'])
    sanity_dir = resolve_path(config['results_paths']['sanity_dir'])
    single_factor_dir = resolve_path(config['results_paths']['single_factor_dir'])

    # Load data
    data_path = bars_with_ofi_dir / f"{symbol}_4h_bars_with_ofi.csv"

    if not data_path.exists():
        print(f"[{symbol}] Error: Data file not found at {data_path}")
        print(f"[{symbol}] Please run build_bars_with_ofi.py first")
        return

    print(f"[{symbol}] Loading data from {data_path}...")
    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"[{symbol}] Loaded {len(df):,} bars")

    # Add future returns
    print(f"[{symbol}] Adding future returns for horizons {horizons}...")
    df = add_future_returns(df, horizons)

    # Run sanity check
    print(f"[{symbol}] Running sanity check...")
    sanity_check_ofi(df, symbol, sanity_dir)

    # Run single-factor analysis
    print(f"[{symbol}] Running single-factor analysis...")
    analyze_ofi_single_factor(
        df,
        symbol,
        horizons,
        single_factor_dir,
        quantile_low=quantile_low,
        quantile_high=quantile_high,
        n_bins=n_bins,
    )

    print(f"[{symbol}] Analysis complete!")

