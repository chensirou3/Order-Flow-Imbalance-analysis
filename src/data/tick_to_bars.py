"""Convert tick data to OHLCV bars."""

from pathlib import Path
import pandas as pd
import numpy as np

from .tick_loader import detect_tick_mode


def ticks_to_bars(ticks: pd.DataFrame, bar_size: str = "4H") -> pd.DataFrame:
    """Aggregate tick data into OHLCV bars.
    
    Args:
        ticks: DataFrame indexed by timestamp with columns:
            - either ['bid', 'ask', 'volume']
            - or ['price', 'volume']
        bar_size: Pandas resample frequency string (e.g., "4H", "1H", "30T")
        
    Returns:
        DataFrame indexed by bar end time with columns:
            ['open', 'high', 'low', 'close', 'volume', 'tick_count']
            
    Notes:
        - Mid price is computed as (bid+ask)/2 for bid_ask mode, or price for price_only mode
        - OHLC are computed from mid prices
        - volume is summed over the bar
        - tick_count is the number of ticks in each bar
    """
    # Detect tick mode
    mode = detect_tick_mode(ticks)
    
    # Compute mid price
    if mode == "bid_ask":
        mid = (ticks['bid'] + ticks['ask']) / 2.0
    else:
        mid = ticks['price']
    
    # Create a DataFrame with mid and volume
    df = pd.DataFrame({
        'mid': mid,
        'volume': ticks['volume']
    })
    
    # Resample to bars
    bars = df.resample(bar_size).agg({
        'mid': ['first', 'max', 'min', 'last', 'count'],
        'volume': 'sum'
    })
    
    # Flatten column names
    bars.columns = ['open', 'high', 'low', 'close', 'tick_count', 'volume']
    
    # Remove bars with no ticks
    bars = bars[bars['tick_count'] > 0].copy()
    
    return bars

