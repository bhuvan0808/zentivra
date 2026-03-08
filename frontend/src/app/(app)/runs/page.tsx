"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  Play,
  Pencil,
  Trash2,
  Plus,
  Loader2,
  Clock,
  Hash,
  ChevronDown,
  Download,
  ScrollText,
  Eye,
  FileText,
} from "lucide-react";
import { motion } from "framer-motion";
import { fmtDate, fmtDateTime, fmtTimeSec } from "@/lib/formatDate";
import { PageHeader } from "@/components/page-header";
import { StatusBadge, getRunStatusVariant } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { downloadTriggerLog } from "@/lib/api";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Run, CrawlSchedule } from "@/lib/types";
import { useRuns } from "@/hooks/use-runs";

function utcToLocal(utcTime: string): string {
  const [h, m] = utcTime.split(":").map(Number);
  const now = new Date();
  now.setUTCHours(h, m, 0, 0);
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function ScheduleTooltip({ schedule }: { schedule: CrawlSchedule }) {
  const localTime = utcToLocal(schedule.time);
  const freq =
    schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1);

  return (
    <Tooltip delayDuration={200}>
      <TooltipTrigger asChild>
        <span className="text-xs font-medium text-foreground underline decoration-dotted underline-offset-4 decoration-muted-foreground/60 cursor-default">
          {freq}
        </span>
      </TooltipTrigger>
      <TooltipContent
        side="bottom"
        align="start"
        className="bg-popover text-popover-foreground border shadow-md text-xs space-y-1 p-2.5"
        hideArrow
      >
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Frequency</span>
          <span className="font-medium">{freq}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Time</span>
          <span className="font-medium">{localTime}</span>
        </div>
        {schedule.periods && schedule.periods.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">
              {schedule.frequency === "weekly" ? "Days" : "Dates"}
            </span>
            <span className="font-medium capitalize">
              {schedule.periods.join(", ")}
            </span>
          </div>
        )}
      </TooltipContent>
    </Tooltip>
  );
}

