# Phase 5: Parameter Optimization & Cost Overlay

## 概述

Phase 5 在 Phase 4 的基础上，对最佳配置进行局部参数优化，并叠加交易成本分析。

**目标**:
- 识别稳健的局部最优参数
- 评估策略对成本的敏感性
- 找出在高成本场景下仍然盈利的配置

## 核心特性

### 1. 参数网格

我们系统地测试以下参数组合：

#### OFI_z 入场分位数
- `[0.80, 0.20]` - 基准（Phase 4使用）
- `[0.85, 0.15]` - 更严格的阈值
- `[0.75, 0.25]` - 更宽松的阈值

#### 最大持仓期 (Hmax)
- `80` bars - 较短持仓
- `100` bars - 中等持仓
- `150` bars - 基准（Phase 4使用）

#### 静态止盈 (TP in R)
- `null` - 无止盈，仅使用追踪止损（Phase 4方式）
- `2.0R` - 保守止盈
- `3.0R` - 中等止盈
- `4.0R` - 激进止盈

**总组合数**: 3 × 3 × 4 = 36 个参数组合

### 2. 成本场景

我们测试两种交易成本场景：

#### 低成本场景 (low_cost)
- **单边成本**: 0.003% (0.00003)
- **往返成本**: 0.006%
- **适用于**: 大型交易所、做市商账户、高流动性品种

#### 高成本场景 (high_cost)
- **单边成本**: 0.07% (0.0007)
- **往返成本**: 0.14%
- **适用于**: 小型交易所、普通账户、滑点较大的情况

### 3. 测试品种和周期

基于 Phase 4 的发现，我们专注于表现最佳的配置：

**品种**:
- BTCUSD
- ETHUSD

**周期**:
- 8H - BTCUSD最佳周期
- 4H - BTCUSD次佳周期
- 1D - ETHUSD最佳周期

**总配置数**: 2 symbols × 3 timeframes × 36 param combos = 216 个测试

## 实现细节

### 1. 成本计算

成本以 R-multiples 计算：

```python
# 往返成本（价格单位）
cost_price = per_side_rate * entry_price + per_side_rate * exit_price

# 转换为 R-multiples
cost_R = cost_price / ATR_entry

# 净收益
final_R_net = final_R_gross - cost_R
```

### 2. 止盈逻辑

新增静态止盈出场条件：

```python
# 在每个bar检查
if tp_R is not None and current_R >= tp_R:
    exit_triggered = True
    exit_reason = "tp_hit"
```

出场优先级：
1. **静态止盈** (tp_hit) - 如果设置了TP且达到
2. **追踪止损** (stop) - 从峰值回撤到入场点
3. **最大持仓** (hmax) - 达到Hmax bars
4. **数据结束** (end_of_data)

### 3. 性能指标

对每个参数组合，我们计算：

#### 基础指标
- `n_trades` - 交易数量
- `n_long` / `n_short` - 多空分布

#### 毛收益指标 (Gross)
- `mean_final_R_gross` - 平均R（成本前）
- `median_final_R_gross` - 中位数R
- `sharpe_R_gross` - Sharpe比率
- `win_rate_gross` - 胜率

#### 净收益指标 (Net) - 每个成本场景
- `mean_final_R_net_{scenario}` - 平均净R
- `median_final_R_net_{scenario}` - 中位数净R
- `sharpe_R_net_{scenario}` - 净Sharpe比率
- `win_rate_net_{scenario}` - 净胜率
- `mean_cost_R_{scenario}` - 平均成本R

#### 交易路径指标
- `median_MFE_R` - MFE中位数
- `p75_MFE_R` / `p90_MFE_R` - MFE分位数
- `median_MAE_R` - MAE中位数
- `median_bars_held` - 持仓时间中位数

#### 出场原因分布
- `pct_stop` - 追踪止损比例
- `pct_tp_hit` - 止盈比例
- `pct_hmax` - 最大持仓比例
- `pct_end_of_data` - 数据结束比例

## 使用方法

### 1. 配置

编辑 `config/settings.yaml`:

```yaml
ofi_param_sweep:
  symbols:
    - BTCUSD
    - ETHUSD
  
  timeframes:
    - 8H
    - 4H
    - 1D
  
  ofi_quantile_sets:
    - [0.80, 0.20]
    - [0.85, 0.15]
    - [0.75, 0.25]
  
  hmax_candidates:
    - 80
    - 100
    - 150
  
  tp_R_levels:
    - null
    - 2.0
    - 3.0
    - 4.0
```

### 2. 运行

```bash
python scripts/run_ofi_param_sweep.py
```

### 3. 输出文件

#### 单配置结果
```
results/param_sweep/ofi_param_sweep_BTCUSD_8H.csv
results/param_sweep/ofi_param_sweep_BTCUSD_4H.csv
results/param_sweep/ofi_param_sweep_ETHUSD_1D.csv
...
```

每个文件包含该配置下所有参数组合的性能指标。

#### 全局汇总
```
results/param_sweep/ofi_param_sweep_all_configs.csv
```

所有配置的完整结果。

#### 排名
```
results/param_sweep/ofi_param_sweep_ranking.csv
```

按不同指标排序的配置排名。

## 分析建议

### 1. 识别稳健参数

查找在两种成本场景下都表现良好的参数：

```python
import pandas as pd

df = pd.read_csv('results/param_sweep/ofi_param_sweep_all_configs.csv')

# 筛选在高成本下仍盈利的配置
profitable = df[df['mean_final_R_net_high_cost'] > 0]

# 按高成本净收益排序
top = profitable.nlargest(10, 'mean_final_R_net_high_cost')
```

### 2. 成本敏感性分析

比较低成本和高成本场景的差异：

```python
df['cost_impact'] = (
    df['mean_final_R_net_low_cost'] - df['mean_final_R_net_high_cost']
)

# 成本敏感性最低的配置
robust = df.nsmallest(10, 'cost_impact')
```

### 3. 止盈效果分析

比较有TP和无TP的表现：

```python
no_tp = df[df['tp_R'].isna()]
with_tp = df[df['tp_R'].notna()]

print("No TP mean R:", no_tp['mean_final_R_net_high_cost'].mean())
print("With TP mean R:", with_tp['mean_final_R_net_high_cost'].mean())
```

## 预期发现

基于 Phase 4 的结果，我们预期：

1. **BTCUSD 8H** 在多数参数组合下表现优异
2. **较长的Hmax** (150) 可能优于较短的 (80)
3. **适度的止盈** (2-3R) 可能优于无止盈或过高止盈
4. **高成本场景** 会显著降低收益，但顶级配置仍应保持盈利
5. **较严格的OFI阈值** (0.85/0.15) 可能提高胜率但减少交易频率

## 下一步

Phase 5 完成后，我们可以：

1. **选择最优参数** - 基于稳健性和成本敏感性
2. **生成策略规格** - 将最优配置转化为正式交易规则
3. **实盘准备** - 开发API接口和自动化交易系统
4. **风险管理** - 设计仓位管理和组合策略

---

**Phase 5 将帮助我们找到真正稳健、可实盘的策略参数！** 🎯📊

