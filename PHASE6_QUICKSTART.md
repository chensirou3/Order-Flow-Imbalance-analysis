# Phase 6 Quick Start Guide

**Goal**: Run Phase 6 analysis modules to generate long/short decomposition, regime analysis, and strategy specs.

---

## Prerequisites

✅ Phase 4 complete (trade paths generated)  
✅ Phase 5 complete (parameter sweep ranking available)  
✅ Python 3.8+ with pandas, numpy, pyyaml

---

## Quick Start (3 Steps)

### Step 1: Run All Modules Locally

```bash
python scripts/run_phase6_all.py
```

This will run:
- Phase 6A: Long/short + regime analysis
- Phase 6B: OFI × ManipScore joint (skips if no ManipScore data)
- Phase 6C: Strategy spec generation

**Expected runtime**: ~30 seconds

---

### Step 2: Run Specific Modules

```bash
# Only long/short analysis
python scripts/run_phase6_all.py --modules 6A

# Only strategy specs
python scripts/run_phase6_all.py --modules 6C

# Multiple modules
python scripts/run_phase6_all.py --modules 6A 6C
```

---

### Step 3: Review Results

**Long/Short Analysis**:
```bash
# View combined summary
cat results/long_short/ofi_long_short_all.csv

# View regime analysis
cat results/long_short/ofi_long_short_regime_all.csv
```

**Strategy Specs**:
```bash
# Open index
open docs/strategy_specs/INDEX.md

# View top strategy
open docs/strategy_specs/OFI_BTCUSD_8H_qh0.85_ql0.15_H150_TPNone.md
```

---

## Server Deployment

### Option 1: One-Command Deploy & Run

```powershell
.\deploy_and_run_phase6.ps1
```

### Option 2: Step-by-Step

```powershell
# 1. Deploy code
.\deploy_phase6.ps1

# 2. Start Phase 6
.\start_phase6.ps1

# 3. Monitor progress
.\monitor_phase6.ps1
```

### Option 3: Run Specific Modules on Server

```powershell
# Only 6A and 6C (skip 6B)
.\start_phase6.ps1 -modules "6A 6C"
```

---

## Configuration

Edit `config/settings.yaml` to customize:

```yaml
phase6:
  long_short_regime:
    symbols: [BTCUSD, ETHUSD]  # Add more symbols
    timeframes: [8H, 4H, 1D]    # Add more timeframes
    
  strategy_spec:
    top_n_per_symbol: 3         # Number of specs per symbol
    ranking_metric: "mean_final_R_net_high_cost"  # Ranking criterion
```

---

## Output Files

### Phase 6A: Long/Short + Regime

```
results/long_short/
├── ofi_long_short_all.csv              # Combined long/short summary
├── ofi_long_short_regime_all.csv       # Combined regime analysis
├── ofi_long_short_summary_{symbol}_{tf}.csv
└── ofi_regime_summary_{symbol}_{tf}.csv
```

**Key columns**:
- `leg`: "long" or "short"
- `mean_final_R_gross`: Average R-multiple
- `sharpe_R_gross`: Sharpe ratio
- `median_MFE_R`, `p75_MFE_R`, `p90_MFE_R`: Profit potential
- `pct_stop`, `pct_hmax`: Exit reason distribution

### Phase 6C: Strategy Specs

```
docs/strategy_specs/
├── INDEX.md                            # Strategy index
└── OFI_{symbol}_{tf}_qh{}_ql{}_H{}_TP{}.md
```

**Sections in each spec**:
1. Overview
2. Market & Timeframe
3. Factor Construction
4. Entry Rules
5. Exit Rules
6. Transaction Costs
7. Historical Performance
8. Notes & Caveats

---

## Common Tasks

### View Top Strategies

```python
import pandas as pd

# Load ranking
ranking = pd.read_csv('results/param_sweep/ofi_param_sweep_ranking.csv')

# Top 5 by high-cost performance
top5 = ranking.nlargest(5, 'mean_final_R_net_high_cost')
print(top5[['symbol', 'timeframe', 'entry_q_high', 'entry_q_low', 
            'hmax_bars', 'mean_final_R_net_high_cost', 'sharpe_R_net_high_cost']])
```

### Compare Long vs Short

```python
import pandas as pd

# Load long/short summary
ls = pd.read_csv('results/long_short/ofi_long_short_all.csv')

# Pivot to compare
pivot = ls.pivot_table(
    index=['symbol', 'timeframe'],
    columns='leg',
    values='mean_final_R_gross'
)
pivot['long_advantage'] = pivot['long'] / pivot['short']
print(pivot)
```

### Analyze Best Regime

```python
import pandas as pd

# Load regime analysis
regime = pd.read_csv('results/long_short/ofi_long_short_regime_all.csv')

# Filter for BTCUSD 8H
btc_8h = regime[(regime['symbol'] == 'BTCUSD') & (regime['timeframe'] == '8H')]

# Sort by Sharpe
best = btc_8h.nlargest(5, 'sharpe_R_gross')
print(best[['regime_type', 'regime_value', 'n_trades', 'mean_final_R_gross', 'sharpe_R_gross']])
```

---

## Troubleshooting

### Issue: "KeyError: 'final_R'"

**Cause**: Phase 4 trade files use lowercase column names (`final_r` not `final_R`)

**Solution**: Already fixed in latest code. Re-run `.\deploy_phase6.ps1`

### Issue: "ManipScore file not found"

**Cause**: Phase 6B requires ManipScore data which may not be available

**Solution**: Skip Phase 6B by running:
```bash
python scripts/run_phase6_all.py --modules 6A 6C
```

### Issue: "No such file: results/param_sweep/ofi_param_sweep_ranking.csv"

**Cause**: Phase 5 not completed

**Solution**: Run Phase 5 first:
```bash
python scripts/run_ofi_param_sweep.py
```

---

## Next Steps

After reviewing Phase 6 results:

1. **Select Strategy**: Choose top 1-2 strategies for live testing
2. **Regime Optimization**: Identify best-performing regimes
3. **Long-Only Variant**: Consider implementing long-only version
4. **Walk-Forward Test**: Validate on out-of-sample data
5. **Production Build**: Implement real-time OFI calculation

---

**For detailed implementation notes, see**: `PHASE6_IMPLEMENTATION_SUMMARY.md`  
**For results analysis, see**: `PHASE6_COMPLETION_SUMMARY.md`

