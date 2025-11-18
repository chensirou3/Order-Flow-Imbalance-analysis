"""
Phase 4.2 & 5: Trade Path Simulation

Simulate individual trades with detailed path tracking:
- Entry based on OFI_z signals
- Exit when loss_in_R <= -MFE_R or Hmax bars reached
- Phase 5: Added optional static TP (take profit) in R-multiples
- Track MFE, MAE, t_MFE, final R, exit reason, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class EntryMode(Enum):
    """Entry mode for OFI signals."""
    TREND = "trend"        # Q_high → long, Q_low → short
    REVERSAL = "reversal"  # Q_high → short, Q_low → long


@dataclass
class TradePathConfig:
    """
    Configuration for trade path simulation.

    Attributes:
        entry_mode: "trend" or "reversal"
        entry_q_high: High quantile threshold (e.g., 0.8)
        entry_q_low: Low quantile threshold (e.g., 0.2)
        atr_period: ATR calculation period
        atr_method: "rolling_mean" or "ema"
        hmax_bars: Maximum holding period in bars
        tp_R: Optional static take profit in R-multiples (None = no TP)
        position_size: Fixed position size (notional)
        save_paths: Whether to save bar-by-bar path history
    """
    entry_mode: str = "trend"
    entry_q_high: float = 0.8
    entry_q_low: float = 0.2
    atr_period: int = 20
    atr_method: str = "rolling_mean"
    hmax_bars: int = 150
    tp_R: Optional[float] = None  # New for Phase 5
    position_size: float = 1.0
    save_paths: bool = False


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
        self.exit_reason = None  # "stop", "tp_hit", "hmax", or "end_of_data"
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
    save_paths: bool = False,
    tp_R: Optional[float] = None
) -> pd.DataFrame:
    """
    Simulate trades based on signals in the dataframe.

    Exit rules:
    1. Static TP: If tp_R is set and current_R >= tp_R, exit with "tp_hit"
    2. Trailing stop: Exit when loss_in_R <= -MFE_R (give back all profit)
    3. Hmax: Exit when bars_held >= hmax_bars
    4. End of data

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
    tp_R : Optional[float]
        Static take profit level in R-multiples (None = no TP)

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

            # Exit condition 1: Static TP (Phase 5)
            if tp_R is not None and current_r >= tp_R:
                exit_triggered = True
                exit_reason = "tp_hit"

            # Exit condition 2: Loss from peak (loss_in_R <= -MFE_R)
            # This means: if we've made profit (MFE_R > 0), exit if we give it all back
            if not exit_triggered and active_trade.mfe_r > 0:
                loss_from_peak = current_r - active_trade.mfe_r
                if loss_from_peak <= -active_trade.mfe_r:
                    exit_triggered = True
                    exit_reason = "stop"

            # Exit condition 3: Maximum holding period
            if not exit_triggered and active_trade.bars_held >= hmax_bars:
                exit_triggered = True
                exit_reason = "hmax"

            # Exit condition 4: End of data
            if idx == len(df) - 1:
                exit_triggered = True
                if exit_reason is None:
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
        'pct_tp_hit': (trade_df['exit_reason'] == 'tp_hit').mean(),
        'pct_hmax': (trade_df['exit_reason'] == 'hmax').mean(),
        'pct_end_of_data': (trade_df['exit_reason'] == 'end_of_data').mean(),

        # Expectancy
        'expectancy_r': trade_df['final_r'].mean(),
        'sharpe_r': trade_df['final_r'].mean() / trade_df['final_r'].std() if trade_df['final_r'].std() > 0 else 0,
    }

    return stats


def simulate_ofi_trade_paths_for_df(
    symbol: str,
    timeframe: str,
    df: pd.DataFrame,
    cfg: TradePathConfig
) -> pd.DataFrame:
    """
    High-level wrapper for trade path simulation with TradePathConfig.

    This function is used by Phase 5 parameter sweep.

    Parameters
    ----------
    symbol : str
        Symbol name (e.g., "BTCUSD")
    timeframe : str
        Timeframe (e.g., "8H")
    df : pd.DataFrame
        Bar data with OFI_z and OHLC columns (ATR will be computed if missing)
    cfg : TradePathConfig
        Configuration object

    Returns
    -------
    pd.DataFrame
        Trade summary with columns:
        - symbol, timeframe
        - entry_time, exit_time, direction
        - entry_price, exit_price, ATR_entry
        - bars_held, MFE_R, MAE_R, t_MFE
        - final_R (gross, pre-cost)
        - exit_reason
    """
    # Ensure required columns exist (except ATR which we'll compute)
    required_cols = ['OFI_z', 'open', 'high', 'low', 'close']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Compute ATR if not present
    from ..trading.ofi_signals import compute_atr, generate_ofi_signals

    df_copy = df.copy()
    if 'ATR' not in df_copy.columns:
        df_copy = compute_atr(df_copy, period=cfg.atr_period, method=cfg.atr_method)

    # Generate signals based on OFI_z quantiles
    df_with_signals = generate_ofi_signals(
        df_copy,
        entry_mode=cfg.entry_mode,
        entry_q_high=cfg.entry_q_high,
        entry_q_low=cfg.entry_q_low
    )

    # Run simulation
    trades_df = simulate_trade_paths(
        df_with_signals,
        hmax_bars=cfg.hmax_bars,
        position_size=cfg.position_size,
        save_paths=cfg.save_paths,
        tp_R=cfg.tp_R
    )

    if trades_df.empty:
        return trades_df

    # Add symbol and timeframe
    trades_df['symbol'] = symbol
    trades_df['timeframe'] = timeframe

    # Rename columns to match expected output format
    trades_df = trades_df.rename(columns={
        'atr': 'ATR_entry',
        'mfe_r': 'MFE_R',
        'mae_r': 'MAE_R',
        't_mfe': 't_MFE',
        'final_r': 'final_R'
    })

    return trades_df
