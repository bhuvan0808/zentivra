"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Pencil, Trash2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
} from "@/lib/api";
import { validateSourceForm, type ValidationError } from "@/lib/validation";
import type { Source, SourceCreate, AgentType } from "@/lib/types";

const AGENT_TYPE_OPTIONS: { value: AgentType; label: string }[] = [
  { value: "competitor", label: "Competitor" },
  { value: "model_provider", label: "Model Provider" },
  { value: "research", label: "Research" },
  { value: "hf_benchmark", label: "HF Benchmark" },
];

const EMPTY_FORM = {
  name: "",
  agent_type: "competitor" as AgentType,
  url: "",
  feed_url: "",
  keywords: "",
  rate_limit_rpm: 10,
  crawl_depth: 1,
  enabled: true,
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("all");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<Source | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchSources = useCallback(async () => {
    const params = filterType !== "all" ? { agent_type: filterType as AgentType } : undefined;
    const res = await getSources(params);
    if (res.ok) {
      setSources(res.data);
    } else {
      toast.error(res.error);
    }
    setLoading(false);
  }, [filterType]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  function openCreate() {
    setEditingSource(null);
    setForm(EMPTY_FORM);
    setErrors([]);
    setDialogOpen(true);
  }

  function openEdit(source: Source) {
    setEditingSource(source);
    setForm({
      name: source.name,
      agent_type: source.agent_type,
      url: source.url,
      feed_url: source.feed_url ?? "",
      keywords: source.keywords.join(", "),
      rate_limit_rpm: source.rate_limit_rpm,
      crawl_depth: source.crawl_depth,
      enabled: source.enabled,
    });
    setErrors([]);
    setDialogOpen(true);
  }

  async function handleSave() {
    const keywordsArr = form.keywords
      .split(",")
      .map((k) => k.trim())
      .filter(Boolean);

    const validationErrors = validateSourceForm({
      name: form.name,
      url: form.url,
      feed_url: form.feed_url,
      rate_limit_rpm: form.rate_limit_rpm,
      crawl_depth: form.crawl_depth,
      keywords: keywordsArr,
    });

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSaving(true);
    const payload: SourceCreate = {
      name: form.name,
      agent_type: form.agent_type,
      url: form.url,
      feed_url: form.feed_url || null,
      keywords: keywordsArr,
      rate_limit_rpm: form.rate_limit_rpm,
      crawl_depth: form.crawl_depth,
      enabled: form.enabled,
    };

    const res = editingSource
      ? await updateSource(editingSource.id, payload)
      : await createSource(payload);

    setSaving(false);

    if (res.ok) {
      toast.success(editingSource ? "Source updated." : "Source created successfully.");
      setDialogOpen(false);
      fetchSources();
    } else {
      toast.error(res.error);
    }
  }

  async function handleToggleEnabled(source: Source) {
    const res = await updateSource(source.id, { enabled: !source.enabled });
    if (res.ok) {
      toast.success(`Source ${res.data.enabled ? "enabled" : "disabled"}.`);
      fetchSources();
    } else {
      toast.error(res.error);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    const res = await deleteSource(deleteTarget.id);
    setDeleting(false);
    if (res.ok) {
      toast.success("Source deleted.");
      setDeleteTarget(null);
      fetchSources();
    } else {
      toast.error(res.error);
    }
  }

  function fieldError(field: string): string | undefined {
    return errors.find((e) => e.field === field)?.message;
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Sources" />
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Sources"
        description="Manage crawl sources for each agent."
      >
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end md:w-auto">
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-full sm:w-44 md:w-48">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {AGENT_TYPE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={openCreate} className="w-full sm:w-auto">
            <Plus className="mr-1.5 size-4" />
            Add New Source
          </Button>
        </div>
      </PageHeader>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Agent Type</TableHead>
                <TableHead className="hidden md:table-cell">URL</TableHead>
                <TableHead>Enabled</TableHead>
                <TableHead className="hidden sm:table-cell">Rate Limit</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No sources configured. Click &ldquo;Add Source&rdquo; to get started.
                  </TableCell>
                </TableRow>
              ) : (
                sources.map((source) => (
                  <TableRow key={source.id}>
                    <TableCell className="font-medium">{source.name}</TableCell>
                    <TableCell>
                      <StatusBadge variant="neutral">
                        {source.agent_type.replace("_", " ")}
                      </StatusBadge>
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        {new URL(source.url).hostname}
                        <ExternalLink className="size-3" />
                      </a>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={source.enabled}
                        onCheckedChange={() => handleToggleEnabled(source)}
                      />
                    </TableCell>
                    <TableCell className="hidden sm:table-cell font-mono text-xs">
                      {source.rate_limit_rpm} rpm
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openEdit(source)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteTarget(source)}
                        >
                          <Trash2 className="size-4 text-danger" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create / Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader className="space-y-2 pr-8">
            <DialogTitle>
              {editingSource ? "Edit Source" : "Add New Source"}
            </DialogTitle>
            <DialogDescription>
              {editingSource
                ? "Update the source configuration below."
                : "Configure a new crawl source for monitoring."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 py-2 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) =>
                  setForm({ ...form, name: e.target.value })
                }
                placeholder="e.g. OpenAI Blog"
              />
              {fieldError("name") && (
                <p className="field-error">{fieldError("name")}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="agent_type">Agent Type</Label>
              <Select
                value={form.agent_type}
                onValueChange={(v) =>
                  setForm({ ...form, agent_type: v as AgentType })
                }
              >
                <SelectTrigger id="agent_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="url">URL</Label>
              <Input
                id="url"
                value={form.url}
                onChange={(e) =>
                  setForm({ ...form, url: e.target.value })
                }
                placeholder="https://example.com/blog"
              />
              {fieldError("url") && (
                <p className="field-error">{fieldError("url")}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="feed_url">Feed URL (optional)</Label>
              <Input
                id="feed_url"
                value={form.feed_url}
                onChange={(e) =>
                  setForm({ ...form, feed_url: e.target.value })
                }
                placeholder="https://example.com/rss.xml"
              />
              {fieldError("feed_url") && (
                <p className="field-error">{fieldError("feed_url")}</p>
              )}
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="keywords">Keywords (comma-separated)</Label>
              <Input
                id="keywords"
                value={form.keywords}
                onChange={(e) =>
                  setForm({ ...form, keywords: e.target.value })
                }
                placeholder="gpt, api, release"
              />
              {fieldError("keywords") && (
                <p className="field-error">{fieldError("keywords")}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="rate_limit">Rate Limit (rpm)</Label>
              <Input
                id="rate_limit"
                type="number"
                min={1}
                max={60}
                value={form.rate_limit_rpm}
                onChange={(e) =>
                  setForm({
                    ...form,
                    rate_limit_rpm: Number(e.target.value),
                  })
                }
              />
              {fieldError("rate_limit_rpm") && (
                <p className="field-error">
                  {fieldError("rate_limit_rpm")}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="crawl_depth">Crawl Depth</Label>
              <Input
                id="crawl_depth"
                type="number"
                min={1}
                max={5}
                value={form.crawl_depth}
                onChange={(e) =>
                  setForm({
                    ...form,
                    crawl_depth: Number(e.target.value),
                  })
                }
              />
              {fieldError("crawl_depth") && (
                <p className="field-error">
                  {fieldError("crawl_depth")}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 pt-1 sm:col-span-2">
              <Switch
                id="enabled"
                checked={form.enabled}
                onCheckedChange={(checked) =>
                  setForm({ ...form, enabled: checked })
                }
              />
              <Label htmlFor="enabled">Enabled</Label>
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving
                ? "Saving..."
                : editingSource
                  ? "Update Source"
                  : "Create Source"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Source</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove &ldquo;{deleteTarget?.name}&rdquo;.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-danger text-danger-foreground hover:bg-danger/90"
            >
              {deleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
