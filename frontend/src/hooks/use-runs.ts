import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import {
  getRuns,
  deleteRun,
  triggerRunById,
  updateRun,
  getRunTriggers,
  getTriggerFindings,
  getTriggerSnapshots,
  getTriggerLogs,
  getTriggerLogPreview,
  getDigestPdfUrl,
} from "@/lib/api";
import type {
  Run,
  RunTrigger,
  Finding,
  Snapshot,
  AgentLogSummary,
  LogPreview,
} from "@/lib/types";

const TERMINAL_STATUSES = new Set([
  "completed",
  "failed",
  "partial",
  "completed_empty",
]);

export function isTerminalStatus(status: string): boolean {
  return TERMINAL_STATUSES.has(status);
}

export interface UseRunsReturn {
  runs: Run[];
  setRuns: React.Dispatch<React.SetStateAction<Run[]>>;
  loading: boolean;
  triggeringId: string | null;
  deletingRun: Run | null;
  setDeletingRun: (run: Run | null) => void;
  triggerHistory: Record<string, RunTrigger[]>;
  loadingTriggers: Set<string>;
  editingRun: Run | null;
  setEditingRun: (run: Run | null) => void;
  selectedTrigger: RunTrigger | null;
  setSelectedTrigger: (trigger: RunTrigger | null) => void;
  triggerFindings: Finding[];
  triggerSnapshots: Snapshot[];
  loadingDetail: boolean;
  agentLogs: AgentLogSummary[];
  logPreviews: Record<string, LogPreview>;
  loadingLogPreview: string | null;
  expandedAgent: string | null;
  expandedRunIds: string[];
  handleTrigger: (run: Run) => Promise<void>;
  handleDelete: () => Promise<void>;
  handleToggleEnabled: (run: Run) => Promise<void>;
  handleAccordionChange: (values: string[]) => Promise<void>;
  handleTriggerDetail: (trigger: RunTrigger) => Promise<void>;
  handleToggleLogPreview: (agentName: string) => Promise<void>;
  handleDownloadDigestPdf: (digestId: string) => Promise<void>;
}

/**
 * Custom hook for the Runs page (main view).
 * Manages fetching runs, intelligent polling for active triggers,
 * expanding/collapsing trigger details, and executing runs.
 *
 * Interacts with:
 * - GET /api/runs
 * - DELETE /api/runs/{id}
 * - POST /api/runs/{id}/trigger
 * - PUT /api/runs/{id}
 * - GET /api/runs/{id}/triggers
 * - GET /api/run-triggers/{id}/findings
 * - GET /api/run-triggers/{id}/snapshots
 * - GET /api/run-triggers/{id}/logs
 * - GET /api/run-triggers/{id}/logs/{agentName}/preview
 */
