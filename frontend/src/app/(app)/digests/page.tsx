"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Download,
  Calendar,
  Eye,
  Inbox,
  Mail,
  X,
  Send,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { motion } from "framer-motion";
import { fmtDate } from "@/lib/formatDate";
import { useDigests } from "@/hooks/use-digests";
import { sendDigestEmail } from "@/lib/api";

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

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [recipientInput, setRecipientInput] = useState("");
  const [recipients, setRecipients] = useState<string[]>([]);
  const [sending, setSending] = useState(false);

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleAddRecipient() {
    const email = recipientInput.trim().toLowerCase();
    if (!email) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.warning("Invalid email address");
      return;
    }
    if (recipients.includes(email)) {
      toast.warning("Already added");
      return;
    }
    setRecipients((prev) => [...prev, email]);
    setRecipientInput("");
  }

  function handleRemoveRecipient(email: string) {
    setRecipients((prev) => prev.filter((r) => r !== email));
  }

  function openDialog() {
    setDialogOpen(true);
  }

  async function handleSend() {
    if (selectedIds.size === 0) {
      toast.warning("Select at least one digest");
      return;
    }
    if (recipients.length === 0) {
      toast.warning("Add at least one recipient");
      return;
    }

    setSending(true);
    const res = await sendDigestEmail([...selectedIds], recipients);
    setSending(false);

    if (res.ok) {
      toast.success(`Sent ${res.data.sent} digest(s) successfully`);
      if (res.data.failed > 0) {
        toast.warning(`${res.data.failed} digest(s) failed to send`);
      }
      setDialogOpen(false);
      setSelectedIds(new Set());
    } else {
      toast.error(res.error);
    }
  }

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

  const completedDigests = digests.filter((d) => d.status === "completed");

  return (
    <div>
      <PageHeader
        title="Digests"
        description="Archive of daily executive digests."
      >
        {completedDigests.length > 0 && (
          <Button onClick={openDialog} size="sm">
            <Mail className="mr-1.5 size-4" />
            Send Email
          </Button>
        )}
      </PageHeader>

      {/* Email Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Send Digests via Email</DialogTitle>
            <DialogDescription>
              Select digests and add recipients to send PDFs via email.
            </DialogDescription>
          </DialogHeader>

          {/* Digest selection */}
          <div className="space-y-2 max-h-48 overflow-y-auto">
            <p className="text-sm font-medium">Select Digests</p>
            {completedDigests.map((digest) => (
              <label
                key={digest.digest_id}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-muted cursor-pointer"
              >
                <Checkbox
                  checked={selectedIds.has(digest.digest_id)}
                  onCheckedChange={() => toggleSelect(digest.digest_id)}
                />
                <FileText className="size-3.5 text-muted-foreground shrink-0" />
                <span className="text-sm truncate">
                  {digest.digest_name ?? fmtDate(digest.created_at)}
                </span>
                {digest.has_pdf && (
                  <span className="ml-auto text-[10px] text-muted-foreground">
                    PDF
                  </span>
                )}
              </label>
            ))}
          </div>

          {/* Recipients */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Recipients</p>
            <div className="flex gap-2">
              <Input
                type="email"
                placeholder="email@example.com"
                value={recipientInput}
                onChange={(e) => setRecipientInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddRecipient();
                  }
                }}
                className="flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddRecipient}
              >
                Add
              </Button>
            </div>
            {recipients.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {recipients.map((email) => (
                  <span
                    key={email}
                    className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs"
                  >
                    {email}
                    <button
                      onClick={() => handleRemoveRecipient(email)}
                      className="hover:text-destructive"
                    >
                      <X className="size-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              onClick={handleSend}
              disabled={sending || selectedIds.size === 0 || recipients.length === 0}
            >
              {sending ? (
                <Loader2 className="mr-1.5 size-4 animate-spin" />
              ) : (
                <Send className="mr-1.5 size-4" />
              )}
              {sending ? "Sending..." : `Send ${selectedIds.size} Digest(s)`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
