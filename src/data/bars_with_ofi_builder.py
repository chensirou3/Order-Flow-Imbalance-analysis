"""End-to-end builder for bars with OFI factor."""

from pathlib import Path
import pandas as pd

from .tick_loader import load_and_clean_ticks
from .tick_to_bars import ticks_to_bars
from ..factors.ofi import (
    add_mid_price, 
    label_tick_directions, 
    compute_ofi_bars, 
    standardize_ofi
)


def build_bars_with_ofi(
    symbol: str,
    ticks_path: Path,
    bar_size: str,
    bars_out_path: Path,
    ofi_window: int = 200,
) -> pd.DataFrame:
    """Full pipeline: ticks → bars + OFI factor.
    
    Args:
        symbol: Symbol name (for logging)
        ticks_path: Path to tick CSV file
        bar_size: Bar size for resampling (e.g., "4H")
        bars_out_path: Path to save output CSV
        ofi_window: Rolling window for OFI standardization
        
    Returns:
        DataFrame with columns:
            - OHLCV: open, high, low, close, volume, tick_count
            - OFI: OFI_raw, OFI_buy_vol, OFI_sell_vol, OFI_tot_vol
            - OFI_z: OFI_mean, OFI_std, OFI_z
            
    Steps:
        1. Load and clean ticks
        2. Add mid price
        3. Label tick directions (tick rule)
        4. Compute OFI bars (OFI_raw, volumes)
        5. Standardize OFI (OFI_z)
        6. Build bar OHLCV via ticks_to_bars
        7. Align/join bars and OFI on bar index
        8. Save to bars_out_path and return
    """
    print(f"[{symbol}] Loading tick data from {ticks_path}...")
    ticks = load_and_clean_ticks(symbol, ticks_path)
    print(f"[{symbol}] Loaded {len(ticks):,} ticks")
    
    print(f"[{symbol}] Adding mid price...")
    ticks = add_mid_price(ticks)
    
    print(f"[{symbol}] Labeling tick directions...")
    ticks = label_tick_directions(ticks)
    
    print(f"[{symbol}] Computing OFI bars...")
    ofi_bars = compute_ofi_bars(ticks, bar_size=bar_size)
    print(f"[{symbol}] Created {len(ofi_bars):,} OFI bars")
    
    print(f"[{symbol}] Standardizing OFI (window={ofi_window})...")
    ofi_bars = standardize_ofi(ofi_bars, window=ofi_window)
    
    print(f"[{symbol}] Building OHLCV bars...")
    bars = ticks_to_bars(ticks, bar_size=bar_size)
    print(f"[{symbol}] Created {len(bars):,} OHLCV bars")
    
    print(f"[{symbol}] Merging bars and OFI...")
    # Join on index (bar timestamp)
    result = bars.join(ofi_bars, how='inner')
    print(f"[{symbol}] Final dataset: {len(result):,} bars")
    
    # Save to CSV
    bars_out_path = Path(bars_out_path)
    bars_out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(bars_out_path)
    print(f"[{symbol}] Saved to {bars_out_path}")
    
    return result

