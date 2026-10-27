# 5-Minute Technical Walkthrough Script: Engineering Lead Review

**Audience**: Internal Technical Lead, Senior Full-Stack Reviewers, Quant Architects.  
**Presenter**: Senior Full-Stack Engineer.  
**Objective**: Explain the software architecture, cutoff anti-leakage implementation, data engineering pipeline, test rigor, CI/CD, and trade-offs.  
**Time Limit**: Exactly 5 minutes.

---

## Click-by-Click Demo Order

```text
0:00 - 1:00 | Architecture & Data Pipeline (Elexon BMRS Ingestion & Caching)
1:00 - 2:15 | Domain Core: Anti-Leakage Cutoff Engine & Boundary Math
2:15 - 3:15 | Statistical Rigor: Hand-Calculated Ground Truth & Test Suite
3:15 - 4:15 | Frontend Engineering: React, TanStack Query, Recharts
4:15 - 5:00 | Production Readiness: Docker, CI/CD, Trade-offs & Next Steps
```

---

## Technical Walkthrough Script

### 0:00 – 1:00 | Architecture & Data Engineering
*(Show Architecture Diagram from `docs/architecture.md`)*

> **Presenter**:  
> "Hi team. For this assignment, I designed a decoupled, high-performance architecture built on Python 3.12, FastAPI, SQLite with WAL mode, and a React 18 + TypeScript single-page application.
>
> Our data source is exclusively the public Elexon BMRS streaming APIs:
> - `FUELHH/stream` filtered by `fuelType=WIND` for outturn generation.
> - `WINDFOR/stream` for wind forecast publications.
>
> In `app.services.ingestion`, we built an asynchronous chunking ingestor with exponential backoff and jitter (`httpx`). Ingesting January 2026 yielded:
> - **1,541 actual records** (1,488 in January with **100% complete coverage**, zero missing half-hours).
> - **20,440 forecast records**.
>
> **Key API Discovery**: WINDFOR publishes target forecasts on the hour (`:00:00Z`), whereas FUELHH publishes half-hourly outturns. Additionally, WINDFOR batches include retrospective rolling historical hours (`horizon < 0`). We store the calculated lead-time horizon `(startTime - publishTime)` in hours, indexed on `(startTime, publishTime)`."

---

### 1:00 – 2:15 | The Cutoff Engine & Anti-Leakage Math
*(Open code `backend/app/services/domain.py` highlighting `select_latest_forecasts_at_cutoff`)*

> **Presenter**:  
> "The heart of our platform is the domain engine. In quantitative power trading, look-ahead bias is fatal. If delivery is day $D$, orders are locked on $D-1$ at cutoff time $T_{cutoff}$ (09:00 UTC default).
>
> In `select_latest_forecasts_at_cutoff`, we apply two strict invariants:
> 1. **Filter $publishTime \le cutoff\_dt$**:
>    - If $publishTime == cutoff\_dt$, it is included (exact boundary condition).
>    - If $publishTime > cutoff\_dt$, it is strictly excluded.
> 2. **Group by target `startTime` and select $\arg\max(publishTime)$**.
>
> Because $cutoff\_dt$ is at least 15 hours prior to the start of day $D$, all selected forecasts have positive horizons of 15.0 to 39.5 hours. It is mathematically impossible for post-decision forecasts to leak into the procurement evaluation."

---

### 2:15 – 3:15 | Testing Rigor & Hand-Calculated Ground Truth
*(Open terminal showing pytest output with 26 passing tests)*

> **Presenter**:  
> "We treated test rigor as a primary deliverable:
> 1. **Cutoff Boundary Tests (`test_cutoff.py`)**: Tests verify that a forecast at `09:00:00Z` is included, while a forecast at `09:00:01Z` (one second later) is excluded.
> 2. **Hand-Computed Metric Verification (`test_domain_metrics.py`)**: Rather than testing against placeholder data, we wrote hand-calculated test vectors where MAE (225.0 MW), RMSE (287.2 MW), Bias (+125.0 MW), and nMAE (9.47%) are verified against exact analytical math.
> 3. **Buffer Sizing Tests (`test_buffer.py`)**: Verifies 90% and 95% shortfall quantile calculations against manual distribution rankings.
> 4. **API Integration Tests (`test_api.py`)**: Fast integration tests with FastAPI `TestClient` verifying every route, 422 validations, and `X-Request-ID` tracing."

---

### 3:15 – 4:15 | Frontend Engineering & UX
*(Show browser dashboard at `http://localhost:3000`)*

> **Presenter**:  
> "For the frontend, we built a responsive React 18 + TypeScript application powered by Vite and TanStack Query:
> - **State & Caching**: TanStack Query ensures that repeated date or cutoff queries are served instantly from client-side memory without redundant network round-trips.
> - **Visual Aesthetics**: Clean energy trading desk theme with electric cyan, generation emerald, and shortfall coral.
> - **Interactive Vintages**: Clicking any delivery slot in the Recharts delivery schedule opens a modal fetching `/api/v1/forecast/vintages`, plotting the step-wise evolution of forecasts over the preceding 48 hours.
> - **Analytical Deep-Dives**: Four tabs covering lead-time horizon degradation (0-48h), diurnal 24h bias, generation regimes (Low/Med/High), and error distribution histograms."

---

### 4:15 – 5:00 | Production Readiness, Trade-Offs & Next Steps
*(Show `docker-compose.yml` and `render.yaml`)*

> **Presenter**:  
> "Production readiness:
> - **Containerization**: Multi-stage `Dockerfile` for frontend (Nginx with gzip, security headers, and reverse proxy) and backend (Python 3.12-slim with healthcheck). `docker-compose.yml` spins both up with one command.
> - **CI/CD**: GitHub Actions pipeline runs Ruff formatting, Ruff linting, Mypy type-checking, Pytest, and Vitest.
> - **Deployment**: Backend is configured for one-click deployment via `render.yaml`; frontend is deployable directly to Vercel via `VITE_API_URL`.
>
> **Key Trade-Offs & Roadmap**:
> 1. *Data Resolution*: We maintained raw hourly forecast resolution to preserve original Elexon data fidelity rather than synthetically interpolating half-hours. A next iteration could offer cubic spline interpolation.
> 2. *Dynamic Imbalance Pricing*: We modeled shortfall MW; the natural next phase is joining with Elexon System Sell/Buy Price (SSP/SBP) to output financial cashout £ risk alongside MW buffers.
>
> Thank you! I welcome your questions and code review."
