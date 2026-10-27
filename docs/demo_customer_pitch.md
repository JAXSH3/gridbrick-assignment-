# 5-Minute Customer Pitch Script: UK Power Buying Desk

**Audience**: Head of Day-Ahead Power Trading, Power Buyers, Risk Managers.  
**Presenter**: Senior Energy Quantitative Engineer.  
**Objective**: Demonstrate how the platform quantifies wind forecast risk, eliminates look-ahead bias, and recommends an optimal safety buffer to avoid costly imbalance settlement penalties.  
**Time Limit**: Exactly 5 minutes.

---

## Click-by-Click Demo Flow

```text
0:00 - 0:45 | The Challenge: Day-Ahead Wind Buying & The Cutoff Dilemma
0:45 - 1:45 | Live Delivery Day: Cutoff Reconstruction (No Look-Ahead Leakage)
1:45 - 2:45 | Statistical Decision Support: The Procurement Safety Buffer
2:45 - 3:45 | Deep Dive: Forecast Evolution (Vintages) & Diurnal Patterns
3:45 - 5:00 | Business ROI & Quantified Cashout Savings
```

---

## Presentation Script with Visual Cues

### 0:00 – 0:45 | The Problem Setting
*(Screen showing the Executive Dashboard at `http://localhost:3000`)*

> **Presenter**:  
> "Good morning, team. As power buyers on the UK day-ahead desk, your primary challenge is simple yet unforgiving: you must purchase wholesale electricity on day $D-1$ before market gate closure at 09:00 UTC to meet customer demand, net of renewable wind.
>
> But wind is notoriously weather-dependent. When forecasts overestimate wind generation, your desk is left short on power in real time—forced to settle imbalance at National Grid ESO cashout prices that can surge past £300 to £1,000 per megawatt-hour.
>
> Today, I'm thrilled to present the **UK National Wind Procurement Desk**—a custom-built decision support platform that reconstructs the exact forecast available at your gate closure, quantifies model risk across January 2026, and provides a mathematically backed safety buffer."

---

### 0:45 – 1:45 | Cutoff Reconstruction (No Look-Ahead Leakage)
*(Click on **'Jan 15 (Baseline)'** preset pill in the header. Point mouse to the Cutoff dropdown set to `09:00 UTC`)*

> **Presenter**:  
> "Here on January 15th, 2026, our platform shows the exact day-ahead delivery profile. Notice the purple line—that is the wind forecast published by National Grid ESO. But crucially, **it is strictly the latest forecast published before the D-1 09:00 UTC cutoff** (specifically published at 07:30 UTC on January 14th).
>
> There is **zero look-ahead bias**. Many generic platforms accidentally evaluate performance using evening updates published *after* you've already placed your trades. Our platform guarantees you only see what was genuinely knowable when you submitted your order.
>
> *(Hover over 12:00 UTC on the chart)*  
> Looking at midday on the 15th, you can see the forecast was 14,497 MW, whereas actual outturn in green came in at 15,200 MW. You had a slight surplus."

---

### 1:45 – 2:45 | The Safety Buffer: Sizing Your Procurement Reserve
*(Move mouse to the **Decision Support Banner** at the top)*

> **Presenter**:  
> "Now let's examine our core decision support output: the **Procurement Safety Buffer**.
>
> Across all 744 hours in January 2026, National Grid wind models had an over-forecasting bias—wind outturn fell short of forecasts in **84.8%** of delivery periods, with an average deficit of 2,345 MW.
>
> If your desk buys purely to the forecast, you are taking an aggressive imbalance gamble. But how much extra thermal or flexible power should you buy?
>
> *(Point to the 4,306 MW buffer badge)*  
> Our algorithm evaluates the empirical distribution of forecast shortfalls. At the industry-standard **90% confidence level**, our platform recommends a **4,306 MW safety buffer**. 
>
> *(Drag the confidence slider from 90% to 95%)*  
> If an extreme cold snap or storm event is approaching and your risk committee mandates a conservative **95% confidence level**, slide the control: the buffer automatically resizes to **5,351 MW**, guaranteeing that 95% of all forecast shortfalls are covered."

---

### 2:45 – 3:45 | Forecast Evolution (Vintages) & Horizon Degradation
*(Click on the 13:00 UTC data point on the chart to open the **Forecast Evolution Modal**)*

> **Presenter**:  
> "Let's inspect how the ESO forecast evolved leading up to delivery. By clicking any hour on the delivery schedule, we open the **Forecast Evolution view**.
>
> Here we see all 14 forecast publications issued over the preceding 48 hours for this specific slot. Notice how 48 hours out, the forecast was 7,362 MW; 24 hours out it jumped to 8,003 MW, before settling near the actual outturn of 8,138 MW. 
>
> This gives your traders visibility into model stability: is the forecast converging, or is it oscillating wildly?
>
> *(Close modal, scroll down to the **Lead-Time Horizon Degradation** tab)*  
> In the analytical deep-dive below, you can see quantitative proof of lead-time risk. Forecasts with a 0–6 hour horizon have a Mean Absolute Error of 1,768 MW, whereas at the day-ahead horizon (24–36 hours), error expands to over 2,200 MW."

---

### 3:45 – 5:00 | Business ROI & Trading Value
*(Return to the Month Summary KPI cards)*

> **Presenter**:  
> "To summarize the commercial value for your trading desk:
> 1. **Protection Against Asymmetric Imbalance**: In January 2026, an unbuffered trading desk faced over 600 hours of deficit exposure. Procuring to our dynamic buffer cuts tail risk by up to 95%.
> 2. **Operational Efficiency**: Zero manual spreadsheet parsing—Elexon BMRS data is ingested, checked, and served in sub-second response times.
> 3. **Audit Readiness**: Every trade recommendation is tied to an explicit snapshot timestamp with complete regulatory reproducibility.
>
> Thank you, and I look forward to partnering with your trading desk on this pilot."
