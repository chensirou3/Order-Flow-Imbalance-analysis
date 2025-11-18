"""Load tick data from partitioned Parquet files.

This module handles loading tick data from a partitioned directory structure:
    data/ticks/symbol=XXX/date=YYYY-MM-DD/*.parquet

Author: OFI Research Project
"""

from pathlib import Path
from typing import Optional
import pandas as pd


def load_partitioned_parquet_ticks(
    symbol: str,
    ticks_dir: Path,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Load tick data from partitioned Parquet files.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSD')
        ticks_dir: Base directory containing partitioned data
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    
    Returns:
        DataFrame with columns: timestamp, bid, ask, volume
        - timestamp: datetime64[ns, UTC]
        - bid: float
        - ask: float
        - volume: float (derived from bid_size + ask_size)
    
    Raises:
        FileNotFoundError: If no data found for symbol
        ValueError: If data format is invalid
    """
    symbol_dir = ticks_dir / f"symbol={symbol}"
    
    if not symbol_dir.exists():
        raise FileNotFoundError(f"No data found for symbol {symbol} in {ticks_dir}")
    
    # Find all date partitions
    date_dirs = sorted([d for d in symbol_dir.iterdir() if d.is_dir() and d.name.startswith("date=")])
    
    if not date_dirs:
        raise FileNotFoundError(f"No date partitions found for {symbol}")
    
    # Filter by date range if specified
    if start_date or end_date:
        filtered_dirs = []
        for date_dir in date_dirs:
            date_str = date_dir.name.replace("date=", "")
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            filtered_dirs.append(date_dir)
        date_dirs = filtered_dirs
    
    if not date_dirs:
        raise FileNotFoundError(f"No data found for {symbol} in date range {start_date} to {end_date}")
    
    print(f"[{symbol}] Found {len(date_dirs)} date partitions")
    print(f"[{symbol}] Date range: {date_dirs[0].name.replace('date=', '')} to {date_dirs[-1].name.replace('date=', '')}")
    
    # Load all parquet files
    dfs = []
    for date_dir in date_dirs:
        parquet_files = list(date_dir.glob("*.parquet"))
        for pq_file in parquet_files:
            try:
                df = pd.read_parquet(pq_file)
                dfs.append(df)
            except Exception as e:
                print(f"[{symbol}] Warning: Failed to load {pq_file}: {e}")
                continue
    
    if not dfs:
        raise ValueError(f"No valid parquet files found for {symbol}")
    
    # Concatenate all data
    df = pd.concat(dfs, ignore_index=True)
    print(f"[{symbol}] Loaded {len(df):,} ticks from {len(dfs)} files")
    
    # Validate required columns
    required_cols = ['ts', 'bid', 'ask']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Rename and prepare columns
    df = df.rename(columns={'ts': 'timestamp'})
    
    # Calculate volume from bid_size and ask_size if available
    if 'bid_size' in df.columns and 'ask_size' in df.columns:
        df['volume'] = df['bid_size'] + df['ask_size']
    else:
        # If no size columns, use a default volume of 1.0
        print(f"[{symbol}] Warning: No bid_size/ask_size columns, using volume=1.0")
        df['volume'] = 1.0
    
    # Select and order columns
    df = df[['timestamp', 'bid', 'ask', 'volume']].copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert to UTC if not already
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    elif str(df['timestamp'].dt.tz) != 'UTC':
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Remove duplicates
    n_before = len(df)
    df = df.drop_duplicates(subset=['timestamp'], keep='first')
    n_after = len(df)
    if n_before > n_after:
        print(f"[{symbol}] Removed {n_before - n_after:,} duplicate timestamps")

    # Remove rows with NaN in critical columns
    df = df.dropna(subset=['timestamp', 'bid', 'ask'])

    # Set timestamp as index (required for resample operations)
    df = df.set_index('timestamp')

    print(f"[{symbol}] Final dataset: {len(df):,} ticks")
    print(f"[{symbol}] Time range: {df.index.min()} to {df.index.max()}")

    return df


def convert_to_csv_format(df: pd.DataFrame, output_path: Path) -> None:
    """Convert loaded parquet data to CSV format expected by existing code.
    
    Args:
        df: DataFrame from load_partitioned_parquet_ticks
        output_path: Path to save CSV file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} ticks to {output_path}")

