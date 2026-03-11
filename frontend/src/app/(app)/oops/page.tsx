"use client";

import {
  Sparkles,
  Send,
  Download,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Loader2,
  Mail,
  Link2,
  History,
  FileText,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useOops } from "@/hooks/use-oops";

const AGENT_LABELS: Record<string, string> = {
  competitor: "Competitor Watcher",
  model_provider: "Model Provider Watcher",
  research: "Research Scout",
  hf_benchmark: "HF Benchmark Tracker",
};

function formatDate(iso: string | null): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function OopsPage() {
  const {
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
  } = useOops();

  return (
    <div>
      <PageHeader
        title="Oops"
        description="Drop a disruptive article link, generate a PDF impact report, and email it."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input form */}
        <Card>
          <CardContent className="py-6 space-y-5">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="size-5 text-primary" />
              <h3 className="text-sm font-semibold">Analyze Article</h3>
            </div>

            {/* URL input */}
            <div className="space-y-2">
              <Label htmlFor="oops-url" className="text-xs font-medium">
                Article URL
              </Label>
              <div className="relative">
                <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="oops-url"
                  type="url"
                  placeholder="https://example.com/breaking-news-article"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={submitting}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Title input */}
            <div className="space-y-2">
              <Label htmlFor="oops-title" className="text-xs font-medium">
                Report Title{" "}
                <span className="text-muted-foreground font-normal">
                  (optional)
                </span>
              </Label>
              <Input
                id="oops-title"
                type="text"
                placeholder="e.g. Breaking: Major AI Announcement"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={submitting}
              />
            </div>

            {/* Email input */}
            <div className="space-y-2">
              <Label htmlFor="oops-email" className="text-xs font-medium">
                Recipient Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  id="oops-email"
                  type="email"
                  placeholder="team@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Submit button */}
            <div className="flex gap-3 pt-2">
              <Button
                onClick={handleSubmit}
                disabled={submitting || !url.trim() || !email.trim()}
                className="flex-1"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 size-4" />
                    Analyze &amp; Send Report
                  </>
                )}
              </Button>
              {(result || error) && (
                <Button variant="outline" onClick={handleReset}>
                  <RotateCcw className="mr-2 size-4" />
                  Reset
                </Button>
              )}
            </div>

            {/* Loading message */}
            {submitting && (
              <p className="text-xs text-muted-foreground text-center">
                All agents are analyzing the article. This may take a minute...
              </p>
            )}
          </CardContent>
        </Card>

        {/* Result panel */}
        <Card
          className={
            !result && !error && !submitting
              ? "flex items-center justify-center"
              : ""
          }
        >
          <CardContent className="py-6">
            {!result && !error && !submitting && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Sparkles className="mb-4 size-10 text-muted-foreground/30" />
                <p className="text-sm text-muted-foreground">
                  Submit an article URL to see the impact analysis here.
                </p>
              </div>
            )}

            {submitting && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Loader2 className="mb-4 size-10 text-primary animate-spin" />
                <p className="text-sm font-medium">Generating Report...</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Crawling article, running agents, compiling PDF...
                </p>
              </div>
            )}

            {error && !result && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <XCircle className="mb-4 size-10 text-destructive/50" />
                <p className="text-sm font-medium text-destructive">
                  Analysis Failed
                </p>
                <p className="mt-2 text-xs text-muted-foreground max-w-sm">
                  {error}
                </p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Success header */}
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="size-5 text-green-500" />
                  <h3 className="text-sm font-semibold">
                    Report Generated Successfully
                  </h3>
                </div>

                <Separator />

                {/* Report details */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Report ID</p>
                    <p className="font-mono text-xs mt-0.5">
                      {result.report_id.slice(0, 8)}...
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Findings</p>
                    <p className="font-semibold mt-0.5">
                      {result.findings_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">
                      Email Status
                    </p>
                    <div className="mt-0.5">
                      {result.email_sent ? (
                        <Badge className="bg-green-500/15 text-green-600 text-[10px] border-0">
                          Sent
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px]">
                          Not Sent
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Agents Used</p>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {result.agents_used.map((a) => (
                        <Badge
                          key={a}
                          variant="outline"
                          className="text-[10px]"
                        >
                          {AGENT_LABELS[a] ?? a}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Message */}
                <p className="text-xs text-muted-foreground">
                  {result.message}
                </p>

                {/* PDF download */}
                {result.pdf_download_url && (
                  <Button
                    onClick={handleDownloadPdf}
                    variant="outline"
                    className="w-full"
                  >
                    <Download className="mr-2 size-4" />
                    Download PDF Report
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Report history */}
      {(history.length > 0 || historyLoading) && (
        <>
          <Separator className="my-6" />

          <div className="flex items-center gap-2 mb-4">
            <History className="size-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Report History</h3>
          </div>

          {historyLoading && history.length === 0 ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((report) => (
                <Card key={report.report_id}>
                  <CardContent className="py-3 flex items-center gap-4">
                    <FileText className="size-5 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium truncate">
                          {report.title || report.url}
                        </p>
                        <Badge variant="secondary" className="text-[10px] shrink-0">
                          {report.findings_count} findings
                        </Badge>
                        {report.email_sent ? (
                          <Badge className="bg-green-500/15 text-green-600 text-[10px] border-0 shrink-0">
                            Emailed
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-[10px] shrink-0">
                            Not Emailed
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-[11px] text-muted-foreground truncate">
                          {report.url}
                        </span>
                        <span className="text-[11px] text-muted-foreground shrink-0">
                          {formatDate(report.created_at)}
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs shrink-0"
                      onClick={() => handleDownloadHistoryPdf(report.report_id)}
                    >
                      <Download className="mr-1.5 size-3" />
                      PDF
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
