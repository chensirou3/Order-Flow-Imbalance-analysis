# Phase 5 快速开始指南

## 🚀 快速运行

### 1. 确保数据准备就绪

Phase 5 需要 Phase 2 生成的合并数据文件：

```
results/BTCUSD_8H_merged_bars_with_ofi.csv
results/BTCUSD_4H_merged_bars_with_ofi.csv
results/BTCUSD_1D_merged_bars_with_ofi.csv
results/ETHUSD_8H_merged_bars_with_ofi.csv
results/ETHUSD_4H_merged_bars_with_ofi.csv
results/ETHUSD_1D_merged_bars_with_ofi.csv
```

### 2. 检查配置

查看 `config/settings.yaml` 中的 `ofi_param_sweep` 部分：

```yaml
ofi_param_sweep:
  symbols:
    - BTCUSD
    - ETHUSD
  
  timeframes:
    - 8H
    - 4H
    - 1D
  
  # ... 其他配置
```

### 3. 运行参数扫描

```bash
python scripts/run_ofi_param_sweep.py
```

### 4. 查看结果

结果保存在 `results/param_sweep/` 目录：

```
results/param_sweep/
├── ofi_param_sweep_BTCUSD_8H.csv      # BTCUSD 8H 的所有参数组合
├── ofi_param_sweep_BTCUSD_4H.csv      # BTCUSD 4H 的所有参数组合
├── ofi_param_sweep_ETHUSD_1D.csv      # ETHUSD 1D 的所有参数组合
├── ofi_param_sweep_all_configs.csv    # 全局汇总
└── ofi_param_sweep_ranking.csv        # 排名
```

## 📊 结果分析

### 查看Top 10配置

```python
import pandas as pd

# 读取全局结果
df = pd.read_csv('results/param_sweep/ofi_param_sweep_all_configs.csv')

# 按高成本净收益排序
top10 = df.nlargest(10, 'mean_final_R_net_high_cost')

# 显示关键列
cols = [
    'symbol', 'timeframe', 'param_combo_id',
    'n_trades', 'mean_final_R_net_high_cost',
    'sharpe_R_net_high_cost', 'pct_tp_hit'
]
print(top10[cols])
```

### 比较成本影响

```python
# 计算成本影响
df['cost_impact'] = (
    df['mean_final_R_net_low_cost'] - 
    df['mean_final_R_net_high_cost']
)

# 成本敏感性最低的配置
robust = df.nsmallest(10, 'cost_impact')
print(robust[['symbol', 'timeframe', 'param_combo_id', 'cost_impact']])
```

### 分析止盈效果

```python
# 无止盈 vs 有止盈
no_tp = df[df['tp_R'].isna()]
with_tp = df[df['tp_R'].notna()]

print("No TP:")
print(f"  Mean R (high cost): {no_tp['mean_final_R_net_high_cost'].mean():.4f}")
print(f"  Sharpe: {no_tp['sharpe_R_net_high_cost'].mean():.4f}")

print("\nWith TP:")
print(f"  Mean R (high cost): {with_tp['mean_final_R_net_high_cost'].mean():.4f}")
print(f"  Sharpe: {with_tp['sharpe_R_net_high_cost'].mean():.4f}")
```

## 🎯 关键指标说明

### 净收益指标

- `mean_final_R_net_low_cost` - 低成本场景下的平均净R
- `mean_final_R_net_high_cost` - 高成本场景下的平均净R
- `sharpe_R_net_low_cost` - 低成本Sharpe比率
- `sharpe_R_net_high_cost` - 高成本Sharpe比率

### 参数组合ID格式

```
qh0.80_ql0.20_hmax150_tpNone  # 无止盈
qh0.85_ql0.15_hmax100_tp2.0   # 2R止盈
qh0.75_ql0.25_hmax80_tp3.0    # 3R止盈
```

- `qh` = entry_q_high (高分位数阈值)
- `ql` = entry_q_low (低分位数阈值)
- `hmax` = 最大持仓bars
- `tp` = 止盈R (None = 无止盈)

