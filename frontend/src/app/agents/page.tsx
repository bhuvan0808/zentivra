"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, Eye, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import {
  getRunAgentActivity,
  getRunAgentLogs,
  getRunAgents,
  getRuns,
} from "@/lib/api";
import type {
  AgentType,
  Run,
  RunAgentActivity,
  RunAgentLog,
  RunAgentSummary,
} from "@/lib/types";

const AGENT_LABELS: Record<AgentType, string> = {
  competitor: "Competitor Watcher",
  model_provider: "Model Provider Watcher",
  research: "Research Scout",
  hf_benchmark: "HF Benchmark Tracker",
};

function isRunActive(run: Run | null): boolean {
  if (!run) return false;
  return run.status === "running" || run.status === "pending";
}

function isAgentRunning(status: string): boolean {
  return status.startsWith("running");
}

function formatLogContext(context: Record<string, unknown> | null): string {
  if (!context || Object.keys(context).length === 0) {
    return "";
  }
  try {
    return ` ${JSON.stringify(context)}`;
  } catch {
    return "";
  }
}

function formatLogLine(log: RunAgentLog): string {
  const ts = new Date(log.created_at).toLocaleTimeString();
  const level = log.level.toUpperCase();
  return `${ts} [${level}] ${log.message}${formatLogContext(log.context)}`;
}

