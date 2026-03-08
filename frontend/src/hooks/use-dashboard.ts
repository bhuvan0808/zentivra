import { useState, useEffect, useCallback } from "react";
import {
  getDashboardKpi,
  getDashboardCharts,
  getDashboardTriggers,
  getDashboardSources,
  getLatestDigest,
  getSchedulerStatus,
} from "@/lib/api";
import type {
  DashboardKpi,
  DashboardCharts,
  DashboardTriggers,
  DashboardSources,
  Digest,
  SchedulerStatus,
  SchedulerJob,
} from "@/lib/types";

export interface UseDashboardReturn {
  kpi: DashboardKpi | null;
  charts: DashboardCharts | null;
  triggers: DashboardTriggers | null;
  sources: DashboardSources | null;
  latestDigest: Digest | null;
  upcomingJobs: SchedulerJob[];
  kpiLoading: boolean;
  chartsLoading: boolean;
  triggersLoading: boolean;
  sourcesLoading: boolean;
  digestLoading: boolean;
  schedulerLoading: boolean;
  refreshing: boolean;
  fetchAll: () => void;
}

/**
 * Custom hook for the Dashboard page.
 * Manages fetching and state for all 6 independent dashboard data sections.
 *
 * Interacts with:
 * - GET /api/dashboard/kpi
 * - GET /api/dashboard/charts
 * - GET /api/dashboard/triggers
 * - GET /api/dashboard/sources
 * - GET /api/digests/latest
 * - GET /scheduler
 */
export function useDashboard(): UseDashboardReturn {
  const [kpi, setKpi] = useState<DashboardKpi | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [triggers, setTriggers] = useState<DashboardTriggers | null>(null);
  const [sources, setSources] = useState<DashboardSources | null>(null);
  const [latestDigest, setLatestDigest] = useState<Digest | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);

  const [kpiLoading, setKpiLoading] = useState(true);
  const [chartsLoading, setChartsLoading] = useState(true);
  const [triggersLoading, setTriggersLoading] = useState(true);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [digestLoading, setDigestLoading] = useState(true);
  const [schedulerLoading, setSchedulerLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAll = useCallback(() => {
    setKpiLoading(true);
    setChartsLoading(true);
    setTriggersLoading(true);
    setSourcesLoading(true);
    setDigestLoading(true);
    setSchedulerLoading(true);

    // Track pending requests to know when refreshing is complete
    let pending = 6;
    const done = () => {
      pending -= 1;
      if (pending === 0) setRefreshing(false);
    };

    getDashboardKpi().then((r) => {
      if (r.ok) setKpi(r.data);
      setKpiLoading(false);
      done();
    });
    getDashboardCharts().then((r) => {
      if (r.ok) setCharts(r.data);
      setChartsLoading(false);
      done();
    });
    getDashboardTriggers().then((r) => {
      if (r.ok) setTriggers(r.data);
      setTriggersLoading(false);
      done();
    });
    getDashboardSources().then((r) => {
      if (r.ok) setSources(r.data);
      setSourcesLoading(false);
      done();
    });
    getLatestDigest().then((r) => {
      if (r.ok) setLatestDigest(r.data);
      setDigestLoading(false);
      done();
    });
    getSchedulerStatus().then((r) => {
      if (r.ok) setScheduler(r.data);
      setSchedulerLoading(false);
      done();
    });
  }, []);

  useEffect(() => {
    fetchAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Compute upcoming jobs (max 3, sorted by next_run ascending)
  const upcomingJobs = scheduler?.jobs
    ? [...scheduler.jobs]
        .filter((j) => j.next_run)
        .sort(
          (a, b) =>
            new Date(a.next_run).getTime() - new Date(b.next_run).getTime(),
        )
        .slice(0, 3)
    : [];

  return {
    kpi,
    charts,
    triggers,
    sources,
    latestDigest,
    upcomingJobs,
    kpiLoading,
    chartsLoading,
    triggersLoading,
    sourcesLoading,
    digestLoading,
    schedulerLoading,
    refreshing,
    fetchAll,
  };
}
