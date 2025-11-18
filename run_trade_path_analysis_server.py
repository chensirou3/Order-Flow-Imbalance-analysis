"""
服务器端运行脚本 - Phase 4 交易路径分析

带进度日志和实时监控功能
"""

import sys
from pathlib import Path
import pandas as pd
import yaml
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.research.ofi_trade_path_analysis import (
    analyze_single_config,
    create_rankings,
    generate_summary_report
)


class ProgressLogger:
    """进度日志记录器"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.start_time = time.time()
        
    def log(self, message: str, also_print: bool = True):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        
        if also_print:
            print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    def log_progress(self, current: int, total: int, item: str):
        """记录进度"""
        elapsed = time.time() - self.start_time
        pct = (current / total * 100) if total > 0 else 0
        
        if current > 0:
            avg_time = elapsed / current
            remaining = avg_time * (total - current)
            eta = datetime.fromtimestamp(time.time() + remaining).strftime('%H:%M:%S')
        else:
            eta = "N/A"
        
        message = f"Progress: [{current}/{total}] ({pct:.1f}%) - {item} - ETA: {eta}"
        self.log(message)


def main():
    """主执行函数"""
    
    # Setup logging
    log_file = project_root / 'trade_path_analysis.log'
    logger = ProgressLogger(log_file)
    
    logger.log("="*80)
    logger.log("OFI Trade Path Analysis - Phase 4 (Server Mode)")
    logger.log("="*80)
    logger.log("")
    
    # Load configuration
    config_file = project_root / 'config' / 'settings.yaml'
    logger.log(f"Loading configuration from: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Extract parameters
    symbols = config['trade_path_symbols']  # Only crypto and metals
    timeframes = config['timeframes']
    trade_path_config = config['ofi_trade_path']
    
    logger.log(f"Symbols: {symbols}")
    logger.log(f"Timeframes: {timeframes}")
    logger.log(f"Entry mode: {trade_path_config['entry_mode']}")
    logger.log(f"Total configurations: {len(symbols) * len(timeframes)}")
    logger.log("")
    
    # Setup paths
    results_dir = project_root / config['paths']['results_dir']
    output_dir = project_root / config['paths']['trade_path_dir']
    summary_dir = project_root / config['paths']['trade_summary_dir']
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each configuration
    all_stats = []
    all_trades = []
    
    total_configs = len(symbols) * len(timeframes)
    current = 0
    success_count = 0
    error_count = 0
    
    logger.log("="*80)
    logger.log("Starting analysis...")
    logger.log("="*80)
    logger.log("")
    
    for symbol in symbols:
        for timeframe in timeframes:
            current += 1
            
            # Log progress
            logger.log_progress(current, total_configs, f"{symbol} {timeframe}")
            
            # Construct data file path
            data_file = results_dir / f"{symbol}_{timeframe}_merged_bars_with_ofi.csv"
            
            if not data_file.exists():
                logger.log(f"  ⚠️  File not found: {data_file}")
                error_count += 1
                continue
            
            try:
                # Analyze this configuration
                trade_df, stats = analyze_single_config(
                    symbol=symbol,
                    timeframe=timeframe,
                    data_file=data_file,
                    config=trade_path_config,
                    save_trades=True,
                    output_dir=output_dir / 'individual_trades'
                )
                
                if len(trade_df) > 0:
                    # Add metadata
                    trade_df['symbol'] = symbol
                    trade_df['timeframe'] = timeframe
                    all_trades.append(trade_df)
                    all_stats.append(stats)
                    success_count += 1
                    
                    logger.log(f"  ✅ Success: {len(trade_df)} trades, Exp R: {stats['expectancy_r']:.3f}")
                else:
                    logger.log(f"  ⚠️  No trades generated")
                    error_count += 1
                
            except Exception as e:
                logger.log(f"  ❌ Error: {e}")
                error_count += 1
                import traceback
                logger.log(traceback.format_exc(), also_print=False)
                continue
            
            logger.log("")
    
    # Save results
    logger.log("="*80)
    logger.log("Saving results...")
    logger.log("="*80)
    
    if len(all_stats) > 0:
        # Create summary DataFrame
        summary_df = pd.DataFrame(all_stats)
        
        # Save summary statistics
        summary_file = summary_dir / 'trade_path_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        logger.log(f"✅ Summary statistics saved: {summary_file}")
        
        # Create and save rankings
        ranked_df = create_rankings(summary_df)
        ranked_file = summary_dir / 'trade_path_rankings.csv'
        ranked_df.to_csv(ranked_file, index=False)
        logger.log(f"✅ Rankings saved: {ranked_file}")
        
        # Generate markdown report
        report_file = summary_dir / 'trade_path_report.md'
        generate_summary_report(summary_df, report_file)
        logger.log(f"✅ Report saved: {report_file}")
    
    if len(all_trades) > 0:
        # Combine all trades
        trades_df = pd.concat(all_trades, ignore_index=True)
        all_trades_file = output_dir / 'all_trades.csv'
        trades_df.to_csv(all_trades_file, index=False)
        logger.log(f"✅ All trades saved: {all_trades_file} ({len(trades_df)} trades)")
    
    # Final summary
    logger.log("")
    logger.log("="*80)
    logger.log("Analysis Complete!")
    logger.log("="*80)
    logger.log(f"Total configurations: {total_configs}")
    logger.log(f"Successful: {success_count}")
    logger.log(f"Errors: {error_count}")
    logger.log(f"Total time: {(time.time() - logger.start_time)/60:.1f} minutes")
    logger.log("")


if __name__ == '__main__':
    main()

