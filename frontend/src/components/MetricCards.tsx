import { HelpCircle, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { AccuracySummaryResponse } from "../types/api";

interface MetricCardsProps {
  summary?: AccuracySummaryResponse;
  isLoading?: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ summary, isLoading }) => {
  if (isLoading || !summary) {
    return (
      <div className="kpi-grid">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="kpi-card" style={{ minHeight: 110, justifyContent: "center" }}>
            <div className="spinner" style={{ width: 24, height: 24, margin: "0 auto" }} />
          </div>
        ))}
      </div>
    );
  }

  const isOverForecast = summary.bias > 0;

  return (
    <div className="kpi-grid">
      {/* MAE */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">Mean Absolute Error</span>
          <span
            className="info-icon"
            title="MAE: The average magnitude of day-ahead forecast error in MW without regard to direction. Measures general expected deviation."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div>
          <span className="kpi-val num">{summary.mae.toLocaleString()}</span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-meta">
          <span>{summary.sample_size} delivery periods evaluated</span>
        </div>
      </div>

      {/* RMSE */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">Root Mean Squared Error</span>
          <span
            className="info-icon"
            title="RMSE: Heavily penalizes large forecast blunders quadratically. Crucial for grid stability and thermal ramping risk."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div>
          <span className="kpi-val num">{summary.rmse.toLocaleString()}</span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-meta">
          <span>Spread vs MAE: +{(summary.rmse - summary.mae).toFixed(1)} MW</span>
        </div>
      </div>

      {/* Forecast Bias */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">Forecast Bias (Mean Error)</span>
          <span
            className="info-icon"
            title="Bias: Forecast minus Actual. Positive indicates the model systematically over-predicts wind generation; negative indicates under-prediction."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "baseline" }}>
          <span
            className="kpi-val num"
            style={{ color: isOverForecast ? "var(--accent-shortfall)" : "var(--accent-actual)" }}
          >
            {summary.bias > 0 ? `+${summary.bias}` : summary.bias}
          </span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-meta">
          {isOverForecast ? (
            <span style={{ color: "var(--accent-shortfall)", display: "flex", alignItems: "center", gap: 3 }}>
              <ArrowUpRight size={13} /> Over-forecasting tendency
            </span>
          ) : (
            <span style={{ color: "var(--accent-actual)", display: "flex", alignItems: "center", gap: 3 }}>
              <ArrowDownRight size={13} /> Conservative under-forecast
            </span>
          )}
        </div>
      </div>

      {/* Normalized MAE (nMAE) */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">Normalized MAE (nMAE)</span>
          <span
            className="info-icon"
            title="nMAE: MAE divided by Mean Actual Generation (11,581 MW). Power industry standard that avoids MAPE distortion during low-wind periods."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div>
          <span className="kpi-val num" style={{ color: "var(--accent-wind)" }}>
            {summary.nmae_pct}%
          </span>
        </div>
        <div className="kpi-meta">
          <span>Mean Actual: {(summary.mean_actual_mw / 1000).toFixed(1)} GW</span>
        </div>
      </div>

      {/* P90 Absolute Error */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">P90 Absolute Error</span>
          <span
            className="info-icon"
            title="P90: 90% of all forecast error deviations fall within this threshold. Fundamental metric for safety sizing."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div>
          <span className="kpi-val num">{summary.p90_abs_error.toLocaleString()}</span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-meta">
          <span>Median (P50): {summary.p50_abs_error.toLocaleString()} MW</span>
        </div>
      </div>

      {/* P95 Absolute Error */}
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-title">P95 Absolute Error</span>
          <span
            className="info-icon"
            title="P95: 95th percentile error bound. Defines the extreme tail risk of day-ahead wind forecasts."
          >
            <HelpCircle size={15} />
          </span>
        </div>
        <div>
          <span className="kpi-val num" style={{ color: "var(--accent-warning)" }}>
            {summary.p95_abs_error.toLocaleString()}
          </span>
          <span className="kpi-unit">MW</span>
        </div>
        <div className="kpi-meta">
          <span>Peak Error: {summary.max_abs_error.toLocaleString()} MW</span>
        </div>
      </div>
    </div>
  );
};
