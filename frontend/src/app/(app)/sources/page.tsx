"use client";

import { Plus, Pencil, Trash2, ExternalLink } from "lucide-react";
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
import { AnimatedRow } from "@/components/animated-row";
import type { AgentType } from "@/lib/types";
import { useSources } from "@/hooks/use-sources";

const AGENT_TYPE_OPTIONS: { value: AgentType; label: string }[] = [
  { value: "competitor", label: "Competitor" },
  { value: "model_provider", label: "Model Provider" },
  { value: "research", label: "Research" },
  { value: "hf_benchmark", label: "HF Benchmark" },
];

export default function SourcesPage() {
  const {
    sources,
    loading,
    filterType,
    setFilterType,
    dialogOpen,
    setDialogOpen,
    editingSource,
    form,
    setForm,
    saving,
    deleteTarget,
    setDeleteTarget,
    deleting,
    openCreate,
    openEdit,
    handleSave,
    handleToggleEnabled,
    handleDelete,
    fieldError,
  } = useSources();

  if (loading) {
    return (
      <div>
        <PageHeader
          title="Sources"
          description="Manage crawl sources for each agent."
        />
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
                <TableHead className="w-12 text-center">#</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Agent Type</TableHead>
                <TableHead className="hidden md:table-cell">URL</TableHead>
                <TableHead>Enabled</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sources.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No sources configured. Click &ldquo;Add New Source&rdquo; to
                    get started.
                  </TableCell>
                </TableRow>
              ) : (
                sources.map((source, i) => (
                  <AnimatedRow key={source.source_id} index={i}>
                    <TableCell className="text-center text-xs text-muted-foreground font-mono">
                      {i + 1}
                    </TableCell>
                    <TableCell className="font-medium">
                      {source.display_name}
                    </TableCell>
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
                        checked={source.is_enabled}
                        onCheckedChange={() => handleToggleEnabled(source)}
                      />
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
                  </AnimatedRow>
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

          <div className="grid gap-6 py-2 sm:grid-cols-2">
            <div className="space-y-2.5">
              <Label htmlFor="display_name">Source Name</Label>
              <Input
                id="display_name"
                value={form.display_name}
                onChange={(e) =>
                  setForm({ ...form, display_name: e.target.value })
                }
                placeholder="e.g. OpenAI Blog"
                autoFocus
              />
              {fieldError("display_name") && (
                <p className="field-error">{fieldError("display_name")}</p>
              )}
            </div>

            <div className="space-y-2.5">
              <Label htmlFor="agent_type">Agent Type</Label>
              <Select
                value={form.agent_type}
                onValueChange={(v) =>
                  setForm({ ...form, agent_type: v as AgentType })
                }
              >
                <SelectTrigger id="agent_type" className="w-full">
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

            <div className="space-y-2.5 sm:col-span-2">
              <Label htmlFor="url">URL</Label>
              <Input
                id="url"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                placeholder="https://example.com/blog"
              />
              {fieldError("url") && (
                <p className="field-error">{fieldError("url")}</p>
              )}
            </div>

            <div className="flex items-center gap-2 pt-1 sm:col-span-2">
              <Switch
                id="is_enabled"
                checked={form.is_enabled}
                onCheckedChange={(checked) =>
                  setForm({ ...form, is_enabled: checked })
                }
              />
              <Label htmlFor="is_enabled">Enabled</Label>
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
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
              This will permanently remove &ldquo;{deleteTarget?.display_name}
              &rdquo;. This action cannot be undone.
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
