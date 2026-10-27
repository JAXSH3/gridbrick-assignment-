# System Architecture & Technical Specifications

## 1. High-Level System Architecture

The UK Wind Day-Ahead Procurement Desk is built as a high-performance, containerized full-stack platform designed to reconstruct exact day-ahead wind forecasts without look-ahead leakage, quantitatively evaluate forecast performance, and size statistical safety buffers for trading desks.

```mermaid
flowchart TB
    subgraph External["External Public Feeds (Elexon BMRS)"]
        direction TB
        E_FUELHH["FUELHH Stream API<br/><b>Half-hourly Actuals (MW)</b><br/><code>fuelType=WIND</code>"]
        E_WINDFOR["WINDFOR Stream API<br/><b>Forecast Publications (MW)</b><br/><code>publishDateTimeFrom=...</code>"]
    end

    subgraph DataLayer["Storage & Cache Layer (Local)"]
        direction TB
        CLI_INGEST["Ingestion Engine CLI<br/><code>python -m app.ingest</code><br/>(httpx with jitter & backoff)"]
        SQLITE_DB[("Local SQLite Database<br/><b>data/energy_cache.db</b><br/>• actuals (1,541 rows)<br/>• forecasts (20,440 rows)<br/>• WAL mode + indexed")]
        CLI_INGEST -->|Idempotent Upsert| SQLITE_DB
    end

    subgraph BackendLayer["Backend Service (FastAPI / Python 3.12)"]
        direction TB
        REPO["Data Access Repository<br/>(Parameterized SQLite queries)"]
        DOMAIN["Pure Domain Services<br/>• Anti-leakage cutoff filter (D-1 cutoff)<br/>• Accuracy metrics (MAE, RMSE, Bias, nMAE)<br/>• Empirical safety buffer calculation<br/>• Lead-time horizon bucketing"]
        ROUTER["REST API v1 Router<br/>• /api/v1/health<br/>• /api/v1/forecast/latest<br/>• /api/v1/forecast/vintages<br/>• /api/v1/accuracy/summary<br/>• /api/v1/accuracy/by-horizon<br/>• /api/v1/accuracy/buffer"]
        MW["Middleware Stack<br/>• Request-ID (X-Request-ID)<br/>• JSON Structured Access Logger<br/>• CORS Middleware"]
        
        SQLITE_DB --> REPO --> DOMAIN --> ROUTER --> MW
    end

    subgraph FrontendLayer["Frontend Application (React 18 + Vite + TS)"]
        direction TB
        STORE["TanStack React Query Cache"]
        HDR["Header & Controls<br/>(Jan 2026 Picker, Preset Pills, Cutoff Time)"]
        DECISION["Decision Support Banner<br/>(Recommended Buffer MW & Interactive Slider)"]
        KPIS["Executive KPI Cards<br/>(MAE, RMSE, Bias, nMAE, P90, P95)"]
        CHART["Delivery Schedule Chart<br/>(Dual line/area Recharts series)"]
        MODAL["Forecast Evolution Modal<br/>(Successive vintages for clicked slot)"]
        TABS["Analytical Tabs<br/>(Horizon degradation, Diurnal, Regimes, Distribution)"]

        MW --> STORE
        STORE --> HDR
        STORE --> DECISION
        STORE --> KPIS
        STORE --> CHART
        STORE --> TABS
        CHART -.->|On Point Click| MODAL
    end

    E_FUELHH --> CLI_INGEST
    E_WINDFOR --> CLI_INGEST
```

---

## 2. Decision Cutoff & Anti-Leakage Workflow

A central requirement of power procurement is **never using future data** when evaluating past decisions. For delivery day $D$, the day-ahead market order is finalized on day $D-1$ at cutoff time $T_{cutoff}$ (default `09:00 UTC`).

```mermaid
sequenceDiagram
    autonumber
    actor Trader as Power Buyer
    participant UI as React Dashboard
    participant API as FastAPI Backend
    participant Domain as Domain Engine
    participant DB as SQLite Cache

    Trader->>UI: Selects Delivery Day D (e.g. 2026-01-15) & Cutoff (e.g. 09:00 UTC)
    UI->>API: GET /api/v1/forecast/latest?target_date=2026-01-15&cutoff=09:00
    API->>Domain: Calculate Cutoff Timestamp: D-1 09:00 UTC (2026-01-14T09:00:00Z)
    API->>DB: Query actuals and all candidate forecasts for 2026-01-15
    DB-->>API: Returns actuals (48 half-hours) & candidate forecasts
    API->>Domain: select_latest_forecasts_at_cutoff(forecasts, cutoff_dt)
    Note over Domain: Filter: publishTime <= cutoff_dt<br/>Strictly exclude publishTime > cutoff_dt<br/>Include boundary publishTime == cutoff_dt<br/>Group by startTime -> choose max(publishTime)
    API->>Domain: join_forecasts_and_actuals(selected_forecasts, actuals)
    Note over Domain: Compute Error = Forecast - Actual<br/>Compute Shortfall = max(0, F - A)<br/>Compute Surplus = max(0, A - F)
    API-->>UI: Returns DayForecastResponse (24 hourly slots + publish times + error)
    UI-->>Trader: Renders Delivery Schedule Chart with clear publishTime tooltips
```

---

## 3. Data Flow & Granularity Mapping

```mermaid
flowchart LR
    A["Elexon FUELHH (WIND)"] -->|"30-min resolution<br/>(:00 and :30)"| B["Actual Outturn (MW)"]
    C["Elexon WINDFOR"] -->|"Hourly resolution<br/>(:00:00Z)"| D["Forecast Vintages (MW)"]

    B & D --> E["StartTime Alignment"]
    E --> F["Paired Analysis Slots (744 January Hours)"]
    F --> G["Empirical Error & Buffer Sizing Engine"]
```
