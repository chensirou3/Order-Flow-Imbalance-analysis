"""
Cost modeling utilities for Phase 5.

This module provides tools to overlay transaction costs on gross trade results.
"""

from dataclasses import dataclass
from typing import List
import pandas as pd
import numpy as np


@dataclass
class CostScenario:
    """
    Represents a transaction cost scenario.
    
    Attributes:
        name: Scenario name (e.g., "low_cost", "high_cost")
        per_side_rate: Cost per side as a fraction of price (e.g., 0.00003 = 0.003%)
    """
    name: str
    per_side_rate: float  # e.g., 0.00003 for 0.003%
    
    def __repr__(self) -> str:
        pct = self.per_side_rate * 100
        return f"CostScenario(name='{self.name}', rate={pct:.4f}%)"


def compute_round_trip_cost_R(row: pd.Series, scenario: CostScenario) -> float:
    """
    Compute the transaction cost in R-multiples for a single trade.
    
    Assumptions:
      - Cost per side = per_side_rate * price
      - Round trip cost in price units ≈ per_side_rate * entry_price + per_side_rate * exit_price
        We approximate it as 2 * per_side_rate * entry_price for simplicity
      - R-multiple = (PnL_price) / ATR_entry
      - So cost_R ≈ round_trip_cost_price / ATR_entry
    
    Args:
        row: A pandas Series containing:
            - 'entry_price': Entry price
            - 'exit_price': Exit price (optional, for more accurate calculation)
            - 'ATR_entry': ATR at entry
        scenario: CostScenario object
    
    Returns:
        Cost in R-multiples (always positive)
    
    Example:
        >>> row = pd.Series({'entry_price': 50000, 'exit_price': 51000, 'ATR_entry': 500})
        >>> scenario = CostScenario('low_cost', 0.00003)
        >>> cost_R = compute_round_trip_cost_R(row, scenario)
        >>> # cost_R ≈ (0.00003 * 50000 + 0.00003 * 51000) / 500 ≈ 6.06 / 500 ≈ 0.012
    """
    entry_price = row['entry_price']
    atr_entry = row['ATR_entry']
    
    if pd.isna(entry_price) or pd.isna(atr_entry) or atr_entry <= 0:
        return 0.0
    
    # More accurate: use both entry and exit prices
    if 'exit_price' in row and not pd.isna(row['exit_price']):
        exit_price = row['exit_price']
        # Round trip cost = entry cost + exit cost
        cost_price = scenario.per_side_rate * entry_price + scenario.per_side_rate * exit_price
    else:
        # Simplified: assume exit price ≈ entry price
        cost_price = 2.0 * scenario.per_side_rate * entry_price
    
    # Convert to R-multiples
    cost_R = cost_price / atr_entry
    
    return cost_R


def apply_cost_scenario_to_trades(
    trades_df: pd.DataFrame,
    scenario: CostScenario
) -> pd.DataFrame:
    """
    Apply a cost scenario to a DataFrame of gross trades.
    
    Given a gross trades_df (with 'final_R', 'entry_price', 'exit_price', 'ATR_entry'),
    compute:
      - 'cost_R_{scenario.name}': Cost in R-multiples
      - 'final_R_net_{scenario.name}': Net R = final_R - cost_R
    
    Args:
        trades_df: DataFrame with gross trade results. Must contain:
            - 'final_R': Gross R-multiple
            - 'entry_price': Entry price
            - 'ATR_entry': ATR at entry
            - 'exit_price': Exit price (optional)
        scenario: CostScenario object
    
    Returns:
        New DataFrame with additional columns:
            - 'cost_R_{scenario.name}'
            - 'final_R_net_{scenario.name}'
    
    Example:
        >>> trades = pd.DataFrame({
        ...     'final_R': [2.5, -0.8, 1.2],
        ...     'entry_price': [50000, 51000, 49000],
        ...     'exit_price': [51250, 50600, 49588],
        ...     'ATR_entry': [500, 510, 490]
        ... })
        >>> scenario = CostScenario('low_cost', 0.00003)
        >>> result = apply_cost_scenario_to_trades(trades, scenario)
        >>> # result will have 'cost_R_low_cost' and 'final_R_net_low_cost' columns
    """
    if trades_df.empty:
        # Return empty DataFrame with expected columns
        result = trades_df.copy()
        result[f'cost_R_{scenario.name}'] = []
        result[f'final_R_net_{scenario.name}'] = []
        return result
    
    # Make a copy to avoid modifying the original
    result = trades_df.copy()
    
    # Compute cost_R for each trade
    result[f'cost_R_{scenario.name}'] = result.apply(
        lambda row: compute_round_trip_cost_R(row, scenario),
        axis=1
    )
    
    # Compute net R
    result[f'final_R_net_{scenario.name}'] = (
        result['final_R'] - result[f'cost_R_{scenario.name}']
    )
    
    return result


def apply_multiple_cost_scenarios(
    trades_df: pd.DataFrame,
    scenarios: List[CostScenario]
) -> pd.DataFrame:
    """
    Apply multiple cost scenarios to a DataFrame of gross trades.
    
    Args:
        trades_df: DataFrame with gross trade results
        scenarios: List of CostScenario objects
    
    Returns:
        DataFrame with cost and net R columns for each scenario
    """
    result = trades_df.copy()
    
    for scenario in scenarios:
        result = apply_cost_scenario_to_trades(result, scenario)
    
    return result

