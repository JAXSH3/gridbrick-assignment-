import { Wind, Clock, Calendar } from "lucide-react";
import { HealthResponse } from "../types/api";

interface HeaderProps {
  targetDate: string;
  onTargetDateChange: (date: string) => void;
  cutoffTime: string;
  onCutoffTimeChange: (cutoff: string) => void;
  health?: HealthResponse;
}

const PRESET_DATES = [
  { label: "Jan 10 (Storm)", date: "2026-01-10" },
  { label: "Jan 15 (Baseline)", date: "2026-01-15" },
  { label: "Jan 22 (Low Wind)", date: "2026-01-22" },
  { label: "Jan 31 (Month-End)", date: "2026-01-31" },
];

export const Header: React.FC<HeaderProps> = ({
  targetDate,
  onTargetDateChange,
  cutoffTime,
  onCutoffTimeChange,
  health,
}) => {
  return (
    <header className="app-header">
      <div className="header-inner">
        {/* Brand & Subtitle */}
        <div className="brand-section">
          <div className="brand-icon-wrap">
            <Wind size={24} color="#ffffff" />
          </div>
          <div className="brand-title-wrap">
            <h1>UK National Wind Procurement Desk</h1>
            <div className="subtitle">
              <span className="status-dot" />
              <span>Elexon BMRS Day-Ahead Decision Support</span>
              {health && (
                <span className="num" style={{ marginLeft: 8, color: "var(--accent-wind)" }}>
                  ({health.total_actuals_rows} actuals / {health.total_forecasts_rows} forecasts)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Date & Cutoff Controls */}
        <div className="controls-bar">
          {/* Target Delivery Date */}
          <div className="control-item">
            <Calendar size={15} color="var(--accent-wind)" />
            <label htmlFor="delivery-date-input" className="control-label">Delivery Day:</label>
            <input
              id="delivery-date-input"
              type="date"
              className="input-date"
              min="2026-01-01"
              max="2026-01-31"
              value={targetDate}
              onChange={(e) => onTargetDateChange(e.target.value)}
            />
          </div>

          {/* Quick Presets */}
          <div className="preset-pills">
            {PRESET_DATES.map((p) => (
              <button
                key={p.date}
                type="button"
                className={`pill-btn ${targetDate === p.date ? "active" : ""}`}
                onClick={() => onTargetDateChange(p.date)}
              >
                {p.label}
              </button>
            ))}
          </div>

          <div style={{ width: 1, height: 24, background: "var(--border-subtle)", margin: "0 4px" }} />

          {/* Cutoff Selector */}
          <div className="control-item">
            <Clock size={15} color="var(--accent-forecast)" />
            <label htmlFor="cutoff-time-select" className="control-label">Cutoff (D-1):</label>
            <select
              id="cutoff-time-select"
              className="select-cutoff"
              value={cutoffTime}
              onChange={(e) => onCutoffTimeChange(e.target.value)}
            >
              <option value="07:00">07:00 UTC (Early Run)</option>
              <option value="09:00">09:00 UTC (Default Gate Closure)</option>
              <option value="11:00">11:00 UTC (Mid-Morning)</option>
              <option value="12:00">12:00 UTC (Noon Fix)</option>
              <option value="17:00">17:00 UTC (Late Afternoon)</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
