"""
Phase 6C: Strategy Spec Generator

Convert top Phase 5 configurations into human-readable strategy specification documents.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import get_config


@dataclass
class StrategySpec:
    """Strategy specification data class."""
    name: str
    symbol: str
    timeframe: str
    entry_mode: str
    entry_q_high: float
    entry_q_low: float
    atr_period: int
    atr_method: str
    hmax_bars: int
    tp_R: float
    cost_low_rate: float
    cost_high_rate: float
    n_trades: int
    mean_final_R_net_low: float
    mean_final_R_net_high: float
    sharpe_R_net_low: float
    sharpe_R_net_high: float
    median_MFE_R: float
    p75_MFE_R: float
    p90_MFE_R: float
    median_MAE_R: float
    pct_stop: float
    pct_tp_hit: float
    pct_hmax: float
    win_rate_net_high: float


def load_top_configs(
    ranking_file: Path,
    top_n_per_symbol: int,
    ranking_metric: str = "mean_final_R_net_high_cost"
) -> pd.DataFrame:
    """
    Load top N configurations per symbol from Phase 5 ranking.
    
    Parameters
    ----------
    ranking_file : Path
        Path to ranking CSV
    top_n_per_symbol : int
        Number of top configs to select per symbol
    ranking_metric : str
        Metric to rank by
    
    Returns
    -------
    pd.DataFrame
        Top configurations
    """
    if not ranking_file.exists():
        raise FileNotFoundError(f"Ranking file not found: {ranking_file}")
    
    ranking_df = pd.read_csv(ranking_file)
    
    # Sort by ranking metric (descending)
    ranking_df = ranking_df.sort_values(ranking_metric, ascending=False)
    
    # Select top N per symbol
    top_configs = []
    for symbol in ranking_df['symbol'].unique():
        symbol_configs = ranking_df[ranking_df['symbol'] == symbol].head(top_n_per_symbol)
        top_configs.append(symbol_configs)
    
    return pd.concat(top_configs, ignore_index=True)


def create_strategy_spec(row: pd.Series, config: Dict) -> StrategySpec:
    """
    Create a StrategySpec object from a ranking row.
    
    Parameters
    ----------
    row : pd.Series
        Row from ranking DataFrame
    config : Dict
        Configuration dict
    
    Returns
    -------
    StrategySpec
        Strategy specification
    """
    # Build strategy name
    tp_str = f"TP{row['tp_R']:.1f}" if not pd.isna(row['tp_R']) else "TPNone"
    name = f"OFI_{row['symbol']}_{row['timeframe']}_qh{row['entry_q_high']:.2f}_ql{row['entry_q_low']:.2f}_H{int(row['hmax_bars'])}_{tp_str}"
    
    # Get cost rates from config
    cost_scenarios = config['ofi_param_sweep']['cost_scenarios']
    cost_low_rate = next(cs['per_side_rate'] for cs in cost_scenarios if cs['name'] == 'low_cost')
    cost_high_rate = next(cs['per_side_rate'] for cs in cost_scenarios if cs['name'] == 'high_cost')
    
    # Get entry mode from config (default to 'trend')
    entry_mode = config.get('ofi_trade_path', {}).get('entry_mode', 'trend')
    
    return StrategySpec(
        name=name,
        symbol=row['symbol'],
        timeframe=row['timeframe'],
        entry_mode=entry_mode,
        entry_q_high=row['entry_q_high'],
        entry_q_low=row['entry_q_low'],
        atr_period=int(row.get('atr_period', 20)),
        atr_method=row.get('atr_method', 'rolling_mean'),
        hmax_bars=int(row['hmax_bars']),
        tp_R=row['tp_R'] if not pd.isna(row['tp_R']) else None,
        cost_low_rate=cost_low_rate,
        cost_high_rate=cost_high_rate,
        n_trades=int(row['n_trades']),
        mean_final_R_net_low=row.get('mean_final_R_net_low_cost', np.nan),
        mean_final_R_net_high=row.get('mean_final_R_net_high_cost', np.nan),
        sharpe_R_net_low=row.get('sharpe_R_net_low_cost', np.nan),
        sharpe_R_net_high=row.get('sharpe_R_net_high_cost', np.nan),
        median_MFE_R=row.get('median_MFE_R', np.nan),
        p75_MFE_R=row.get('p75_MFE_R', np.nan),
        p90_MFE_R=row.get('p90_MFE_R', np.nan),
        median_MAE_R=row.get('median_MAE_R', np.nan),
        pct_stop=row.get('pct_stop', np.nan),
        pct_tp_hit=row.get('pct_tp_hit', np.nan),
        pct_hmax=row.get('pct_hmax', np.nan),
        win_rate_net_high=row.get('win_rate_net_high_cost', np.nan)
    )


def generate_strategy_markdown(spec: StrategySpec, include_sections: List[str]) -> str:
    """
    Generate markdown documentation for a strategy spec.

    Parameters
    ----------
    spec : StrategySpec
        Strategy specification
    include_sections : List[str]
        Which sections to include

    Returns
    -------
    str
        Markdown content
    """
    lines = []

    # Header
    lines.append(f"# {spec.name}")
    lines.append("")
    lines.append(f"**Strategy Type**: OFI-based Trend Following")
    lines.append(f"**Market**: {spec.symbol}")
    lines.append(f"**Timeframe**: {spec.timeframe}")
    lines.append(f"**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Overview
    if 'overview' in include_sections:
        lines.append("## Overview")
        lines.append("")
        lines.append(f"This strategy uses **Order Flow Imbalance (OFI)** as the primary signal to identify ")
        lines.append(f"high-probability {spec.entry_mode} opportunities in {spec.symbol} on {spec.timeframe} timeframe.")
        lines.append("")
        lines.append("**Key Characteristics**:")
        lines.append(f"- Entry mode: **{spec.entry_mode.upper()}**")
        lines.append(f"- Signal thresholds: OFI_z >= {spec.entry_q_high:.2f} (long) or <= {1-spec.entry_q_low:.2f} (short)")
        lines.append(f"- Maximum holding period: **{spec.hmax_bars} bars**")
        if spec.tp_R:
            lines.append(f"- Take profit: **{spec.tp_R}R**")
        else:
            lines.append(f"- Take profit: **None** (trailing exit only)")
        lines.append(f"- Historical trades: **{spec.n_trades}**")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Market & Timeframe
    if 'market_and_timeframe' in include_sections:
        lines.append("## Market & Timeframe")
        lines.append("")
        lines.append(f"**Symbol**: {spec.symbol}")
        lines.append("")
        if 'BTC' in spec.symbol or 'ETH' in spec.symbol:
            lines.append("**Asset Class**: Cryptocurrency")
            lines.append("")
            lines.append("Cryptocurrencies exhibit strong order flow dynamics due to:")
            lines.append("- High retail participation")
            lines.append("- Transparent order book data")
            lines.append("- 24/7 trading with continuous price discovery")
        elif 'XAU' in spec.symbol or 'XAG' in spec.symbol:
            lines.append("**Asset Class**: Precious Metals")
            lines.append("")
            lines.append("Precious metals show moderate OFI effectiveness due to:")
            lines.append("- Safe-haven flows during risk-off periods")
            lines.append("- Central bank activity")
        lines.append("")
        lines.append(f"**Timeframe**: {spec.timeframe}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Factor Construction
    if 'factor_construction' in include_sections:
        lines.append("## Factor Construction")
        lines.append("")
        lines.append("### Order Flow Imbalance (OFI)")
        lines.append("")
        lines.append("OFI measures the imbalance between buy and sell volume:")
        lines.append("")
        lines.append("```")
        lines.append("OFI_raw = (buy_volume - sell_volume) / (total_volume + ε)")
        lines.append("```")
        lines.append("")
        lines.append("**Standardization**:")
        lines.append("```")
        lines.append("OFI_z = (OFI_raw - rolling_mean(OFI_raw, 200)) / rolling_std(OFI_raw, 200)")
        lines.append("```")
        lines.append("")
        lines.append("**Interpretation**:")
        lines.append("- OFI_z > 0: Net buying pressure")
        lines.append("- OFI_z < 0: Net selling pressure")
        lines.append(f"- |OFI_z| >= {spec.entry_q_high:.2f} quantile: Strong signal")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Entry Rules
    if 'entry_rules' in include_sections:
        lines.append("## Entry Rules")
        lines.append("")
        lines.append(f"**Entry Mode**: {spec.entry_mode.upper()}")
        lines.append("")
        if spec.entry_mode == 'trend':
            lines.append("**Long Entry**:")
            lines.append(f"- OFI_z >= {spec.entry_q_high:.2f} quantile (strong buying pressure)")
            lines.append("- Direction: LONG (follow the order flow)")
            lines.append("")
            lines.append("**Short Entry**:")
            lines.append(f"- OFI_z <= {spec.entry_q_low:.2f} quantile (strong selling pressure)")
            lines.append("- Direction: SHORT (follow the order flow)")
        else:  # reversal
            lines.append("**Long Entry**:")
            lines.append(f"- OFI_z <= {spec.entry_q_low:.2f} quantile (extreme selling pressure)")
            lines.append("- Direction: LONG (fade the order flow)")
            lines.append("")
            lines.append("**Short Entry**:")
            lines.append(f"- OFI_z >= {spec.entry_q_high:.2f} quantile (extreme buying pressure)")
            lines.append("- Direction: SHORT (fade the order flow)")
        lines.append("")
        lines.append("**Position Sizing**:")
        lines.append("- Fixed notional: 1.0 unit")
        lines.append(f"- Risk per trade: 1 ATR ({spec.atr_period}-period {spec.atr_method})")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Exit Rules
    if 'exit_rules' in include_sections:
        lines.append("## Exit Rules")
        lines.append("")
        lines.append("**Exit Priority** (checked in order):")
        lines.append("")
        if spec.tp_R:
            lines.append(f"1. **Take Profit**: Exit when profit >= {spec.tp_R}R")
        else:
            lines.append(f"1. **Take Profit**: None (disabled)")
        lines.append(f"2. **Trailing Stop**: Exit when price gives back all MFE (Maximum Favorable Excursion)")
        lines.append(f"   - Trigger: current_R <= entry_R (i.e., loss_from_peak >= MFE_R)")
        lines.append(f"3. **Maximum Holding**: Exit after {spec.hmax_bars} bars")
        lines.append(f"4. **End of Data**: Exit at last available bar")
        lines.append("")
        lines.append("**Rationale**:")
        lines.append("- Trailing stop allows profits to run while protecting against full reversal")
        lines.append(f"- Hmax={spec.hmax_bars} prevents indefinite holding in sideways markets")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Transaction Costs
    if 'transaction_costs' in include_sections:
        lines.append("## Transaction Costs")
        lines.append("")
        lines.append("**Cost Model**: Per-side percentage of entry/exit price")
        lines.append("")
        lines.append("**Scenarios**:")
        lines.append(f"- **Low Cost**: {spec.cost_low_rate*100:.4f}% per side ({spec.cost_low_rate*2*100:.4f}% round-trip)")
        lines.append(f"- **High Cost**: {spec.cost_high_rate*100:.4f}% per side ({spec.cost_high_rate*2*100:.4f}% round-trip)")
        lines.append("")
        lines.append("**Cost Calculation**:")
        lines.append("```")
        lines.append("cost_price = per_side_rate × entry_price + per_side_rate × exit_price")
        lines.append("cost_R = cost_price / ATR_entry")
        lines.append("final_R_net = final_R_gross - cost_R")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Historical Performance
    if 'historical_performance' in include_sections:
        lines.append("## Historical Performance")
        lines.append("")
        lines.append("**Sample Period**: Based on available historical data")
        lines.append("")
        lines.append("### Key Metrics (High-Cost Scenario)")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Trades | {spec.n_trades} |")
        lines.append(f"| Mean R (Net) | {spec.mean_final_R_net_high:.3f} |")
        lines.append(f"| Sharpe Ratio | {spec.sharpe_R_net_high:.3f} |")
        if not pd.isna(spec.win_rate_net_high):
            lines.append(f"| Win Rate | {spec.win_rate_net_high*100:.1f}% |")
        lines.append(f"| Median MFE | {spec.median_MFE_R:.3f}R |")
        lines.append(f"| 75th pct MFE | {spec.p75_MFE_R:.3f}R |")
        lines.append(f"| 90th pct MFE | {spec.p90_MFE_R:.3f}R |")
        lines.append(f"| Median MAE | {spec.median_MAE_R:.3f}R |")
        lines.append("")
        lines.append("### Exit Reason Distribution")
        lines.append("")
        lines.append(f"| Exit Reason | Percentage |")
        lines.append(f"|-------------|------------|")
        lines.append(f"| Trailing Stop | {spec.pct_stop*100:.1f}% |")
        if spec.tp_R:
            lines.append(f"| Take Profit | {spec.pct_tp_hit*100:.1f}% |")
        lines.append(f"| Max Holding (Hmax) | {spec.pct_hmax*100:.1f}% |")
        lines.append("")
        lines.append("### Performance Comparison")
        lines.append("")
        lines.append(f"| Cost Scenario | Mean R (Net) | Sharpe Ratio |")
        lines.append(f"|---------------|--------------|--------------|")
        lines.append(f"| Low Cost ({spec.cost_low_rate*100:.4f}%) | {spec.mean_final_R_net_low:.3f} | {spec.sharpe_R_net_low:.3f} |")
        lines.append(f"| High Cost ({spec.cost_high_rate*100:.4f}%) | {spec.mean_final_R_net_high:.3f} | {spec.sharpe_R_net_high:.3f} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Notes & Caveats
    if 'notes_and_caveats' in include_sections:
        lines.append("## Notes & Caveats")
        lines.append("")
        lines.append("### Strengths")
        lines.append("")
        lines.append("- **Positive Expectancy**: Strategy shows positive expected R-multiple even under high costs")
        lines.append("- **Trend Capture**: Trailing exit allows capturing extended moves")
        lines.append("- **Risk Management**: Fixed R-multiple framework provides consistent risk sizing")
        lines.append("")
        lines.append("### Limitations")
        lines.append("")
        lines.append("- **Low Win Rate**: Typical of trend-following strategies (~5-10%)")
        lines.append("- **Requires Patience**: Long holding periods (up to Hmax bars)")
        lines.append("- **Market Regime Dependent**: Performance may vary across different market conditions")
        lines.append("- **Slippage Not Modeled**: Actual execution costs may be higher than modeled")
        lines.append("")
        lines.append("### Implementation Considerations")
        lines.append("")
        lines.append("1. **Data Quality**: Requires high-quality tick data for accurate OFI calculation")
        lines.append("2. **Execution**: Use limit orders where possible to minimize slippage")
        lines.append("3. **Position Sizing**: Consider portfolio-level risk management")
        lines.append("4. **Monitoring**: Track actual vs expected performance metrics")
        lines.append("5. **Regime Awareness**: Consider pausing strategy during extreme volatility events")
        lines.append("")
        lines.append("### Recommended Next Steps")
        lines.append("")
        lines.append("1. **Walk-Forward Testing**: Validate on out-of-sample data")
        lines.append("2. **Live Paper Trading**: Test execution infrastructure")
        lines.append("3. **Regime Analysis**: Analyze performance across different market regimes")
        lines.append("4. **Portfolio Integration**: Combine with other uncorrelated strategies")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer
    lines.append("## Disclaimer")
    lines.append("")
    lines.append("This strategy specification is for research and educational purposes only. ")
    lines.append("Past performance does not guarantee future results. ")
    lines.append("Always conduct thorough due diligence and risk assessment before deploying any trading strategy.")
    lines.append("")

    return "\n".join(lines)


def generate_index_markdown(specs: List[StrategySpec]) -> str:
    """
    Generate index markdown listing all strategy specs.

    Parameters
    ----------
    specs : List[StrategySpec]
        List of strategy specifications

    Returns
    -------
    str
        Index markdown content
    """
    lines = []

    lines.append("# Strategy Specifications Index")
    lines.append("")
    lines.append(f"**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total Strategies**: {len(specs)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This directory contains strategy specifications for the top-performing OFI-based ")
    lines.append("configurations identified in Phase 5 parameter optimization.")
    lines.append("")
    lines.append("Each strategy spec includes:")
    lines.append("- Market and timeframe details")
    lines.append("- Factor construction methodology")
    lines.append("- Entry and exit rules")
    lines.append("- Transaction cost modeling")
    lines.append("- Historical performance metrics")
    lines.append("- Implementation notes and caveats")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Strategy List")
    lines.append("")
    lines.append("| Strategy | Symbol | Timeframe | Entry Thresholds | Hmax | TP | Mean R (High Cost) | Sharpe |")
    lines.append("|----------|--------|-----------|------------------|------|----|--------------------|--------|")

    for spec in specs:
        tp_str = f"{spec.tp_R}R" if spec.tp_R else "None"
        lines.append(
            f"| [{spec.name}]({spec.name}.md) | "
            f"{spec.symbol} | {spec.timeframe} | "
            f"{spec.entry_q_high:.2f}/{spec.entry_q_low:.2f} | "
            f"{spec.hmax_bars} | {tp_str} | "
            f"{spec.mean_final_R_net_high:.3f} | "
            f"{spec.sharpe_R_net_high:.3f} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## By Symbol")
    lines.append("")

    # Group by symbol
    by_symbol = {}
    for spec in specs:
        if spec.symbol not in by_symbol:
            by_symbol[spec.symbol] = []
        by_symbol[spec.symbol].append(spec)

    for symbol in sorted(by_symbol.keys()):
        lines.append(f"### {symbol}")
        lines.append("")
        for spec in by_symbol[symbol]:
            lines.append(f"- [{spec.name}]({spec.name}.md) - {spec.timeframe} - Mean R: {spec.mean_final_R_net_high:.3f}")
        lines.append("")

    return "\n".join(lines)


def run_phase6C_strategy_spec_generation(config_path: Path) -> None:
    """
    Phase 6C main runner: Generate strategy specification documents.

    Parameters
    ----------
    config_path : Path
        Path to config YAML file
    """
    print("=" * 80)
    print("Phase 6C: Strategy Spec Generation")
    print("=" * 80)
    print()

    # Load config
    config = get_config(str(config_path))
    spec_cfg = config['phase6']['strategy_spec']

    ranking_file = Path(spec_cfg['ranking_file'])
    top_n = spec_cfg['top_n_per_symbol']
    ranking_metric = spec_cfg['ranking_metric']
    out_dir = Path(spec_cfg['out_dir'])
    include_sections = spec_cfg['include_sections']

    print(f"Ranking file: {ranking_file}")
    print(f"Top N per symbol: {top_n}")
    print(f"Ranking metric: {ranking_metric}")
    print(f"Output directory: {out_dir}")
    print()

    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load top configs
    print("Loading top configurations...")
    top_configs = load_top_configs(ranking_file, top_n, ranking_metric)
    print(f"  Selected {len(top_configs)} configurations")
    print()

    # Generate strategy specs
    specs = []
    for idx, row in top_configs.iterrows():
        spec = create_strategy_spec(row, config)
        specs.append(spec)

        print(f"Generating spec: {spec.name}")

        # Generate markdown
        markdown = generate_strategy_markdown(spec, include_sections)

        # Save to file
        spec_file = out_dir / f"{spec.name}.md"
        spec_file.write_text(markdown, encoding='utf-8')
        print(f"  Saved: {spec_file}")

    print()

    # Generate index
    print("Generating index...")
    index_markdown = generate_index_markdown(specs)
    index_file = out_dir / "INDEX.md"
    index_file.write_text(index_markdown, encoding='utf-8')
    print(f"  Saved: {index_file}")

    print()
    print("=" * 80)
    print(f"Phase 6C complete! Generated {len(specs)} strategy specs.")
    print("=" * 80)


if __name__ == "__main__":
    config_path = Path("config/settings.yaml")
    run_phase6C_strategy_spec_generation(config_path)

