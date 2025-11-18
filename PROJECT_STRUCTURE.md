# 项目结构说明

## 目录树

```
ofi_factor_project/
│
├── README.md                          # 项目总览
├── QUICKSTART.md                      # 快速入门指南
├── PROJECT_STRUCTURE.md               # 本文件
├── requirements.txt                   # Python依赖
├── .gitignore                         # Git忽略规则
│
├── config/                            # 配置文件
│   └── settings.yaml                  # 全局配置（符号、路径、参数等）
│
├── data/                              # 数据目录
│   ├── DATA_FORMAT.md                 # 数据格式说明
│   ├── ticks/                         # 原始tick数据（用户提供）
│   │   └── .gitkeep
│   └── bars/                          # K线数据输出（可选）
│       └── .gitkeep
│
├── results/                           # 分析结果输出
│   ├── .gitkeep
│   ├── {symbol}_4h_bars_with_ofi.csv  # 带OFI的K线数据
│   ├── sanity/                        # Phase 3: 健全性检查
│   │   └── ofi_R0_sanity_{symbol}.md
│   └── single_factor/                 # Phase 3: 单因子分析
│       ├── ofi_R1_single_factor_{symbol}.csv
│       └── ofi_R1_bins_{symbol}.csv
│
├── docs/                              # 文档
│   ├── OFI_DESIGN_NOTES.md            # Phase 0: OFI因子设计说明
│   └── PHASE0_3_PROGRESS_LOG.md       # 开发进度日志
│
├── src/                               # 源代码
│   ├── __init__.py
│   ├── config_loader.py               # 配置加载器
│   │
│   ├── data/                          # 数据处理模块
│   │   ├── __init__.py
│   │   ├── tick_loader.py             # Phase 1: Tick数据加载
│   │   ├── tick_to_bars.py            # Phase 1: Tick到K线聚合
│   │   └── bars_with_ofi_builder.py   # Phase 2: 端到端构建器
│   │
│   ├── factors/                       # 因子计算模块
│   │   ├── __init__.py
│   │   └── ofi.py                     # Phase 2: OFI因子核心逻辑
│   │
│   ├── research/                      # 研究分析模块
│   │   ├── __init__.py
│   │   └── ofi_single_factor.py       # Phase 3: 单因子分析
│   │
│   └── utils/                         # 工具函数
│       ├── __init__.py
│       └── stats_utils.py             # 统计工具（t检验、OLS等）
│
└── scripts/                           # 可执行脚本
    ├── build_bars_with_ofi.py         # 构建K线+OFI
    └── run_ofi_single_factor.py       # 运行单因子分析
```

## 模块说明

### 配置模块 (config/)

- **settings.yaml**: 集中管理所有配置参数
  - 交易品种列表
  - 数据路径
  - K线周期
  - OFI参数（窗口大小等）
  - 分析参数（时间跨度、分位数阈值等）

### 数据处理模块 (src/data/)

#### tick_loader.py
- `detect_tick_mode()`: 自动检测tick数据格式（bid/ask或单一价格）
- `load_and_clean_ticks()`: 加载、清洗、排序tick数据

#### tick_to_bars.py
- `ticks_to_bars()`: 将tick数据聚合为OHLCV K线

#### bars_with_ofi_builder.py
- `build_bars_with_ofi()`: 端到端流程，从tick到带OFI的K线

### 因子模块 (src/factors/)

#### ofi.py
- `add_mid_price()`: 计算中间价
- `label_tick_directions()`: 使用tick规则标记买卖方向
- `compute_ofi_bars()`: 聚合为K线级别的OFI_raw
- `standardize_ofi()`: 计算滚动标准化的OFI_z

### 研究模块 (src/research/)

#### ofi_single_factor.py
- `add_future_returns()`: 添加未来收益列
- `sanity_check_ofi()`: OFI分布和相关性检查
- `analyze_ofi_single_factor()`: 条件收益和回归分析
- `run_ofi_single_factor_for_symbol()`: 完整分析流程

### 工具模块 (src/utils/)

#### stats_utils.py
- `mean_std_t()`: 计算均值、标准差、t统计量
- `simple_ols()`: 简单线性回归

### 脚本 (scripts/)

#### build_bars_with_ofi.py
1. 读取配置
2. 遍历所有符号
3. 加载tick数据
4. 构建K线和OFI因子
5. 保存到results/

#### run_ofi_single_factor.py
1. 读取配置
2. 遍历所有符号
3. 加载K线+OFI数据
4. 运行健全性检查
5. 运行单因子分析
6. 保存报告到results/sanity/和results/single_factor/

## 数据流

```
Tick数据 (CSV)
    ↓
[tick_loader.py] 加载和清洗
    ↓
Tick DataFrame (带mid, sign, vol)
    ↓
[tick_to_bars.py] 聚合OHLCV
    ↓
Bar DataFrame (OHLCV)
    ↓
[ofi.py] 计算OFI因子
    ↓
Bar + OFI DataFrame (OHLCV + OFI_raw + OFI_z)
    ↓
保存到 results/{symbol}_4h_bars_with_ofi.csv
    ↓
[ofi_single_factor.py] 分析
    ↓
生成报告:
  - results/sanity/ofi_R0_sanity_{symbol}.md
  - results/single_factor/ofi_R1_single_factor_{symbol}.csv
  - results/single_factor/ofi_R1_bins_{symbol}.csv
```

## 扩展点

### 添加新因子
1. 在 `src/factors/` 创建新模块（如 `manip_score.py`）
2. 在 `bars_with_ofi_builder.py` 中集成
3. 在 `config/settings.yaml` 添加参数

### 添加新分析
1. 在 `src/research/` 创建新模块
2. 在 `scripts/` 创建对应的执行脚本
3. 在 `config/settings.yaml` 添加配置

### 支持新数据源
1. 在 `src/data/` 添加新的加载器
2. 确保输出格式与现有流程兼容

### 添加回测功能
1. 创建 `src/backtest/` 模块
2. 使用现有的K线+因子数据
3. 实现交易逻辑和性能评估

## 设计原则

1. **模块化**: 每个模块职责单一，易于测试和维护
2. **配置驱动**: 所有参数集中在配置文件，避免硬编码
3. **可扩展**: 易于添加新因子、新分析、新数据源
4. **类型安全**: 使用类型提示提高代码质量
5. **文档完善**: 每个函数都有详细的docstring

