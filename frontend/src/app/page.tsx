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
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/page-header";
import { StatusBadge, getRunStatusVariant } from "@/components/status-badge";
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
  const topCategory = stats?.by_category
    ? Object.entries(stats.by_category).sort(([, a], [, b]) => b - a)[0]
    : null;

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
    <div className="relative">
      <div className="pointer-events-none absolute -top-20 -left-24 size-72 rounded-full bg-sky-500/15 blur-3xl dark:bg-sky-900/40" />
      <div className="pointer-events-none absolute top-16 right-0 size-72 rounded-full bg-violet-500/15 blur-3xl dark:bg-violet-900/40" />
      <div className="pointer-events-none absolute bottom-20 left-1/3 size-72 rounded-full bg-emerald-500/10 blur-3xl dark:bg-emerald-900/35" />

      <div className="relative z-10">
        <PageHeader
          title="Dashboard"
          description="Overview of the Frontier AI Radar system."
        />

        {/* Status row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Health */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 0 * 0.07, ease: "easeOut" }}
          >
            <DashboardFlipCard
              front={
                <Card className="h-full border-sky-500/20 bg-gradient-to-br from-sky-500/15 via-card to-card dark:border-sky-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-sky-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      System Status
                    </CardTitle>
                    <Activity className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <StatusBadge
                      variant={
                        health?.status === "operational" ? "success" : "danger"
                      }
                      dot
                    >
                      {health?.status ?? "Unknown"}
                    </StatusBadge>
                    <p className="mt-2 text-xs text-muted-foreground">
                      LLM: {health?.llm_provider ?? "—"} &middot; v
                      {health?.version ?? "—"}
                    </p>
                    <p className="mt-3 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Hover to flip
                    </p>
                  </CardContent>
                </Card>
              }
              back={
                <Card className="h-full border-cyan-500/20 bg-gradient-to-br from-cyan-500/15 via-card to-card dark:border-cyan-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-cyan-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      System Details
                    </CardTitle>
                    <Activity className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Service</span>
                      <span className="font-medium">
                        {health?.name ?? "Unknown"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Email Alerts
                      </span>
                      <span className="font-medium">
                        {health?.email_configured
                          ? "Configured"
                          : "Not configured"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Provider</span>
                      <span className="font-medium uppercase">
                        {health?.llm_provider ?? "—"}
                      </span>
                    </div>
                    <p className="pt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Move away to flip back
                    </p>
                  </CardContent>
                </Card>
              }
            />
          </motion.div>

          {/* Scheduler */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 1 * 0.07, ease: "easeOut" }}
          >
            <DashboardFlipCard
              front={
                <Card className="h-full border-emerald-500/20 bg-gradient-to-br from-emerald-500/15 via-card to-card dark:border-emerald-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-emerald-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Next Run
                    </CardTitle>
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
                    <p className="mt-3 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Hover to flip
                    </p>
                  </CardContent>
                </Card>
              }
              back={
                <Card className="h-full border-teal-500/20 bg-gradient-to-br from-teal-500/15 via-card to-card dark:border-teal-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-teal-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Scheduler Details
                    </CardTitle>
                    <Clock className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <span className="font-medium">
                        {scheduler?.running ? "Running" : "Stopped"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Scheduled Jobs
                      </span>
                      <span className="font-medium">
                        {scheduler?.jobs?.length ?? 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Next Trigger
                      </span>
                      <span className="font-medium">
                        {scheduler?.jobs?.[0]
                          ? new Date(
                              scheduler.jobs[0].next_run,
                            ).toLocaleDateString()
                          : "—"}
                      </span>
                    </div>
                    <p className="pt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Move away to flip back
                    </p>
                  </CardContent>
                </Card>
              }
            />
          </motion.div>

          {/* Total findings */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 2 * 0.07, ease: "easeOut" }}
          >
            <DashboardFlipCard
              front={
                <Card className="h-full border-violet-500/20 bg-gradient-to-br from-violet-500/15 via-card to-card dark:border-violet-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-violet-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Total Findings
                    </CardTitle>
                    <BarChart3 className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold">
                      {stats?.total_findings ?? 0}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Avg impact: {stats?.avg_impact_score?.toFixed(1) ?? "—"}
                    </p>
                    <p className="mt-3 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Hover to flip
                    </p>
                  </CardContent>
                </Card>
              }
              back={
                <Card className="h-full border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-500/15 via-card to-card dark:border-fuchsia-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-fuchsia-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Finding Insights
                    </CardTitle>
                    <BarChart3 className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Categories</span>
                      <span className="font-medium">
                        {stats?.by_category
                          ? Object.keys(stats.by_category).length
                          : 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        Top Category
                      </span>
                      <span className="font-medium capitalize">
                        {topCategory?.[0] ?? "—"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Top Count</span>
                      <span className="font-medium">
                        {topCategory?.[1] ?? 0}
                      </span>
                    </div>
                    <p className="pt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Move away to flip back
                    </p>
                  </CardContent>
                </Card>
              }
            />
          </motion.div>

          {/* Latest digest */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 3 * 0.07, ease: "easeOut" }}
          >
            <DashboardFlipCard
              front={
                <Card className="h-full border-amber-500/20 bg-gradient-to-br from-amber-500/15 via-card to-card dark:border-amber-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-amber-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Latest Digest
                    </CardTitle>
                    <FileText className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    {latestDigest ? (
                      <>
                        <p className="text-sm font-medium">
                          {latestDigest.date}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {latestDigest.total_findings} findings
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No digests yet
                      </p>
                    )}
                    <p className="mt-3 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Hover to flip
                    </p>
                  </CardContent>
                </Card>
              }
              back={
                <Card className="h-full border-orange-500/20 bg-gradient-to-br from-orange-500/15 via-card to-card dark:border-orange-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-orange-950/70">
                  <CardHeader className="flex flex-row items-center justify-between pb-2">
                    <CardTitle className="text-sm font-medium">
                      Digest Details
                    </CardTitle>
                    <FileText className="size-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs">
                    {latestDigest ? (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Created</span>
                          <span className="font-medium">
                            {new Date(
                              latestDigest.created_at,
                            ).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Email</span>
                          <span className="font-medium">
                            {latestDigest.email_sent ? "Sent" : "Not sent"}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">
                            Recipients
                          </span>
                          <span className="font-medium">
                            {latestDigest.recipients.length}
                          </span>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No digest generated yet.
                      </p>
                    )}
                    <p className="pt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                      Move away to flip back
                    </p>
                  </CardContent>
                </Card>
              }
            />
          </motion.div>
        </div>

        {/* Category breakdown + Digest card */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Findings by category */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 5 * 0.07, ease: "easeOut" }}
          >
            <Card className="h-full border-violet-500/20 bg-gradient-to-br from-violet-500/10 via-card to-card dark:border-violet-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-violet-950/70">
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  Findings by Category
                </CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.by_category ? (
                  <div className="space-y-3">
                    {Object.entries(stats.by_category).map(([cat, count]) => (
                      <div
                        key={cat}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm capitalize">{cat}</span>
                        <div className="flex items-center gap-3">
                          <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary"
                              style={{
                                width: `${Math.min(
                                  100,
                                  (count / stats.total_findings) * 100,
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
                  <p className="text-sm text-muted-foreground">
                    No data available
                  </p>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Latest digest detail */}
          <motion.div
            initial={{ opacity: 0, filter: "blur(4px)" }}
            animate={{ opacity: 1, filter: "blur(0px)" }}
            transition={{ duration: 0.35, delay: 6 * 0.07, ease: "easeOut" }}
          >
            <Card className="h-full border-amber-500/20 bg-gradient-to-br from-amber-500/10 via-card to-card dark:border-amber-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-amber-950/70">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-medium">
                  Executive Summary
                </CardTitle>
                {latestDigest && (
                  <Button variant="outline" size="sm" asChild>
                    <a
                      href={getDigestPdfUrl(latestDigest.id)}
                      target="_blank"
                      rel="noreferrer"
                    >
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
          </motion.div>
        </div>

        {/* Recent runs */}
        <motion.div
          initial={{ opacity: 0, filter: "blur(4px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.35, delay: 7 * 0.07, ease: "easeOut" }}
          className="mt-6"
        >
          <Card className="border-sky-500/20 bg-gradient-to-br from-sky-500/10 via-card to-card dark:border-sky-800/45 dark:from-slate-950 dark:via-slate-900 dark:to-sky-950/70">
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
                  {recentRuns.map((run, i) => (
                    <motion.div
                      key={run.id}
                      initial={{ opacity: 0, filter: "blur(4px)" }}
                      animate={{ opacity: 1, filter: "blur(0px)" }}
                      transition={{
                        duration: 0.35,
                        delay: (8 + i) * 0.05,
                        ease: "easeOut",
                      }}
                      className="flex items-center justify-between rounded-md border bg-background/60 px-4 py-3 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-950/70"
                    >
                      <div className="flex items-center gap-3">
                        <StatusBadge
                          variant={getRunStatusVariant(run.status)}
                          dot
                        >
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
                    </motion.div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No runs recorded yet.
                </p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

function DashboardFlipCard({
  front,
  back,
}: {
  front: React.ReactNode;
  back: React.ReactNode;
}) {
  return (
    <button
      type="button"
      className="group h-full w-full rounded-xl text-left [perspective:1200px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      aria-label="Hover over card to flip"
    >
      <div
        className="grid h-full [transform:rotateY(0deg)] transition-transform duration-500 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)] group-focus-visible:[transform:rotateY(180deg)]"
        style={{
          willChange: "transform",
        }}
      >
        <div className="col-start-1 row-start-1 [backface-visibility:hidden]">
          {front}
        </div>
        <div className="col-start-1 row-start-1 [backface-visibility:hidden] [transform:rotateY(180deg)]">
          {back}
        </div>
      </div>
    </button>
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
