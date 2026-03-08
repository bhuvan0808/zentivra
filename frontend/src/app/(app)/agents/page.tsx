"use client";

import {
  Activity,
  RefreshCw,
  ExternalLink,
  Eye,
  ScrollText,
  Globe,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
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

export default function AgentsPage() {
  const {
    agents,
    loading,
    selectedAgent,
    activeTab,
    setActiveTab,
    logs,
    logsLoading,
    logsTrigger,
    totalLogLines,
    sources,
    sourcesLoading,
    selectAgentLogs,
    selectAgentSources,
    refreshLogs,
  } = useAgents();

  const selected = agents.find((a) => a.key === selectedAgent);

  return (
    <div>
      <PageHeader
        title="Agents"
        description="Agent overview, live monitoring, and crawl sources."
      />

      {/* Agent cards grid */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[160px] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {agents.map((agent) => (
            <Card
              key={agent.key}
              className={cn(
                "cursor-pointer transition-shadow hover:shadow-md",
                selectedAgent === agent.key &&
                  "ring-2 ring-primary shadow-md",
              )}
              onClick={() => selectAgentLogs(agent.key)}
            >
              <CardContent className="space-y-3 py-5">
                {/* Header row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {/* Status dot */}
                    <span
                      className={cn(
                        "inline-block size-2.5 rounded-full",
                        agent.status === "running"
                          ? "bg-green-500 animate-pulse"
                          : "bg-muted-foreground/30",
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
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-[10px]">
                    {agent.sources_count}{" "}
                    {agent.sources_count === 1 ? "source" : "sources"}
                  </Badge>
                  {agent.status === "running" && (
                    <Badge className="bg-green-500/15 text-green-600 text-[10px] border-0">
                      Running
                    </Badge>
                  )}
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
                      selectAgentSources(agent.key);
                    }}
                  >
                    <Eye className="mr-1.5 size-3" />
                    View Crawl
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Detail panel for selected agent */}
      {selectedAgent && selected && (
        <>
          <Separator className="my-6" />

          <Card>
            <CardContent className="py-4">
              {/* Panel header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "inline-block size-2.5 rounded-full",
                      selected.status === "running"
                        ? "bg-green-500 animate-pulse"
                        : "bg-muted-foreground/30",
                    )}
                  />
                  <h3 className="text-sm font-semibold">{selected.label}</h3>
                  {selected.status === "running" && (
                    <Badge className="bg-green-500/15 text-green-600 text-[10px] border-0">
                      Live
                    </Badge>
                  )}
                </div>
                {activeTab === "logs" && (
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
                )}
              </div>

              <Tabs
                value={activeTab}
                onValueChange={(v) => {
                  const tab = v as "logs" | "sources";
                  setActiveTab(tab);
                  if (tab === "sources") {
                    selectAgentSources(selectedAgent);
                  } else {
                    selectAgentLogs(selectedAgent);
                  }
                }}
              >
                <TabsList className="mb-3">
                  <TabsTrigger value="logs" className="text-xs">
                    <ScrollText className="mr-1.5 size-3" />
                    Live Logs
                  </TabsTrigger>
                  <TabsTrigger value="sources" className="text-xs">
                    <Globe className="mr-1.5 size-3" />
                    Crawl Sources
                  </TabsTrigger>
                </TabsList>

                {/* Logs tab */}
                <TabsContent value="logs">
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
                      {logsTrigger && (
                        <p className="mb-2 text-[11px] text-muted-foreground">
                          Trigger:{" "}
                          <span className="font-mono">
                            {logsTrigger.slice(0, 8)}
                          </span>{" "}
                          &middot; {totalLogLines} lines
                          {selected.status === "running" && (
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
                </TabsContent>

                {/* Sources tab */}
                <TabsContent value="sources">
                  {sourcesLoading ? (
                    <div className="space-y-2">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <Skeleton key={i} className="h-12 w-full" />
                      ))}
                    </div>
                  ) : sources.length === 0 ? (
                    <div className="py-10 text-center text-sm text-muted-foreground">
                      No crawl sources configured for this agent. Add sources
                      in the Sources page.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {sources.map((src) => (
                        <div
                          key={src.source_id}
                          className="flex items-center justify-between rounded-md border px-4 py-3"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium truncate">
                              {src.display_name}
                            </p>
                            <p className="text-xs text-muted-foreground truncate font-mono">
                              {src.url}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 ml-3 shrink-0">
                            <Badge
                              variant={src.is_enabled ? "default" : "secondary"}
                              className="text-[10px]"
                            >
                              {src.is_enabled ? "Active" : "Disabled"}
                            </Badge>
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                              >
                                <ExternalLink className="size-3.5" />
                              </Button>
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
