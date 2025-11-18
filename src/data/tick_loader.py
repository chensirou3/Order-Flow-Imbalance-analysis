"""Tick data loading and cleaning utilities."""

from pathlib import Path
from typing import Literal
import pandas as pd
import numpy as np

TickMode = Literal["bid_ask", "price_only"]


def detect_tick_mode(df: pd.DataFrame) -> TickMode:
    """Detect whether tick data has bid/ask or single price.
    
    Args:
        df: DataFrame with tick data
        
    Returns:
        "bid_ask" if both 'bid' and 'ask' columns exist, else "price_only"
    """
    has_bid = 'bid' in df.columns
    has_ask = 'ask' in df.columns
    
    if has_bid and has_ask:
        return "bid_ask"
    else:
        return "price_only"


def load_and_clean_ticks(symbol: str, path: Path) -> pd.DataFrame:
    """Load raw tick data for a symbol and return a cleaned DataFrame.
    
    Args:
        symbol: Symbol name (for logging/error messages)
        path: Path to the tick CSV file
        
    Returns:
        Cleaned DataFrame with:
        - timestamp as DatetimeIndex (UTC)
        - sorted by timestamp ascending
        - duplicates removed
        - either (bid, ask, volume) or (price, volume) columns
        - volume column created if missing (default=1)
        
    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If required columns are missing
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Tick data file not found for {symbol}: {path}")
    
    # Load CSV
    df = pd.read_csv(path)
    
    # Check for timestamp column
    if 'timestamp' not in df.columns:
        raise ValueError(f"Missing 'timestamp' column in {symbol} tick data")
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Drop exact duplicates
    df = df.drop_duplicates()
    
    # Detect tick mode
    mode = detect_tick_mode(df)
    
    # Validate required columns based on mode
    if mode == "bid_ask":
        required_cols = ['bid', 'ask']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns for bid_ask mode in {symbol}: {missing}")
    else:
        if 'price' not in df.columns:
            raise ValueError(f"Missing 'price' column in {symbol} tick data")
    
    # Ensure volume column exists
    if 'volume' not in df.columns:
        df['volume'] = 1.0
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    return df

