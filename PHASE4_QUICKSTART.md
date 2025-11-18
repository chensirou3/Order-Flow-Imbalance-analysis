# Phase 4 快速开始指南

## 🎯 目标

分析基于OFI因子的交易路径特征，为后续策略设计提供依据。

## 📊 分析范围

- **品种**: BTCUSD, ETHUSD, XAUUSD, XAGUSD（仅加密货币和贵金属）
- **周期**: 5min, 15min, 30min, 1H, 2H, 4H, 8H, 1D
- **总配置**: 32个

## 🚀 快速开始

### 方法1: 服务器运行（推荐）

#### 步骤1: 部署并启动

```powershell
.\deploy_and_run_trade_path.ps1
```

这个脚本会：
1. 上传所有Phase 4代码到服务器
2. 验证Python环境
3. 在后台启动分析
4. 显示初始日志

#### 步骤2: 监控进度

```powershell
.\monitor_trade_path.ps1
```

或实时查看日志：

```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "tail -f Order-Flow-Imbalance-analysis/trade_path_analysis.log"
```

#### 步骤3: 下载结果

分析完成后：

```powershell
# 下载汇总报告
scp -i mishi/lianxi.pem -r ubuntu@49.51.244.154:~/Order-Flow-Imbalance-analysis/results/trade_summaries .

# 下载所有交易数据（可选）
scp -i mishi/lianxi.pem -r ubuntu@49.51.244.154:~/Order-Flow-Imbalance-analysis/results/trade_paths .
```

### 方法2: 本地测试

测试单个配置：

```bash
python test_trade_path_local.py
```

运行完整分析：

```bash
python scripts/run_ofi_trade_path.py
```

## 📁 输出文件

### 汇总报告（重要）

- `results/trade_summaries/trade_path_summary.csv` - 所有配置的统计汇总
- `results/trade_summaries/trade_path_rankings.csv` - 按各指标排名
- `results/trade_summaries/trade_path_report.md` - Markdown格式报告

### 交易数据

- `results/trade_paths/all_trades.csv` - 所有交易的详细记录
- `results/trade_paths/individual_trades/{symbol}_{tf}_trades.csv` - 单配置交易

## 📊 关键指标说明

### R倍数统计

- **Mean R**: 平均每笔交易的R倍数收益
- **Median R**: 中位数R（更稳健的指标）
- **Expectancy R**: 期望值（考虑胜率的平均收益）
- **Sharpe R**: 风险调整后收益

### 交易路径指标

- **MFE_R** (Maximum Favorable Excursion): 最大有利偏移
  - 表示交易过程中达到的最大盈利
  - 用于设计止盈策略
  
- **MAE_R** (Maximum Adverse Excursion): 最大不利偏移
  - 表示交易过程中的最大回撤
  - 用于设计止损策略

- **t_MFE**: 达到MFE的时间（bars）
  - 了解最佳出场时机
  - 优化持仓期

### 出场原因

- **Stop**: 触发止损（loss_in_R <= -MFE_R）
- **Hmax**: 达到最大持仓时间（150 bars）
- **End of Data**: 数据结束

## 🎯 预期结果

基于Phase 3的发现，预期最佳配置：

1. **ETHUSD 1D** - 最高期望值
2. **BTCUSD 8H** - 最高Sharpe
3. **ETHUSD 8H** - 稳定表现

## ⏱️ 预计时间

- **单配置**: 1-3分钟
- **全部32配置**: 30-60分钟

## 🔍 监控命令

### 检查进程

```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ps aux | grep python3"
```

### 查看最新日志

```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "tail -30 Order-Flow-Imbalance-analysis/trade_path_analysis.log"
```

### 检查输出文件

```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ls -lh Order-Flow-Imbalance-analysis/results/trade_summaries/"
```

## 📈 后续应用

Phase 4的结果将用于：

1. **止盈/止损设计**
   - 基于MFE/MAE分布
   - 优化出场规则

2. **动态出场策略**
   - 基于t_MFE统计
   - 跟踪止损设计

3. **仓位管理**
   - 基于R倍数分布
   - Kelly准则应用

4. **实盘准备**
   - 理解典型交易路径
   - 设定合理预期

## ⚠️ 注意事项

1. **不是回测**: 这是路径分析，不考虑资金管理
2. **固定仓位**: 每笔交易1单位，忽略风险限制
3. **理想化执行**: 假设完美执行，无滑点
4. **目的**: 理解交易行为，为策略设计提供依据

## 🆘 故障排除

### 问题: 进程没有启动

检查日志：
```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "cat Order-Flow-Imbalance-analysis/trade_path_analysis.log"
```

### 问题: 找不到数据文件

确认合并文件存在：
```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "ls Order-Flow-Imbalance-analysis/results/*_merged_bars_with_ofi.csv | wc -l"
```

应该有48个文件（6品种 × 8周期）

### 问题: 内存不足

检查内存使用：
```powershell
ssh.exe -i mishi/lianxi.pem ubuntu@49.51.244.154 "free -h"
```

Phase 4的内存使用应该很低（<2GB），因为每次只处理一个配置。

---

**准备开始Phase 4！** 🚀

