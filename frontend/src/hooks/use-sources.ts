import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  getSources,
  createSource,
  updateSource,
  deleteSource,
} from "@/lib/api";
import { validateSourceForm, toSlug, type ValidationError } from "@/lib/validation";
import type { Source, SourceCreate, AgentType } from "@/lib/types";

export const EMPTY_FORM = {
  display_name: "",
  agent_type: "competitor" as AgentType,
  url: "",
  is_enabled: true,
};

export interface UseSourcesReturn {
  sources: Source[];
  loading: boolean;
  filterType: string;
  setFilterType: (v: string) => void;
  dialogOpen: boolean;
  setDialogOpen: (v: boolean) => void;
  editingSource: Source | null;
  form: typeof EMPTY_FORM;
  setForm: React.Dispatch<React.SetStateAction<typeof EMPTY_FORM>>;
  saving: boolean;
  deleteTarget: Source | null;
  setDeleteTarget: (v: Source | null) => void;
  deleting: boolean;
  openCreate: () => void;
  openEdit: (source: Source) => void;
  handleSave: () => Promise<void>;
  handleToggleEnabled: (source: Source) => Promise<void>;
  handleDelete: () => Promise<void>;
  fieldError: (field: string) => string | undefined;
}

/**
 * Custom hook for the Sources page.
 * Manages fetching, creating, updating, and deleting sources.
 *
 * Interacts with:
 * - GET /api/sources
 * - POST /api/sources
 * - PUT /api/sources/{id}
 * - DELETE /api/sources/{id}
 */
export function useSources(): UseSourcesReturn {
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
    const params =
      filterType !== "all"
        ? { agent_type: filterType as AgentType }
        : undefined;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openCreate() {
    setEditingSource(null);
    setForm(EMPTY_FORM);
    setErrors([]);
    setDialogOpen(true);
  }

  function openEdit(source: Source) {
    setEditingSource(source);
    setForm({
      display_name: source.display_name,
      agent_type: source.agent_type,
      url: source.url,
      is_enabled: source.is_enabled,
    });
    setErrors([]);
    setDialogOpen(true);
  }

  async function handleSave() {
    const validationErrors = validateSourceForm({
      display_name: form.display_name,
      url: form.url,
    });

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSaving(true);
    const slug = toSlug(form.display_name);

    if (editingSource) {
      const res = await updateSource(editingSource.source_id, {
        source_name: slug,
        display_name: form.display_name,
        agent_type: form.agent_type,
        url: form.url,
        is_enabled: form.is_enabled,
      });
      setSaving(false);
      if (res.ok) {
        toast.success("Source updated.");
        setDialogOpen(false);
        fetchSources();
      } else {
        toast.error(res.error);
      }
    } else {
      const payload: SourceCreate = {
        source_name: slug,
        display_name: form.display_name,
        agent_type: form.agent_type,
        url: form.url,
      };
      const res = await createSource(payload);
      setSaving(false);
      if (res.ok) {
        toast.success("Source created successfully.");
        setDialogOpen(false);
        fetchSources();
      } else {
        toast.error(res.error);
      }
    }
  }

  async function handleToggleEnabled(source: Source) {
    const res = await updateSource(source.source_id, {
      is_enabled: !source.is_enabled,
    });
    if (res.ok) {
      toast.success(`Source ${res.data.is_enabled ? "enabled" : "disabled"}.`);
      fetchSources();
    } else {
      toast.error(res.error);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    const res = await deleteSource(deleteTarget.source_id);
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

  return {
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
  };
}