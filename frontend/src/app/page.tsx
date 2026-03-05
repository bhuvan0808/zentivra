"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Clock,
  FileText,
  BarChart3,
  Download,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/page-header";
import {
  StatusBadge,
  getRunStatusVariant,
} from "@/components/status-badge";
import {
  getHealth,
  getSchedulerStatus,
  getFindingsStats,
  getLatestDigest,
  getRuns,
  getDigestPdfUrl,
} from "@/lib/api";
import type {
  HealthStatus,
  SchedulerStatus,
  FindingsStats,
  Digest,
  Run,
} from "@/lib/types";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [stats, setStats] = useState<FindingsStats | null>(null);
  const [latestDigest, setLatestDigest] = useState<Digest | null>(null);
  const [recentRuns, setRecentRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [hRes, sRes, stRes, dRes, rRes] = await Promise.all([
        getHealth(),
        getSchedulerStatus(),
        getFindingsStats(),
        getLatestDigest(),
        getRuns(5),
      ]);
      if (hRes.ok) setHealth(hRes.data);
      if (sRes.ok) setScheduler(sRes.data);
      if (stRes.ok) setStats(stRes.data);
      if (dRes.ok) setLatestDigest(dRes.data);
      if (rRes.ok) setRecentRuns(rRes.data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <DashboardSkeleton />;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of the Frontier AI Radar system."
      />

      {/* Status row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Health */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <StatusBadge
              variant={health?.status === "operational" ? "success" : "danger"}
              dot
            >
              {health?.status ?? "Unknown"}
            </StatusBadge>
            <p className="mt-2 text-xs text-muted-foreground">
              LLM: {health?.llm_provider ?? "—"} &middot; v{health?.version ?? "—"}
            </p>
          </CardContent>
        </Card>

        {/* Scheduler */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Next Run</CardTitle>
            <Clock className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold font-mono">
              {scheduler?.jobs?.[0]
                ? new Date(scheduler.jobs[0].next_run).toLocaleString()
                : "—"}
            </p>
            <p className="text-xs text-muted-foreground">
              Scheduler {scheduler?.running ? "active" : "stopped"}
            </p>
          </CardContent>
        </Card>

        {/* Total findings */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Findings</CardTitle>
            <BarChart3 className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {stats?.total_findings ?? 0}
            </p>
            <p className="text-xs text-muted-foreground">
              Avg impact: {stats?.avg_impact_score?.toFixed(1) ?? "—"}
            </p>
          </CardContent>
        </Card>

        {/* Latest digest */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Latest Digest</CardTitle>
            <FileText className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {latestDigest ? (
              <>
                <p className="text-sm font-medium">{latestDigest.date}</p>
                <p className="text-xs text-muted-foreground">
                  {latestDigest.total_findings} findings
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No digests yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Category breakdown + Digest card */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Findings by category */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Findings by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.by_category ? (
              <div className="space-y-3">
                {Object.entries(stats.by_category).map(([cat, count]) => (
                  <div key={cat} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{cat}</span>
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{
                            width: `${Math.min(
                              100,
                              (count / stats.total_findings) * 100
                            )}%`,
                          }}
                        />
                      </div>
                      <span className="w-8 text-right text-sm font-mono font-medium">
                        {count}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data available</p>
            )}
          </CardContent>
        </Card>

        {/* Latest digest detail */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">
              Executive Summary
            </CardTitle>
            {latestDigest && (
              <Button variant="outline" size="sm" asChild>
                <a href={getDigestPdfUrl(latestDigest.id)} target="_blank" rel="noreferrer">
                  <Download className="mr-1.5 size-3.5" />
                  PDF
                </a>
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {latestDigest ? (
              <>
                <p className="text-sm leading-relaxed">
                  {latestDigest.executive_summary}
                </p>
                <Separator className="my-3" />
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{latestDigest.total_findings} findings</span>
                  <span>
                    {latestDigest.email_sent ? "Email sent" : "Not emailed"}
                  </span>
                  <span>
                    {latestDigest.recipients.length} recipient
                    {latestDigest.recipients.length !== 1 ? "s" : ""}
                  </span>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                No digest generated yet. Trigger a run to produce one.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent runs */}
      <Card className="mt-6">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-medium">Recent Runs</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/runs">
              View all
              <ArrowRight className="ml-1 size-3.5" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {recentRuns.length > 0 ? (
            <div className="space-y-3">
              {recentRuns.map((run) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between rounded-md border px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <StatusBadge variant={getRunStatusVariant(run.status)} dot>
                      {run.status}
                    </StatusBadge>
                    <span className="text-xs font-mono text-muted-foreground">
                      {run.id.slice(0, 8)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{run.total_findings} findings</span>
                    <span>
                      {new Date(run.started_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No runs recorded yet.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of the Frontier AI Radar system."
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-6 w-20" />
              <Skeleton className="mt-2 h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="mt-6">
        <CardHeader>
          <Skeleton className="h-4 w-28" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
