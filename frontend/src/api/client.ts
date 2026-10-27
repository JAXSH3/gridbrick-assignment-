// API client for UK Wind Procurement Platform

import {
  AccuracySummaryResponse,
  BufferResponse,
  DayForecastResponse,
  ErrorDistributionResponse,
  HealthResponse,
  HorizonAccuracyResponse,
  HourAccuracyResponse,
  VintageResponse,
  WindLevelAccuracyResponse,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "/api/v1";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let errMsg = `API error (${res.status}): ${res.statusText}`;
    try {
      const errObj = await res.json();
      if (errObj && errObj.detail) {
        errMsg = typeof errObj.detail === "string" ? errObj.detail : JSON.stringify(errObj.detail);
      }
    } catch {
      // Ignore json parse error
    }
    throw new Error(errMsg);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>(`${API_BASE}/health`);
}

export async function fetchDayForecast(
  targetDate: string,
  cutoff: string = "09:00"
): Promise<DayForecastResponse> {
  const params = new URLSearchParams({ target_date: targetDate, cutoff });
  return fetchJson<DayForecastResponse>(`${API_BASE}/forecast/latest?${params}`);
}

export async function fetchVintages(startTime: string): Promise<VintageResponse> {
  const params = new URLSearchParams({ start_time: startTime });
  return fetchJson<VintageResponse>(`${API_BASE}/forecast/vintages?${params}`);
}

export async function fetchAccuracySummary(
  startDate: string = "2026-01-01",
  endDate: string = "2026-01-31",
  cutoff: string = "09:00"
): Promise<AccuracySummaryResponse> {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate, cutoff });
  return fetchJson<AccuracySummaryResponse>(`${API_BASE}/accuracy/summary?${params}`);
}

export async function fetchHorizonAccuracy(): Promise<HorizonAccuracyResponse> {
  return fetchJson<HorizonAccuracyResponse>(`${API_BASE}/accuracy/by-horizon`);
}

export async function fetchHourAccuracy(
  startDate: string = "2026-01-01",
  endDate: string = "2026-01-31",
  cutoff: string = "09:00"
): Promise<HourAccuracyResponse> {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate, cutoff });
  return fetchJson<HourAccuracyResponse>(`${API_BASE}/accuracy/by-hour?${params}`);
}

export async function fetchWindLevelAccuracy(
  startDate: string = "2026-01-01",
  endDate: string = "2026-01-31",
  cutoff: string = "09:00"
): Promise<WindLevelAccuracyResponse> {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate, cutoff });
  return fetchJson<WindLevelAccuracyResponse>(`${API_BASE}/accuracy/by-wind-level?${params}`);
}

export async function fetchBufferRecommendation(
  confidence: number = 0.9,
  startDate: string = "2026-01-01",
  endDate: string = "2026-01-31",
  cutoff: string = "09:00"
): Promise<BufferResponse> {
  const params = new URLSearchParams({
    confidence: confidence.toString(),
    start_date: startDate,
    end_date: endDate,
    cutoff,
  });
  return fetchJson<BufferResponse>(`${API_BASE}/accuracy/buffer?${params}`);
}

export async function fetchErrorDistribution(
  startDate: string = "2026-01-01",
  endDate: string = "2026-01-31",
  cutoff: string = "09:00",
  bins: number = 15
): Promise<ErrorDistributionResponse> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
    cutoff,
    bins: bins.toString(),
  });
  return fetchJson<ErrorDistributionResponse>(`${API_BASE}/accuracy/distribution?${params}`);
}
