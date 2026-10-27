import React from "react";
import { ShieldCheck, AlertTriangle, TrendingUp, Sliders } from "lucide-react";
import { BufferResponse } from "../types/api";

interface DecisionBannerProps {
  bufferData?: BufferResponse;
  confidence: number;
  onConfidenceChange: (conf: number) => void;
  isLoading?: boolean;
}

export const DecisionBanner: React.FC<DecisionBannerProps> = ({
  bufferData,
  confidence,
  onConfidenceChange,
  isLoading,
}) => {
  // Local state for smooth drag without premature refetches
  const [localPct, setLocalPct] = React.useState<number>(Math.round(confidence * 100));

  React.useEffect(() => {
    setLocalPct(Math.round(confidence * 100));
  }, [confidence]);

  if (!bufferData) {
    return (
      <div className="card decision-banner">
        <div className="state-box" style={{ padding: "32px 0" }}>
          <div className="spinner" />
          <span>Calculating procurement risk & buffer sizing...</span>
        </div>
      </div>
    );
  }

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalPct(Number(e.target.value));
  };

  const commitConfidence = () => {
    const newConf = localPct / 100.0;
    if (newConf !== confidence) {
      onConfidenceChange(newConf);
    }
  };

  return (
    <div className="card decision-banner">
      {/* Recommended Buffer Hero */}
      <div className="buffer-highlight">
        <div className="buffer-badge">
          <ShieldCheck size={14} />
          <span>Decision Support | Day-Ahead Procurement</span>
          {isLoading && (
            <span
              className="spinner"
              style={{ width: 12, height: 12, borderWidth: 2, marginLeft: 8, display: "inline-block" }}
              title="Updating buffer..."
            />
          )}
        </div>
        <div
          className="buffer-value-row"
          style={{ opacity: isLoading ? 0.65 : 1, transition: "opacity 0.2s ease" }}
        >
          <span className="buffer-mw-big num">
            {bufferData.recommended_buffer_mw.toLocaleString()}
          </span>
          <span className="buffer-unit">MW Safety Buffer</span>
        </div>
        <p className="buffer-explanation">
          At <strong>{localPct}% confidence</strong>, procuring an additional{" "}
          <strong className="num">{bufferData.recommended_buffer_mw} MW</strong> of flexible power beyond the
          day-ahead wind forecast covers <strong>{localPct}%</strong> of observed forecast deficit events.
        </p>

        <div style={{ display: "flex", gap: "16px", marginTop: "4px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-faint)" }}>
            Standard 90% Buffer: <strong className="num" style={{ color: "var(--text-main)" }}>{bufferData.buffer_90_mw} MW</strong>
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--text-faint)" }}>
            Conservative 95% Buffer: <strong className="num" style={{ color: "var(--accent-warning)" }}>{bufferData.buffer_95_mw} MW</strong>
          </div>
        </div>
      </div>

      {/* Interactive Controls & Deficit Split */}
      <div className="slider-control-box">
        <div className="slider-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Sliders size={15} color="var(--accent-wind)" />
            <span className="slider-label">Coverage Confidence Level:</span>
          </div>
          <span className="slider-val-badge num">{localPct}%</span>
        </div>

        <input
          type="range"
          min="80"
          max="99"
          step="1"
          value={localPct}
          onChange={handleSliderChange}
          onMouseUp={commitConfidence}
          onTouchEnd={commitConfidence}
          onPointerUp={commitConfidence}
          onKeyUp={(e) => {
            if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "PageUp", "PageDown"].includes(e.key)) {
              commitConfidence();
            }
          }}
          className="range-slider"
          aria-label="Procurement safety buffer confidence slider"
        />

        {/* Shortfall vs Surplus Distribution */}
        <div className="risk-split-bar">
          <div className="split-bar-track">
            <div
              className="split-shortfall"
              style={{ width: `${bufferData.over_forecast_pct}%` }}
              title={`Over-Forecast Shortfalls: ${bufferData.over_forecast_pct}%`}
            />
            <div
              className="split-surplus"
              style={{ width: `${bufferData.under_forecast_pct}%` }}
              title={`Under-Forecast Surplus: ${bufferData.under_forecast_pct}%`}
            />
          </div>
          <div className="split-legend">
            <span style={{ color: "var(--accent-shortfall)", display: "flex", alignItems: "center", gap: 4 }}>
              <AlertTriangle size={12} />
              Shortfall Exposure: <strong className="num">{bufferData.over_forecast_pct}%</strong> (Avg: {bufferData.mean_shortfall_mw} MW)
            </span>
            <span style={{ color: "var(--accent-actual)", display: "flex", alignItems: "center", gap: 4 }}>
              <TrendingUp size={12} />
              Surplus Periods: <strong className="num">{bufferData.under_forecast_pct}%</strong> (Avg: {bufferData.mean_surplus_mw} MW)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
