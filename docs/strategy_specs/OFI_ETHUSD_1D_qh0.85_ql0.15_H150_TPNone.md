# OFI_ETHUSD_1D_qh0.85_ql0.15_H150_TPNone

**Strategy Type**: OFI-based Trend Following
**Market**: ETHUSD
**Timeframe**: 1D
**Generated**: 2025-11-19

---

## Overview

This strategy uses **Order Flow Imbalance (OFI)** as the primary signal to identify 
high-probability trend opportunities in ETHUSD on 1D timeframe.

**Key Characteristics**:
- Entry mode: **TREND**
- Signal thresholds: OFI_z >= 0.85 (long) or <= 0.85 (short)
- Maximum holding period: **150 bars**
- Take profit: **None** (trailing exit only)
- Historical trades: **104**

---

## Market & Timeframe

**Symbol**: ETHUSD

**Asset Class**: Cryptocurrency

Cryptocurrencies exhibit strong order flow dynamics due to:
- High retail participation
- Transparent order book data
- 24/7 trading with continuous price discovery

**Timeframe**: 1D

---

## Factor Construction

### Order Flow Imbalance (OFI)

OFI measures the imbalance between buy and sell volume:

```
OFI_raw = (buy_volume - sell_volume) / (total_volume + ε)
```

**Standardization**:
```
OFI_z = (OFI_raw - rolling_mean(OFI_raw, 200)) / rolling_std(OFI_raw, 200)
```

**Interpretation**:
- OFI_z > 0: Net buying pressure
- OFI_z < 0: Net selling pressure
- |OFI_z| >= 0.85 quantile: Strong signal

---

## Entry Rules

**Entry Mode**: TREND

**Long Entry**:
- OFI_z >= 0.85 quantile (strong buying pressure)
- Direction: LONG (follow the order flow)

**Short Entry**:
- OFI_z <= 0.15 quantile (strong selling pressure)
- Direction: SHORT (follow the order flow)

**Position Sizing**:
- Fixed notional: 1.0 unit
- Risk per trade: 1 ATR (20-period rolling_mean)

---

## Exit Rules

**Exit Priority** (checked in order):

1. **Take Profit**: None (disabled)
2. **Trailing Stop**: Exit when price gives back all MFE (Maximum Favorable Excursion)
   - Trigger: current_R <= entry_R (i.e., loss_from_peak >= MFE_R)
3. **Maximum Holding**: Exit after 150 bars
4. **End of Data**: Exit at last available bar

**Rationale**:
- Trailing stop allows profits to run while protecting against full reversal
- Hmax=150 prevents indefinite holding in sideways markets

---

## Transaction Costs

**Cost Model**: Per-side percentage of entry/exit price

**Scenarios**:
- **Low Cost**: 0.0030% per side (0.0060% round-trip)
- **High Cost**: 0.0700% per side (0.1400% round-trip)

**Cost Calculation**:
```
cost_price = per_side_rate × entry_price + per_side_rate × exit_price
cost_R = cost_price / ATR_entry
final_R_net = final_R_gross - cost_R
```

---

## Historical Performance

**Sample Period**: Based on available historical data

### Key Metrics (High-Cost Scenario)

| Metric | Value |
|--------|-------|
| Total Trades | 104 |
| Mean R (Net) | 1.254 |
| Sharpe Ratio | 0.138 |
| Win Rate | 8.7% |
| Median MFE | 0.486R |
| 75th pct MFE | 1.134R |
| 90th pct MFE | 7.788R |
| Median MAE | -0.561R |

### Exit Reason Distribution

| Exit Reason | Percentage |
|-------------|------------|
| Trailing Stop | 90.4% |
| Max Holding (Hmax) | 8.7% |

### Performance Comparison

| Cost Scenario | Mean R (Net) | Sharpe Ratio |
|---------------|--------------|--------------|
| Low Cost (0.0030%) | 1.281 | 0.141 |
| High Cost (0.0700%) | 1.254 | 0.138 |

---

## Notes & Caveats

### Strengths

- **Positive Expectancy**: Strategy shows positive expected R-multiple even under high costs
- **Trend Capture**: Trailing exit allows capturing extended moves
- **Risk Management**: Fixed R-multiple framework provides consistent risk sizing

### Limitations

- **Low Win Rate**: Typical of trend-following strategies (~5-10%)
- **Requires Patience**: Long holding periods (up to Hmax bars)
- **Market Regime Dependent**: Performance may vary across different market conditions
- **Slippage Not Modeled**: Actual execution costs may be higher than modeled

### Implementation Considerations

1. **Data Quality**: Requires high-quality tick data for accurate OFI calculation
2. **Execution**: Use limit orders where possible to minimize slippage
3. **Position Sizing**: Consider portfolio-level risk management
4. **Monitoring**: Track actual vs expected performance metrics
5. **Regime Awareness**: Consider pausing strategy during extreme volatility events

### Recommended Next Steps

1. **Walk-Forward Testing**: Validate on out-of-sample data
2. **Live Paper Trading**: Test execution infrastructure
3. **Regime Analysis**: Analyze performance across different market regimes
4. **Portfolio Integration**: Combine with other uncorrelated strategies

---

## Disclaimer

This strategy specification is for research and educational purposes only. 
Past performance does not guarantee future results. 
Always conduct thorough due diligence and risk assessment before deploying any trading strategy.
