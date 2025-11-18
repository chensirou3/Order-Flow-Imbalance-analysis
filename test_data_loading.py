#!/usr/bin/env python3
"""
测试数据加载
"""
from src.data.parquet_tick_loader import load_partitioned_parquet_ticks
import pandas as pd
from pathlib import Path

print("=" * 60)
print("数据加载测试")
print("=" * 60)
print()

# 测试BTCUSD
print("测试读取 BTCUSD 数据...")
ticks_dir = Path('data/ticks')
df_btc = load_partitioned_parquet_ticks(
    'BTCUSD',
    ticks_dir,
    '2024-01-01',
    '2024-01-02'
)
print(f"✅ 成功读取 {len(df_btc):,} 条tick数据")
print(f"   列: {list(df_btc.columns)}")
print(f"   时间范围: {df_btc.index.min()} 到 {df_btc.index.max()}")
print()

# 测试XAUUSD
print("测试读取 XAUUSD 数据...")
df_xau = load_partitioned_parquet_ticks(
    'XAUUSD',
    ticks_dir,
    '2024-01-01',
    '2024-01-02'
)
print(f"✅ 成功读取 {len(df_xau):,} 条tick数据")
print(f"   时间范围: {df_xau.index.min()} 到 {df_xau.index.max()}")
print()

# 测试XAGUSD
print("测试读取 XAGUSD 数据...")
df_xag = load_partitioned_parquet_ticks(
    'XAGUSD',
    ticks_dir,
    '2024-01-01',
    '2024-01-02'
)
print(f"✅ 成功读取 {len(df_xag):,} 条tick数据")
print()

print("=" * 60)
print("✅ 所有数据读取测试通过！")
print("=" * 60)

