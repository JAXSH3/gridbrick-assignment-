import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "../App";

describe("App dashboard component", () => {
  it("renders the procurement desk title and navigation", () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    );

    expect(
      screen.getByText(/UK National Wind Procurement Desk/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Delivery Day:/i)).toBeInTheDocument();
  });
});
