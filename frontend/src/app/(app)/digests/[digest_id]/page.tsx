"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { getDigest, getDigestHtmlUrl, getDigestPdfUrl } from "@/lib/api";
import type { Digest } from "@/lib/types";
import { fmtDate } from "@/lib/formatDate";

export default function DigestPreviewPage() {
  const { digest_id } = useParams<{ digest_id: string }>();
  const router = useRouter();
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [digest, setDigest] = useState<Digest | null>(null);
  const [htmlBlobUrl, setHtmlBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const res = await getDigest(digest_id);
      if (!res.ok) {
        setError(res.error);
        setLoading(false);
        return;
      }
      setDigest(res.data);

      if (!res.data.html_path) {
        setError("HTML not available for this digest.");
        setLoading(false);
        return;
      }

      try {
        const token = localStorage.getItem("auth_token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const htmlRes = await fetch(getDigestHtmlUrl(digest_id), { headers });
        if (!htmlRes.ok) {
          setError("Failed to load digest HTML.");
          setLoading(false);
          return;
        }
        const html = await htmlRes.text();
        const blob = new Blob([html], { type: "text/html" });
        setHtmlBlobUrl(URL.createObjectURL(blob));
      } catch {
        setError("Unable to reach the server.");
      }
      setLoading(false);
    }

    void load();

    return () => {
      if (htmlBlobUrl) URL.revokeObjectURL(htmlBlobUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [digest_id]);

  async function handleDownloadPdf() {
    if (!digest) return;
    try {
      toast.info("Preparing PDF download...");
      const token = localStorage.getItem("auth_token");
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(getDigestPdfUrl(digest.digest_id), { headers });
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

  const title = digest
    ? (digest.digest_name ?? fmtDate(digest.created_at))
    : "";

  return (
    <div className="pb-6">
      <PageHeader
        title={`Digest — ${title}`}
        description={digest ? `ID: ${digest.digest_id.slice(0, 8)}` : undefined}
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push("/digests")}
        >
          <ArrowLeft className="mr-1.5 size-3.5" />
          Back
        </Button>
        {digest?.pdf_path && (
          <Button variant="outline" size="sm" onClick={handleDownloadPdf}>
            <Download className="mr-1.5 size-3.5" />
            Download PDF
          </Button>
        )}
      </PageHeader>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <div className="flex items-center justify-center py-20">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {htmlBlobUrl && (
        <div className="w-full bg-white rounded-lg border pl-4">
          <iframe
            ref={iframeRef}
            src={htmlBlobUrl}
            className="w-full"
            style={{ minHeight: "calc(100vh - 11rem)" }}
            title="Digest Preview"
            sandbox="allow-same-origin"
          />
        </div>
      )}
    </div>
  );
}