### 出场原因

- `pct_stop` - 追踪止损出场比例
- `pct_tp_hit` - 止盈出场比例
- `pct_hmax` - 最大持仓出场比例
- `pct_end_of_data` - 数据结束比例

## 🔧 自定义配置

### 修改测试品种

编辑 `config/settings.yaml`:

```yaml
ofi_param_sweep:
  symbols:
    - BTCUSD
    - ETHUSD
    - XAUUSD  # 添加黄金
```

### 修改参数范围

```yaml
ofi_param_sweep:
  # 测试更多OFI阈值
  ofi_quantile_sets:
    - [0.80, 0.20]
    - [0.85, 0.15]
    - [0.75, 0.25]
    - [0.90, 0.10]  # 新增：更严格
  
  # 测试更多Hmax
  hmax_candidates:
    - 50   # 新增：更短
    - 80
    - 100
    - 150
    - 200  # 新增：更长
  
  # 测试更多TP水平
  tp_R_levels:
    - null
    - 1.5  # 新增
    - 2.0
    - 2.5  # 新增
    - 3.0
    - 4.0
```

### 修改成本场景

```yaml
ofi_param_sweep:
  cost_scenarios:
    - name: "ultra_low_cost"
      per_side_rate: 0.00001   # 0.001% per side
    - name: "low_cost"
      per_side_rate: 0.00003   # 0.003% per side
    - name: "medium_cost"
      per_side_rate: 0.0002    # 0.02% per side
    - name: "high_cost"
      per_side_rate: 0.0007    # 0.07% per side
```

## ⚠️ 注意事项

### 运行时间

- 每个配置约需 1-5 秒
- 总配置数 = symbols × timeframes × param_combos
- 默认: 2 × 3 × 36 = 216 个配置
- 预计总时间: 5-15 分钟

### 内存使用

- 每个配置加载完整的bar数据
- 建议至少 4GB 可用内存
- 如果内存不足，减少测试的symbol/timeframe数量

### 数据要求

- 必须有 `OFI_z` 列
- 必须有 `ATR` 列
- 必须有 OHLC 列 (`open`, `high`, `low`, `close`)
- 索引必须是 datetime

## 📈 预期输出示例

```
================================================================================
Phase 5: Parameter Optimization & Cost Overlay
================================================================================

Cost scenarios: [CostScenario(name='low_cost', rate=0.0030%), 
                 CostScenario(name='high_cost', rate=0.0700%)]

Parameter combinations: 36
  - OFI quantile sets: [[0.8, 0.2], [0.85, 0.15], [0.75, 0.25]]
  - Hmax candidates: [80, 100, 150]
  - TP_R levels: [None, 2.0, 3.0, 4.0]

Output directory: results/param_sweep

================================================================================
Processing BTCUSD 8H
Loading data from: results/BTCUSD_8H_merged_bars_with_ofi.csv
Loaded 3117 bars
BTCUSD 8H: 100%|████████████████████| 36/36 [00:12<00:00,  2.89it/s]
Saved: results/param_sweep/ofi_param_sweep_BTCUSD_8H.csv (36 rows)

...

================================================================================
Saved global results: results/param_sweep/ofi_param_sweep_all_configs.csv
Total rows: 216

================================================================================
Creating rankings...
Saved rankings: results/param_sweep/ofi_param_sweep_ranking.csv

================================================================================
Top 10 by mean_final_R_net_high_cost:
================================================================================
   symbol timeframe                    param_combo_id  n_trades  mean_final_R_net_high_cost  ...
0  BTCUSD        8H  qh0.80_ql0.20_hmax150_tpNone       138                    1.450  ...
1  BTCUSD        4H  qh0.85_ql0.15_hmax150_tp2.0        280                    1.220  ...
...

================================================================================
Phase 5 parameter sweep complete!
================================================================================
```

---

**现在您可以开始参数优化了！** 🚀

