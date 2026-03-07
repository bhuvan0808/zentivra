"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Box,
  FileText,
  BarChart3,
  Download,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { motion } from "framer-motion";
import { fmtDate, fmtDateTime } from "@/lib/formatDate";
import {
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { getDashboardStats, getLatestDigest, getDigestPdfUrl } from "@/lib/api";
import type { DashboardStats, Digest } from "@/lib/types";

// Dynamic chart colors inspired by the theme
const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [latestDigest, setLatestDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [statsRes, digestRes] = await Promise.all([
        getDashboardStats(),
        getLatestDigest(),
      ]);
      if (statsRes.ok) setStats(statsRes.data);
      if (digestRes.ok) setLatestDigest(digestRes.data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading || !stats) return <DashboardSkeleton />;

  // Prepare chart data
  const categoryData = Object.entries(stats.by_category)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const agentData = Object.entries(stats.by_agent_type)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const confidenceData = [
    {
      name: "High (>0.7)",
      value: stats.confidence_distribution.high,
      fill: "var(--color-success)",
    },
    {
      name: "Medium",
      value: stats.confidence_distribution.medium,
      fill: "var(--color-warning)",
    },
    {
      name: "Low (<0.3)",
      value: stats.confidence_distribution.low,
      fill: "var(--color-danger)",
    },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Daily Intelligence Multi-Agent Command Centre."
      />

      {/* Row 1: KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, filter: "blur(4px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.35, delay: 0.0, ease: "easeOut" }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Findings
              </CardTitle>
              <BarChart3 className="size-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.total_findings}</div>
              <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
                <TrendingUp className="size-3 text-success" /> Since inception
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, filter: "blur(4px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.35, delay: 0.1, ease: "easeOut" }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Sources Monitored
              </CardTitle>
              <Box className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.total_sources}</div>
              <p className="mt-1 text-xs text-muted-foreground">
                Active external feeds
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, filter: "blur(4px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.35, delay: 0.2, ease: "easeOut" }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Latest Digest
              </CardTitle>
              {latestDigest?.pdf_path ? (
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
              {latestDigest ? (
                <>
                  <div className="text-lg font-semibold">
                    {fmtDate(latestDigest.created_at)}
                  </div>
                  <div className="mt-2">
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

      {/* Row 2: Charts (Categories + Timeline) */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <Card className="h-full text-card-foreground relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Findings by Category
              </CardTitle>
              <CardDescription>
                Distribution across defined intelligence topics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                {categoryData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                      >
                        {categoryData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={CHART_COLORS[index % CHART_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          backgroundColor: "var(--color-card)",
                          color: "var(--color-card-foreground)",
                        }}
                        itemStyle={{
                          color: "var(--color-foreground)",
                          fontSize: "14px",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    No data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Findings Timeline
              </CardTitle>
              <CardDescription>
                Volume of intelligence gathered per trigger run
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                {stats.findings_timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={stats.findings_timeline}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient
                          id="colorCount"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="var(--color-primary)"
                            stopOpacity={0.3}
                          />
                          <stop
                            offset="95%"
                            stopColor="var(--color-primary)"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="var(--color-border)"
                      />
                      <XAxis
                        dataKey="date"
                        tickLine={false}
                        axisLine={false}
                        tick={{
                          fontSize: 12,
                          fill: "var(--color-muted-foreground)",
                        }}
                      />
                      <YAxis
                        tickLine={false}
                        axisLine={false}
                        tick={{
                          fontSize: 12,
                          fill: "var(--color-muted-foreground)",
                        }}
                      />
                      <Tooltip
                        labelFormatter={(label, payload) =>
                          payload?.[0]?.payload?.full_date || label
                        }
                        contentStyle={{
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          backgroundColor: "var(--color-card)",
                        }}
                        labelStyle={{
                          color: "var(--color-muted-foreground)",
                          marginBottom: "4px",
                        }}
                        itemStyle={{
                          color: "var(--color-primary)",
                          fontWeight: "500",
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="count"
                        stroke="var(--color-primary)"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorCount)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    No data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 3: Agent Performance + Confidence */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Agent Performance
              </CardTitle>
              <CardDescription>
                Findings volume grouped by agent type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                {agentData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      layout="vertical"
                      data={agentData}
                      margin={{ top: 0, right: 10, left: 20, bottom: 0 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        horizontal={true}
                        vertical={false}
                        stroke="var(--color-border)"
                      />
                      <XAxis type="number" hide />
                      <YAxis
                        dataKey="name"
                        type="category"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 13, fill: "var(--color-foreground)" }}
                        width={100}
                      />
                      <Tooltip
                        cursor={{ fill: "var(--color-muted)", opacity: 0.4 }}
                        contentStyle={{
                          borderRadius: "8px",
                          border: "1px solid var(--color-border)",
                          backgroundColor: "var(--color-card)",
                        }}
                      />
                      <Bar
                        dataKey="value"
                        fill="var(--color-chart-2)"
                        radius={[0, 4, 4, 0]}
                        barSize={24}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                    No data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.6 }}
        >
          <Card className="h-full relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
            <CardHeader>
              <CardTitle className="text-sm font-medium">
                Confidence Distribution
              </CardTitle>
              <CardDescription>
                Reliability scoring of extracted intelligence
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={confidenceData}
                    margin={{ top: 20, right: 10, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="var(--color-border)"
                    />
                    <XAxis
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{
                        fontSize: 12,
                        fill: "var(--color-muted-foreground)",
                      }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{
                        fontSize: 12,
                        fill: "var(--color-muted-foreground)",
                      }}
                    />
                    <Tooltip
                      cursor={{ fill: "var(--color-muted)", opacity: 0.4 }}
                      contentStyle={{
                        borderRadius: "8px",
                        border: "1px solid var(--color-border)",
                        backgroundColor: "var(--color-card)",
                      }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={40}>
                      {confidenceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Row 4: Recent Triggers */}
      <motion.div
        initial={{ opacity: 0, filter: "blur(4px)" }}
        animate={{ opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.35, delay: 0.7, ease: "easeOut" }}
      >
        <Card className="mt-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 to-transparent pointer-events-none" />
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
            {stats.recent_triggers.length > 0 ? (
              <div className="space-y-1">
                {stats.recent_triggers.map((trigger, i) => (
                  <motion.div
                    key={trigger.run_trigger_id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: 0.8 + i * 0.05,
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

function DashboardSkeleton() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Daily Intelligence Multi-Agent Command Centre."
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={`chart-${i}`} className="h-[350px]">
            <CardHeader>
              <Skeleton className="h-5 w-40 mb-1" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent className="flex items-center justify-center p-6">
              <Skeleton className="h-full w-full rounded-md" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
