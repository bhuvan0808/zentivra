"use client";

import { useRouter } from "next/navigation";
import { FileText, Download, Calendar, Eye, Inbox } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { motion } from "framer-motion";
import { fmtDate } from "@/lib/formatDate";
import { useDigests } from "@/hooks/use-digests";

function statusVariant(status: string) {
  switch (status) {
    case "completed":
      return "success" as const;
    case "failed":
      return "danger" as const;
    case "generating":
      return "warning" as const;
    default:
      return "neutral" as const;
  }
}

export default function DigestsPage() {
  const router = useRouter();
  const { digests, loading, handleDownloadPdf } = useDigests();

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Digests"
          description="Archive of daily executive digests."
        />
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="py-3">
              <CardContent className="p-2">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-3 w-16" />
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
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {digests.map((digest, i) => (
            <motion.div
              key={digest.digest_id}
              initial={{ opacity: 0, filter: "blur(4px)" }}
              animate={{ opacity: 1, filter: "blur(0px)" }}
              transition={{ duration: 0.35, delay: i * 0.05, ease: "easeOut" }}
            >
              <Card className="transition-shadow hover:shadow-md py-3">
                <CardContent className="p-2 space-y-2">
                  <div className="flex items-center gap-2">
                    <Calendar className="size-3.5 text-muted-foreground shrink-0" />
                    <p className="text-sm font-semibold leading-tight truncate">
                      {digest.digest_name ?? fmtDate(digest.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground font-mono">
                      {digest.digest_id.slice(0, 8)}
                    </span>
                    <StatusBadge variant={statusVariant(digest.status)}>
                      <FileText className="mr-0.5 size-2.5" />
                      {digest.status}
                    </StatusBadge>
                  </div>
                  <div className="flex items-center gap-1.5 pt-1">
                    {digest.html_path && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs px-2 flex-1"
                        onClick={() =>
                          router.push(`/digests/${digest.digest_id}`)
                        }
                      >
                        <Eye className="mr-1 size-3" />
                        Preview
                      </Button>
                    )}
                    {digest.pdf_path && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs px-2 flex-1"
                        onClick={() => handleDownloadPdf(digest.digest_id)}
                      >
                        <Download className="mr-1 size-3" />
                        PDF
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