export function useRuns(): UseRunsReturn {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [deletingRun, setDeletingRun] = useState<Run | null>(null);

  const [triggerHistory, setTriggerHistory] = useState<
    Record<string, RunTrigger[]>
  >({});
  const [loadingTriggers, setLoadingTriggers] = useState<Set<string>>(
    new Set(),
  );
  const [editingRun, setEditingRun] = useState<Run | null>(null);
  const [selectedTrigger, setSelectedTrigger] = useState<RunTrigger | null>(
    null,
  );

  const [triggerFindings, setTriggerFindings] = useState<Finding[]>([]);
  const [triggerSnapshots, setTriggerSnapshots] = useState<Snapshot[]>([]);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Execution logs state
  const [agentLogs, setAgentLogs] = useState<AgentLogSummary[]>([]);
  const [logPreviews, setLogPreviews] = useState<Record<string, LogPreview>>(
    {},
  );
  const [loadingLogPreview, setLoadingLogPreview] = useState<string | null>(
    null,
  );
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);

  const [expandedRunIds, setExpandedRunIds] = useState<string[]>([]);

  const triggerHistoryRef = useRef(triggerHistory);
  useEffect(() => {
    triggerHistoryRef.current = triggerHistory;
  }, [triggerHistory]);

  const fetchRuns = useCallback(async () => {
    const res = await getRuns(50);
    if (res.ok) setRuns(res.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    void fetchRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Layer 1: Runs-level polling — refresh the runs list every 15s
  useEffect(() => {
    const id = setInterval(() => void fetchRuns(), 15_000);
    return () => clearInterval(id);
  }, [fetchRuns]);

  // Layer 2: Per-run trigger polling — poll triggers every 5s for expanded runs with active triggers
  useEffect(() => {
    const intervals = new Map<string, NodeJS.Timeout>();

    for (const runId of expandedRunIds) {
      const id = setInterval(async () => {
        const triggers = triggerHistoryRef.current[runId];
        if (!triggers) return;
        if (!triggers.some((t) => !isTerminalStatus(t.status))) {
          clearInterval(intervals.get(runId)!);
          intervals.delete(runId);
          return;
        }
        const res = await getRunTriggers(runId, 10);
        if (res.ok) {
          setTriggerHistory((prev) => ({ ...prev, [runId]: res.data }));
        }
      }, 5_000);
      intervals.set(runId, id);
    }

    return () => {
      for (const [, id] of intervals) clearInterval(id);
    };
  }, [expandedRunIds]);

  async function handleTrigger(run: Run) {
    if (!run.is_enabled) {
      toast.error("Cannot trigger a disabled run.");
      return;
    }
    setTriggeringId(run.run_id);
    const res = await triggerRunById(run.run_id);
    setTriggeringId(null);
    if (res.ok) {
      toast.success(res.data.message);
      const triggersRes = await getRunTriggers(run.run_id, 10);
      if (triggersRes.ok) {
        setTriggerHistory((prev) => ({
          ...prev,
          [run.run_id]: triggersRes.data,
        }));
      }
      setExpandedRunIds((prev) =>
        prev.includes(run.run_id) ? prev : [...prev, run.run_id],
      );
    } else {
      toast.error(res.error);
    }
  }

  async function handleDelete() {
    if (!deletingRun) return;
    const res = await deleteRun(deletingRun.run_id);
    if (res.ok) {
      toast.success("Run deleted.");
      setRuns((prev) => prev.filter((r) => r.run_id !== deletingRun.run_id));
    } else {
      toast.error(res.error);
    }
    setDeletingRun(null);
  }

  async function handleToggleEnabled(run: Run) {
    const res = await updateRun(run.run_id, { is_enabled: !run.is_enabled });
    if (res.ok) {
      setRuns((prev) =>
        prev.map((r) => (r.run_id === run.run_id ? res.data : r)),
      );
      toast.success(res.data.is_enabled ? "Run enabled." : "Run disabled.");
    } else {
      toast.error(res.error);
    }
  }

  async function handleAccordionChange(values: string[]) {
    setExpandedRunIds(values);
    for (const runId of values) {
      if (loadingTriggers.has(runId)) continue;
      setLoadingTriggers((prev) => new Set(prev).add(runId));
      const res = await getRunTriggers(runId, 10);
      if (res.ok) {
        setTriggerHistory((prev) => ({ ...prev, [runId]: res.data }));
      }
      setLoadingTriggers((prev) => {
        const next = new Set(prev);
        next.delete(runId);
        return next;
      });
    }
  }

  async function handleTriggerDetail(trigger: RunTrigger) {
    setSelectedTrigger(trigger);
    setLoadingDetail(true);
    setAgentLogs([]);
    setLogPreviews({});
    setExpandedAgent(null);
    const [findingsRes, snapshotsRes, logsRes] = await Promise.all([
      getTriggerFindings(trigger.run_trigger_id, 20),
      getTriggerSnapshots(trigger.run_trigger_id),
      getTriggerLogs(trigger.run_trigger_id),
    ]);
    if (findingsRes.ok) setTriggerFindings(findingsRes.data);
    if (snapshotsRes.ok) setTriggerSnapshots(snapshotsRes.data);
    if (logsRes.ok) setAgentLogs(logsRes.data);
    setLoadingDetail(false);
  }

  async function handleToggleLogPreview(agentName: string) {
    if (expandedAgent === agentName) {
      setExpandedAgent(null);
      return;
    }
    setExpandedAgent(agentName);
    if (logPreviews[agentName]) return;
    if (!selectedTrigger) return;
    setLoadingLogPreview(agentName);
    const res = await getTriggerLogPreview(
      selectedTrigger.run_trigger_id,
      agentName,
      100,
    );
    if (res.ok) {
      setLogPreviews((prev) => ({ ...prev, [agentName]: res.data }));
    }
    setLoadingLogPreview(null);
  }

  async function handleDownloadDigestPdf(digestId: string) {
    try {
      const url = getDigestPdfUrl(digestId);
      const token = localStorage.getItem("auth_token");
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(url, { headers });
      if (!res.ok) {
        const body = await res.json();
        toast.warning(
          typeof body.detail === "string"
            ? body.detail
            : "Unable to download PDF.",
        );
        return;
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `zentivra_digest.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      toast.error("Unable to reach the server. Please check your connection.");
    }
  }

  return {
    runs,
    setRuns,
    loading,
    triggeringId,
    deletingRun,
    setDeletingRun,
    triggerHistory,
    loadingTriggers,
    editingRun,
    setEditingRun,
    selectedTrigger,
    setSelectedTrigger,
    triggerFindings,
    triggerSnapshots,
    loadingDetail,
    agentLogs,
    logPreviews,
    loadingLogPreview,
    expandedAgent,
    expandedRunIds,
    handleTrigger,
    handleDelete,
    handleToggleEnabled,
    handleAccordionChange,
    handleTriggerDetail,
    handleToggleLogPreview,
    handleDownloadDigestPdf,
  };
}
