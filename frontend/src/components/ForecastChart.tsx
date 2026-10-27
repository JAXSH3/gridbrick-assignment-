import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { Info, ExternalLink } from "lucide-react";
import { DayForecastResponse, ForecastSlotItem } from "../types/api";

interface ForecastChartProps {
  dayForecast?: DayForecastResponse;
  onSlotClick: (startTime: string) => void;
  isLoading?: boolean;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: ForecastSlotItem }>;
}

const CustomChartTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const slot = payload[0].payload;

  const slotTime = slot.start_time.substring(11, 16);
  const isDeficit = slot.error_mw !== null && slot.error_mw > 0;

  return (
    <div className="custom-tooltip">
      <div className="tooltip-time">
        Delivery Slot: {slotTime} UTC ({slot.start_time.substring(0, 10)})
      </div>

      <div className="tooltip-row">
        <span style={{ color: "var(--accent-forecast)" }}>Cutoff-Selected Forecast:</span>
        <strong className="num">
          {slot.forecast_mw !== null ? `${slot.forecast_mw.toLocaleString()} MW` : "N/A"}
        </strong>
      </div>

      <div className="tooltip-row">
        <span style={{ color: "var(--accent-actual)" }}>Actual Outturn Generation:</span>
        <strong className="num">
          {slot.actual_mw !== null ? `${slot.actual_mw.toLocaleString()} MW` : "N/A"}
        </strong>
      </div>

      {slot.error_mw !== null && (
        <div className="tooltip-row">
          <span>Error (F - A):</span>
          <strong
            className="num"
            style={{ color: isDeficit ? "var(--accent-shortfall)" : "var(--accent-actual)" }}
          >
            {slot.error_mw > 0 ? `+${slot.error_mw}` : slot.error_mw} MW
            {isDeficit ? " (Shortfall)" : " (Surplus)"}
          </strong>
        </div>
      )}

      {slot.publish_time && (
        <div className="tooltip-row" style={{ fontSize: "0.75rem", color: "var(--text-faint)", marginTop: 4 }}>
          <span>Published at Cutoff:</span>
          <span className="num">{slot.publish_time.replace("T", " ").replace("Z", "")} UTC</span>
        </div>
      )}

      {slot.horizon_hours !== null && (
        <div className="tooltip-row" style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
          <span>Decision Lead Time:</span>
          <span className="num">{slot.horizon_hours} hours</span>
        </div>
      )}

      <div className="tooltip-hint">
        <ExternalLink size={10} style={{ display: "inline", marginRight: 4 }} />
        Click point to inspect forecast evolution across vintages
      </div>
    </div>
  );
};

export const ForecastChart: React.FC<ForecastChartProps> = ({
  dayForecast,
  onSlotClick,
  isLoading,
}) => {
  if (isLoading || !dayForecast) {
    return (
      <div className="card chart-card" style={{ minHeight: 400 }}>
        <div className="state-box" style={{ margin: "auto" }}>
          <div className="spinner" />
          <span>Loading delivery schedule and cutoff forecasts...</span>
        </div>
      </div>
    );
  }

  // Format chart data
  const chartData = dayForecast.slots.map((slot) => ({
    ...slot,
    displayTime: slot.start_time.substring(11, 16),
  }));

  const handleClick = (state: any) => {
    if (state && state.activePayload && state.activePayload.length) {
      const clickedSlot: ForecastSlotItem = state.activePayload[0].payload;
      onSlotClick(clickedSlot.start_time);
    }
  };

  return (
    <div className="card chart-card">
      <div className="chart-header">
        <div className="chart-title-wrap">
          <h2>Forecast at Decision Cutoff vs Actual Generation</h2>
          <p>
            Delivery Day: <strong>{dayForecast.target_date}</strong> | Evaluated at D-1{" "}
            <strong>{dayForecast.cutoff_time} UTC</strong> ({dayForecast.cutoff_datetime})
          </p>
        </div>

        <div className="chart-legend-custom">
          <div className="legend-item">
            <div className="legend-color" style={{ background: "var(--accent-actual)" }} />
            <span>Actual Outturn (FUELHH)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: "var(--accent-forecast)" }} />
            <span>Forecast at Cutoff (WINDFOR)</span>
          </div>
        </div>
      </div>

      <div style={{ width: "100%", height: 380 }}>
        <ResponsiveContainer>
          <ComposedChart
            data={chartData}
            margin={{ top: 15, right: 20, left: 10, bottom: 5 }}
            onClick={handleClick}
            style={{ cursor: "pointer" }}
          >
            <defs>
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />

            <XAxis
              dataKey="displayTime"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              interval={3}
            />

            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              domain={["auto", "auto"]}
              label={{
                value: "Generation (MW)",
                angle: -90,
                position: "insideLeft",
                fill: "#64748b",
                fontSize: 11,
              }}
            />

            <Tooltip content={<CustomChartTooltip />} />

            {/* Actual Outturn Area */}
            <Area
              type="monotone"
              dataKey="actual_mw"
              stroke="#10b981"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#actualGradient)"
              name="Actual Wind"
            />

            {/* Forecast Line */}
            <Line
              type="monotone"
              dataKey="forecast_mw"
              stroke="#818cf8"
              strokeWidth={2.5}
              dot={{ r: 3, fill: "#818cf8" }}
              activeDot={{ r: 6, fill: "#0ea5e9", stroke: "#fff" }}
              name="Selected Forecast"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-faint)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <Info size={13} />
          Anti-leakage enforced: No forecast published after {dayForecast.cutoff_time} UTC on D-1 is used.
        </span>
        <span>Click any delivery slot to open the Forecast Evolution drawer</span>
      </div>
    </div>
  );
};
