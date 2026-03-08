import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { getFindings } from "@/lib/api";
import type { Finding, FindingCategory } from "@/lib/types";

export interface UseFindingsReturn {
  findings: Finding[];
  loading: boolean;
  expandedId: string | null;
  setExpandedId: (v: string | null | ((prev: string | null) => string | null)) => void;
  category: string;
  setCategory: (v: string) => void;
  minConfidence: string;
  setMinConfidence: (v: string) => void;
  page: number;
  setPage: (v: number | ((prev: number) => number)) => void;
  pageSize: number;
}

/**
 * Custom hook for the Findings page.
 * Manages fetching findings, pagination, filtering, and row expansion.
 *
 * Interacts with:
 * - GET /api/findings
 */
export function useFindings(): UseFindingsReturn {
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

  return {
    findings,
    loading,
    expandedId,
    setExpandedId,
    category,
    setCategory,
    minConfidence,
    setMinConfidence,
    page,
    setPage,
    pageSize,
  };
}