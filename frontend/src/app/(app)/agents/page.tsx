"use client";

import {
  Activity,
  RefreshCw,
  ExternalLink,
  ScrollText,
  ChevronDown,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useAgents } from "@/hooks/use-agents";

function levelColor(level: string): string {
  switch (level.toUpperCase()) {
    case "ERROR":
      return "text-red-500";
    case "WARNING":
    case "WARN":
      return "text-amber-500";
    case "DEBUG":
      return "text-muted-foreground/60";
    default:
      return "text-foreground";
  }
}

function formatTs(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function statusDot(agent: { status: "running" | "idle"; recent_triggers: any[] }): string {
  if (agent.status === "running") return "bg-green-500 animate-pulse";
  if (agent.recent_triggers.length > 0) {
    const last = agent.recent_triggers[0];
    if (last.trigger_status === "failed") return "bg-red-500";
    if (last.trigger_status === "running") return "bg-green-500 animate-pulse";
    return "bg-green-500";
  }
  return "bg-neutral-400";
}

function statusLabel(agent: { status: "running" | "idle"; recent_triggers: any[] }): {
  text: string;
  className: string;
} {
  if (agent.status === "running") {
    return { text: "Running", className: "bg-green-500/15 text-green-600 border-0" };
  }
  if (agent.recent_triggers.length > 0) {
    const last = agent.recent_triggers[0];
    if (last.trigger_status === "failed") {
      return { text: "Failed", className: "bg-red-500/15 text-red-600 border-0" };
    }
    if (last.trigger_status === "running") {
      return { text: "Running", className: "bg-green-500/15 text-green-600 border-0" };
    }
    return { text: "Completed", className: "bg-green-500/15 text-green-600 border-0" };
  }
  return { text: "Offline", className: "bg-neutral-500/15 text-neutral-500 border-0" };
}

export default function AgentsPage() {
  const {
    agents,
    loading,
    selectedAgent,
    logs,
    logsLoading,
    selectedTrigger,
    totalLogLines,
    selectAgentLogs,
    fetchLogsForTrigger,
    openCrawlSources,
    refreshLogs,
  } = useAgents();

  const selected = agents.find((a) => a.key === selectedAgent);

  return (
    <div>
      <PageHeader
        title="Agents"
        description="Agent overview, live monitoring, and crawl sources."
      />

      {/* Agent cards — always visible (4 static cards with live data overlay) */}
      <div className="grid gap-4 md:grid-cols-2">
        {agents.map((agent) => {
          const badge = statusLabel(agent);
          return (
            <Card
              key={agent.key}
              className={cn(
                "cursor-pointer transition-shadow hover:shadow-md",
                selectedAgent === agent.key && "ring-2 ring-primary shadow-md",
              )}
              onClick={() => {
                selectAgentLogs(agent.key);
                setTimeout(() => {
                  document.getElementById("logs-panel")?.scrollIntoView({ behavior: "smooth" });
                }, 100);
              }}
            >
              <CardContent className="space-y-3 py-5">
                {/* Header row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "inline-block size-2.5 rounded-full",
                        statusDot(agent),
                      )}
                    />
                    <h3 className="text-sm font-semibold">{agent.label}</h3>
                  </div>
                  <Activity className="size-4 text-muted-foreground" />
                </div>

                {/* Description */}
                <p className="text-xs text-muted-foreground">
                  {agent.description}
                </p>

                {/* Stats row */}
                <div className="flex items-center gap-2 flex-wrap">
                  {loading ? (
                    <Skeleton className="h-4 w-16 rounded" />
                  ) : (
                    <Badge variant="secondary" className="text-[10px]">
                      {agent.sources_count}{" "}
                      {agent.sources_count === 1 ? "source" : "sources"}
                    </Badge>
                  )}
                  <Badge className={cn("text-[10px]", badge.className)}>
                    {badge.text}
                  </Badge>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 pt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      selectAgentLogs(agent.key);
                      setTimeout(() => {
                        document.getElementById("logs-panel")?.scrollIntoView({ behavior: "smooth" });
                      }, 100);
                    }}
                  >
                    <ScrollText className="mr-1.5 size-3" />
                    View Logs
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs flex-1"
                    onClick={(e) => {
                      e.stopPropagation();
                      openCrawlSources(agent.key);
                    }}
                  >
                    <ExternalLink className="mr-1.5 size-3" />
                    View Crawl
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Logs panel for selected agent */}
      {selectedAgent && selected && (
        <>
          <Separator className="my-6" />

          <Card id="logs-panel">
            <CardContent className="py-4">
              {/* Panel header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "inline-block size-2.5 rounded-full",
                      statusDot(selected),
                    )}
                  />
                  <h3 className="text-sm font-semibold">{selected.label}</h3>
                  {(() => {
                    const isRunning = selected.status === "running" || selected.recent_triggers[0]?.trigger_status === "running" || selected.recent_triggers[0]?.trigger_status === "pending";
                    if (!isRunning) return null;
                    return (
                      <Badge className="bg-green-500/15 text-green-600 text-[10px] border-0">
                        Live
                      </Badge>
                    );
                  })()}
                </div>

                <div className="flex items-center gap-2">
                  {/* Run selector dropdown */}
                  {selected.recent_triggers.length > 0 && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                        >
                          Run:{" "}
                          {selectedTrigger
                            ? selectedTrigger.trigger_id.slice(0, 8)
                            : "latest"}
                          <ChevronDown className="ml-1.5 size-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-56">
                        {selected.recent_triggers.map((t) => (
                          <DropdownMenuItem
                            key={t.trigger_id}
                            className={cn(
                              "text-xs font-mono cursor-pointer",
                              selectedTrigger?.trigger_id === t.trigger_id &&
                                "bg-accent",
                            )}
                            onClick={() =>
                              fetchLogsForTrigger(selectedAgent, t.trigger_id)
                            }
                          >
                            <span className="flex-1">
                              {t.trigger_id.slice(0, 8)}
                            </span>
                            <Badge
                              variant="secondary"
                              className="text-[9px] ml-2"
                            >
                              {t.trigger_status}
                            </Badge>
                            <span className="text-muted-foreground ml-2">
                              {formatDate(t.created_at)}
                            </span>
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={refreshLogs}
                    disabled={logsLoading}
                  >
                    <RefreshCw
                      className={cn(
                        "mr-1.5 size-3",
                        logsLoading && "animate-spin",
                      )}
                    />
                    Refresh
                  </Button>
                </div>
              </div>

              {/* Log viewer */}
              {logsLoading && logs.length === 0 ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-5 w-full" />
                  ))}
                </div>
              ) : logs.length === 0 ? (
                <div className="py-10 text-center text-sm text-muted-foreground">
                  No logs available for this agent yet. Trigger a run to
                  generate logs.
                </div>
              ) : (
                <>
                  {selectedTrigger && (
                    <p className="mb-2 text-[11px] text-muted-foreground">
                      Trigger:{" "}
                      <span className="font-mono">
                        {selectedTrigger.trigger_id.slice(0, 8)}
                      </span>{" "}
                      &middot; {totalLogLines} lines &middot;{" "}
                      {formatDate(selectedTrigger.created_at)}
                      {(selected.status === "running" || selected.recent_triggers[0]?.trigger_status === "running" || selected.recent_triggers[0]?.trigger_status === "pending") && (
                        <span className="ml-2 text-green-600">
                          (auto-refreshing)
                        </span>
                      )}
                    </p>
                  )}
                  <ScrollArea className="h-[360px] rounded-md border bg-muted/30">
                    <div className="p-3 font-mono text-[11px] leading-relaxed space-y-0.5">
                      {logs.map((entry, i) => (
                        <div key={i} className="flex gap-2">
                          <span className="text-muted-foreground shrink-0 w-[60px]">
                            {formatTs(entry.ts)}
                          </span>
                          <span
                            className={cn(
                              "shrink-0 w-[44px] uppercase font-semibold",
                              levelColor(entry.level),
                            )}
                          >
                            {entry.level}
                          </span>
                          <span className="text-blue-500 shrink-0 w-[60px] truncate">
                            {entry.step}
                          </span>
                          <span className="flex-1 break-all">
                            {entry.event}
                          </span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
