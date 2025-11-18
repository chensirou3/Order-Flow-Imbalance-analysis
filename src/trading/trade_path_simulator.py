"""
Phase 4.2: Trade Path Simulation

Simulate individual trades with detailed path tracking:
- Entry based on OFI_z signals
- Exit when loss_in_R <= -MFE_R or Hmax bars reached
- Track MFE, MAE, t_MFE, final R, exit reason, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional


class Trade:
    """Represents a single trade with path tracking."""
    
    def __init__(
        self,
        entry_idx: int,
        entry_time: pd.Timestamp,
        entry_price: float,
        direction: int,  # 1 for long, -1 for short
        atr: float,
        position_size: float = 1.0
    ):
        self.entry_idx = entry_idx
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction
        self.atr = atr
        self.position_size = position_size
        
        # Path tracking
        self.bars_held = 0
        self.mfe = 0.0  # Maximum Favorable Excursion (in price)
        self.mae = 0.0  # Maximum Adverse Excursion (in price)
        self.mfe_r = 0.0  # MFE in R-multiples
        self.mae_r = 0.0  # MAE in R-multiples
        self.t_mfe = 0  # Time (bars) to reach MFE
        self.t_mae = 0  # Time (bars) to reach MAE
        
        # Exit info
        self.exit_idx = None
        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None  # "stop", "hmax", or "end_of_data"
        self.final_r = None
        self.final_pnl = None
        
        # Path history (optional)
        self.path_history = []
    
    def update(self, bar_idx: int, bar_time: pd.Timestamp, high: float, low: float, close: float):
        """Update trade with new bar data."""
        self.bars_held += 1
        
        # Calculate excursions based on direction
        if self.direction == 1:  # Long
            favorable = high - self.entry_price
            adverse = low - self.entry_price
        else:  # Short
            favorable = self.entry_price - low
            adverse = self.entry_price - high
        
        # Update MFE
        if favorable > self.mfe:
            self.mfe = favorable
            self.mfe_r = favorable / self.atr if self.atr > 0 else 0
            self.t_mfe = self.bars_held
        
        # Update MAE
        if adverse < self.mae:
            self.mae = adverse
            self.mae_r = adverse / self.atr if self.atr > 0 else 0
            self.t_mae = self.bars_held
        
        # Current P&L in R
        current_pnl = (close - self.entry_price) * self.direction
        current_r = current_pnl / self.atr if self.atr > 0 else 0
        
        return current_r
    
    def close(self, exit_idx: int, exit_time: pd.Timestamp, exit_price: float, exit_reason: str):
        """Close the trade."""
        self.exit_idx = exit_idx
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        
        # Calculate final P&L
        self.final_pnl = (exit_price - self.entry_price) * self.direction * self.position_size
        self.final_r = self.final_pnl / (self.atr * self.position_size) if self.atr > 0 else 0
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary for DataFrame."""
        return {
            'entry_idx': self.entry_idx,
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'direction': self.direction,
            'atr': self.atr,
            'bars_held': self.bars_held,
            'mfe': self.mfe,
            'mae': self.mae,
            'mfe_r': self.mfe_r,
            'mae_r': self.mae_r,
            't_mfe': self.t_mfe,
            't_mae': self.t_mae,
            'exit_idx': self.exit_idx,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'exit_reason': self.exit_reason,
            'final_r': self.final_r,
            'final_pnl': self.final_pnl,
        }


