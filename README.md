# OFI Factor Research Project

这是一个专注于研究**订单流失衡（Order Flow Imbalance, OFI）**因子的独立项目。

## 🎉 项目状态：已完成

**完成时间**: 2025-11-19
**分析状态**: ✅ 全部完成

- ✅ 6个品种（BTCUSD, ETHUSD, EURUSD, USDJPY, XAGUSD, XAUUSD）
- ✅ 8个时间周期（5min, 15min, 30min, 1H, 2H, 4H, 8H, 1D）
- ✅ 48个合并文件，9,247,557行数据
- ✅ 完整分析报告已生成

**核心发现**:
- 🥇 **ETHUSD 1D**: Q5-Q1收益差 4.09%, Sharpe 1.89
- 🥈 **BTCUSD 8H**: Q5-Q1收益差 0.80%, Sharpe 2.32（最高）
- 🥉 **ETHUSD 8H**: Q5-Q1收益差 1.09%, Sharpe 1.15

详见 [FINAL_ANALYSIS_COMPLETE.md](FINAL_ANALYSIS_COMPLETE.md)

## 项目概述

本项目从原始tick数据出发，构建OFI因子并进行单因子分析。项目设计模块化、可扩展，便于后续添加其他因子、交易路径分析或实盘交易集成。

## 研究阶段

### ✅ Phase 0 – 理论基础与项目框架（已完成）
- ✅ 文档化OFI因子的理论动机
- ✅ 定义研究假设
- ✅ 创建项目骨架

### ✅ Phase 1 – 数据加载与K线聚合（已完成）
- ✅ 从tick数据加载和清洗
- ✅ 支持Parquet格式（Hive分区）
- ✅ 支持多种时间周期（5min-1D）
- ✅ 支持bid/ask和单一价格两种tick格式

### ✅ Phase 2 – OFI因子构建（已完成）
- ✅ 使用tick规则标记买卖方向
- ✅ 计算原始OFI（OFI_raw）
- ✅ 计算标准化OFI（OFI_z）
- ✅ 批处理大规模数据

### ✅ Phase 3 – OFI单因子诊断（已完成）
- ✅ OFI分布和统计特性检查
- ✅ 条件未来收益分析
- ✅ 分位数分析（Q1-Q5）
- ✅ 相关性分析
- ✅ Sharpe比率计算

### ✅ Phase 4 – 大规模分析（已完成）
- ✅ 6个品种全覆盖
- ✅ 8个时间周期全覆盖
- ✅ 服务器批处理优化
- ✅ 内存管理优化（OOM问题解决）
- ✅ 完整分析报告生成

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config/settings.yaml` 设置：
- 交易品种列表
- 数据路径
- K线周期
- 分析参数

### 3. 准备数据

**推荐格式：Parquet（Hive分区）**

```
data/ticks/
├── symbol=BTCUSD/
│   ├── date=2017-05-07/
│   │   └── part-0.parquet
│   ├── date=2017-05-08/
│   │   └── part-0.parquet
│   └── ...
├── symbol=ETHUSD/
│   └── ...
```

**Parquet文件字段**：
- `timestamp` (datetime64)
- `bid` (float64)
- `ask` (float64)
- `bid_vol` (float64)
- `ask_vol` (float64)

**传统CSV格式也支持**：

选项A（bid/ask格式）：
```
timestamp,bid,ask,volume
2024-01-01 00:00:00,42000.5,42001.0,1.5
```

选项B（单一价格格式）：
```
timestamp,price,volume
2024-01-01 00:00:00,42000.75,1.5
```

### 4. 运行分析

**单品种分析**：
```bash
# 构建K线 + OFI因子
python scripts/build_bars_with_ofi.py

# 运行单因子分析
python scripts/run_ofi_single_factor.py
```

**批量分析（推荐）**：
```bash
# 单品种批处理（适合大数据）
python run_single_symbol_batch.py

# 所有品种顺序处理
python run_all_symbols_sequential.py

# 分析结果汇总
python analyze_ofi_results.py
```

## 输出结果

### 数据输出

**批次文件**：
- `results/{SYMBOL}_{TIMEFRAME}_{BATCH}_bars_with_ofi.csv`

**合并文件**（推荐使用）：
- `results/{SYMBOL}_{TIMEFRAME}_merged_bars_with_ofi.csv`

**字段说明**：
- `open`, `high`, `low`, `close` - OHLC价格
- `volume` - 成交量
- `OFI` - 原始订单流失衡
- `OFI_z` - 标准化OFI（滚动窗口200）
- `fut_ret_2`, `fut_ret_5`, `fut_ret_10` - 未来2/5/10期收益率

### 分析报告

**完整分析**：
- `results/analysis_summary.csv` - 所有品种和周期的统计汇总

**单品种报告**：
- `results/sanity/ofi_R0_sanity_{symbol}.md` - OFI因子健全性检查
- `results/single_factor/ofi_R1_single_factor_{symbol}.csv` - 条件收益分析
- `results/single_factor/ofi_R1_bins_{symbol}.csv` - 分位数分析

## 项目结构

```
ofi_factor_project/
├── config/              # 配置文件
├── data/                # 数据目录
│   ├── ticks/          # 原始tick数据（用户提供）
│   └── bars/           # K线数据输出
├── results/            # 分析结果
│   ├── sanity/         # 健全性检查
│   └── single_factor/  # 单因子分析
├── docs/               # 文档
├── src/                # 源代码
│   ├── config_loader.py
│   ├── data/           # 数据处理模块
│   ├── factors/        # 因子计算模块
│   ├── research/       # 研究分析模块
│   └── utils/          # 工具函数
└── scripts/            # 可执行脚本
```

## 扩展性

项目设计支持未来扩展：
- 添加更多因子（如ManipScore）并在K线级别合并
- 添加交易路径和退出规则分析
- 集成简单回测框架
- 连接实盘交易系统

## 技术栈

- Python 3.10+
- pandas - 数据处理
- numpy - 数值计算
- matplotlib - 可视化
- pyyaml - 配置管理

## 核心发现

### Top 3 最佳配置

1. **ETHUSD + 1D（日线）** ⭐⭐⭐⭐⭐
   - Q5-Q1收益差: 4.09%
   - OFI相关性: 0.0804
   - Sharpe比率: 1.89
   - 推荐策略: 做多Q5组，做空Q1组，持仓10天

2. **BTCUSD + 8H** ⭐⭐⭐⭐⭐
   - Q5-Q1收益差: 0.80%
   - OFI相关性: 0.0417
   - Sharpe比率: 2.32（最高！）
   - 推荐策略: 做多Q5组，做空Q1组，持仓80小时

3. **ETHUSD + 8H** ⭐⭐⭐⭐
   - Q5-Q1收益差: 1.09%
   - OFI相关性: 0.0360
   - Sharpe比率: 1.15

### 关键洞察

- ✅ **加密货币**（BTCUSD, ETHUSD）OFI因子效果显著
- ✅ **中长周期**（4H-1D）表现最佳
- ⚠️ **外汇品种**（EURUSD, USDJPY）OFI因子效果很弱
- ❌ **短周期**（5min）噪音太大，不推荐

## 文档

详细文档请参阅：
- `FINAL_ANALYSIS_COMPLETE.md` - 最终完成报告（推荐阅读）
- `analysis_summary_complete.csv` - 完整统计数据
- `docs/OFI_DESIGN_NOTES.md` - OFI因子设计说明
- `docs/PHASE0_3_PROGRESS_LOG.md` - 开发进度日志
- `使用Parquet数据指南.md` - Parquet数据使用说明
- `批量分析使用指南.md` - 批量分析指南

