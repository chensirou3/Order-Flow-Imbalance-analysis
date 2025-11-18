# OFI因子设计说明

## 背景

**订单流失衡（Order Flow Imbalance, OFI）** 是一个衡量市场买卖压力不平衡程度的指标。它基于tick级别的交易数据，通过区分买方主动成交和卖方主动成交来量化市场的即时供需关系。

在高频交易和量化研究中，OFI被广泛用于：
- 预测短期价格走势
- 识别流动性冲击
- 检测知情交易（informed trading）
- 构建市场微观结构模型

## 核心直觉

### OFI_raw的含义

OFI_raw定义为：

```
OFI_raw = (买方成交量 - 卖方成交量) / (总成交量 + ε)
```

其取值范围在[-1, +1]之间：

- **OFI_raw ≈ +1**: 几乎所有交易都是买方主动发起的（强烈买压）
  - 市场参与者急于买入，愿意支付卖方报价
  - 可能预示价格上涨压力

- **OFI_raw ≈ -1**: 几乎所有交易都是卖方主动发起的（强烈卖压）
  - 市场参与者急于卖出，愿意接受买方报价
  - 可能预示价格下跌压力

- **OFI_raw ≈ 0**: 买卖双方力量相对平衡
  - 市场处于相对均衡状态

### OFI_z的含义

OFI_z是OFI_raw的标准化版本：

```
OFI_z = (OFI_raw - rolling_mean(OFI_raw)) / rolling_std(OFI_raw)
```

OFI_z的优势：
- **相对性**: 衡量当前订单流相对于历史水平的极端程度
- **可比性**: 不同资产和时间段的OFI_z可以直接比较
- **信号强度**: |OFI_z|越大，表示当前订单流越异常

当|OFI_z|很大时：
- 当前K线的订单流失衡相对于近期历史是极端的
- 可能表示"有事情正在发生"（信息性交易、流动性事件等）
- 可能伴随更大的价格波动

## 研究问题

本项目旨在回答以下核心问题：

### RQ1: 波动性预测
**当|OFI_z|极端时，未来收益的绝对值是否也更大？**

- 假设：极端的订单流失衡可能预示即将到来的价格波动
- 检验方法：比较高|OFI_z|和低|OFI_z|条件下的|future_return|

### RQ2: 方向性预测
**OFI_z的符号是否提供短期收益的方向性优势？**

- 趋势假设：正OFI_z → 正未来收益（动量效应）
- 反转假设：正OFI_z → 负未来收益（均值回归）
- 检验方法：
  - 条件收益分析（高OFI_z vs 低OFI_z）
  - 简单回归：future_return ~ OFI_z

### RQ3: 稳健性
**OFI模式在不同资产和时间段是否稳健？**

- 跨资产检验：BTCUSD（加密货币）vs XAUUSD（贵金属）
- 时间稳定性：不同时期的表现是否一致
- 检验方法：对比不同品种和子时期的结果

## 实现阶段

### Phase 0: 理论基础与项目框架
- 文档化设计思路
- 创建项目结构
- 定义研究假设

### Phase 1: 数据加载与K线聚合
- 实现tick数据加载和清洗
- 支持bid/ask和单一价格两种格式
- 将tick聚合为4小时OHLCV K线

### Phase 2: OFI因子构建
- **Tick规则标记**: 根据价格变化方向判断买卖方向
  - mid_price上升 → 买方主动
  - mid_price下降 → 卖方主动
  - mid_price不变 → 继承前一tick方向
- **OFI_raw计算**: 在K线级别聚合买卖成交量
- **OFI_z计算**: 滚动标准化（默认200个K线窗口）

### Phase 3: OFI单因子诊断
- **健全性检查**:
  - OFI_raw和OFI_z的分布统计
  - 关键分位数（1%, 5%, 95%, 99%）
  - 与成交量、波动率的相关性
- **条件收益分析**:
  - 高/低OFI_z分组的未来收益对比
  - 不同时间跨度（2/5/10个K线）
  - 简单OLS回归
  - 分位数分组分析

## 技术细节

### Tick规则（Tick Rule）

由于我们使用的是tick数据而非逐笔成交数据，无法直接观察到交易的主动方向。因此使用经典的tick规则：

```python
if mid_price[t] > mid_price[t-1]:
    direction[t] = +1  # 买方主动
elif mid_price[t] < mid_price[t-1]:
    direction[t] = -1  # 卖方主动
else:
    direction[t] = direction[t-1]  # 继承前值
```

### 中间价（Mid Price）

- 如果有bid和ask: `mid = (bid + ask) / 2`
- 如果只有单一价格: `mid = price`

### 滚动标准化窗口

默认使用200个K线作为滚动窗口：
- 对于4H K线，200个K线 ≈ 33天
- 足够捕捉短期动态，同时保持一定稳定性
- 可根据具体资产特性调整

## 未来扩展方向

1. **多因子组合**: 将OFI与其他因子（如ManipScore）结合
2. **交易路径分析**: 研究OFI信号的最优进出场策略
3. **高频优化**: 探索更短周期（1H, 30min）的OFI表现
4. **机器学习**: 使用OFI作为特征训练预测模型
5. **实盘交易**: 集成到自动化交易系统

## 参考文献

- Cont, R., Kukanov, A., & Stoikov, S. (2014). The price impact of order book events. Journal of Financial Econometrics.
- Easley, D., López de Prado, M. M., & O'Hara, M. (2012). Flow toxicity and liquidity in a high-frequency world. Review of Financial Studies.

