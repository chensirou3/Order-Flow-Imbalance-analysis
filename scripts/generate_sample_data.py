"""Generate sample tick data for testing the OFI factor research project.

This script creates synthetic tick data that mimics real market data.
Use this for testing the system before you have real tick data.

Usage:
    python scripts/generate_sample_data.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import resolve_path


def generate_tick_data(
    symbol: str,
    start_date: str,
    n_ticks: int,
    base_price: float,
    volatility: float = 10.0,
    tick_freq: str = '30S',
    format_type: str = 'bid_ask',
) -> pd.DataFrame:
    """Generate synthetic tick data.
    
    Args:
        symbol: Symbol name
        start_date: Start date string
        n_ticks: Number of ticks to generate
        base_price: Starting price
        volatility: Price volatility (std of price changes)
        tick_freq: Frequency of ticks (pandas freq string)
        format_type: 'bid_ask' or 'price_only'
        
    Returns:
        DataFrame with synthetic tick data
    """
    print(f"Generating {n_ticks:,} ticks for {symbol}...")
    
    # Generate timestamps
    timestamps = pd.date_range(start_date, periods=n_ticks, freq=tick_freq)
    
    # Generate price path (random walk)
    np.random.seed(hash(symbol) % (2**32))  # Reproducible but different per symbol
    price_changes = np.random.randn(n_ticks) * volatility
    prices = base_price + np.cumsum(price_changes)
    
    # Ensure prices stay positive
    prices = np.maximum(prices, base_price * 0.5)
    
    # Generate volumes (exponential distribution)
    volumes = np.random.exponential(1.0, n_ticks)
    
    if format_type == 'bid_ask':
        # Add bid-ask spread (0.1% of price)
        spread = prices * 0.001
        bid = prices - spread / 2
        ask = prices + spread / 2
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'bid': bid,
            'ask': ask,
            'volume': volumes,
        })
    else:
        df = pd.DataFrame({
            'timestamp': timestamps,
            'price': prices,
            'volume': volumes,
        })
    
    return df


def main():
    """Generate sample data for configured symbols."""
    print("=" * 80)
    print("Sample Tick Data Generator")
    print("=" * 80)
    print()
    
    # Output directory
    ticks_dir = resolve_path('data/ticks')
    ticks_dir.mkdir(parents=True, exist_ok=True)
    
    # Define sample data configurations
    # Note: Need enough ticks to generate >200 bars for OFI_z calculation
    # At 30s intervals, 4H bars = 480 ticks per bar
    # For 250 bars: 250 * 480 = 120,000 ticks (about 35 days)
    configs = [
        {
            'symbol': 'BTCUSD',
            'start_date': '2024-01-01',
            'n_ticks': 150000,  # ~43 days at 30s intervals, ~260 bars
            'base_price': 42000.0,
            'volatility': 50.0,
            'format_type': 'bid_ask',
        },
        {
            'symbol': 'XAUUSD',
            'start_date': '2024-01-01',
            'n_ticks': 150000,  # ~43 days at 30s intervals, ~260 bars
            'base_price': 2050.0,
            'volatility': 2.0,
            'format_type': 'price_only',
        },
    ]
    
    for config in configs:
        symbol = config['symbol']
        print(f"Processing {symbol}...")
        
        # Generate data
        df = generate_tick_data(**config)
        
        # Save to CSV
        output_path = ticks_dir / f"{symbol}_ticks_sample.csv"
        df.to_csv(output_path, index=False)
        
        print(f"  Generated {len(df):,} ticks")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Saved to: {output_path}")
        print()
    
    print("=" * 80)
    print("Sample data generation complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the generated files in data/ticks/")
    print("  2. Run: python scripts/build_bars_with_ofi.py")
    print("  3. Run: python scripts/run_ofi_single_factor.py")


if __name__ == "__main__":
    main()

