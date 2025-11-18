"""Order Flow Imbalance (OFI) factor calculation."""

import pandas as pd
import numpy as np
from typing import Tuple

from ..data.tick_loader import detect_tick_mode


def add_mid_price(ticks: pd.DataFrame) -> pd.DataFrame:
    """Ensure a 'mid' column exists using bid/ask or price.
    
    Args:
        ticks: DataFrame with either ['bid', 'ask'] or ['price'] columns
        
    Returns:
        DataFrame with added 'mid' column
        
    Notes:
        - If 'bid' and 'ask' exist: mid = (bid + ask) / 2
        - Else: mid = price
    """
    ticks = ticks.copy()
    
    mode = detect_tick_mode(ticks)
    
    if mode == "bid_ask":
        ticks['mid'] = (ticks['bid'] + ticks['ask']) / 2.0
    else:
        ticks['mid'] = ticks['price']
    
    return ticks


def label_tick_directions(ticks: pd.DataFrame) -> pd.DataFrame:
    """Apply the tick rule to label buyer/seller initiated trades.
    
    Args:
        ticks: DataFrame with at least a 'mid' column (or will be created)
        
    Returns:
        DataFrame with added columns:
            - 'mid': mid price
            - 'sign': +1 for buyer-initiated, -1 for seller-initiated
            - 'vol': volume used for OFI (from 'volume' column)
            
    Notes:
        Tick rule:
        - if mid[t] > mid[t-1] → sign[t] = +1 (buyer-initiated)
        - if mid[t] < mid[t-1] → sign[t] = -1 (seller-initiated)
        - if mid[t] == mid[t-1] → sign[t] = sign[t-1] (inherit previous)
        
        The first tick defaults to sign = +1.
    """
    ticks = ticks.copy()
    
    # Ensure mid price exists
    if 'mid' not in ticks.columns:
        ticks = add_mid_price(ticks)
    
    # Compute price changes
    mid = ticks['mid']
    mid_prev = mid.shift(1)
    
    # Apply tick rule
    sign = np.where(mid > mid_prev, 1, 
                    np.where(mid < mid_prev, -1, np.nan))
    
    # Convert to Series for forward fill
    sign = pd.Series(sign, index=ticks.index)
    
    # Forward fill to handle unchanged prices (inherit previous sign)
    sign = sign.fillna(method='ffill')
    
    # Fill any remaining NaN (first tick) with +1
    sign = sign.fillna(1)
    
    ticks['sign'] = sign.astype(int)
    
    # Copy volume to 'vol' for consistency
    ticks['vol'] = ticks['volume']
    
    return ticks


def compute_ofi_bars(
    ticks: pd.DataFrame,
    bar_size: str = "4H",
    eps: float = 1e-8,
) -> pd.DataFrame:
    """Aggregate tick-level order flow into bar-level OFI with OHLCV.

    Args:
        ticks: DataFrame with columns ['mid', 'sign', 'vol']
        bar_size: Pandas resample frequency string
        eps: Small constant to avoid division by zero

    Returns:
        DataFrame indexed by bar end time with columns:
            - 'open', 'high', 'low', 'close': OHLC from mid price
            - 'volume': total volume
            - 'OFI_raw': (buy_vol - sell_vol) / (tot_vol + eps)
            - 'OFI_buy_vol': total buy volume
            - 'OFI_sell_vol': total sell volume
            - 'OFI_tot_vol': total volume

    Notes:
        - buy_vol = sum(vol where sign = +1)
        - sell_vol = sum(vol where sign = -1)
        - OFI_raw ranges from -1 (all sells) to +1 (all buys)
    """
    # Ensure required columns exist
    required = ['mid', 'sign', 'vol']
    missing = [col for col in required if col not in ticks.columns]
    if missing:
        raise ValueError(f"Missing required columns for OFI computation: {missing}")

    # Separate buy and sell volumes
    buy_vol = ticks['vol'].where(ticks['sign'] == 1, 0)
    sell_vol = ticks['vol'].where(ticks['sign'] == -1, 0)

    # Create DataFrame for resampling with OHLCV
    df = pd.DataFrame({
        'mid': ticks['mid'],
        'buy_vol': buy_vol,
        'sell_vol': sell_vol,
        'tot_vol': ticks['vol']
    }, index=ticks.index)

    # Resample to bars - OHLCV
    ohlc = df['mid'].resample(bar_size).ohlc()
    volume = df['tot_vol'].resample(bar_size).sum()

    # Resample to bars - OFI components
    ofi_components = df[['buy_vol', 'sell_vol', 'tot_vol']].resample(bar_size).sum()

    # Combine OHLCV and OFI
    ofi_bars = pd.concat([ohlc, volume.rename('volume'), ofi_components], axis=1)

    # Compute OFI_raw
    ofi_bars['OFI_raw'] = (
        (ofi_bars['buy_vol'] - ofi_bars['sell_vol']) /
        (ofi_bars['tot_vol'] + eps)
    )

    # Rename OFI columns for clarity
    ofi_bars = ofi_bars.rename(columns={
        'buy_vol': 'OFI_buy_vol',
        'sell_vol': 'OFI_sell_vol',
        'tot_vol': 'OFI_tot_vol'
    })

    # Remove bars with no volume
    ofi_bars = ofi_bars[ofi_bars['volume'] > 0].copy()

    return ofi_bars


def standardize_ofi(ofi_bars: pd.DataFrame, window: int = 200) -> pd.DataFrame:
    """Compute rolling mean/std and z-score for OFI_raw.
    
    Args:
        ofi_bars: DataFrame with 'OFI_raw' column
        window: Rolling window size for mean and std calculation
        
    Returns:
        DataFrame with added columns:
            - 'OFI_mean': rolling mean of OFI_raw
            - 'OFI_std': rolling std of OFI_raw
            - 'OFI_z': (OFI_raw - OFI_mean) / OFI_std
            
    Notes:
        - Initial values (before window is full) will be NaN
        - OFI_z measures how extreme current OFI is relative to recent history
    """
    ofi_bars = ofi_bars.copy()
    
    if 'OFI_raw' not in ofi_bars.columns:
        raise ValueError("OFI_raw column not found in input DataFrame")
    
    # Compute rolling statistics
    ofi_bars['OFI_mean'] = ofi_bars['OFI_raw'].rolling(window=window).mean()
    ofi_bars['OFI_std'] = ofi_bars['OFI_raw'].rolling(window=window).std()
    
    # Compute z-score
    ofi_bars['OFI_z'] = (
        (ofi_bars['OFI_raw'] - ofi_bars['OFI_mean']) / 
        ofi_bars['OFI_std']
    )
    
    return ofi_bars

