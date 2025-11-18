"""
本地测试脚本 - 测试Phase 4代码

在单个配置上测试交易路径分析功能
"""

import sys
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.trading.ofi_signals import prepare_trading_data
from src.trading.trade_path_simulator import simulate_trade_paths, analyze_trade_statistics


def test_single_config():
    """测试单个配置"""
    
    print("="*80)
    print("Testing Phase 4: Trade Path Analysis")
    print("="*80)
    print()
    
    # Load configuration
    config_file = project_root / 'config' / 'settings.yaml'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    trade_path_config = config['ofi_trade_path']
    
    # Test with ETHUSD 1D (best performer from Phase 3)
    symbol = 'ETHUSD'
    timeframe = '1D'
    
    print(f"Testing: {symbol} {timeframe}")
    print()
    
    # Find data file
    data_file = project_root / 'results' / f'{symbol}_{timeframe}_merged_bars_with_ofi.csv'
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        print()
        print("Available files:")
        results_dir = project_root / 'results'
        for f in sorted(results_dir.glob('*_merged_bars_with_ofi.csv')):
            print(f"  {f.name}")
        return
    
    print(f"Loading data from: {data_file}")
    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    print(f"  Loaded {len(df)} bars")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    print()
    
    # Prepare trading data
    print("Preparing trading data...")
    df = prepare_trading_data(
        df,
        entry_mode=trade_path_config['entry_mode'],
        entry_q_high=trade_path_config['entry_q_high'],
        entry_q_low=trade_path_config['entry_q_low'],
        atr_period=trade_path_config['atr_period'],
        atr_method=trade_path_config['atr_method']
    )
    
    n_long = (df['signal'] == 1).sum()
    n_short = (df['signal'] == -1).sum()
    print(f"  Long signals: {n_long}")
    print(f"  Short signals: {n_short}")
    print(f"  Total signals: {n_long + n_short}")
    print()
    
    # Simulate trades
    print("Simulating trades...")
    trade_df = simulate_trade_paths(
        df,
        hmax_bars=trade_path_config['hmax_bars'],
        position_size=trade_path_config['fixed_position_size'],
        save_paths=trade_path_config['save_paths']
    )
    
    if len(trade_df) == 0:
        print("❌ No trades generated!")
        return
    
    print(f"  Generated {len(trade_df)} trades")
    print()
    
    # Analyze statistics
    print("Computing statistics...")
    stats = analyze_trade_statistics(trade_df)
    print()
    
    # Print results
    print("="*80)
    print("Results Summary")
    print("="*80)
    print()
    
    print(f"Trades:")
    print(f"  Total: {stats['n_trades']}")
    print(f"  Long: {stats['n_long']}")
    print(f"  Short: {stats['n_short']}")
    print()
    
    print(f"R-Multiple Statistics:")
    print(f"  Mean R: {stats['mean_r']:.3f}")
    print(f"  Median R: {stats['median_r']:.3f}")
    print(f"  Std R: {stats['std_r']:.3f}")
    print(f"  Min R: {stats['min_r']:.3f}")
    print(f"  Max R: {stats['max_r']:.3f}")
    print()
    
    print(f"Performance:")
    print(f"  Win Rate: {stats['win_rate']:.1%}")
    print(f"  Avg Win R: {stats['avg_win_r']:.3f}")
    print(f"  Avg Loss R: {stats['avg_loss_r']:.3f}")
    print(f"  Expectancy R: {stats['expectancy_r']:.3f}")
    print(f"  Sharpe R: {stats['sharpe_r']:.3f}")
    print()
    
    print(f"Excursions:")
    print(f"  Mean MFE_R: {stats['mean_mfe_r']:.3f}")
    print(f"  Median MFE_R: {stats['median_mfe_r']:.3f}")
    print(f"  Mean MAE_R: {stats['mean_mae_r']:.3f}")
    print(f"  Median MAE_R: {stats['median_mae_r']:.3f}")
    print()
    
    print(f"Timing:")
    print(f"  Mean Bars Held: {stats['mean_bars_held']:.1f}")
    print(f"  Median Bars Held: {stats['median_bars_held']:.1f}")
    print(f"  Mean t_MFE: {stats['mean_t_mfe']:.1f}")
    print(f"  Median t_MFE: {stats['median_t_mfe']:.1f}")
    print()
    
    print(f"Exit Reasons:")
    print(f"  Stop: {stats['pct_stop']:.1%}")
    print(f"  Hmax: {stats['pct_hmax']:.1%}")
    print(f"  End of Data: {stats['pct_end_of_data']:.1%}")
    print()
    
    # Show sample trades
    print("="*80)
    print("Sample Trades (first 5)")
    print("="*80)
    print()
    
    sample_cols = ['entry_time', 'direction', 'bars_held', 'mfe_r', 'mae_r', 'final_r', 'exit_reason']
    print(trade_df[sample_cols].head(5).to_string())
    print()
    
    # Save test results
    output_file = project_root / 'test_trade_path_results.csv'
    trade_df.to_csv(output_file, index=False)
    print(f"✅ Test results saved to: {output_file}")
    print()
    
    print("="*80)
    print("✅ Test completed successfully!")
    print("="*80)
    print()


if __name__ == '__main__':
    test_single_config()

