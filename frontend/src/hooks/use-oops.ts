import { useState } from "react";
import { toast } from "sonner";
import {
  submitOopsReport,
  getOopsReportPdfUrl,
} from "@/lib/oops-api";
import type { OopsResponse } from "@/lib/oops-api";

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
  handleSubmit: () => Promise<void>;
  handleReset: () => void;
  handleDownloadPdf: () => void;
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
    handleSubmit,
    handleReset,
    handleDownloadPdf,
  };
}
