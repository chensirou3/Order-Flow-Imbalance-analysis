# Phase 0–3 开发进度日志

## [2025-11-17] 项目初始化

### 完成内容
- ✅ 创建项目目录结构
- ✅ 编写项目README和配置文件
- ✅ 完成OFI设计文档（OFI_DESIGN_NOTES.md）

### 项目结构
```
ofi_factor_project/
├── config/settings.yaml
├── data/ticks/ (待用户提供数据)
├── results/
├── docs/
├── src/
└── scripts/
```

---

## [2025-11-17] Phase 1: 数据加载与K线聚合

### 实现模块
- ✅ `src/config_loader.py` - 配置文件加载器
- ✅ `src/data/tick_loader.py` - Tick数据加载和清洗
  - 支持bid/ask格式
  - 支持单一价格格式
  - 自动检测tick模式
  - 时间戳解析和排序
- ✅ `src/data/tick_to_bars.py` - Tick到K线聚合
  - OHLCV计算
  - 成交量和tick计数统计

### 功能特性
- 灵活的数据格式支持
- 自动数据清洗和去重
- 时区感知的时间处理

---

## [2025-11-17] Phase 2: OFI因子构建

### 实现模块
- ✅ `src/factors/ofi.py` - OFI因子核心逻辑
  - Tick规则标记（买卖方向判断）
  - OFI_raw计算（订单流失衡原始值）
  - OFI_z计算（滚动标准化）
- ✅ `src/data/bars_with_ofi_builder.py` - 端到端构建器
  - 整合tick加载、K线聚合、OFI计算
  - 输出包含OFI的完整K线数据

### 技术实现
- Tick规则：基于中间价变化判断交易方向
- OFI_raw：(买量-卖量)/(总量+ε)，范围[-1, +1]
- OFI_z：200期滚动窗口标准化

---

## [2025-11-17] Phase 3: OFI单因子诊断

### 实现模块
- ✅ `src/utils/stats_utils.py` - 统计工具函数
  - t统计量计算
  - 简单OLS回归
- ✅ `src/research/ofi_single_factor.py` - 单因子分析
  - 健全性检查（分布、相关性）
  - 条件收益分析（高/低OFI_z分组）
  - 分位数分组分析
  - OLS回归分析

### 分析内容
1. **健全性检查**:
   - OFI_raw和OFI_z的描述性统计
   - 关键分位数（1%, 5%, 95%, 99%）
   - 与成交量、波动率的相关性

2. **条件收益分析**:
   - 高OFI_z组（>90%分位数）vs 低OFI_z组（<10%分位数）
   - 多个时间跨度（2/5/10个K线）
   - 均值、标准差、t统计量

3. **回归分析**:
   - future_return ~ OFI_z
   - 报告beta系数和t统计量

4. **分位数分析**:
   - 将OFI_z分为5组
   - 每组的平均未来收益

---

## [2025-11-17] 可执行脚本

### 实现脚本
- ✅ `scripts/build_bars_with_ofi.py` - 构建K线+OFI数据
  - 读取配置文件
  - 处理所有配置的品种
  - 输出到results目录

- ✅ `scripts/run_ofi_single_factor.py` - 运行单因子分析
  - 加载K线+OFI数据
  - 执行健全性检查
  - 执行条件收益分析
  - 生成分析报告

---

## 待完成任务

### 数据准备
- ⏳ 用户需要将tick数据放入`data/ticks/`目录
- ⏳ 根据实际数据调整`config/settings.yaml`中的品种列表

### 首次运行
- ⏳ 运行`python scripts/build_bars_with_ofi.py`
- ⏳ 运行`python scripts/run_ofi_single_factor.py`

---

## 关键发现（待填充）

### BTCUSD
- 待运行分析后填充

### XAUUSD
- 待运行分析后填充

---

## 技术笔记

### Tick规则实现
使用pandas的shift和fillna实现高效的tick规则标记：
```python
sign = np.where(mid > mid.shift(1), 1, np.where(mid < mid.shift(1), -1, np.nan))
sign = pd.Series(sign).fillna(method='ffill').fillna(1)
```

### OFI聚合
使用groupby和自定义聚合函数，分别统计买方和卖方成交量。

### 滚动标准化
使用pandas的rolling函数，窗口大小可配置（默认200）。

---

## 下一步计划

Phase 0-3已完成，后续可扩展方向：
1. 添加更多因子（如ManipScore）
2. 实现交易路径分析
3. 构建简单回测框架
4. 探索机器学习模型
5. 优化因子参数（窗口大小、分位数阈值等）

