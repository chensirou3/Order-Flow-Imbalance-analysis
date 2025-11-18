"""Generate visualizations for OFI analysis results."""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_loader import get_project_root


def main():
    project_root = get_project_root()
    results_dir = project_root / "results"
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Load summary data
    summary_file = results_dir / "OFI_FULL_SUMMARY.csv"
    if not summary_file.exists():
        print(f"Error: {summary_file} not found. Run generate_summary_report.py first.")
        return
    
    df = pd.read_csv(summary_file)
    
    print(f"Loaded {len(df)} configurations")
    
    # Plot 1: Spread by symbol and horizon
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('OFI Factor Performance: Spread (High OFI - Low OFI) by Symbol', fontsize=16)
    
    symbols = sorted(df['symbol'].unique())
    for idx, symbol in enumerate(symbols):
        ax = axes[idx // 3, idx % 3]
        symbol_data = df[df['symbol'] == symbol]
        
        for bar_size in sorted(symbol_data['bar_size'].unique()):
            data = symbol_data[symbol_data['bar_size'] == bar_size]
            ax.plot(data['horizon'], data['spread'] * 100, marker='o', label=bar_size)
        
        ax.set_title(f'{symbol}')
        ax.set_xlabel('Horizon')
        ax.set_ylabel('Spread (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plot1_file = plots_dir / "spread_by_symbol_horizon.png"
    plt.savefig(plot1_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {plot1_file}")
    plt.close()
    
    # Plot 2: T-statistics heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create pivot table for heatmap
    pivot_data = df.pivot_table(
        values='high_ofi_t_stat',
        index=['symbol', 'bar_size'],
        columns='horizon',
        aggfunc='mean'
    )
    
    im = ax.imshow(pivot_data.values, cmap='RdYlGn', aspect='auto', vmin=-2, vmax=6)
    
    # Set ticks
    ax.set_xticks(range(len(pivot_data.columns)))
    ax.set_xticklabels(pivot_data.columns)
    ax.set_yticks(range(len(pivot_data.index)))
    ax.set_yticklabels([f"{s[0]} {s[1]}" for s in pivot_data.index])
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('t-statistic', rotation=270, labelpad=20)
    
    # Add text annotations
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            value = pivot_data.values[i, j]
            if not pd.isna(value):
                text = ax.text(j, i, f'{value:.1f}',
                             ha="center", va="center", color="black", fontsize=8)
    
    ax.set_title('OFI Factor: t-statistics Heatmap (High OFI Group)', fontsize=14)
    ax.set_xlabel('Horizon')
    ax.set_ylabel('Symbol - Bar Size')
    
    plt.tight_layout()
    plot2_file = plots_dir / "t_statistics_heatmap.png"
    plt.savefig(plot2_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {plot2_file}")
    plt.close()
    
    # Plot 3: Top configurations bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    top_configs = df.nlargest(20, 'spread')
    labels = [f"{row.symbol}\n{row.bar_size}\nH={row.horizon}" 
              for row in top_configs.itertuples()]
    
    bars = ax.barh(range(len(top_configs)), top_configs['spread'] * 100)
    
    # Color bars by symbol
    colors = {'BTCUSD': 'orange', 'ETHUSD': 'purple', 'EURUSD': 'blue',
              'USDJPY': 'green', 'XAGUSD': 'gray', 'XAUUSD': 'gold'}
    for i, (bar, symbol) in enumerate(zip(bars, top_configs['symbol'])):
        bar.set_color(colors.get(symbol, 'gray'))
    
    ax.set_yticks(range(len(top_configs)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Spread: High OFI - Low OFI (%)', fontsize=12)
    ax.set_title('Top 20 Configurations by Spread', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color, label=symbol) 
                      for symbol, color in colors.items()]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plot3_file = plots_dir / "top20_configurations.png"
    plt.savefig(plot3_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {plot3_file}")
    plt.close()
    
    # Plot 4: Scatter plot - Spread vs t-statistic
    fig, ax = plt.subplots(figsize=(10, 8))
    
    for symbol in symbols:
        symbol_data = df[df['symbol'] == symbol]
        ax.scatter(symbol_data['spread'] * 100, symbol_data['high_ofi_t_stat'],
                  label=symbol, alpha=0.6, s=50)
    
    ax.set_xlabel('Spread: High OFI - Low OFI (%)', fontsize=12)
    ax.set_ylabel('t-statistic (High OFI)', fontsize=12)
    ax.set_title('OFI Factor: Spread vs Statistical Significance', fontsize=14)
    ax.axhline(y=1.96, color='r', linestyle='--', alpha=0.5, label='95% significance')
    ax.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plot4_file = plots_dir / "spread_vs_tstat.png"
    plt.savefig(plot4_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {plot4_file}")
    plt.close()
    
    print(f"\n✅ All plots saved to {plots_dir}/")
    print(f"\nGenerated plots:")
    print(f"  1. spread_by_symbol_horizon.png - Spread trends by symbol and horizon")
    print(f"  2. t_statistics_heatmap.png - Statistical significance heatmap")
    print(f"  3. top20_configurations.png - Best performing configurations")
    print(f"  4. spread_vs_tstat.png - Spread vs statistical significance")


if __name__ == "__main__":
    main()

