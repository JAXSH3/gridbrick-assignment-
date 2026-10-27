import { useQuery } from "@tanstack/react-query";
import { X, History, AlertCircle } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import { fetchVintages } from "../api/client";

interface VintageModalProps {
  startTime: string | null;
  onClose: () => void;
}

export const VintageModal: React.FC<VintageModalProps> = ({ startTime, onClose }) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ["vintages", startTime],
    queryFn: () => (startTime ? fetchVintages(startTime) : Promise.reject("No start time")),
    enabled: !!startTime,
  });

  if (!startTime) return null;

  const slotFormatted = startTime.replace("T", " ").replace("Z", " UTC");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <History size={18} color="var(--accent-wind)" />
              <h3>Forecast Evolution (Vintages)</h3>
            </div>
            <p>
              Target Delivery Slot: <strong>{slotFormatted}</strong>
              {data?.actual_mw !== null && data?.actual_mw !== undefined && (
                <span style={{ marginLeft: 12, color: "var(--accent-actual)" }}>
                  Final Actual Outturn: <strong className="num">{data.actual_mw.toLocaleString()} MW</strong>
                </span>
              )}
            </p>
          </div>

          <button type="button" className="close-btn" onClick={onClose} aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        {isLoading && (
          <div className="state-box">
            <div className="spinner" />
            <span>Loading forecast vintages...</span>
          </div>
        )}

        {error && (
          <div className="state-box" style={{ color: "var(--accent-shortfall)" }}>
            <AlertCircle size={24} />
            <span>Failed to load vintages: {String(error)}</span>
          </div>
        )}

        {data && data.vintages.length > 0 && (
          <>
            {/* Evolution Line Chart */}
            <div style={{ width: "100%", height: 260 }}>
              <ResponsiveContainer>
                <LineChart
                  data={data.vintages.map((v) => ({
                    ...v,
                    displayPublish: v.publish_time.substring(5, 16).replace("T", " "),
                  }))}
                  margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="displayPublish"
                    stroke="#64748b"
                    fontSize={10}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={10}
                    tickLine={false}
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(15, 23, 42, 0.95)",
                      borderColor: "rgba(255, 255, 255, 0.15)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(val: any) => [`${Number(val).toLocaleString()} MW`, "Forecast"]}
                    labelFormatter={(lbl) => `Published: ${lbl} UTC`}
                  />

                  {data.actual_mw !== null && (
                    <ReferenceLine
                      y={data.actual_mw}
                      stroke="#10b981"
                      strokeDasharray="4 4"
                      label={{
                        value: `Actual: ${data.actual_mw} MW`,
                        position: "insideTopRight",
                        fill: "#10b981",
                        fontSize: 10,
                      }}
                    />
                  )}

                  <Line
                    type="stepAfter"
                    dataKey="forecast_mw"
                    stroke="#818cf8"
                    strokeWidth={2}
                    dot={{ r: 4, fill: "#818cf8" }}
                    activeDot={{ r: 6, fill: "#0ea5e9" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Vintages Table */}
            <div style={{ overflowX: "auto", maxHeight: 240 }}>
              <table className="vintages-table">
                <thead>
                  <tr>
                    <th>Publication Time (UTC)</th>
                    <th>Lead Time (Horizon)</th>
                    <th>Forecast Generation</th>
                    <th>Delta vs Previous</th>
                    <th>Delta vs Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {data.vintages.map((v, idx) => {
                    const prev = idx > 0 ? data.vintages[idx - 1] : null;
                    const deltaPrev = prev ? v.forecast_mw - prev.forecast_mw : null;
                    const deltaAct = data.actual_mw !== null ? v.forecast_mw - data.actual_mw : null;

                    return (
                      <tr key={v.publish_time}>
                        <td className="num">{v.publish_time.replace("T", " ").replace("Z", "")}</td>
                        <td className="num">{v.horizon_hours} hours</td>
                        <td className="num" style={{ fontWeight: 600 }}>
                          {v.forecast_mw.toLocaleString()} MW
                        </td>
                        <td className="num">
                          {deltaPrev !== null ? (
                            <span style={{ color: deltaPrev >= 0 ? "var(--accent-wind)" : "var(--accent-warning)" }}>
                              {deltaPrev >= 0 ? `+${deltaPrev.toFixed(1)}` : deltaPrev.toFixed(1)} MW
                            </span>
                          ) : (
                            <span style={{ color: "var(--text-faint)" }}>— (Initial)</span>
                          )}
                        </td>
                        <td className="num">
                          {deltaAct !== null ? (
                            <span style={{ color: deltaAct > 0 ? "var(--accent-shortfall)" : "var(--accent-actual)" }}>
                              {deltaAct > 0 ? `+${deltaAct.toFixed(1)}` : deltaAct.toFixed(1)} MW
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
