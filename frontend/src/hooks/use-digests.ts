import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { getDigests, getDigestPdfUrl } from "@/lib/api";
import type { Digest } from "@/lib/types";

export interface UseDigestsReturn {
  digests: Digest[];
  loading: boolean;
  handleDownloadPdf: (digestId: string) => Promise<void>;
}

/**
 * Custom hook for the Digests page.
 * Manages fetching digest archives and downloading digest PDFs.
 *
 * Interacts with:
 * - GET /api/digests
 * - GET /api/digests/{id}/pdf
 */
export function useDigests(): UseDigestsReturn {
  const [digests, setDigests] = useState<Digest[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDigests = useCallback(async () => {
    const res = await getDigests(30);
    if (res.ok) {
      setDigests(res.data);
    } else {
      toast.error(res.error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void fetchDigests();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [fetchDigests]);

  async function handleDownloadPdf(digestId: string) {
    try {
      const url = getDigestPdfUrl(digestId);
      const token = localStorage.getItem("auth_token");
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(url, { headers });
      if (!res.ok) {
        const body = await res.json();
        toast.warning(
          typeof body.detail === "string"
            ? body.detail
            : "Unable to download PDF.",
        );
        return;
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `zentivra_digest.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      toast.error("Unable to reach the server. Please check your connection.");
    }
  }

  return {
    digests,
    loading,
    handleDownloadPdf,
  };
}