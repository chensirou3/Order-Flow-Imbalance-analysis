# Phase 4: OFI Trade Path Analysis

## 概述

Phase 4 专注于**交易路径级别的行为分析**，而非投资组合回测。我们模拟基于OFI_z信号的交易，记录详细的每笔交易路径统计（MFE, MAE, t_MFE, 最终R倍数, 出场原因等）。

**重要**: 这是分析，不是资金加权回测。我们忽略仓位大小约束和风险限制，每笔交易假设固定仓位（1单位名义价值）。

## 分析范围

基于Phase 3的发现，我们只分析**加密货币和贵金属**：

- **加密货币**: BTCUSD, ETHUSD
- **贵金属**: XAUUSD, XAGUSD
- **时间周期**: 5min, 15min, 30min, 1H, 2H, 4H, 8H, 1D

**排除**: EURUSD, USDJPY（已证明OFI因子无效）

## Phase 4 子阶段

### Phase 4.1: 信号定义

基于OFI_z分位数生成多空信号：

- **趋势模式** (trend): 
  - OFI_z >= Q_high (80%) → 做多
  - OFI_z <= Q_low (20%) → 做空
  
- **反转模式** (reversal):
  - OFI_z >= Q_high → 做空
  - OFI_z <= Q_low → 做多

**当前配置**: 趋势模式

### Phase 4.2: 交易路径模拟

对每笔交易进行详细路径跟踪：

**入场**:
- 基于OFI_z信号
- 使用收盘价入场
- 记录ATR用于R倍数计算

**持仓期间跟踪**:
- MFE (Maximum Favorable Excursion): 最大有利偏移
- MAE (Maximum Adverse Excursion): 最大不利偏移
- t_MFE: 达到MFE的时间（bars）
- t_MAE: 达到MAE的时间（bars）
- 当前P&L（以R倍数表示）

**出场规则**:
1. **止损**: 当 loss_in_R <= -MFE_R 时
   - 即：如果从峰值回撤到入场点以下，出场
2. **时间限制**: 达到Hmax bars（默认150）
3. **数据结束**: 到达数据末尾

**记录信息**:
- 入场/出场时间、价格、索引
- 持仓时间（bars）
- MFE/MAE（价格和R倍数）
- 最终P&L和R倍数
- 出场原因

### Phase 4.3: 单配置统计

对每个品种/周期组合计算：

- 交易数量（总数、多头、空头）
- R倍数统计（均值、中位数、标准差、最大/最小）
- 胜率、平均盈利R、平均亏损R
- MFE/MAE分布
- 持仓时间分布
- 出场原因分布
- 期望值和Sharpe比率

### Phase 4.4: 跨资产汇总和排名

汇总所有配置的结果：

- 按期望值R排名
- 按Sharpe比率排名
- 按胜率排名
- 综合排名
- 按品种汇总
- 生成Markdown报告

## 配置参数

在 `config/settings.yaml` 中：

```yaml
trade_path_symbols:
  - BTCUSD
  - ETHUSD
  - XAUUSD
  - XAGUSD

ofi_trade_path:
  entry_mode: "trend"          # "trend" 或 "reversal"
  entry_q_high: 0.8            # 上分位数阈值
  entry_q_low: 0.2             # 下分位数阈值
  atr_period: 20               # ATR周期
  atr_method: "rolling_mean"   # ATR计算方法
  hmax_bars: 150               # 最大持仓bars
  save_paths: false            # 是否保存逐bar路径
  fixed_position_size: 1.0     # 固定仓位大小
```

## 使用方法

### 本地运行

```bash
python scripts/run_ofi_trade_path.py
```

### 服务器运行（推荐）

1. **部署并启动**:
```powershell
.\deploy_and_run_trade_path.ps1
```

2. **监控进度**:
```powershell
.\monitor_trade_path.ps1
```

3. **实时查看日志**:
```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "tail -f Order-Flow-Imbalance-analysis/trade_path_analysis.log"
```

## 输出文件

### 交易数据

- `results/trade_paths/all_trades.csv` - 所有交易的详细记录
- `results/trade_paths/individual_trades/{symbol}_{tf}_trades.csv` - 单配置交易记录

### 汇总报告

- `results/trade_summaries/trade_path_summary.csv` - 统计汇总
- `results/trade_summaries/trade_path_rankings.csv` - 排名结果
- `results/trade_summaries/trade_path_report.md` - Markdown报告

## 预期结果

基于Phase 3的发现，我们预期：

### 最佳配置

1. **ETHUSD 1D** - 最高期望值
2. **BTCUSD 8H** - 最高Sharpe
3. **ETHUSD 8H** - 稳定表现

### 关键指标

- **期望值R**: 平均每笔交易的R倍数收益
- **Sharpe R**: 风险调整后收益
- **MFE_R**: 了解潜在利润空间
- **MAE_R**: 了解需要承受的回撤
- **t_MFE**: 了解最佳出场时机

## 后续应用

Phase 4的结果将用于：

1. **设计止盈/止损规则**
   - 基于MFE/MAE分布
   - 优化出场时机

2. **动态出场策略**
   - 基于t_MFE统计
   - 跟踪止损设计

3. **仓位管理**
   - 基于R倍数分布
   - Kelly准则应用

4. **实盘交易准备**
   - 理解典型交易路径
   - 设定合理预期

## 技术实现

### 核心模块

- `src/trading/ofi_signals.py` - 信号生成
- `src/trading/trade_path_simulator.py` - 交易模拟
- `src/research/ofi_trade_path_analysis.py` - 分析和报告

### 关键类

- `Trade` - 单笔交易对象，跟踪完整路径
- `simulate_trade_paths()` - 主模拟函数
- `analyze_trade_statistics()` - 统计计算

## 预计运行时间

- **配置数**: 32 (4 symbols × 8 timeframes)
- **每配置**: 1-3分钟
- **总时间**: 30-60分钟

## 注意事项

1. **不是回测**: 这是路径分析，不考虑资金管理
2. **固定仓位**: 每笔交易1单位，忽略风险限制
3. **理想化执行**: 假设完美执行，无滑点
4. **目的**: 理解交易行为，为后续策略设计提供依据

---

**准备开始Phase 4分析！** 🚀

