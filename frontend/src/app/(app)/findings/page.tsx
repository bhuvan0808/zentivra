"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Filter,
  Inbox,
} from "lucide-react";
import { toast } from "sonner";
import { fmtDate } from "@/lib/formatDate";
import { PageHeader } from "@/components/page-header";
import { StatusBadge, getConfidenceVariant } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getFindings } from "@/lib/api";
import { motion } from "framer-motion";
import type { Finding, FindingCategory } from "@/lib/types";

const CATEGORY_OPTIONS: { value: FindingCategory | "all"; label: string }[] = [
  { value: "all", label: "All Categories" },
  { value: "models", label: "Models" },
  { value: "apis", label: "APIs" },
  { value: "pricing", label: "Pricing" },
  { value: "benchmarks", label: "Benchmarks" },
  { value: "safety", label: "Safety" },
  { value: "tooling", label: "Tooling" },
  { value: "research", label: "Research" },
  { value: "other", label: "Other" },
];

export default function FindingsPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const [category, setCategory] = useState<string>("all");
  const [minConfidence, setMinConfidence] = useState<string>("0");
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const fetchFindings = useCallback(async () => {
    setLoading(true);
    const res = await getFindings({
      page,
      page_size: pageSize,
      category: category !== "all" ? (category as FindingCategory) : undefined,
      min_confidence: minConfidence !== "0" ? Number(minConfidence) : undefined,
    });
    if (res.ok) {
      setFindings(res.data);
    } else {
      toast.error(res.error);
    }
    setLoading(false);
  }, [page, category, minConfidence]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void fetchFindings();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [fetchFindings]);

  return (
    <div>
      <PageHeader
        title="Findings"
        description="Browse and search intelligence findings."
      />

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select
          value={category}
          onValueChange={(v) => {
            setCategory(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44">
            <Filter className="mr-1.5 size-3.5" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CATEGORY_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={minConfidence}
          onValueChange={(v) => {
            setMinConfidence(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Min confidence" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">Any confidence</SelectItem>
            <SelectItem value="0.5">≥ 50% confidence</SelectItem>
            <SelectItem value="0.7">≥ 70% confidence</SelectItem>
            <SelectItem value="0.9">≥ 90% confidence</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Results */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-3/4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="mt-2 h-4 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : findings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Inbox className="mb-4 size-12 text-muted-foreground/50" />
          <p className="text-lg font-medium">No findings match your filters</p>
          <p className="text-sm text-muted-foreground">
            Try broadening your search or changing the category filter.
          </p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {findings.map((finding, i) => {
              const isExpanded = expandedId === finding.finding_id;
              return (
                <motion.div
                  key={finding.finding_id}
                  initial={{ opacity: 0, filter: "blur(4px)" }}
                  animate={{ opacity: 1, filter: "blur(0px)" }}
                  transition={{
                    duration: 0.35,
                    delay: i * 0.05,
                    ease: "easeOut",
                  }}
                >
                  <Card className="overflow-hidden">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-sm font-semibold leading-snug line-clamp-2">
                          <span className="mr-1.5 font-mono text-xs text-muted-foreground">
                            {(page - 1) * pageSize + i + 1}.
                          </span>
                          {finding.summary || finding.src_url}
                        </h3>
                        {finding.category && (
                          <StatusBadge variant="neutral">
                            {finding.category}
                          </StatusBadge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{fmtDate(finding.created_at)}</span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="mt-1 flex items-center gap-2">
                        <StatusBadge
                          variant={getConfidenceVariant(finding.confidence)}
                        >
                          {(finding.confidence * 100).toFixed(0)}% conf
                        </StatusBadge>
                        <a
                          href={finding.src_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          Source
                          <ExternalLink className="size-3" />
                        </a>
                      </div>

                      {finding.content && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-3 w-full"
                            onClick={() =>
                              setExpandedId(
                                isExpanded ? null : finding.finding_id,
                              )
                            }
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="mr-1 size-3.5" />
                                Show less
                              </>
                            ) : (
                              <>
                                <ChevronDown className="mr-1 size-3.5" />
                                Show more
                              </>
                            )}
                          </Button>

                          {isExpanded && (
                            <div className="mt-3 space-y-3">
                              <Separator />
                              <div>
                                <p className="data-label mb-1">Content</p>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                                  {finding.content}
                                </p>
                              </div>
                              {finding.run_trigger_id && (
                                <div>
                                  <p className="data-label mb-1">Run Trigger</p>
                                  <p className="text-xs font-mono text-muted-foreground">
                                    {finding.run_trigger_id}
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          {/* Pagination */}
          <div className="mt-6 flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">Page {page}</span>
            <Button
              variant="outline"
              size="sm"
              disabled={findings.length < pageSize}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
