"""Run OFI single-factor analysis.

This script:
1. Reads configuration from config/settings.yaml
2. For each symbol:
   - Loads bars_with_ofi data from results/{symbol}_4h_bars_with_ofi.csv
   - Adds future returns for configured horizons
   - Runs sanity checks on OFI distribution
   - Runs conditional return analysis (high/low OFI_z groups)
   - Runs quantile bin analysis
   - Saves results to results/sanity/ and results/single_factor/
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_config
from src.research.ofi_single_factor import run_ofi_single_factor_for_symbol


def main():
    """Main entry point for OFI single-factor analysis."""
    print("=" * 80)
    print("OFI Single-Factor Analysis")
    print("=" * 80)
    print()
    
    # Load config
    config = get_config()
    
    symbols = config['symbols']
    horizons = config['analysis']['horizons']
    quantile_low = config['analysis']['quantile_low']
    quantile_high = config['analysis']['quantile_high']
    n_bins = config['analysis']['n_bins']
    
    print(f"Configuration:")
    print(f"  Symbols: {symbols}")
    print(f"  Horizons: {horizons}")
    print(f"  Quantile thresholds: low={quantile_low}, high={quantile_high}")
    print(f"  Number of bins: {n_bins}")
    print()
    
    # Process each symbol
    for symbol in symbols:
        print("-" * 80)
        print(f"Analyzing {symbol}")
        print("-" * 80)
        
        try:
            run_ofi_single_factor_for_symbol(symbol)
            print()
            
        except Exception as e:
            print(f"[{symbol}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()
            continue
    
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)
    print()
    print("Results saved to:")
    print("  - results/sanity/ofi_R0_sanity_{symbol}.md")
    print("  - results/single_factor/ofi_R1_single_factor_{symbol}.csv")
    print("  - results/single_factor/ofi_R1_bins_{symbol}.csv")


if __name__ == "__main__":
    main()

