# 使用Parquet分区数据指南

## ✅ 数据检查结果

您的数据已成功验证并可以使用！

### 数据格式
- **文件格式**: Parquet
- **组织结构**: 分区目录（`symbol=XXX/date=YYYY-MM-DD/*.parquet`）
- **数据列**: `ts`, `symbol`, `bid`, `ask`, `bid_size`, `ask_size`
- **可用品种**: BTCUSD, ETHUSD, EURUSD, USDJPY, XAGUSD, XAUUSD

### 测试结果（BTCUSD, 2020-2025）
- ✅ **Tick数据**: 364,466,201 条
- ✅ **时间范围**: 2020-01-01 到 2025-10-08
- ✅ **生成K线**: 12,174 个4小时K线
- ✅ **OFI覆盖率**: 98.37% (11,975/12,174)
- ✅ **分析报告**: 已成功生成

---

## 🚀 快速开始

### 1. 配置品种和日期范围

编辑 `config/settings.yaml`:

```yaml
# 选择要分析的品种
symbols:
  - BTCUSD
  # - ETHUSD
  # - EURUSD
  # - USDJPY
  # - XAGUSD
  # - XAUUSD

# 设置日期范围（可选）
data:
  start_date: "2020-01-01"  # 开始日期
  end_date: null            # null = 到最新数据
```

### 2. 构建K线和OFI因子

```bash
python scripts/build_bars_from_parquet.py
```

这个脚本会：
- 从分区Parquet文件加载tick数据
- 计算中间价（mid price）
- 标记买卖方向（tick rule）
- 聚合成4小时K线
- 计算OFI_raw和OFI_z
- 保存到 `results/{SYMBOL}_4h_bars_with_ofi.csv`

### 3. 运行单因子分析

```bash
python scripts/run_ofi_single_factor.py
```

这个脚本会生成：
- 健全性检查报告（`results/sanity/ofi_R0_sanity_{symbol}.md`）
- 条件收益分析（`results/single_factor/ofi_R1_single_factor_{symbol}.csv`）
- 分位数分析（`results/single_factor/ofi_R1_bins_{symbol}.csv`）

---

## 📊 分析结果示例（BTCUSD）

### OFI_z 分布统计
```
count    11975.000000
mean         0.017372
std          1.054304
min         -8.956403
max          7.592741

关键分位数:
  10%: -1.1861
  50%: -0.0445
  90%:  1.3173
```

### 分位数分组收益（horizon=10个K线）
```
Bin 1 (最低OFI_z): -8.96 到 -0.78 → 平均收益: -0.03%
Bin 2:              -0.78 到 -0.19 → 平均收益:  0.09%
Bin 3:              -0.19 到  0.19 → 平均收益:  0.22%
Bin 4:               0.19 到  0.79 → 平均收益:  0.30%
Bin 5 (最高OFI_z):  0.79 到  7.59 → 平均收益:  0.50%
```

**观察**: 高OFI_z（买方压力大）对应更高的未来收益，显示出一定的预测能力。

---

## ⚙️ 配置选项

### K线周期
在 `config/settings.yaml` 中修改：
```yaml
ofi:
  bar_size: "4H"  # 可改为 "1H", "2H", "8H", "1D" 等
```

### OFI标准化窗口
```yaml
ofi:
  zscore_window: 200  # 滚动窗口大小
```

### 分析参数
```yaml
analysis:
  horizons: [2, 5, 10]    # 未来收益时间跨度（K线数）
  quantile_low: 0.10      # 低分位数阈值
  quantile_high: 0.90     # 高分位数阈值
  n_bins: 5               # 分位数分组数
```

---

## 📁 数据结构说明

### 输入数据（Parquet）
```
data/ticks/
├── symbol=BTCUSD/
│   ├── date=2020-01-01/
│   │   └── BTCUSD_2020-01-01.parquet
│   ├── date=2020-01-02/
│   │   └── BTCUSD_2020-01-02.parquet
│   └── ...
├── symbol=ETHUSD/
│   └── ...
└── ...
```

每个Parquet文件包含：
- `ts`: 时间戳（datetime64[ms, UTC]）
- `symbol`: 交易品种
- `bid`: 买价
- `ask`: 卖价
- `bid_size`: 买量
- `ask_size`: 卖量

### 输出数据（CSV）

**K线+OFI数据** (`results/{SYMBOL}_4h_bars_with_ofi.csv`):
- `timestamp`: K线时间
- `open`, `high`, `low`, `close`: OHLC价格
- `volume`: 成交量
- `tick_count`: tick数量
- `OFI_raw`: 原始OFI（-1到+1）
- `OFI_z`: 标准化OFI（z-score）

---

## 🔍 技术细节

### OFI计算流程

1. **加载Parquet数据** → 按日期分区读取
2. **计算中间价** → `mid = (bid + ask) / 2`
3. **Tick规则标记** → 
   - 价格上涨 → 买方主导 (+1)
   - 价格下跌 → 卖方主导 (-1)
4. **聚合到K线** → 
   - `buy_vol = sum(volume where sign=+1)`
   - `sell_vol = sum(volume where sign=-1)`
   - `OFI_raw = (buy_vol - sell_vol) / total_vol`
5. **标准化** → 
   - `OFI_z = (OFI_raw - rolling_mean) / rolling_std`

### 数据量估算

以BTCUSD为例（2020-2025）:
- Tick数据: ~3.6亿条
- 4H K线: ~12,000个
- 处理时间: ~5-10分钟（取决于硬件）

---

## 💡 使用建议

### 1. 首次使用
- 先用单个品种测试（如BTCUSD）
- 设置较短的日期范围（如1年）
- 确认结果正确后再扩展

### 2. 批量处理
编辑 `config/settings.yaml`，启用多个品种：
```yaml
symbols:
  - BTCUSD
  - ETHUSD
  - XAUUSD
```

### 3. 内存优化
如果数据量太大导致内存不足：
- 缩短日期范围
- 一次只处理一个品种
- 增大K线周期（如使用8H或1D）

---

## 📈 下一步

1. **查看分析结果**
   ```bash
   type results\sanity\ofi_R0_sanity_BTCUSD.md
   ```

2. **分析其他品种**
   - 在配置文件中启用其他品种
   - 重新运行脚本

3. **调整参数**
   - 尝试不同的K线周期
   - 调整OFI标准化窗口
   - 修改分析时间跨度

4. **扩展研究**
   - 添加新的因子
   - 构建多因子模型
   - 开发回测系统

---

## ⚠️ 注意事项

1. **Pandas警告**: 代码中使用了一些pandas的旧API，会有弃用警告，但不影响功能
2. **数据量**: 处理全部数据可能需要较长时间和较大内存
3. **OFI_z覆盖率**: 前200个K线的OFI_z为NaN（需要历史数据计算滚动统计）

---

**您的数据已经可以正常使用了！** 🎉

如有问题，请查看：
- `QUICKSTART.md` - 快速入门
- `README.md` - 项目总览
- `docs/OFI_DESIGN_NOTES.md` - 理论设计

