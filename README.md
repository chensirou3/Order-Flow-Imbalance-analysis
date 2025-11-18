# OFI Factor Research Project

这是一个专注于研究**订单流失衡（Order Flow Imbalance, OFI）**因子的独立项目。

## 项目概述

本项目从原始tick数据出发，构建OFI因子并进行单因子分析。项目设计模块化、可扩展，便于后续添加其他因子、交易路径分析或实盘交易集成。

## 研究阶段

### Phase 0 – 理论基础与项目框架
- 文档化OFI因子的理论动机
- 定义研究假设
- 创建项目骨架

### Phase 1 – 数据加载与K线聚合
- 从tick数据加载和清洗
- 将tick数据聚合为4小时K线（OHLCV）
- 支持bid/ask和单一价格两种tick格式

### Phase 2 – OFI因子构建
- 使用tick规则标记买卖方向
- 计算原始OFI（OFI_raw）
- 计算标准化OFI（OFI_z）

### Phase 3 – OFI单因子诊断
- OFI分布和统计特性检查
- 条件未来收益分析
- 简单回归和分位数分析

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

将tick级别的CSV数据放入 `data/ticks/` 目录，例如：
- `data/ticks/BTCUSD_ticks_2017_2024.csv`
- `data/ticks/XAUUSD_ticks_2015_2024.csv`

**Tick数据格式要求：**

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

```bash
# 步骤1: 构建4H K线 + OFI因子
python scripts/build_bars_with_ofi.py

# 步骤2: 运行OFI单因子研究分析
python scripts/run_ofi_single_factor.py
```

## 输出结果

### 数据输出
- `results/{symbol}_4h_bars_with_ofi.csv` - 包含OFI因子的4H K线数据

### 分析报告
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

## 文档

详细文档请参阅：
- `docs/OFI_DESIGN_NOTES.md` - OFI因子设计说明
- `docs/PHASE0_3_PROGRESS_LOG.md` - 开发进度日志

