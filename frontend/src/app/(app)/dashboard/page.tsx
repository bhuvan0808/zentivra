"use client";

import Link from "next/link";
import {
  Box,
  FileText,
  BarChart3,
  Download,
  ArrowRight,
  TrendingUp,
  Activity,
  Clock,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";
import { fmtDate, fmtDateTime } from "@/lib/formatDate";
import {
  PieChart,
  Pie,
  Label,
  LineChart,
  Line,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  PolarAngleAxis,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { getDigestPdfUrl } from "@/lib/api";
import type { DashboardCharts, DashboardSources } from "@/lib/types";
import { useDashboard } from "@/hooks/use-dashboard";

function formatRelativeTime(dateStr: string): string {
  const diff = new Date(dateStr).getTime() - Date.now();
  if (diff < 0) return "overdue";
  const hours = Math.floor(diff / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  if (hours > 24) return `in ${Math.floor(hours / 24)}d ${hours % 24}h`;
  if (hours > 0) return `in ${hours}h ${minutes}m`;
  return `in ${minutes}m`;
}

const fadeBlur = (delay: number) => ({
  initial: { opacity: 0, filter: "blur(4px)" } as const,
  animate: { opacity: 1, filter: "blur(0px)" } as const,
  transition: { duration: 0.35, delay, ease: "easeOut" as const },
});

const fadeY = (delay: number) => ({
  initial: { opacity: 0, y: 10 } as const,
  animate: { opacity: 1, y: 0 } as const,
  transition: { duration: 0.4, delay },
});

export default function DashboardPage() {
  const {
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
  } = useDashboard();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Daily Intelligence Multi-Agent Command Centre."
      >
        <Button
          variant="outline"
          size="sm"
          disabled={refreshing}
          onClick={() => {
            fetchAll();
          }}
        >
          <RefreshCw
            className={`size-4 mr-1.5 ${refreshing ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </PageHeader>

      {/* Row 1: KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4">
        {/* Total Findings */}
        <motion.div {...fadeBlur(0)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Findings
              </CardTitle>
              <BarChart3 className="size-4 text-primary" />
            </CardHeader>
            <CardContent>
              {kpiLoading ? (
                <>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </>
              ) : kpi ? (
                <>
                  <div className="text-2xl font-bold">{kpi.total_findings}</div>
                  <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
                    <TrendingUp className="size-3 text-success" /> Since
                    inception
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">—</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Sources Monitored */}
        <motion.div {...fadeBlur(0.05)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Sources Monitored
              </CardTitle>
              <Box className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {kpiLoading ? (
                <>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </>
              ) : kpi ? (
                <>
                  <div className="text-2xl font-bold">{kpi.total_sources}</div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Active external feeds
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">—</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Total Runs */}
        <motion.div {...fadeBlur(0.1)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
              <Activity className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {kpiLoading ? (
                <>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </>
              ) : kpi ? (
                <>
                  <div className="text-2xl font-bold">
                    {kpi.runs_overview.total_runs}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {kpi.runs_overview.enabled_runs} enabled
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">—</p>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Latest Digest */}
        <motion.div {...fadeBlur(0.15)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Latest Digest
              </CardTitle>
              {!digestLoading && latestDigest?.has_pdf ? (
                <a
                  href={getDigestPdfUrl(latestDigest.digest_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary hover:text-primary/80 transition-colors"
                >
                  <Download className="size-4" />
                </a>
              ) : (
                <FileText className="size-4 text-muted-foreground" />
              )}
            </CardHeader>
            <CardContent>
              {digestLoading ? (
                <>
                  <Skeleton className="h-5 w-28 mb-2" />
                  <Skeleton className="h-5 w-20" />
                </>
              ) : latestDigest ? (
                <>
                  <div className="text-base font-semibold">
                    {fmtDate(latestDigest.created_at)}
                  </div>
                  <div className="mt-1">
                    <StatusBadge
                      variant={
                        latestDigest.status === "completed"
                          ? "success"
                          : "neutral"
                      }
                      dot
                    >
                      {latestDigest.status}
                    </StatusBadge>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No digests yet.</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 2: Upcoming Runs + Confidence Distribution */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <motion.div {...fadeBlur(0.25)} className="lg:col-span-2">
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm font-medium">
                  Upcoming Runs
                </CardTitle>
                <CardDescription>
                  Next scheduled pipeline executions
                </CardDescription>
              </div>
              <Clock className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {schedulerLoading ? (
                <Skeleton className="h-[150px] w-full rounded-md" />
              ) : upcomingJobs.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[50px]">#</TableHead>
                        <TableHead>Job Name</TableHead>
                        <TableHead>Frequency</TableHead>
                        <TableHead className="text-right">Next Run</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {upcomingJobs.map((job, i) => (
                        <TableRow key={job.id}>
                          <TableCell className="font-medium text-muted-foreground">
                            {i + 1}
                          </TableCell>
                          <TableCell className="font-medium">
                            {job.name}
                          </TableCell>
                          <TableCell>
                            <StatusBadge variant="neutral">
                              {job.frequency}
                            </StatusBadge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex flex-col items-end">
                              <span className="font-medium">
                                {formatRelativeTime(job.next_run)}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {fmtDateTime(job.next_run)}
                              </span>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-muted-foreground border border-dashed rounded-lg bg-muted/20">
                  No upcoming scheduled runs found.
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div {...fadeY(0.3)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Confidence Distribution
              </CardTitle>
              <CardDescription>
                Reliability scoring of extracted intelligence
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <div className="flex items-center justify-center p-6">
                  <Skeleton className="h-[200px] w-[200px] rounded-full" />
                </div>
              ) : charts ? (
                <ConfidenceRadial data={charts.confidence_distribution} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 3: Daily Findings + Confidence Trend */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <motion.div {...fadeY(0.3)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Daily Findings
              </CardTitle>
              <CardDescription>
                Volume of intelligence gathered per day
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <Skeleton className="h-[250px] w-full rounded-md" />
              ) : charts && charts.daily_findings.length > 0 ? (
                <DailyFindingsArea data={charts.daily_findings} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div {...fadeY(0.4)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Confidence Trend
              </CardTitle>
              <CardDescription>
                Average confidence score over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <Skeleton className="h-[250px] w-full rounded-md" />
              ) : charts ? (
                <ConfidenceTrendLine data={charts.confidence_trend} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 4: Findings by Category + Trigger Outcomes */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <motion.div {...fadeY(0.5)}>
          <Card className="h-full text-card-foreground relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Findings by Category
              </CardTitle>
              <CardDescription>
                Distribution across defined intelligence topics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <div className="flex items-center justify-center p-6">
                  <Skeleton className="h-[220px] w-[220px] rounded-full" />
                </div>
              ) : charts ? (
                <CategoryDonut
                  data={charts.by_category}
                  totalFindings={kpi?.total_findings ?? 0}
                />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div {...fadeY(0.6)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Trigger Outcomes
              </CardTitle>
              <CardDescription>
                Execution status of all recent triggers
              </CardDescription>
            </CardHeader>
            <CardContent>
              {triggersLoading ? (
                <div className="flex items-center justify-center p-6">
                  <Skeleton className="h-[220px] w-[220px] rounded-full" />
                </div>
              ) : triggers ? (
                <TriggerOutcomesDonut data={triggers.trigger_status_counts} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 5: Top Sources + Agent Performance */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <motion.div {...fadeY(0.7)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">Top Sources</CardTitle>
              <CardDescription>Sources with the most findings</CardDescription>
            </CardHeader>
            <CardContent>
              {sourcesLoading ? (
                <Skeleton className="h-[250px] w-full rounded-md" />
              ) : sources && sources.findings_by_source.length > 0 ? (
                <TopSourcesBar data={sources.findings_by_source} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div {...fadeY(0.8)}>
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Agent Performance
              </CardTitle>
              <CardDescription>
                Findings volume grouped by agent type
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chartsLoading ? (
                <Skeleton className="h-[250px] w-full rounded-md" />
              ) : charts && Object.keys(charts.by_agent_type).length > 0 ? (
                <AgentPerformanceBar data={charts.by_agent_type} />
              ) : (
                <NoData />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 6: Recent Activity */}
      <motion.div {...fadeBlur(0.7)}>
        <Card className="mt-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-linear-to-br from-foreground/5 to-transparent pointer-events-none" />
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-medium">
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest execution runs across all pipelines
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/runs">
                View all
                <ArrowRight className="ml-1 size-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {triggersLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full rounded-md" />
                ))}
              </div>
            ) : triggers && triggers.recent_triggers.length > 0 ? (
              <div className="space-y-1">
                {triggers.recent_triggers.map((trigger, i) => (
                  <motion.div
                    key={trigger.run_trigger_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: 0.1 + i * 0.05,
                      ease: "easeOut",
                    }}
                    className="flex items-center justify-between rounded-md px-4 py-3 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <StatusBadge
                        variant={
                          trigger.status === "completed"
                            ? "success"
                            : trigger.status === "failed"
                              ? "danger"
                              : "warning"
                        }
                        dot
                      >
                        {trigger.status}
                      </StatusBadge>
                      <div>
                        <div className="text-sm font-medium text-foreground">
                          {trigger.run_name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5 font-mono">
                          {trigger.run_trigger_id}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <div className="hidden sm:flex flex-col items-end">
                        <span className="font-medium">
                          {trigger.findings_count}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          findings
                        </span>
                      </div>
                      <div className="hidden sm:flex flex-col items-end">
                        <span className="font-medium">
                          {trigger.snapshots_count}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          sources
                        </span>
                      </div>
                      <div className="text-right min-w-[100px] text-muted-foreground">
                        {trigger.created_at
                          ? fmtDateTime(trigger.created_at)
                          : "—"}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-sm text-muted-foreground border border-dashed rounded-lg bg-muted/20">
                No trigger history found. Go to Runs to start the intelligence
                pipeline.
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

/* ── Sub-charts ── */

function NoData() {
  return (
    <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
      No data available
    </div>
  );
}

function ConfidenceRadial({
  data,
}: {
  data: DashboardCharts["confidence_distribution"];
}) {
  const chartData = [
    { name: "high", value: data.high, fill: "var(--color-high)" },
    { name: "medium", value: data.medium, fill: "var(--color-medium)" },
    { name: "low", value: data.low, fill: "var(--color-low)" },
  ];
  const config = {
    high: { label: "High (>0.7)", color: "var(--success)" },
    medium: { label: "Medium", color: "var(--warning)" },
    low: { label: "Low (<0.3)", color: "var(--danger)" },
  } satisfies ChartConfig;

  return (
    <ChartContainer
      config={config}
      className="mx-auto aspect-square max-h-[280px]"
    >
      <RadialBarChart
        data={chartData}
        innerRadius={70}
        outerRadius={150}
        startAngle={180}
        endAngle={0}
      >
        <PolarAngleAxis type="number" domain={[0, "auto"]} tick={false} />
        <ChartTooltip content={<ChartTooltipContent nameKey="name" />} />
        <RadialBar dataKey="value" cornerRadius={4} />
        <ChartLegend content={<ChartLegendContent nameKey="name" />} />
      </RadialBarChart>
    </ChartContainer>
  );
}

function DailyFindingsArea({
  data,
}: {
  data: DashboardCharts["daily_findings"];
}) {
  const config = {
    count: { label: "Findings", color: "var(--chart-1)" },
  } satisfies ChartConfig;

  return (
    <ChartContainer config={config} className="h-[250px] w-full">
      <AreaChart
        data={data}
        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
      >
        <defs>
          <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="5%"
              stopColor="var(--color-count)"
              stopOpacity={0.3}
            />
            <stop offset="95%" stopColor="var(--color-count)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(v) => {
            const d = new Date(v);
            return d.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          }}
        />
        <YAxis tickLine={false} axisLine={false} tickMargin={8} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="var(--color-count)"
          fillOpacity={1}
          fill="url(#colorCount)"
        />
      </AreaChart>
    </ChartContainer>
  );
}

function ConfidenceTrendLine({
  data,
}: {
  data: DashboardCharts["confidence_trend"];
}) {
  const filtered = data
    .filter((d) => d.avg_confidence !== null)
    .map((d) => ({
      ...d,
      avg_confidence: Number(d.avg_confidence?.toFixed(2)),
    }));

  const config = {
    avg_confidence: { label: "Avg Confidence", color: "var(--chart-3)" },
  } satisfies ChartConfig;

  if (filtered.length === 0) return <NoData />;

  return (
    <ChartContainer config={config} className="h-[250px] w-full">
      <LineChart
        data={filtered}
        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
      >
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tickFormatter={(v) => {
            const d = new Date(v);
            return d.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          }}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          domain={[0, 1]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line
          type="monotone"
          dataKey="avg_confidence"
          stroke="var(--color-avg_confidence)"
          strokeWidth={2}
          dot={{ r: 3, fill: "var(--color-avg_confidence)" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ChartContainer>
  );
}

function CategoryDonut({
  data,
  totalFindings,
}: {
  data: Record<string, number>;
  totalFindings: number;
}) {
  const entries = Object.entries(data)
    .map(([name, value]) => ({ name, value, fill: `var(--color-${name})` }))
    .sort((a, b) => b.value - a.value);

  const config: ChartConfig = {
    value: { label: "Findings" },
    ...Object.fromEntries(
      entries.map((e, i) => [
        e.name,
        {
          label: e.name.charAt(0).toUpperCase() + e.name.slice(1),
          color: `var(--chart-${(i % 5) + 1})`,
        },
      ]),
    ),
  };

  if (entries.length === 0) return <NoData />;

  return (
    <ChartContainer
      config={config}
      className="mx-auto aspect-square max-h-[280px]"
    >
      <PieChart>
        <ChartTooltip
          content={<ChartTooltipContent nameKey="name" hideLabel />}
        />
        <Pie
          data={entries}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={85}
          paddingAngle={4}
          strokeWidth={0}
        >
          <Label
            content={({ viewBox }) => {
              if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                return (
                  <text
                    x={viewBox.cx}
                    y={viewBox.cy}
                    textAnchor="middle"
                    dominantBaseline="middle"
                  >
                    <tspan
                      x={viewBox.cx}
                      y={viewBox.cy}
                      className="fill-foreground text-3xl font-bold"
                    >
                      {totalFindings.toLocaleString()}
                    </tspan>
                    <tspan
                      x={viewBox.cx}
                      y={(viewBox.cy || 0) + 24}
                      className="fill-muted-foreground text-sm"
                    >
                      Findings
                    </tspan>
                  </text>
                );
              }
            }}
          />
        </Pie>
        <ChartLegend content={<ChartLegendContent nameKey="name" />} />
      </PieChart>
    </ChartContainer>
  );
}

function TriggerOutcomesDonut({ data }: { data: Record<string, number> }) {
  const statusColors: Record<string, string> = {
    completed: "var(--chart-1)",
    failed: "var(--chart-5)",
    partial: "var(--chart-4)",
    completed_empty: "var(--chart-3)",
    running: "var(--chart-2)",
  };

  const entries = Object.entries(data)
    .filter(([, count]) => count > 0)
    .map(([status, count]) => ({
      status,
      count,
      fill: statusColors[status] ?? "var(--color-muted)",
    }))
    .sort((a, b) => b.count - a.count);

  const config: ChartConfig = {
    count: { label: "Triggers" },
    ...Object.fromEntries(
      entries.map((d) => [
        d.status,
        { label: d.status.replace("_", " "), color: d.fill },
      ]),
    ),
  };

  if (entries.length === 0) return <NoData />;

  return (
    <ChartContainer
      config={config}
      className="mx-auto aspect-square max-h-[280px]"
    >
      <PieChart>
        <ChartTooltip
          content={<ChartTooltipContent nameKey="status" hideLabel />}
        />
        <Pie
          data={entries}
          dataKey="count"
          nameKey="status"
          innerRadius={60}
          outerRadius={85}
          paddingAngle={4}
          strokeWidth={0}
        >
          <Label
            content={({ viewBox }) => {
              if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                return (
                  <text
                    x={viewBox.cx}
                    y={viewBox.cy}
                    textAnchor="middle"
                    dominantBaseline="middle"
                  >
                    <tspan
                      x={viewBox.cx}
                      y={viewBox.cy}
                      className="fill-foreground text-3xl font-bold"
                    >
                      {entries
                        .reduce((a, c) => a + c.count, 0)
                        .toLocaleString()}
                    </tspan>
                    <tspan
                      x={viewBox.cx}
                      y={(viewBox.cy || 0) + 24}
                      className="fill-muted-foreground text-sm"
                    >
                      Triggers
                    </tspan>
                  </text>
                );
              }
            }}
          />
        </Pie>
        <ChartLegend content={<ChartLegendContent nameKey="status" />} />
      </PieChart>
    </ChartContainer>
  );
}

function TopSourcesBar({
  data,
}: {
  data: DashboardSources["findings_by_source"];
}) {
  const reversed = [...data].reverse();
  const config = {
    count: { label: "Findings", color: "var(--chart-4)" },
  } satisfies ChartConfig;

  return (
    <ChartContainer config={config} className="h-[250px] w-full">
      <BarChart
        layout="vertical"
        data={reversed}
        margin={{ top: 0, right: 10, left: 20, bottom: 0 }}
      >
        <CartesianGrid horizontal={false} />
        <XAxis type="number" hide />
        <YAxis
          dataKey="display_name"
          type="category"
          axisLine={false}
          tickLine={false}
          tickMargin={8}
          width={120}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar
          dataKey="count"
          fill="var(--color-count)"
          radius={[0, 4, 4, 0]}
          barSize={24}
        />
      </BarChart>
    </ChartContainer>
  );
}

function AgentPerformanceBar({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const config = {
    value: { label: "Findings", color: "var(--chart-2)" },
  } satisfies ChartConfig;

  return (
    <ChartContainer config={config} className="h-[250px] w-full">
      <BarChart
        layout="vertical"
        data={entries}
        margin={{ top: 0, right: 10, left: 20, bottom: 0 }}
      >
        <CartesianGrid horizontal={false} />
        <XAxis type="number" hide />
        <YAxis
          dataKey="name"
          type="category"
          axisLine={false}
          tickLine={false}
          tickMargin={8}
          width={100}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar
          dataKey="value"
          fill="var(--color-value)"
          radius={[0, 4, 4, 0]}
          barSize={24}
        />
      </BarChart>
    </ChartContainer>
  );
}
