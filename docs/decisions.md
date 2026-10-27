# Design Decisions & Domain Assumptions

This document outlines key technical and domain decisions made in building the UK Wind Day-Ahead Procurement Desk.

---

## 1. Decision Cutoff & Gate Closure Time

### Context & Assumption
In the UK power market, day-ahead power auctions and bilateral contracts close on day $D-1$ before delivery day $D$. Power buyers on the trading desk must lock in their day-ahead position based strictly on forecasts available at that decision moment.
- **Default Cutoff**: `09:00 UTC` on $D-1$.
- **Configurability**: Configurable via the environment variable `DEFAULT_CUTOFF_TIME` and dynamically via the UI cutoff dropdown (`07:00`, `09:00`, `11:00`, `12:00`, `17:00`).

### Mathematical Formulation
For target delivery date $D$:
$$\text{Cutoff Datetime} = \text{datetime}(D - 1\text{ day}, T_{cutoff}, \text{tz}=\text{UTC})$$

For each delivery slot $T_{start}$ on day $D$:
$$\text{Eligible Forecasts} = \{ \text{row} \mid \text{startTime} = T_{start} \land \text{publishTime} \le \text{Cutoff Datetime} \}$$
$$\text{Selected Forecast} = \arg\max_{\text{publishTime}} (\text{Eligible Forecasts})$$

### Boundary & Anti-Leakage Guarantee
- **Exact Boundary**: If $\text{publishTime} == \text{Cutoff Datetime}$, the forecast is valid and included.
- **Strict Exclusion**: Any forecast published at $\text{publishTime} > \text{Cutoff Datetime}$ is strictly excluded. This guarantees zero look-ahead bias.

---

## 2. Timezone & Granularity Alignment

### Timezone
All data is stored and processed in **UTC (ISO-8601)** (`YYYY-MM-DDTHH:MM:SSZ`). The UK operates on Greenwich Mean Time (UTC+0) throughout January 2026, meaning UTC aligns directly with local British time without daylight saving transitions.

### Granularity Adaptation (API Characteristics)
- **Actuals (`FUELHH`)**: Published at **30-minute settlement periods** (48 periods per day, 1,488 in January 2026).
- **Forecasts (`WINDFOR`)**: Published by the ESO at **hourly resolution** on the hour (`:00:00Z`, 24 target slots per day, 744 in January 2026).
- **Design Adaptation**: 
  - Accuracy metrics and safety buffer sizing are computed on the 744 hourly on-the-hour slots where both actual and forecast coexist.
  - The delivery schedule chart displays all target hours, with clear visual tooltips identifying publish timestamps and lead-time horizons.

---

## 3. Missing Data Treatment

1. **Missing Actuals**: If an actual outturn record is missing or corrupt, it is recorded as `NaN` / `None`, excluded from error metric computations, and flagged in data quality audit reports. (In our January 2026 dataset, coverage is 100.0% with zero missing periods).
2. **Missing Pre-Cutoff Forecasts**: If no forecast was published prior to cutoff for a slot, `forecast_mw` is set to `null`, excluding that slot from error aggregates while displaying a clear visual badge on the delivery schedule.
3. **Negative Horizons in WINDFOR Feeds**: The raw WINDFOR stream contains rolling files where some entries have $\text{startTime} < \text{publishTime}$ (historical retrospective records). For forward procurement analysis, only entries where $\text{publishTime} \le \text{Cutoff Datetime} < \text{startTime}$ (positive horizons $\ge 15\text{ hours}$) are eligible.

---

## 4. Accuracy Metric Formulations

Given $N$ valid paired slots with forecast $F_i$ and actual $A_i$:

1. **Forecast Error**:
   $$e_i = F_i - A_i$$
   - $e_i > 0$: Over-forecast (utility expected more wind than was generated; exposed to deficit shortfall).
   - $e_i < 0$: Under-forecast (utility experienced surplus wind).

2. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |F_i - A_i|$$

3. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (F_i - A_i)^2}$$
   *Penalizes severe forecast blunders quadratically, reflecting non-linear thermal ramping costs.*

4. **Forecast Bias (Mean Error)**:
   $$\text{Bias} = \frac{1}{N} \sum_{i=1}^N (F_i - A_i)$$

5. **Normalized MAE (nMAE)**:
   $$\text{nMAE} = \frac{\text{MAE}}{\frac{1}{N}\sum A_i} \times 100\%$$
   *Industry-standard metric for power utilities. Unlike MAPE ($\frac{|F-A|}{A}$), nMAE does not divide by near-zero generation on calm wind days and remains mathematically stable across all weather regimes.*

6. **Percentiles of Absolute Error**:
   - $P_{50}$: Median error (MW).
   - $P_{90}$: 90% of observed errors fall below this value.
   - $P_{95}$: 95% tail risk bound.

---

## 5. Statistical Safety Buffer Formulation

### Imbalance Risk Model
When a power buying desk procures thermal/alternative energy to cover $\text{Demand} - F$, any shortfall $F > A$ leaves the utility short on energy in real-time, incurring expensive imbalance cashout prices.

For each period $i$, the shortfall is:
$$S_i = \max(0, F_i - A_i)$$

### Sizing the Safety Buffer
To guarantee with confidence level $C$ (e.g. $90\%$ or $95\%$) that procurement shortfall does not exceed the reserve buffer $B_C$:
$$B_C = \text{Quantile}_C(\{ S_i \})$$

- At **90% confidence**, the recommended buffer $B_{90}$ ensures that unhedged deficit events occur in $\le 10\%$ of delivery periods.
- The platform also computes the shortfall exposure rate ($\%$ of periods with $F > A$) and average deficit magnitude during shortfalls.
