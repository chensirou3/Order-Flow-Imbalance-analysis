# OFI因子研究 - 快速入门指南

## 第一步：安装依赖

```bash
pip install -r requirements.txt
```

## 第二步：准备数据

### 2.1 将tick数据放入data/ticks目录

您的tick数据CSV文件应该放在 `data/ticks/` 目录下。

**文件命名格式：** `{SYMBOL}_ticks*.csv`

例如：
- `data/ticks/BTCUSD_ticks_2017_2024.csv`
- `data/ticks/XAUUSD_ticks_2015_2024.csv`

### 2.2 数据格式

支持两种格式（详见 `data/DATA_FORMAT.md`）：

**格式A - Bid/Ask:**
```csv
timestamp,bid,ask,volume
2024-01-01 00:00:00,42000.5,42001.0,1.5
```

**格式B - 单一价格:**
```csv
timestamp,price,volume
2024-01-01 00:00:00,42000.75,1.5
```

### 2.3 配置符号列表

编辑 `config/settings.yaml`，设置要分析的交易品种：

```yaml
symbols:
  - BTCUSD
  - XAUUSD
```

## 第三步：构建K线和OFI因子

运行以下命令从tick数据构建4小时K线并计算OFI因子：

```bash
python scripts/build_bars_with_ofi.py
```

**输出：**
- `results/BTCUSD_4h_bars_with_ofi.csv`
- `results/XAUUSD_4h_bars_with_ofi.csv`

每个文件包含：
- OHLCV数据（open, high, low, close, volume）
- OFI原始值（OFI_raw）
- OFI标准化值（OFI_z）
- 其他统计信息

## 第四步：运行OFI单因子分析

```bash
python scripts/run_ofi_single_factor.py
```

**输出：**

### 健全性检查报告
- `results/sanity/ofi_R0_sanity_BTCUSD.md`
- `results/sanity/ofi_R0_sanity_XAUUSD.md`

包含：
- OFI_raw和OFI_z的描述性统计
- 关键分位数
- 与成交量、波动率的相关性

### 单因子分析结果
- `results/single_factor/ofi_R1_single_factor_BTCUSD.csv`
- `results/single_factor/ofi_R1_single_factor_XAUUSD.csv`

包含：
- 高/低OFI_z分组的条件收益
- t统计量
- OLS回归结果

### 分位数分析
- `results/single_factor/ofi_R1_bins_BTCUSD.csv`
- `results/single_factor/ofi_R1_bins_XAUUSD.csv`

包含：
- OFI_z分为5个分位数组
- 每组的平均未来收益

## 第五步：查看结果

### 查看健全性检查

```bash
# Windows
type results\sanity\ofi_R0_sanity_BTCUSD.md

# Linux/Mac
cat results/sanity/ofi_R0_sanity_BTCUSD.md
```

### 查看单因子分析

在Excel或Python中打开CSV文件：

```python
import pandas as pd

# 单因子分析
df = pd.read_csv('results/single_factor/ofi_R1_single_factor_BTCUSD.csv')
print(df)

# 分位数分析
bins = pd.read_csv('results/single_factor/ofi_R1_bins_BTCUSD.csv')
print(bins)
```

## 配置参数说明

在 `config/settings.yaml` 中可以调整以下参数：

```yaml
# K线周期
ofi:
  bar_size: "4H"        # 可改为 "1H", "2H", "8H" 等
  zscore_window: 200    # OFI标准化的滚动窗口

# 分析参数
analysis:
  horizons: [2, 5, 10]  # 未来收益的时间跨度（K线数量）
  quantile_low: 0.10    # 低分位数阈值
  quantile_high: 0.90   # 高分位数阈值
  n_bins: 5             # 分位数分析的分组数
```

## 常见问题

### Q1: 找不到tick数据文件

**错误信息：** `ERROR: No tick data found`

**解决方法：**
1. 确认文件在 `data/ticks/` 目录下
2. 检查文件名是否匹配 `{SYMBOL}_ticks*.csv` 格式
3. 确认 `config/settings.yaml` 中的符号名称与文件名匹配

### Q2: 时间戳解析错误

**解决方法：**
确保CSV中的timestamp列格式正确，推荐使用ISO 8601格式：
```
2024-01-01 00:00:00
```

### Q3: OFI_z全是NaN

**原因：** 数据量不足，无法填充滚动窗口

**解决方法：**
- 减小 `zscore_window` 参数（默认200）
- 或提供更多tick数据

### Q4: 想分析更短的时间周期

**解决方法：**
修改 `config/settings.yaml` 中的 `bar_size`：
```yaml
ofi:
  bar_size: "1H"  # 改为1小时K线
```

然后重新运行两个脚本。

## 下一步

1. **查看文档：** 阅读 `docs/OFI_DESIGN_NOTES.md` 了解OFI因子的理论基础
2. **调整参数：** 尝试不同的K线周期、窗口大小、分位数阈值
3. **添加品种：** 在 `config/settings.yaml` 中添加更多交易品种
4. **扩展分析：** 基于现有代码添加自定义分析

## 获取帮助

- 查看 `README.md` 了解项目整体结构
- 查看 `docs/PHASE0_3_PROGRESS_LOG.md` 了解实现细节
- 查看源代码中的docstring了解函数用法

