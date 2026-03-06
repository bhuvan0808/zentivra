"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Play, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import {
  StatusBadge,
  getRunStatusVariant,
} from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getRuns, triggerRun, getRun } from "@/lib/api";
import type { AgentType, Run } from "@/lib/types";

const AGENT_OPTIONS: { key: AgentType; label: string }[] = [
  { key: "competitor", label: "Competitor" },
  { key: "model_provider", label: "Model Provider" },
  { key: "research", label: "Research" },
  { key: "hf_benchmark", label: "HF Benchmark" },
];

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [maxSourcesPerAgent, setMaxSourcesPerAgent] = useState(3);
  const [recipientEmails, setRecipientEmails] = useState("");
  const [agentSelection, setAgentSelection] = useState<Record<AgentType, boolean>>({
    competitor: true,
    model_provider: true,
    research: true,
    hf_benchmark: true,
  });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRuns = useCallback(async () => {
    const res = await getRuns(20);
    if (res.ok) setRuns(res.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void fetchRuns();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [fetchRuns]);

  // Auto-poll when any run is active
  useEffect(() => {
    const hasActive = runs.some(
      (r) => r.status === "running" || r.status === "pending"
    );
    if (hasActive) {
      pollRef.current = setInterval(fetchRuns, 5000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [runs, fetchRuns]);

  async function handleTrigger() {
    const selectedAgents = AGENT_OPTIONS.filter(
      (agent) => agentSelection[agent.key]
    ).map((agent) => agent.key);
    const recipients = recipientEmails
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);

    if (selectedAgents.length === 0) {
      toast.error("Select at least one agent before triggering.");
      return;
    }

    setTriggering(true);
    const res = await triggerRun({
      agent_types: selectedAgents,
      recipients: recipients.length > 0 ? recipients : undefined,
      max_sources_per_agent:
        Number.isFinite(maxSourcesPerAgent) && maxSourcesPerAgent > 0
          ? maxSourcesPerAgent
          : undefined,
    });
    setTriggering(false);
    if (res.ok) {
      toast.success(res.data.message);
      fetchRuns();
    } else {
      toast.error(res.error);
    }
  }

  async function handleViewRun(run: Run) {
    const res = await getRun(run.id);
    if (res.ok) {
      setSelectedRun(res.data);
    } else {
      toast.error(res.error);
    }
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Runs" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Runs"
        description="Trigger and monitor pipeline runs."
      >
        <Button onClick={handleTrigger} disabled={triggering}>
          {triggering ? (
            <Loader2 className="mr-1.5 size-4 animate-spin" />
          ) : (
            <Play className="mr-1.5 size-4" />
          )}
          {triggering ? "Triggering..." : "Trigger Run"}
        </Button>
      </PageHeader>

      <Card className="mb-4">
        <CardContent className="space-y-3 py-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="max-sources">Max sources per agent (cost control)</Label>
              <Input
                id="max-sources"
                type="number"
                min={1}
                max={50}
                value={maxSourcesPerAgent}
                onChange={(e) => setMaxSourcesPerAgent(Number(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="recipient-emails">
                Recipient emails (comma-separated, optional)
              </Label>
              <Input
                id="recipient-emails"
                placeholder="lead@company.com, ops@company.com"
                value={recipientEmails}
                onChange={(e) => setRecipientEmails(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-sm font-medium">Agents to execute</p>
            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
              {AGENT_OPTIONS.map((agent) => (
                <div
                  key={agent.key}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-xs">{agent.label}</span>
                  <Switch
                    checked={agentSelection[agent.key]}
                    onCheckedChange={(checked) =>
                      setAgentSelection((prev) => ({
                        ...prev,
                        [agent.key]: checked,
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Run ID</TableHead>
                <TableHead>Started</TableHead>
                <TableHead className="hidden md:table-cell">
                  Completed
                </TableHead>
                <TableHead className="hidden sm:table-cell">
                  Findings
                </TableHead>
                <TableHead className="hidden lg:table-cell">
                  Triggered By
                </TableHead>
                <TableHead>Agent Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No runs yet. Click &ldquo;Trigger Run&rdquo; to start one.
                  </TableCell>
                </TableRow>
              ) : (
                runs.map((run) => (
                  <TableRow
                    key={run.id}
                    className="cursor-pointer"
                    onClick={() => handleViewRun(run)}
                  >
                    <TableCell>
                      <StatusBadge
                        variant={getRunStatusVariant(run.status)}
                        dot
                      >
                        {run.status}
                      </StatusBadge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {run.id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {new Date(run.started_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm">
                      {run.completed_at
                        ? new Date(run.completed_at).toLocaleString()
                        : "—"}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell font-mono">
                      {run.total_findings}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm capitalize">
                      {run.triggered_by}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {run.agent_statuses
                          ? Object.entries(run.agent_statuses).map(
                              ([agent, status]) => {
                                const isCompleted = status.startsWith("completed");
                                const isPending = status === "pending";
                                return (
                                  <StatusBadge
                                    key={agent}
                                    variant={
                                      isCompleted
                                        ? "success"
                                        : isPending
                                          ? "neutral"
                                          : "warning"
                                    }
                                  >
                                    {agent.replace("_", " ")}
                                  </StatusBadge>
                                );
                              }
                            )
                          : <span className="text-xs text-muted-foreground">—</span>
                        }
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Run detail dialog */}
      <Dialog
        open={!!selectedRun}
        onOpenChange={(open) => !open && setSelectedRun(null)}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Run Detail</DialogTitle>
          </DialogHeader>
          {selectedRun && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="data-label">Run ID</p>
                  <p className="font-mono text-sm">{selectedRun.id}</p>
                </div>
                <div>
                  <p className="data-label">Status</p>
                  <StatusBadge
                    variant={getRunStatusVariant(selectedRun.status)}
                    dot
                  >
                    {selectedRun.status}
                  </StatusBadge>
                </div>
                <div>
                  <p className="data-label">Started</p>
                  <p className="text-sm">
                    {new Date(selectedRun.started_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="data-label">Completed</p>
                  <p className="text-sm">
                    {selectedRun.completed_at
                      ? new Date(selectedRun.completed_at).toLocaleString()
                      : "In progress"}
                  </p>
                </div>
                <div>
                  <p className="data-label">Total Findings</p>
                  <p className="text-sm font-mono">
                    {selectedRun.total_findings}
                  </p>
                </div>
                <div>
                  <p className="data-label">Triggered By</p>
                  <p className="text-sm capitalize">
                    {selectedRun.triggered_by}
                  </p>
                </div>
              </div>

              {selectedRun.agent_statuses && (
                <div>
                  <p className="data-label mb-2">Agent Statuses</p>
                  <div className="space-y-2">
                    {Object.entries(selectedRun.agent_statuses).map(
                      ([agent, status]) => (
                        <div
                          key={agent}
                          className="flex items-center justify-between rounded-md border px-3 py-2"
                        >
                          <span className="text-sm capitalize">
                            {agent.replace("_", " ")}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {status}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

              {selectedRun.error_log && (
                <div>
                  <p className="data-label mb-1">Error Log</p>
                  <pre className="rounded-md bg-muted p-3 text-xs font-mono overflow-x-auto">
                    {selectedRun.error_log}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
