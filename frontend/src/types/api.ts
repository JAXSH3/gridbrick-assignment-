// TypeScript interfaces for API data models

export interface ForecastSlotItem {
  start_time: string;
  publish_time: string | null;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  abs_error_mw: number | null;
  horizon_hours: number | null;
}

export interface DayForecastResponse {
  target_date: string;
  cutoff_time: string;
  cutoff_datetime: string;
  slots: ForecastSlotItem[];
  slot_count: number;
  has_missing_actuals: boolean;
  has_missing_forecasts: boolean;
}

export interface VintageItem {
  start_time: string;
  publish_time: string;
  forecast_mw: number;
  horizon_hours: number;
}

export interface VintageResponse {
  start_time: string;
  actual_mw: number | null;
  vintages: VintageItem[];
  vintage_count: number;
}

export interface AccuracySummaryResponse {
  start_date: string;
  end_date: string;
  cutoff_time: string;
  sample_size: number;
  mean_actual_mw: number;
  mean_forecast_mw: number;
  mae: number;
  rmse: number;
  bias: number;
  nmae_pct: number;
  mape_pct: number;
  p50_abs_error: number;
  p90_abs_error: number;
  p95_abs_error: number;
  max_abs_error: number;
}

export interface HorizonBucketItem {
  bucket: string;
  min_hours: number;
  max_hours: number;
  sample_size: number;
  mae: number;
  rmse: number;
  bias: number;
  p90_abs_error: number;
}

export interface HorizonAccuracyResponse {
  buckets: HorizonBucketItem[];
}

export interface HourAccuracyItem {
  hour: number;
  hour_label: string;
  sample_size: number;
  avg_actual_mw: number;
  avg_forecast_mw: number;
  mae: number;
  rmse: number;
  bias: number;
}

export interface HourAccuracyResponse {
  hours: HourAccuracyItem[];
}

export interface WindLevelAccuracyItem {
  regime: string;
  range_label: string;
  sample_size: number;
  mean_actual_mw: number;
  mae: number;
  rmse: number;
  bias: number;
  nmae_pct: number;
}

export interface WindLevelAccuracyResponse {
  regimes: WindLevelAccuracyItem[];
}

export interface BufferResponse {
  confidence: number;
  recommended_buffer_mw: number;
  buffer_90_mw: number;
  buffer_95_mw: number;
  over_forecast_count: number;
  under_forecast_count: number;
  over_forecast_pct: number;
  under_forecast_pct: number;
  mean_shortfall_mw: number;
  p90_shortfall_mw: number;
  p95_shortfall_mw: number;
  mean_surplus_mw: number;
  p90_surplus_mw: number;
  recommendation_text: string;
}

export interface DistributionBin {
  bin_start: number;
  bin_end: number;
  bin_mid: number;
  count: number;
  type: string;
}

export interface ErrorDistributionResponse {
  bins: DistributionBin[];
  quantiles: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  version: string;
  database_connected: boolean;
  total_actuals_rows: number;
  total_forecasts_rows: number;
  earliest_actual_date: string | null;
  latest_actual_date: string | null;
}
