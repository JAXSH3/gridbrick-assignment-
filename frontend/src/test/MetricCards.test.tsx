import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MetricCards } from "../components/MetricCards";
import { AccuracySummaryResponse } from "../types/api";

const mockSummary: AccuracySummaryResponse = {
  start_date: "2026-01-01",
  end_date: "2026-01-31",
  cutoff_time: "09:00",
  sample_size: 744,
  mean_actual_mw: 11580.7,
  mean_forecast_mw: 12744.4,
  mae: 1420.5,
  rmse: 1890.2,
  bias: 350.2,
  nmae_pct: 12.27,
  mape_pct: 14.5,
  p50_abs_error: 1120.0,
  p90_abs_error: 2850.0,
  p95_abs_error: 3410.0,
  max_abs_error: 5120.0,
};

describe("MetricCards component", () => {
  it("renders all key metrics and labels correctly", () => {
    render(<MetricCards summary={mockSummary} />);

    expect(screen.getByText(/Mean Absolute Error/i)).toBeInTheDocument();
    expect(screen.getByText("1,420.5")).toBeInTheDocument();

    expect(screen.getByText(/Root Mean Squared Error/i)).toBeInTheDocument();
    expect(screen.getByText("1,890.2")).toBeInTheDocument();

    expect(screen.getByText(/Forecast Bias/i)).toBeInTheDocument();
    expect(screen.getByText("+350.2")).toBeInTheDocument();

    expect(screen.getByText(/Normalized MAE \(nMAE\)/i)).toBeInTheDocument();
    expect(screen.getByText("12.27%")).toBeInTheDocument();

    expect(screen.getByText(/P90 Absolute Error/i)).toBeInTheDocument();
    expect(screen.getByText("2,850")).toBeInTheDocument();
  });
});
