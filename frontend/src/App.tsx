import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Header } from "./components/Header";
import { DecisionBanner } from "./components/DecisionBanner";
import { MetricCards } from "./components/MetricCards";
import { ForecastChart } from "./components/ForecastChart";
import { AccuracyTabs } from "./components/AccuracyTabs";
import { VintageModal } from "./components/VintageModal";
import {
  fetchHealth,
  fetchDayForecast,
  fetchAccuracySummary,
  fetchHorizonAccuracy,
  fetchHourAccuracy,
  fetchWindLevelAccuracy,
  fetchBufferRecommendation,
  fetchErrorDistribution,
} from "./api/client";

export default function App() {
  const [targetDate, setTargetDate] = useState<string>("2026-01-15");
  const [cutoffTime, setCutoffTime] = useState<string>("09:00");
  const [confidence, setConfidence] = useState<number>(0.90);
  const [selectedSlotForVintage, setSelectedSlotForVintage] = useState<string | null>(null);

  // Queries
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  const dayForecastQuery = useQuery({
    queryKey: ["dayForecast", targetDate, cutoffTime],
    queryFn: () => fetchDayForecast(targetDate, cutoffTime),
  });

  const summaryQuery = useQuery({
    queryKey: ["summary", cutoffTime],
    queryFn: () => fetchAccuracySummary("2026-01-01", "2026-01-31", cutoffTime),
  });

  const bufferQuery = useQuery({
    queryKey: ["buffer", confidence, cutoffTime],
    queryFn: () => fetchBufferRecommendation(confidence, "2026-01-01", "2026-01-31", cutoffTime),
    placeholderData: keepPreviousData,
  });

  const horizonQuery = useQuery({
    queryKey: ["horizon"],
    queryFn: fetchHorizonAccuracy,
  });

  const hourQuery = useQuery({
    queryKey: ["hour", cutoffTime],
    queryFn: () => fetchHourAccuracy("2026-01-01", "2026-01-31", cutoffTime),
  });

  const windLevelQuery = useQuery({
    queryKey: ["windLevel", cutoffTime],
    queryFn: () => fetchWindLevelAccuracy("2026-01-01", "2026-01-31", cutoffTime),
  });

  const distributionQuery = useQuery({
    queryKey: ["distribution", cutoffTime],
    queryFn: () => fetchErrorDistribution("2026-01-01", "2026-01-31", cutoffTime),
  });

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        targetDate={targetDate}
        onTargetDateChange={setTargetDate}
        cutoffTime={cutoffTime}
        onCutoffTimeChange={setCutoffTime}
        health={healthQuery.data}
      />

      {/* Main Trading Desk Dashboard */}
      <main className="main-content">
        {/* Decision Support Hero Banner */}
        <DecisionBanner
          bufferData={bufferQuery.data}
          confidence={confidence}
          onConfidenceChange={setConfidence}
          isLoading={bufferQuery.isLoading}
        />

        {/* Month Summary KPI Cards */}
        <MetricCards
          summary={summaryQuery.data}
          isLoading={summaryQuery.isLoading}
        />

        {/* Day-Ahead Delivery Chart */}
        <ForecastChart
          dayForecast={dayForecastQuery.data}
          onSlotClick={setSelectedSlotForVintage}
          isLoading={dayForecastQuery.isLoading}
        />

        {/* Deep Dive Analytical Tabs */}
        <AccuracyTabs
          horizonData={horizonQuery.data}
          hourData={hourQuery.data}
          windLevelData={windLevelQuery.data}
          distributionData={distributionQuery.data}
          isLoading={horizonQuery.isLoading}
        />
      </main>

      {/* Forecast Evolution (Vintages) Modal */}
      <VintageModal
        startTime={selectedSlotForVintage}
        onClose={() => setSelectedSlotForVintage(null)}
      />
    </div>
  );
}
