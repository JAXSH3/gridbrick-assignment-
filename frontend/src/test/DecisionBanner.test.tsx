import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DecisionBanner } from "../components/DecisionBanner";
import { BufferResponse } from "../types/api";

const mockBuffer: BufferResponse = {
  confidence: 0.9,
  recommended_buffer_mw: 2450.0,
  buffer_90_mw: 2450.0,
  buffer_95_mw: 3100.0,
  over_forecast_count: 420,
  under_forecast_count: 324,
  over_forecast_pct: 56.5,
  under_forecast_pct: 43.5,
  mean_shortfall_mw: 1650.0,
  p90_shortfall_mw: 2950.0,
  p95_shortfall_mw: 3500.0,
  mean_surplus_mw: 1420.0,
  p90_surplus_mw: 2600.0,
  recommendation_text: "At 90% confidence, maintaining a 2450 MW buffer covers shortfalls.",
};

describe("DecisionBanner component", () => {
  it("renders recommended safety buffer and shortfalls", () => {
    const onConfChange = vi.fn();
    render(
      <DecisionBanner
        bufferData={mockBuffer}
        confidence={0.9}
        onConfidenceChange={onConfChange}
      />
    );

    expect(screen.getByText("2,450")).toBeInTheDocument();
    expect(screen.getByText(/MW Safety Buffer/i)).toBeInTheDocument();
    expect(screen.getAllByText(/90%/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Shortfall Exposure:/i)).toBeInTheDocument();
    expect(screen.getByText(/56.5%/i)).toBeInTheDocument();
  });

  it("triggers confidence change on slider release", () => {
    const onConfChange = vi.fn();
    render(
      <DecisionBanner
        bufferData={mockBuffer}
        confidence={0.9}
        onConfidenceChange={onConfChange}
      />
    );

    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "95" } });
    fireEvent.mouseUp(slider);
    expect(onConfChange).toHaveBeenCalledWith(0.95);
  });
});
