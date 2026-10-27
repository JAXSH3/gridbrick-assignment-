import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Header } from "../components/Header";

describe("Header component", () => {
  it("renders desk title and controls", () => {
    const onDateChange = vi.fn();
    const onCutoffChange = vi.fn();

    render(
      <Header
        targetDate="2026-01-15"
        onTargetDateChange={onDateChange}
        cutoffTime="09:00"
        onCutoffTimeChange={onCutoffChange}
      />
    );

    expect(
      screen.getByText(/UK National Wind Procurement Desk/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Delivery Day:/i)).toBeInTheDocument();
    expect(screen.getByText(/Cutoff \(D-1\):/i)).toBeInTheDocument();
  });

  it("handles quick preset pill clicks", () => {
    const onDateChange = vi.fn();
    const onCutoffChange = vi.fn();

    render(
      <Header
        targetDate="2026-01-15"
        onTargetDateChange={onDateChange}
        cutoffTime="09:00"
        onCutoffTimeChange={onCutoffChange}
      />
    );

    const stormBtn = screen.getByRole("button", { name: /Jan 10 \(Storm\)/i });
    fireEvent.click(stormBtn);
    expect(onDateChange).toHaveBeenCalledWith("2026-01-10");
  });

  it("handles cutoff time changes", () => {
    const onDateChange = vi.fn();
    const onCutoffChange = vi.fn();

    render(
      <Header
        targetDate="2026-01-15"
        onTargetDateChange={onDateChange}
        cutoffTime="09:00"
        onCutoffTimeChange={onCutoffChange}
      />
    );

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "12:00" } });
    expect(onCutoffChange).toHaveBeenCalledWith("12:00");
  });
});
