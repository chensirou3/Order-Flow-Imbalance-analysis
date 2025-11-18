"""
Phase 4.1: OFI Signal Generation

Generate long/short entry signals based on OFI_z quantile thresholds.
"""

import pandas as pd
import numpy as np


def generate_ofi_signals(
    df: pd.DataFrame,
    entry_mode: str = "trend",
    entry_q_high: float = 0.8,
    entry_q_low: float = 0.2,
) -> pd.DataFrame:
    """
    Generate entry signals based on OFI_z quantiles.
    
    Parameters
    ----------
    df : pd.DataFrame
        Bar data with 'OFI_z' column
    entry_mode : str
        "trend" or "reversal"
        - "trend": high OFI_z → long, low OFI_z → short
        - "reversal": high OFI_z → short, low OFI_z → long
    entry_q_high : float
        Upper quantile threshold (e.g., 0.8 for 80th percentile)
    entry_q_low : float
        Lower quantile threshold (e.g., 0.2 for 20th percentile)
    
    Returns
    -------
    pd.DataFrame
        Input dataframe with added 'signal' column:
        - 1: long entry
        - -1: short entry
        - 0: no entry
    """
    df = df.copy()
    
    # Calculate quantile thresholds
    q_high_val = df['OFI_z'].quantile(entry_q_high)
    q_low_val = df['OFI_z'].quantile(entry_q_low)
    
    # Initialize signal column
    df['signal'] = 0
    
    if entry_mode == "trend":
        # Trend following: high OFI_z → long, low OFI_z → short
        df.loc[df['OFI_z'] >= q_high_val, 'signal'] = 1   # Long
        df.loc[df['OFI_z'] <= q_low_val, 'signal'] = -1   # Short
    
    elif entry_mode == "reversal":
        # Mean reversion: high OFI_z → short, low OFI_z → long
        df.loc[df['OFI_z'] >= q_high_val, 'signal'] = -1  # Short
        df.loc[df['OFI_z'] <= q_low_val, 'signal'] = 1    # Long
    
    else:
        raise ValueError(f"Unknown entry_mode: {entry_mode}. Must be 'trend' or 'reversal'.")
    
    return df


def compute_atr(
    df: pd.DataFrame,
    period: int = 20,
    method: str = "rolling_mean"
) -> pd.DataFrame:
    """
    Compute Average True Range (ATR) for R-multiple calculations.
    
    Parameters
    ----------
    df : pd.DataFrame
        Bar data with 'high', 'low', 'close' columns
    period : int
        ATR period (default: 20)
    method : str
        "rolling_mean" or "ema"
    
    Returns
    -------
    pd.DataFrame
        Input dataframe with added 'ATR' column
    """
    df = df.copy()
    
    # Calculate True Range
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift(1))
    low_close = np.abs(df['low'] - df['close'].shift(1))
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Calculate ATR
    if method == "rolling_mean":
        df['ATR'] = tr.rolling(window=period, min_periods=1).mean()
    elif method == "ema":
        df['ATR'] = tr.ewm(span=period, adjust=False).mean()
    else:
        raise ValueError(f"Unknown ATR method: {method}")
    
    return df


def prepare_trading_data(
    df: pd.DataFrame,
    entry_mode: str = "trend",
    entry_q_high: float = 0.8,
    entry_q_low: float = 0.2,
    atr_period: int = 20,
    atr_method: str = "rolling_mean"
) -> pd.DataFrame:
    """
    Prepare complete trading data with signals and ATR.
    
    This is a convenience function that combines signal generation and ATR calculation.
    
    Parameters
    ----------
    df : pd.DataFrame
        Bar data with OHLC and OFI_z
    entry_mode : str
        "trend" or "reversal"
    entry_q_high : float
        Upper quantile threshold
    entry_q_low : float
        Lower quantile threshold
    atr_period : int
        ATR period
    atr_method : str
        ATR calculation method
    
    Returns
    -------
    pd.DataFrame
        Complete trading data with 'signal' and 'ATR' columns
    """
    # Generate signals
    df = generate_ofi_signals(df, entry_mode, entry_q_high, entry_q_low)
    
    # Compute ATR
    df = compute_atr(df, atr_period, atr_method)
    
    return df