def simulate_trade_paths(
    df: pd.DataFrame,
    hmax_bars: int = 150,
    position_size: float = 1.0,
    save_paths: bool = False
) -> pd.DataFrame:
    """
    Simulate trades based on signals in the dataframe.
    
    Exit rule: Exit when loss_in_R <= -MFE_R or when Hmax bars reached.
    
    Parameters
    ----------
    df : pd.DataFrame
        Trading data with 'signal', 'ATR', OHLC columns
        Index should be datetime
    hmax_bars : int
        Maximum holding period in bars
    position_size : float
        Fixed position size (notional)
    save_paths : bool
        Whether to save bar-by-bar path history
    
    Returns
    -------
    pd.DataFrame
        Trade summary with one row per trade
    """
    trades = []
    active_trade = None
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        bar_time = df.index[idx]
        
        # Check if we have an active trade
        if active_trade is not None:
            # Update trade with current bar
            current_r = active_trade.update(
                idx, bar_time, row['high'], row['low'], row['close']
            )
            
            # Check exit conditions
            exit_triggered = False
            exit_reason = None

            # Exit condition 1: Loss from peak (loss_in_R <= -MFE_R)
            # This means: if we've made profit (MFE_R > 0), exit if we give it all back
            if active_trade.mfe_r > 0:
                loss_from_peak = current_r - active_trade.mfe_r
                if loss_from_peak <= -active_trade.mfe_r:
                    exit_triggered = True
                    exit_reason = "stop"

            # Exit condition 2: Maximum holding period
            if active_trade.bars_held >= hmax_bars:
                exit_triggered = True
                exit_reason = "hmax"

            # Exit condition 3: End of data
            if idx == len(df) - 1:
                exit_triggered = True
                exit_reason = "end_of_data"

            # Execute exit if triggered
            if exit_triggered:
                active_trade.close(idx, bar_time, row['close'], exit_reason)
                trades.append(active_trade)
                active_trade = None

        # Check for new entry signal (only if no active trade)
        if active_trade is None and row['signal'] != 0:
            # Skip if ATR is invalid
            if pd.isna(row['ATR']) or row['ATR'] <= 0:
                continue

            # Create new trade
            active_trade = Trade(
                entry_idx=idx,
                entry_time=bar_time,
                entry_price=row['close'],
                direction=int(row['signal']),
                atr=row['ATR'],
                position_size=position_size
            )

    # Convert trades to DataFrame
    if len(trades) == 0:
        return pd.DataFrame()

    trade_df = pd.DataFrame([t.to_dict() for t in trades])

    return trade_df


def analyze_trade_statistics(trade_df: pd.DataFrame) -> Dict:
    """
    Compute aggregate statistics from trade results.

    Parameters
    ----------
    trade_df : pd.DataFrame
        Trade summary from simulate_trade_paths

    Returns
    -------
    Dict
        Dictionary of statistics
    """
    if len(trade_df) == 0:
        return {
            'n_trades': 0,
            'n_long': 0,
            'n_short': 0,
        }

    stats = {
        # Basic counts
        'n_trades': len(trade_df),
        'n_long': (trade_df['direction'] == 1).sum(),
        'n_short': (trade_df['direction'] == -1).sum(),

        # Final R statistics
        'mean_r': trade_df['final_r'].mean(),
        'median_r': trade_df['final_r'].median(),
        'std_r': trade_df['final_r'].std(),
        'min_r': trade_df['final_r'].min(),
        'max_r': trade_df['final_r'].max(),

        # Win rate
        'win_rate': (trade_df['final_r'] > 0).mean(),
        'avg_win_r': trade_df[trade_df['final_r'] > 0]['final_r'].mean() if (trade_df['final_r'] > 0).any() else 0,
        'avg_loss_r': trade_df[trade_df['final_r'] <= 0]['final_r'].mean() if (trade_df['final_r'] <= 0).any() else 0,

        # MFE/MAE statistics
        'mean_mfe_r': trade_df['mfe_r'].mean(),
        'median_mfe_r': trade_df['mfe_r'].median(),
        'mean_mae_r': trade_df['mae_r'].mean(),
        'median_mae_r': trade_df['mae_r'].median(),

        # Time statistics
        'mean_bars_held': trade_df['bars_held'].mean(),
        'median_bars_held': trade_df['bars_held'].median(),
        'mean_t_mfe': trade_df['t_mfe'].mean(),
        'median_t_mfe': trade_df['t_mfe'].median(),

        # Exit reasons
        'pct_stop': (trade_df['exit_reason'] == 'stop').mean(),
        'pct_hmax': (trade_df['exit_reason'] == 'hmax').mean(),
        'pct_end_of_data': (trade_df['exit_reason'] == 'end_of_data').mean(),

        # Expectancy
        'expectancy_r': trade_df['final_r'].mean(),
        'sharpe_r': trade_df['final_r'].mean() / trade_df['final_r'].std() if trade_df['final_r'].std() > 0 else 0,
    }

    return stats

