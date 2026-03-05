"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Filter,
  Inbox,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import {
  StatusBadge,
  getConfidenceVariant,
  getImpactVariant,
} from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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

  const [searchQuery, setSearchQuery] = useState("");
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
      search: searchQuery || undefined,
      include_duplicates: false,
    });
    if (res.ok) {
      setFindings(res.data);
    } else {
      toast.error(res.error);
    }
    setLoading(false);
  }, [page, category, minConfidence, searchQuery]);

  useEffect(() => {
    fetchFindings();
  }, [fetchFindings]);

  function handleSearch() {
    setPage(1);
    fetchFindings();
  }

  return (
    <div>
      <PageHeader
        title="Findings"
        description="Browse and search intelligence findings."
      />

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search findings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="pl-9"
          />
        </div>
        <Select value={category} onValueChange={(v) => { setCategory(v); setPage(1); }}>
          <SelectTrigger className="w-40">
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
        <Select value={minConfidence} onValueChange={(v) => { setMinConfidence(v); setPage(1); }}>
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
            {findings.map((finding) => {
              const isExpanded = expandedId === finding.id;
              return (
                <Card key={finding.id} className="overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-semibold leading-snug">
                        {finding.title}
                      </h3>
                      <StatusBadge variant="neutral">
                        {finding.category}
                      </StatusBadge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{finding.publisher}</span>
                      <span>&middot;</span>
                      <span>
                        {new Date(finding.date_detected).toLocaleDateString()}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {finding.summary_short}
                    </p>

                    <div className="mt-3 flex items-center gap-2">
                      <StatusBadge
                        variant={getConfidenceVariant(finding.confidence)}
                      >
                        {(finding.confidence * 100).toFixed(0)}% conf
                      </StatusBadge>
                      <StatusBadge
                        variant={getImpactVariant(finding.impact_score)}
                      >
                        {finding.impact_score.toFixed(1)} impact
                      </StatusBadge>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-1">
                      {finding.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    {/* Expand toggle */}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-3 w-full"
                      onClick={() =>
                        setExpandedId(isExpanded ? null : finding.id)
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
                          <p className="data-label mb-1">Detailed Summary</p>
                          <p className="text-sm leading-relaxed">
                            {finding.summary_long}
                          </p>
                        </div>
                        <div>
                          <p className="data-label mb-1">Why It Matters</p>
                          <p className="text-sm leading-relaxed">
                            {finding.why_it_matters}
                          </p>
                        </div>
                        {finding.evidence.claims.length > 0 && (
                          <div>
                            <p className="data-label mb-1">Evidence</p>
                            <ul className="list-disc pl-4 text-sm space-y-1">
                              {finding.evidence.claims.map((claim, i) => (
                                <li key={i}>{claim}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <div>
                          <p className="data-label mb-1">Entities</p>
                          <div className="flex flex-wrap gap-1">
                            {finding.entities.companies.map((e) => (
                              <Badge
                                key={e}
                                variant="secondary"
                                className="text-xs"
                              >
                                {e}
                              </Badge>
                            ))}
                            {finding.entities.models.map((e) => (
                              <Badge
                                key={e}
                                variant="secondary"
                                className="text-xs"
                              >
                                {e}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <a
                          href={finding.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          View source
                          <ExternalLink className="size-3" />
                        </a>
                      </div>
                    )}
                  </CardContent>
                </Card>
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
