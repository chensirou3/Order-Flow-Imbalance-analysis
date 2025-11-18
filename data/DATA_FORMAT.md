# Tick数据格式说明

## 文件位置

将tick级别的CSV数据文件放入 `data/ticks/` 目录。

## 文件命名

文件名应遵循以下模式：
```
{SYMBOL}_ticks*.csv
```

例如：
- `BTCUSD_ticks_2017_2024.csv`
- `XAUUSD_ticks_2015_2024.csv`
- `ETHUSD_ticks.csv`

## 数据格式

系统支持两种tick数据格式：

### 格式A：Bid/Ask格式（推荐）

包含买卖报价的完整tick数据。

**必需列：**
- `timestamp`: 时间戳（任何pandas可解析的日期时间格式）
- `bid`: 买方报价
- `ask`: 卖方报价

**可选列：**
- `volume`: 成交量（如果缺失，默认为1）

**示例CSV：**
```csv
timestamp,bid,ask,volume
2024-01-01 00:00:00,42000.5,42001.0,1.5
2024-01-01 00:00:05,42000.0,42000.5,2.3
2024-01-01 00:00:10,42001.0,42001.5,0.8
```

### 格式B：单一价格格式

只包含成交价格的简化tick数据。

**必需列：**
- `timestamp`: 时间戳
- `price`: 成交价格

**可选列：**
- `volume`: 成交量（如果缺失，默认为1）

**示例CSV：**
```csv
timestamp,price,volume
2024-01-01 00:00:00,42000.75,1.5
2024-01-01 00:00:05,42000.25,2.3
2024-01-01 00:00:10,42001.25,0.8
```

## 时间戳格式

时间戳可以是以下任何格式（pandas会自动解析）：

- ISO 8601: `2024-01-01T00:00:00Z`
- 标准格式: `2024-01-01 00:00:00`
- Unix时间戳: `1704067200`
- 带时区: `2024-01-01 00:00:00+00:00`

**建议：** 使用UTC时区的时间戳以避免时区混淆。

## 数据质量要求

1. **排序**: 数据不需要预先排序，系统会自动按时间戳排序
2. **重复**: 系统会自动删除完全重复的行
3. **缺失值**: 价格列不应有缺失值
4. **数据量**: 建议至少有几千个tick以生成有意义的4H K线

## 示例数据生成

如果您需要测试系统但没有真实数据，可以使用以下Python代码生成示例数据：

```python
import pandas as pd
import numpy as np

# 生成示例tick数据
np.random.seed(42)
n_ticks = 10000

timestamps = pd.date_range('2024-01-01', periods=n_ticks, freq='1min')
base_price = 42000
prices = base_price + np.cumsum(np.random.randn(n_ticks) * 10)

# 格式A: Bid/Ask
df_bidask = pd.DataFrame({
    'timestamp': timestamps,
    'bid': prices - 0.5,
    'ask': prices + 0.5,
    'volume': np.random.exponential(1.0, n_ticks)
})
df_bidask.to_csv('data/ticks/BTCUSD_ticks_example.csv', index=False)

# 格式B: 单一价格
df_price = pd.DataFrame({
    'timestamp': timestamps,
    'price': prices,
    'volume': np.random.exponential(1.0, n_ticks)
})
df_price.to_csv('data/ticks/XAUUSD_ticks_example.csv', index=False)
```

## 配置符号列表

在 `config/settings.yaml` 中配置要处理的交易品种：

```yaml
symbols:
  - BTCUSD
  - XAUUSD
  - ETHUSD
```

确保每个符号在 `data/ticks/` 目录中都有对应的CSV文件。

