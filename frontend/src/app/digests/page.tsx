"use client";

import { useEffect, useState, useCallback } from "react";
import {
  FileText,
  Download,
  Mail,
  MailX,
  Calendar,
  Inbox,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { getDigests, getDigest, getDigestPdfUrl } from "@/lib/api";
import { motion } from "framer-motion";
import type { Digest } from "@/lib/types";

function digestSummaryPreview(summary: string | null | undefined): string {
  if (!summary) return "No executive summary available.";
  return summary
    .replace(/\*\*/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export default function DigestsPage() {
  const [digests, setDigests] = useState<Digest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDigest, setSelectedDigest] = useState<Digest | null>(null);

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

  async function handleView(digest: Digest) {
    const res = await getDigest(digest.id);
    if (res.ok) {
      setSelectedDigest(res.data);
    } else {
      toast.error(res.error);
    }
  }

  async function handleDownloadPdf(id: string) {
    try {
      const url = getDigestPdfUrl(id);
      const res = await fetch(url);
      if (!res.ok) {
        const body = await res.json();
        toast.warning(
          typeof body.detail === "string"
            ? body.detail
            : "Unable to download PDF."
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

  if (loading) {
    return (
      <div>
        <PageHeader title="Digests" description="Archive of daily executive digests." />
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="mt-2 h-4 w-3/4" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Digests"
        description="Archive of daily executive digests."
      />

      {digests.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <Inbox className="mb-4 size-12 text-muted-foreground/50" />
          <p className="text-lg font-medium">No digests generated yet</p>
          <p className="text-sm text-muted-foreground">
            Digests are created after a successful pipeline run.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {digests.map((digest, i) => (
            <motion.div
              key={digest.id}
              initial={{ opacity: 0, filter: "blur(4px)" }}
              animate={{ opacity: 1, filter: "blur(0px)" }}
              transition={{ duration: 0.35, delay: i * 0.05, ease: "easeOut" }}
            >
            <Card
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => handleView(digest)}
            >
              <CardContent className="flex items-start justify-between gap-4 py-5">
                <div className="flex min-w-0 items-start gap-4">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Calendar className="size-5 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold">{digest.date}</p>
                    <p className="mt-0.5 text-sm text-muted-foreground [display:-webkit-box] overflow-hidden text-ellipsis [-webkit-box-orient:vertical] [-webkit-line-clamp:2] break-words">
                      {digestSummaryPreview(digest.executive_summary)}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <StatusBadge variant="neutral">
                        <FileText className="mr-1 size-3" />
                        {digest.total_findings} findings
                      </StatusBadge>
                      <StatusBadge
                        variant={digest.email_sent ? "success" : "neutral"}
                      >
                        {digest.email_sent ? (
                          <Mail className="mr-1 size-3" />
                        ) : (
                          <MailX className="mr-1 size-3" />
                        )}
                        {digest.email_sent
                          ? `Sent to ${digest.recipients?.length ?? 0}`
                          : "Not sent"}
                      </StatusBadge>
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownloadPdf(digest.id);
                  }}
                >
                  <Download className="mr-1.5 size-3.5" />
                  PDF
                </Button>
              </CardContent>
            </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Digest detail dialog */}
      <Dialog
        open={!!selectedDigest}
        onOpenChange={(open) => !open && setSelectedDigest(null)}
      >
        <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Digest &mdash; {selectedDigest?.date}
            </DialogTitle>
          </DialogHeader>
          {selectedDigest && (
            <div className="space-y-4">
              <div>
                <p className="data-label mb-1">Executive Summary</p>
                <div className="max-h-[42vh] overflow-y-auto rounded-md border bg-muted/20 p-3 text-sm leading-relaxed whitespace-pre-wrap break-words">
                  {selectedDigest.executive_summary}
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="data-label">Total Findings</p>
                  <p className="text-sm font-mono">
                    {selectedDigest.total_findings}
                  </p>
                </div>
                <div>
                  <p className="data-label">Run ID</p>
                  <p className="text-sm font-mono break-all">
                    {selectedDigest.run_id}
                  </p>
                </div>
                <div>
                  <p className="data-label">Email Sent</p>
                  <StatusBadge
                    variant={selectedDigest.email_sent ? "success" : "neutral"}
                    dot
                  >
                    {selectedDigest.email_sent ? "Yes" : "No"}
                  </StatusBadge>
                </div>
                <div>
                  <p className="data-label">Created</p>
                  <p className="text-sm">
                    {new Date(selectedDigest.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {(selectedDigest.recipients?.length ?? 0) > 0 && (
                <div>
                  <p className="data-label mb-1">Recipients</p>
                  <div className="flex flex-wrap gap-1">
                    {(selectedDigest.recipients ?? []).map((r) => (
                      <span
                        key={r}
                        className="inline-flex rounded-md bg-muted px-2 py-0.5 text-xs font-mono"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <Button
                className="w-full"
                onClick={() => handleDownloadPdf(selectedDigest.id)}
              >
                <Download className="mr-1.5 size-4" />
                Download PDF
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
