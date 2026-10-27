import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("App", () => {
  it("renders the procurement desk title", () => {
    render(<App />);
    expect(screen.getByText(/UK Wind Day-Ahead Procurement Desk/i)).toBeInTheDocument();
  });
});