export default function RunsPage() {
  const {
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
  } = useRuns();

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Runs"
          description="Manage run configurations and trigger pipeline runs."
        />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Runs"
        description="Manage run configurations and trigger pipeline runs."
      >
        <Button asChild>
          <Link href="/runs/configure">
            <Plus className="mr-1.5 size-4" />
            Configure Run
          </Link>
        </Button>
      </PageHeader>

      {runs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-muted-foreground">No run configurations yet.</p>
            <Button asChild className="mt-4" variant="outline">
              <Link href="/runs/configure">
                <Plus className="mr-1.5 size-4" />
                Create your first run
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Accordion
          type="multiple"
          value={expandedRunIds}
          onValueChange={handleAccordionChange}
          className="space-y-3"
        >
          {runs.map((run, i) => (
            <motion.div
              key={run.run_id}
              initial={{ opacity: 0, filter: "blur(4px)" }}
              animate={{ opacity: 1, filter: "blur(0px)" }}
              transition={{ duration: 0.3, delay: i * 0.04, ease: "easeOut" }}
            >
              <AccordionItem
                value={run.run_id}
                className="group/row rounded-lg border bg-card px-4 last:border-b"
              >
                <div className="flex items-center gap-3 py-3">
                  <span className="shrink-0 w-6 text-center text-xs text-muted-foreground font-mono">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <AccordionTrigger className="hover:no-underline py-0 [&>svg]:hidden">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">
                            {run.run_name}
                          </p>
                          <StatusBadge
                            variant={run.is_enabled ? "success" : "neutral"}
                            dot
                          >
                            {run.is_enabled ? "Active" : "Disabled"}
                          </StatusBadge>
                          {run.has_active_triggers && (
                            <span className="inline-flex items-center gap-1.5 text-xs text-warning">
                              <span className="relative flex size-2">
                                <span className="absolute inline-flex size-full animate-ping rounded-full bg-warning opacity-75" />
                                <span className="relative inline-flex size-2 rounded-full bg-warning" />
                              </span>
                              <span className="hidden sm:inline">Running</span>
                            </span>
                          )}
                        </div>
                        <p className="mt-1.5 text-xs text-muted-foreground truncate flex items-center gap-1">
                          <span>{run.sources?.length ?? 0} sources</span>
                          <span>&middot;</span>
                          {run.crawl_frequency ? (
                            <ScheduleTooltip schedule={run.crawl_frequency} />
                          ) : (
                            <span>Manual</span>
                          )}
                          <span>&middot;</span>
                          <span>{fmtDate(run.created_at)}</span>
                        </p>
                      </div>
                    </AccordionTrigger>
                  </div>

                  <div className="ml-auto flex shrink-0 items-center gap-1">
                    <Switch
                      checked={run.is_enabled}
                      onCheckedChange={() => handleToggleEnabled(run)}
                      className="mr-1"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-8"
                      disabled={triggeringId === run.run_id || !run.is_enabled}
                      onClick={() => handleTrigger(run)}
                    >
                      {triggeringId === run.run_id ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        <Play className="size-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-8"
                      onClick={() => setEditingRun(run)}
                    >
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-8 text-danger hover:text-danger"
                      onClick={() => setDeletingRun(run)}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                    <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform duration-200 group-data-[state=open]/row:rotate-180" />
                  </div>
                </div>

                <AccordionContent>
                  {/* Run details */}
                  <div className="grid gap-3 rounded-md border bg-muted/30 p-4 text-xs sm:grid-cols-3">
                    <div>
                      <p className="data-label">Description</p>
                      <p className="mt-0.5">{run.description || "—"}</p>
                    </div>
                    <div>
                      <p className="data-label">Email Alerts</p>
                      <p className="mt-0.5">
                        {run.enable_email_alert ? "Yes" : "No"}
                      </p>
                    </div>
                    <div>
                      <p className="data-label">Keywords</p>
                      <p className="mt-0.5">
                        {run.keywords && run.keywords.length > 0
                          ? run.keywords.join(", ")
                          : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Trigger history */}
                  <div className="mt-4">
                    <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Trigger History
                    </p>
                    {loadingTriggers.has(run.run_id) ? (
                      <div className="flex items-center gap-2 py-3 text-xs text-muted-foreground">
                        <Loader2 className="size-3 animate-spin" />
                        Loading triggers...
                      </div>
                    ) : (triggerHistory[run.run_id] ?? []).length === 0 ? (
                      <p className="py-3 text-xs text-muted-foreground">
                        No triggers yet. Click the play button to trigger this
                        run.
                      </p>
                    ) : (
                      <div className="space-y-1.5">
                        {(triggerHistory[run.run_id] ?? []).map((trigger) => (
                          <button
                            key={trigger.run_trigger_id}
                            onClick={() => handleTriggerDetail(trigger)}
                            className="flex w-full items-center gap-3 rounded-md border px-3 py-2 text-xs text-left transition-colors hover:bg-muted/40"
                          >
                            <StatusBadge
                              variant={getRunStatusVariant(trigger.status)}
                              dot
                            >
                              {trigger.status}
                            </StatusBadge>
                            <span className="text-muted-foreground capitalize">
                              {trigger.trigger_method}
                            </span>
                            <span className="flex items-center gap-1 text-muted-foreground">
                              <Hash className="size-3" />
                              {trigger.findings_count} findings
                            </span>
                            <span className="hidden sm:flex items-center gap-1 text-muted-foreground">
                              {trigger.snapshots_count} snapshots
                            </span>
                            <span className="ml-auto flex items-center gap-1 text-muted-foreground">
                              <Clock className="size-3" />
                              {fmtDateTime(trigger.created_at)}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </motion.div>
          ))}
        </Accordion>
      )}

      {/* Delete confirmation */}
      <AlertDialog
        open={!!deletingRun}
        onOpenChange={(open) => !open && setDeletingRun(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Run</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove &ldquo;{deletingRun?.run_name}&rdquo;
              and all its configuration. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-danger text-white hover:bg-danger/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {editingRun && (
        <RunEditDialog
          run={editingRun}
          onClose={() => setEditingRun(null)}
          onSaved={(updated) => {
            setRuns((prev) =>
              prev.map((r) => (r.run_id === updated.run_id ? updated : r)),
            );
            setEditingRun(null);
          }}
        />
      )}

      {/* Trigger detail dialog */}
      <Dialog
        open={!!selectedTrigger}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedTrigger(null);
          }
        }}
      >
        <DialogContent className="max-w-5xl lg:max-w-[70vw] max-h-[85vh] overflow-y-auto overflow-x-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Trigger Details
              {selectedTrigger && (
                <StatusBadge
                  variant={getRunStatusVariant(selectedTrigger.status)}
                  dot
                >
                  {selectedTrigger.status}
                </StatusBadge>
              )}
            </DialogTitle>
          </DialogHeader>
          {selectedTrigger && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                <div>
                  <p className="data-label">Method</p>
                  <p className="mt-0.5 capitalize">
                    {selectedTrigger.trigger_method}
                  </p>
                </div>
                <div>
                  <p className="data-label">Findings</p>
                  <p className="mt-0.5 font-mono">
                    {selectedTrigger.findings_count}
                  </p>
                </div>
                <div>
                  <p className="data-label">Snapshots</p>
                  <p className="mt-0.5 font-mono">
                    {selectedTrigger.snapshots_count}
                  </p>
                </div>
                <div>
                  <p className="data-label">Created</p>
                  <p className="mt-0.5">
                    {fmtDateTime(selectedTrigger.created_at)}
                  </p>
                </div>
              </div>

              {loadingDetail ? (
                <div className="flex items-center gap-2 py-6 justify-center text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  Loading details...
                </div>
              ) : (
                <>
                  {selectedTrigger.digest_id && (
                    <div>
                      <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Executive Digest
                      </p>
                      <div className="flex items-center gap-3 rounded-md border px-3 py-2 text-xs">
                        <FileText className="size-4 text-muted-foreground" />
                        <span className="font-medium shrink-0">
                          {selectedTrigger.digest_id.slice(0, 8)}
                        </span>
                        <StatusBadge
                          variant={
                            selectedTrigger.digest_status === "completed"
                              ? "success"
                              : selectedTrigger.digest_status === "failed"
                                ? "danger"
                                : "warning"
                          }
                          dot
                        >
                          {selectedTrigger.digest_status}
                        </StatusBadge>
                        <div className="ml-auto w-full md:w-auto flex flex-col md:flex-row items-center gap-1.5 pt-1 md:pt-0">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs px-2 w-full md:w-auto"
                            asChild
                          >
                            <Link
                              href={`/digests/${selectedTrigger.digest_id}`}
                            >
                              <Eye className="mr-1 size-3" />
                              Preview
                            </Link>
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs px-2 w-full md:w-auto"
                            onClick={() =>
                              handleDownloadDigestPdf(
                                selectedTrigger.digest_id!,
                              )
                            }
                          >
                            <Download className="mr-1 size-3" />
                            PDF
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {triggerSnapshots.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Snapshots
                      </p>
                      <div className="space-y-1.5">
                        {triggerSnapshots.map((snap) => (
                          <div
                            key={snap.snapshot_id}
                            className="flex items-center gap-3 rounded-md border px-3 py-2 text-xs"
                          >
                            <StatusBadge
                              variant={getRunStatusVariant(snap.status)}
                              dot
                            >
                              {snap.status}
                            </StatusBadge>
                            <span className="font-medium truncate">
                              {snap.source_name}
                            </span>
                            <span className="text-muted-foreground">
                              {snap.total_findings} findings
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {triggerFindings.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Findings
                      </p>
                      <div className="space-y-1.5">
                        {triggerFindings.map((finding) => (
                          <div
                            key={finding.finding_id}
                            className="rounded-md border px-3 py-2 text-xs space-y-1"
                          >
                            <div className="flex items-center gap-2">
                              {finding.category && (
                                <StatusBadge variant="neutral">
                                  {finding.category}
                                </StatusBadge>
                              )}
                              <span className="font-mono text-muted-foreground">
                                {Math.round(finding.confidence * 100)}%
                                confidence
                              </span>
                            </div>
                            <p className="text-sm">
                              {finding.summary ?? finding.content ?? "—"}
                            </p>
                            {finding.src_url && (
                              <a
                                href={finding.src_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline truncate block"
                              >
                                {finding.src_url}
                              </a>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Execution Logs */}
                  {agentLogs.length > 0 && (
                    <div className="w-full overflow-hidden">
                      <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                        <ScrollText className="size-3.5" />
                        Execution Logs
                      </p>
                      <div className="space-y-1.5">
                        {agentLogs.map((agent) => (
                          <div key={agent.agent_name}>
                            <div
                              role="button"
                              tabIndex={0}
                              onClick={() =>
                                handleToggleLogPreview(agent.agent_name)
                              }
                              onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  handleToggleLogPreview(agent.agent_name);
                                }
                              }}
                              className="flex w-full items-center gap-3 rounded-md border px-3 py-2 text-xs text-left transition-colors hover:bg-muted/40 cursor-pointer"
                            >
                              <StatusBadge variant="neutral" dot>
                                {agent.agent_name.replace(/_/g, " ")}
                              </StatusBadge>
                              <span className="text-muted-foreground">
                                {agent.line_count} log lines
                              </span>
                              <span className="text-muted-foreground text-[10px]">
                                {(agent.file_size / 1024).toFixed(1)} KB
                              </span>
                              {selectedTrigger && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (selectedTrigger) {
                                      downloadTriggerLog(
                                        selectedTrigger.run_trigger_id,
                                        agent.agent_name,
                                      );
                                    }
                                  }}
                                  className="ml-auto"
                                  title="Download full log"
                                >
                                  <Download className="size-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                                </button>
                              )}
                              <ChevronDown
                                className={`size-3.5 shrink-0 text-muted-foreground transition-transform duration-200 ${
                                  expandedAgent === agent.agent_name
                                    ? "rotate-180"
                                    : ""
                                }`}
                              />
                            </div>

                            {expandedAgent === agent.agent_name && (
                              <div className="mt-1.5 rounded-md border bg-muted/20 overflow-x-auto max-w-full">
                                {loadingLogPreview === agent.agent_name ? (
                                  <div className="flex items-center gap-2 py-4 px-3 text-xs text-muted-foreground">
                                    <Loader2 className="size-3 animate-spin" />
                                    Loading log preview...
                                  </div>
                                ) : logPreviews[agent.agent_name] ? (
                                  <>
                                    <Table>
                                      <TableHeader>
                                        <TableRow>
                                          <TableHead className="text-[10px] w-[160px]">
                                            Timestamp
                                          </TableHead>
                                          <TableHead className="text-[10px] w-[60px]">
                                            Level
                                          </TableHead>
                                          <TableHead className="text-[10px] w-[100px]">
                                            Step
                                          </TableHead>
                                          <TableHead className="text-[10px] w-[140px]">
                                            Event
                                          </TableHead>
                                          <TableHead className="text-[10px]">
                                            Details
                                          </TableHead>
                                        </TableRow>
                                      </TableHeader>
                                      <TableBody>
                                        {logPreviews[
                                          agent.agent_name
                                        ].preview.map((entry, idx) => {
                                          const detailKeys = Object.keys(
                                            entry,
                                          ).filter(
                                            (k) =>
                                              ![
                                                "ts",
                                                "trigger_id",
                                                "level",
                                                "agent",
                                                "step",
                                                "event",
                                                "filename",
                                                "lineno",
                                                "line_number",
                                                "file_name",
                                                "pathname",
                                              ].includes(k),
                                          );
                                          const details = detailKeys
                                            .map(
                                              (k) =>
                                                `${k}=${typeof entry[k] === "object" ? JSON.stringify(entry[k]) : entry[k]}`,
                                            )
                                            .join(" ");

                                          return (
                                            <TableRow
                                              key={idx}
                                              className="text-[11px]"
                                            >
                                              <TableCell className="font-mono text-muted-foreground py-1">
                                                {fmtTimeSec(entry.ts)}
                                              </TableCell>
                                              <TableCell className="py-1">
                                                <span
                                                  className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${
                                                    entry.level === "ERROR"
                                                      ? "bg-red-500/15 text-red-500"
                                                      : entry.level ===
                                                          "WARNING"
                                                        ? "bg-amber-500/15 text-amber-500"
                                                        : "bg-blue-500/15 text-blue-400"
                                                  }`}
                                                >
                                                  {entry.level}
                                                </span>
                                              </TableCell>
                                              <TableCell className="py-1 text-muted-foreground">
                                                {entry.step}
                                              </TableCell>
                                              <TableCell className="py-1 font-medium">
                                                {entry.event}
                                              </TableCell>
                                              <TableCell
                                                className="py-1 text-muted-foreground font-mono truncate max-w-[200px]"
                                                title={details}
                                              >
                                                {details || "—"}
                                              </TableCell>
                                            </TableRow>
                                          );
                                        })}
                                      </TableBody>
                                    </Table>
                                    {logPreviews[agent.agent_name].total_lines >
                                      logPreviews[agent.agent_name].preview
                                        .length && (
                                      <p className="px-3 py-2 text-[10px] text-muted-foreground border-t">
                                        Showing{" "}
                                        {
                                          logPreviews[agent.agent_name].preview
                                            .length
                                        }{" "}
                                        of{" "}
                                        {
                                          logPreviews[agent.agent_name]
                                            .total_lines
                                        }{" "}
                                        lines. Download the full log to view all
                                        entries.
                                      </p>
                                    )}
                                  </>
                                ) : null}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {triggerFindings.length === 0 &&
                    triggerSnapshots.length === 0 &&
                    agentLogs.length === 0 && (
                      <p className="py-4 text-center text-sm text-muted-foreground">
                        No findings, snapshots, or logs for this trigger.
                      </p>
                    )}
                </>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CircleHelp, Check, X, Search } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import type { AgentType } from "@/lib/types";

const AGENT_TYPE_LABELS: Record<AgentType, string> = {
  competitor: "Competitor",
  model_provider: "Model Provider",
  research: "Research",
  hf_benchmark: "HF Benchmark",
};

import { useRunEdit } from "@/hooks/use-run-edit";

function RunEditDialog({
  run,
  onClose,
  onSaved,
}: {
  run: Run;
  onClose: () => void;
  onSaved: (updated: Run) => void;
}) {
  const {
    runName,
    setRunName,
    description,
    setDescription,
    enableEmailAlert,
    setEnableEmailAlert,
    recipients,
    recipientInput,
    setRecipientInput,
    crawlFrequency,
    setCrawlFrequency,
    scheduleTime,
    setScheduleTime,
    scheduleDays,
    scheduleDates,
    crawlDepth,
    setCrawlDepth,
    keywords,
    keywordInput,
    setKeywordInput,
    saving,
    selectedSourceIds,
    sourceSearch,
    setSourceSearch,
    agentFilter,
    setAgentFilter,
    loadingSources,
    filteredSources,
    toggleSource,
    toggleDay,
    toggleDate,
    addRecipient,
    removeRecipient,
    handleSave,
    addKeyword,
    removeKeyword,
    WEEK_DAYS,
  } = useRunEdit(run, onClose, onSaved);

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()} modal={true}>
      <DialogContent className="max-w-4xl sm:max-w-4xl w-full max-h-[85vh] overflow-y-auto overflow-x-hidden">
        <DialogHeader>
          <DialogTitle>Edit Run</DialogTitle>
        </DialogHeader>
        <div className="space-y-6">
          <div className="space-y-2.5">
            <Label>Run Name *</Label>
            <Input
              value={runName}
              onChange={(e) => setRunName(e.target.value)}
              maxLength={255}
            />
          </div>
          <div className="space-y-2.5">
            <Label>Description</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          {/* Email Alerts + Recipients */}
          <div className="flex flex-col gap-4 rounded-md border p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Email Alerts</span>
              <Switch
                checked={enableEmailAlert}
                onCheckedChange={setEnableEmailAlert}
              />
            </div>

            {enableEmailAlert && (
              <div className="space-y-3 pt-2 border-t">
                <Label>Recipients</Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="Add recipient email..."
                    value={recipientInput}
                    onChange={(e) => setRecipientInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addRecipient();
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addRecipient}
                  >
                    Add
                  </Button>
                </div>
                {recipients.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {recipients.map((email) => (
                      <span
                        key={email}
                        className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium"
                      >
                        {email}
                        <button
                          type="button"
                          onClick={() => removeRecipient(email)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="size-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Crawl Frequency */}
          <div className="space-y-2.5">
            <Label>Crawl Frequency</Label>
            <Select
              value={crawlFrequency}
              onValueChange={(v) =>
                setCrawlFrequency(v as CrawlSchedule["frequency"])
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Schedule Time */}
          <div className="space-y-2.5">
            <Label htmlFor="edit-schedule-time">Run Time</Label>
            <Input
              id="edit-schedule-time"
              type="time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="w-40"
            />
            <p className="text-xs text-muted-foreground">
              What time should the run execute?
            </p>
          </div>

          {/* Day-of-week (weekly) */}
          {crawlFrequency === "weekly" && (
            <div className="space-y-2.5">
              <Label>Days of the Week</Label>
              <div className="flex gap-1.5">
                {WEEK_DAYS.map((d) => (
                  <button
                    key={d.key}
                    type="button"
                    onClick={() => toggleDay(d.key)}
                    className={cn(
                      "flex size-9 cursor-pointer items-center justify-center rounded-md border text-sm font-medium transition-colors",
                      scheduleDays.has(d.key)
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-input bg-background text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Selected: {Array.from(scheduleDays).join(", ") || "none"}
              </p>
            </div>
          )}

          {/* Date-of-month (monthly) */}
          {crawlFrequency === "monthly" && (
            <div className="space-y-2.5">
              <Label>Dates of the Month</Label>
              <div className="inline-grid grid-cols-7 gap-1 rounded-lg border p-2">
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => toggleDate(d)}
                    className={cn(
                      "flex size-9 cursor-pointer items-center justify-center rounded-md text-xs font-medium transition-colors",
                      scheduleDates.has(d)
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {d}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Selected:{" "}
                {Array.from(scheduleDates)
                  .sort((a, b) => a - b)
                  .join(", ") || "none"}
              </p>
            </div>
          )}

          <div className="space-y-2.5">
            <div className="flex items-center gap-1.5">
              <Label>Crawl Depth</Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <CircleHelp className="size-3.5 text-muted-foreground cursor-help" />
                </TooltipTrigger>
                <TooltipContent
                  side="right"
                  className="max-w-xs text-xs leading-relaxed"
                >
                  <p className="font-semibold mb-1">Crawl Depth Levels</p>
                  <p>
                    <strong>Level 0</strong> — Only the source URL itself
                  </p>
                  <p>
                    <strong>Level 1</strong> — Source URL + URLs in its RSS feed
                  </p>
                  <p>
                    <strong>Level 2</strong> — Level 1 + RSS URLs from Level 1
                    pages
                  </p>
                  <p>
                    <strong>Level 3+</strong> — Continues recursively per level
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
            <Input
              type="number"
              min={0}
              max={5}
              value={crawlDepth}
              onChange={(e) => setCrawlDepth(Number(e.target.value))}
            />
          </div>

          <div className="space-y-2.5">
            <Label>Keywords</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Add keyword..."
                maxLength={50}
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addKeyword();
                  }
                }}
              />
              <Button variant="outline" size="sm" onClick={addKeyword}>
                Add
              </Button>
            </div>
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {keywords.map((kw) => (
                  <span
                    key={kw}
                    className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium"
                  >
                    {kw}
                    <button
                      onClick={() => removeKeyword(kw)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Source selection */}
          <div className="space-y-2.5">
            <Label>Sources ({selectedSourceIds.size})</Label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search..."
                  className="pl-8 h-8 text-xs"
                  value={sourceSearch}
                  onChange={(e) => setSourceSearch(e.target.value)}
                />
              </div>
              <Select value={agentFilter} onValueChange={setAgentFilter}>
                <SelectTrigger className="w-36 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  {(
                    Object.entries(AGENT_TYPE_LABELS) as [AgentType, string][]
                  ).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {loadingSources ? (
              <p className="text-xs text-muted-foreground py-2">Loading...</p>
            ) : (
              <div className="rounded-md border max-h-40 overflow-y-auto">
                {filteredSources.map((s) => (
                  <label
                    key={s.source_id}
                    className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-xs hover:bg-muted/30"
                  >
                    <Checkbox
                      checked={selectedSourceIds.has(s.source_id)}
                      onCheckedChange={() => toggleSource(s.source_id)}
                    />
                    <span className="truncate">{s.display_name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <Loader2 className="mr-1.5 size-4 animate-spin" />
              ) : (
                <Check className="mr-1.5 size-4" />
              )}
              Save
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
