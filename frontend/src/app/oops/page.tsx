"use client";

import { useMemo, useState } from "react";
import { Loader2, Mail, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { runDisruptiveArticle } from "@/lib/api";
import type {
  AgentType,
  DisruptiveArticleResponse,
} from "@/lib/types";

const AGENTS: { key: AgentType; label: string }[] = [
  { key: "competitor", label: "Competitor Watcher" },
  { key: "model_provider", label: "Model Provider Watcher" },
  { key: "research", label: "Research Scout" },
  { key: "hf_benchmark", label: "HF Benchmark Tracker" },
];

export default function OopsPage() {
  const [url, setUrl] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<DisruptiveArticleResponse | null>(null);
  const [agentSelection, setAgentSelection] = useState<Record<AgentType, boolean>>({
    competitor: true,
    model_provider: true,
    research: true,
    hf_benchmark: true,
  });

  const selectedAgents = useMemo(
    () =>
      (Object.entries(agentSelection) as [AgentType, boolean][])
        .filter(([, enabled]) => enabled)
        .map(([agent]) => agent),
    [agentSelection]
  );

  async function handleSubmit() {
    if (!url.trim()) {
      toast.error("Please enter an article URL.");
      return;
    }
    if (!recipientEmail.trim()) {
      toast.error("Please enter a recipient email.");
      return;
    }
    if (selectedAgents.length === 0) {
      toast.error("Select at least one agent.");
      return;
    }

    setSubmitting(true);
    const res = await runDisruptiveArticle({
      url: url.trim(),
      recipient_email: recipientEmail.trim(),
      title: title.trim() || undefined,
      agent_types: selectedAgents,
    });
    setSubmitting(false);

    if (!res.ok) {
      toast.error(res.error);
      return;
    }

    setResult(res.data);
    toast.success(res.data.message);
  }

  return (
    <div>
      <PageHeader
        title="Oops"
        description="Drop a disruptive article link, generate a PDF report, and email it."
      />

      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Disruptive Article Intake</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="article-url">Article URL</Label>
              <Input
                id="article-url"
                placeholder="https://example.com/disruptive-ai-news"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="recipient-email">Recipient Email</Label>
              <Input
                id="recipient-email"
                placeholder="team@company.com"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="report-title">Optional Report Title</Label>
              <Input
                id="report-title"
                placeholder="AI Infrastructure Shockwave - March 2026"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <Separator />

            <div className="space-y-3">
              <p className="text-sm font-medium">Agents to run</p>
              {AGENTS.map((agent) => (
                <div
                  key={agent.key}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-sm">{agent.label}</span>
                  <Switch
                    checked={agentSelection[agent.key]}
                    onCheckedChange={(checked) =>
                      setAgentSelection((prev) => ({
                        ...prev,
                        [agent.key]: checked,
                      }))
                    }
                  />
                </div>
              ))}
            </div>

            <Button onClick={handleSubmit} disabled={submitting} className="w-full">
              {submitting ? (
                <>
                  <Loader2 className="mr-1.5 size-4 animate-spin" />
                  Generating Report...
                </>
              ) : (
                <>
                  <Sparkles className="mr-1.5 size-4" />
                  Generate PDF + Send Email
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Last Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!result ? (
              <p className="text-sm text-muted-foreground">
                No disruptive article report run yet.
              </p>
            ) : (
              <>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Report ID</p>
                  <p className="font-mono text-sm">{result.report_id}</p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge variant={result.email_sent ? "success" : "warning"} dot>
                    {result.email_sent ? "Email sent" : "Email not sent"}
                  </StatusBadge>
                  <StatusBadge variant="neutral">
                    {result.findings_count} findings
                  </StatusBadge>
                </div>

                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Agents Used</p>
                  <div className="flex flex-wrap gap-1">
                    {result.agents_used.map((agent) => (
                      <StatusBadge key={agent} variant="neutral">
                        {agent.replace("_", " ")}
                      </StatusBadge>
                    ))}
                  </div>
                </div>

                <p className="text-sm text-muted-foreground">{result.message}</p>

                {result.pdf_download_url && (
                  <Button asChild variant="outline" className="w-full">
                    <a href={result.pdf_download_url} target="_blank" rel="noreferrer">
                      Download Generated PDF
                    </a>
                  </Button>
                )}

                <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                  <Mail className="mr-1 inline size-3.5" />
                  Make sure SMTP is configured in backend `.env` to enable email send.
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
