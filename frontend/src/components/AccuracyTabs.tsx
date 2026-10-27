import { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  Legend,
} from "recharts";
import {
  HourAccuracyResponse,
  HorizonAccuracyResponse,
  WindLevelAccuracyResponse,
  ErrorDistributionResponse,
} from "../types/api";

interface AccuracyTabsProps {
  horizonData?: HorizonAccuracyResponse;
  hourData?: HourAccuracyResponse;
  windLevelData?: WindLevelAccuracyResponse;
  distributionData?: ErrorDistributionResponse;
  isLoading?: boolean;
}

export const AccuracyTabs: React.FC<AccuracyTabsProps> = ({
  horizonData,
  hourData,
  windLevelData,
  distributionData,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<"horizon" | "hour" | "wind" | "distribution">(
    "horizon"
  );

  return (
    <div className="card tabs-card">
      {/* Navigation */}
      <div className="tabs-nav">
        <button
          type="button"
          className={`tab-btn ${activeTab === "horizon" ? "active" : ""}`}
          onClick={() => setActiveTab("horizon")}
        >
          Lead-Time Horizon Degradation (0–48h)
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "hour" ? "active" : ""}`}
          onClick={() => setActiveTab("hour")}
        >
          Diurnal Hour-of-Day Profile (24h)
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "wind" ? "active" : ""}`}
          onClick={() => setActiveTab("wind")}
        >
          Wind Generation Regimes (Low / Med / High)
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === "distribution" ? "active" : ""}`}
          onClick={() => setActiveTab("distribution")}
        >
          Error Distribution & Quantile Risk
        </button>
      </div>

      {isLoading && (
        <div className="state-box" style={{ padding: "40px 0" }}>
          <div className="spinner" />
          <span>Calculating analytical breakdowns...</span>
        </div>
      )}

      {!isLoading && (
        <>
          {/* TAB 1: Horizon Degradation */}
          {activeTab === "horizon" && horizonData && (
            <div>
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#fff" }}>
                  Forecast Accuracy Degradation by Lead Time
                </h3>
                <p style={{ margin: "4px 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Evaluates all forward forecast publications in January 2026. Error (MAE & RMSE) expands as lead time increases from 0-6h out to 36-48h.
                </p>
              </div>

              <div style={{ width: "100%", height: 320 }}>
                <ResponsiveContainer>
                  <BarChart
                    data={horizonData.buckets}
                    margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="bucket" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(v) => `${v} MW`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(15, 23, 42, 0.95)",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(val: any, name: any) => [
                        `${Number(val).toLocaleString()} MW`,
                        name === "mae" ? "MAE (Mean Absolute Error)" : "RMSE (Root Mean Square)",
                      ]}
                    />
                    <Legend />
                    <Bar dataKey="mae" fill="#0ea5e9" name="MAE (MW)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="rmse" fill="#818cf8" name="RMSE (MW)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 2: Diurnal Profile */}
          {activeTab === "hour" && hourData && (
            <div>
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#fff" }}>
                  Diurnal Bias and Error Across 24 Hours (UTC)
                </h3>
                <p style={{ margin: "4px 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Reveals systematic morning ramp or evening peak over/under-forecast tendencies.
                </p>
              </div>

              <div style={{ width: "100%", height: 320 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={hourData.hours}
                    margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="hour_label" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(15, 23, 42, 0.95)",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="avg_actual_mw"
                      stroke="#10b981"
                      strokeWidth={2}
                      name="Average Actual (MW)"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="avg_forecast_mw"
                      stroke="#818cf8"
                      strokeWidth={2}
                      name="Average Forecast (MW)"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="mae"
                      stroke="#0ea5e9"
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      name="MAE (MW)"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 3: Wind Generation Regimes */}
          {activeTab === "wind" && windLevelData && (
            <div>
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#fff" }}>
                  Accuracy Across Wind Generation Regimes
                </h3>
                <p style={{ margin: "4px 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Performance partitioned into Low (&lt;6 GW), Medium (6–13 GW), and High (&gt;13 GW) actual wind outturn.
                </p>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
                {windLevelData.regimes.map((r) => (
                  <div
                    key={r.regime}
                    style={{
                      background: "rgba(15, 23, 42, 0.7)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      padding: "16px 20px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <span style={{ fontSize: "1.05rem", fontWeight: 700, color: "#fff" }}>
                        {r.regime} Wind
                      </span>
                      <span style={{ fontSize: "0.78rem", color: "var(--text-faint)" }}>
                        {r.range_label}
                      </span>
                    </div>

                    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6, fontSize: "0.84rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-muted)" }}>Sample Size:</span>
                        <strong className="num">{r.sample_size} slots</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-muted)" }}>MAE:</span>
                        <strong className="num">{r.mae.toLocaleString()} MW</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-muted)" }}>RMSE:</span>
                        <strong className="num">{r.rmse.toLocaleString()} MW</strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-muted)" }}>Normalized MAE:</span>
                        <strong className="num" style={{ color: "var(--accent-wind)" }}>
                          {r.nmae_pct}%
                        </strong>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "var(--text-muted)" }}>Bias:</span>
                        <strong
                          className="num"
                          style={{ color: r.bias > 0 ? "var(--accent-shortfall)" : "var(--accent-actual)" }}
                        >
                          {r.bias > 0 ? `+${r.bias}` : r.bias} MW
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: Error Distribution */}
          {activeTab === "distribution" && distributionData && (
            <div>
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: "1rem", color: "#fff" }}>
                  Empirical Error Distribution Histogram (Forecast − Actual)
                </h3>
                <p style={{ margin: "4px 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Positive values indicate shortfalls (utility short on wind); negative values indicate surplus wind.
                </p>
              </div>

              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <BarChart
                    data={distributionData.bins}
                    margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis
                      dataKey="bin_mid"
                      stroke="#64748b"
                      fontSize={10}
                      tickLine={false}
                      tickFormatter={(v) => `${v > 0 ? `+${v}` : v}`}
                    />
                    <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(15, 23, 42, 0.95)",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                      formatter={(val: any, _name: any, item: any) => [
                        `${val} periods (${item.payload.type})`,
                        `Range: [${item.payload.bin_start} to ${item.payload.bin_end} MW]`,
                      ]}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {distributionData.bins.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.bin_mid > 0 ? "var(--accent-shortfall)" : "var(--accent-actual)"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Quantiles Bar */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-around",
                  background: "rgba(15, 23, 42, 0.6)",
                  padding: "10px 14px",
                  borderRadius: "var(--radius-sm)",
                  marginTop: 10,
                  fontSize: "0.82rem",
                }}
              >
                <span>P10: <strong className="num">{distributionData.quantiles.p10} MW</strong></span>
                <span>P25: <strong className="num">{distributionData.quantiles.p25} MW</strong></span>
                <span>Median (P50): <strong className="num">{distributionData.quantiles.p50} MW</strong></span>
                <span>P75: <strong className="num">+{distributionData.quantiles.p75} MW</strong></span>
                <span>P90 (Tail Shortfall): <strong className="num" style={{ color: "var(--accent-shortfall)" }}>+{distributionData.quantiles.p90} MW</strong></span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