export default function AgentsPage() {
  const [loading, setLoading] = useState(true);
  const [latestRun, setLatestRun] = useState<Run | null>(null);
  const [summaries, setSummaries] = useState<RunAgentSummary[]>([]);

  const [selectedAgentType, setSelectedAgentType] = useState<AgentType | null>(null);
  const [activity, setActivity] = useState<RunAgentActivity[]>([]);
  const [logs, setLogs] = useState<RunAgentLog[]>([]);
  const [activityLoading, setActivityLoading] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const detailPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const selectedAgent = useMemo(
    () => summaries.find((agent) => agent.agent_type === selectedAgentType) ?? null,
    [summaries, selectedAgentType]
  );

  const loadLatestRunAndAgents = useCallback(async () => {
    const runsRes = await getRuns(1);
    if (!runsRes.ok) {
      if (loading) toast.error(runsRes.error);
      setLoading(false);
      return;
    }

    const run = runsRes.data[0] ?? null;
    setLatestRun(run);

    if (!run) {
      setSummaries([]);
      setLoading(false);
      return;
    }

    const agentsRes = await getRunAgents(run.id);
    if (!agentsRes.ok) {
      if (loading) toast.error(agentsRes.error);
      setLoading(false);
      return;
    }

    setSummaries(agentsRes.data);
    setLoading(false);
  }, [loading]);

  const loadAgentDetails = useCallback(
    async (agentType: AgentType, silent = false) => {
      if (!latestRun) return;

      if (!silent) {
        setActivityLoading(true);
        setLogsLoading(true);
      }

      const [activityRes, logsRes] = await Promise.all([
        getRunAgentActivity(latestRun.id, agentType, 300),
        getRunAgentLogs(latestRun.id, agentType, 500),
      ]);

      if (!silent) {
        setActivityLoading(false);
        setLogsLoading(false);
      }

      if (!activityRes.ok) {
        if (!silent) toast.error(activityRes.error);
      } else {
        setActivity(activityRes.data);
      }

      if (!logsRes.ok) {
        if (!silent) toast.error(logsRes.error);
      } else {
        setLogs(logsRes.data);
      }
    },
    [latestRun]
  );

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadLatestRunAndAgents();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadLatestRunAndAgents]);

  useEffect(() => {
    if (!isRunActive(latestRun)) {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = null;
      return;
    }

    pollRef.current = setInterval(loadLatestRunAndAgents, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = null;
    };
  }, [latestRun, loadLatestRunAndAgents]);

  useEffect(() => {
    if (!selectedAgentType || !latestRun || !isRunActive(latestRun)) {
      if (detailPollRef.current) clearInterval(detailPollRef.current);
      detailPollRef.current = null;
      return;
    }

    detailPollRef.current = setInterval(() => {
      void loadAgentDetails(selectedAgentType, true);
    }, 3000);

    return () => {
      if (detailPollRef.current) clearInterval(detailPollRef.current);
      detailPollRef.current = null;
    };
  }, [latestRun, selectedAgentType, loadAgentDetails]);

  async function handleOpenAgent(agent: RunAgentSummary) {
    setSelectedAgentType(agent.agent_type);
    await loadAgentDetails(agent.agent_type, false);
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Agents" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Agents"
        description="Live agent cards, crawl activity, and execution logs."
      >
        <Button variant="outline" onClick={loadLatestRunAndAgents}>
          <RefreshCw className="mr-1.5 size-4" />
          Refresh
        </Button>
      </PageHeader>

      {!latestRun ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No runs found yet. Trigger a run first to monitor agents.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <Card>
            <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
              <div className="text-sm">
                <span className="text-muted-foreground">Latest Run:</span>{" "}
                <span className="font-mono">{latestRun.id.slice(0, 8)}</span>
              </div>
              <StatusBadge
                variant={
                  latestRun.status === "failed"
                    ? "danger"
                    : latestRun.status === "partial"
                      ? "warning"
                      : latestRun.status === "completed"
                        ? "success"
                        : "neutral"
                }
                dot
              >
                {latestRun.status}
              </StatusBadge>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summaries.map((agent) => {
              const running = isAgentRunning(agent.status);
              return (
                <Card
                  key={agent.agent_type}
                  className={cn(
                    "cursor-pointer transition-shadow hover:shadow-md",
                    !running && "border-danger/35"
                  )}
                  onClick={() => handleOpenAgent(agent)}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center justify-between text-sm">
                      <span>{AGENT_LABELS[agent.agent_type]}</span>
                      <Activity className="size-4 text-muted-foreground" />
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "size-2 rounded-full",
                            running ? "bg-success" : "bg-danger"
                          )}
                        />
                        <span
                          className={cn(
                            "text-xs font-medium",
                            running ? "text-success" : "text-danger"
                          )}
                        >
                          {running ? "Running" : "Not Running"}
                        </span>
                      </div>
                      <StatusBadge variant={running ? "success" : "danger"}>
                        {agent.status}
                      </StatusBadge>
                    </div>

                    <div className="text-xs text-muted-foreground">
                      <div>Findings: {agent.findings_count}</div>
                      <div>URLs crawled: {agent.urls_crawled}</div>
                      <div>
                        Last activity:{" "}
                        {agent.last_activity_at
                          ? new Date(agent.last_activity_at).toLocaleString()
                          : "—"}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      <Dialog
        open={!!selectedAgentType}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedAgentType(null);
            setActivity([]);
            setLogs([]);
          }
        }}
      >
        <DialogContent className="max-h-[85vh] max-w-4xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedAgentType ? AGENT_LABELS[selectedAgentType] : "Agent"}
            </DialogTitle>
          </DialogHeader>

          {selectedAgentType && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm">
                <div className="text-muted-foreground">
                  Live logs auto-refresh every 3 seconds while run is active.
                </div>
                {selectedAgent && (
                  <StatusBadge
                    variant={isAgentRunning(selectedAgent.status) ? "success" : "danger"}
                    dot
                  >
                    {selectedAgent.status}
                  </StatusBadge>
                )}
              </div>

              <section className="space-y-2">
                <h3 className="text-sm font-semibold">Agent Logs</h3>
                {logsLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <Skeleton key={i} className="h-7 w-full" />
                    ))}
                  </div>
                ) : logs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No logs captured for this agent yet.
                  </p>
                ) : (
                  <div className="max-h-64 space-y-1 overflow-y-auto rounded-md border bg-muted/30 p-2">
                    {logs.map((log) => (
                      <pre
                        key={log.id}
                        className="whitespace-pre-wrap break-words rounded-sm px-2 py-1 font-mono text-xs"
                      >
                        {formatLogLine(log)}
                      </pre>
                    ))}
                  </div>
                )}
              </section>

              <section className="space-y-2">
                <h3 className="text-sm font-semibold">Crawl Activity</h3>
                {activityLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-16 w-full" />
                    ))}
                  </div>
                ) : activity.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No crawl activity captured for this agent yet.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {activity.map((item, idx) => (
                      <div
                        key={`${item.url}-${item.fetched_at}-${idx}`}
                        className="rounded-md border px-3 py-2 text-sm"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate font-medium">{item.source_name}</p>
                            <p className="truncate text-xs text-muted-foreground">
                              {item.url}
                            </p>
                          </div>
                          <Button asChild size="sm" variant="outline">
                            <a href={item.url} target="_blank" rel="noreferrer">
                              <Eye className="mr-1.5 size-3.5" />
                              View Crawl
                            </a>
                          </Button>
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          HTTP {item.http_status ?? "—"} · Changed:{" "}
                          {item.content_changed == null
                            ? "unknown"
                            : item.content_changed
                              ? "yes"
                              : "no"}{" "}
                          · {new Date(item.fetched_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
