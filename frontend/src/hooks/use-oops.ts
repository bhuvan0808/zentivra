import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  submitOopsReport,
  getOopsReportPdfUrl,
  getReportHistory,
} from "@/lib/oops-api";
import type { OopsResponse, OopsReportSummary } from "@/lib/oops-api";

export interface UseOopsReturn {
  url: string;
  setUrl: (v: string) => void;
  title: string;
  setTitle: (v: string) => void;
  email: string;
  setEmail: (v: string) => void;
  submitting: boolean;
  result: OopsResponse | null;
  error: string | null;
  history: OopsReportSummary[];
  historyLoading: boolean;
  handleSubmit: () => Promise<void>;
  handleReset: () => void;
  handleDownloadPdf: () => void;
  handleDownloadHistoryPdf: (reportId: string) => void;
}

/**
 * Custom hook for the Oops page.
 * Manages form state, submission, and result display for the
 * disruptive article workflow.
 *
 * Interacts with:
 * - POST /api/workflows/disruptive-article
 * - GET  /api/workflows/reports/{report_id}/pdf
 */
export function useOops(): UseOopsReturn {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<OopsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<OopsReportSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    const res = await getReportHistory();
    if (res.ok) {
      setHistory(res.data);
    }
    setHistoryLoading(false);
  }, []);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory]);

  async function handleSubmit() {
    if (!url.trim()) {
      toast.error("Please enter an article URL.");
      return;
    }
    if (!email.trim()) {
      toast.error("Please enter a recipient email address.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setResult(null);

    const res = await submitOopsReport({
      url: url.trim(),
      recipient_email: email.trim(),
      title: title.trim() || undefined,
    });

    setSubmitting(false);

    if (res.ok) {
      setResult(res.data);
      toast.success(res.data.message);
      // Refresh history after new report
      void fetchHistory();
    } else {
      setError(res.error);
      toast.error(res.error);
    }
  }

  function handleReset() {
    setUrl("");
    setTitle("");
    setEmail("");
    setResult(null);
    setError(null);
  }

  function handleDownloadPdf() {
    if (!result?.pdf_download_url) return;
    const pdfUrl = getOopsReportPdfUrl(result.report_id);
    window.open(pdfUrl, "_blank");
  }

  function handleDownloadHistoryPdf(reportId: string) {
    const pdfUrl = getOopsReportPdfUrl(reportId);
    window.open(pdfUrl, "_blank");
  }

  return {
    url,
    setUrl,
    title,
    setTitle,
    email,
    setEmail,
    submitting,
    result,
    error,
    history,
    historyLoading,
    handleSubmit,
    handleReset,
    handleDownloadPdf,
    handleDownloadHistoryPdf,
  };
}
