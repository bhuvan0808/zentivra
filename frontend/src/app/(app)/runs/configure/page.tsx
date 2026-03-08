"use client";

import { Fragment, useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleHelp,
  Loader2,
  Play,
  Search,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { StatusBadge } from "@/components/status-badge";
import { getSources, createRun } from "@/lib/api";
import type { Source, AgentType, CrawlSchedule } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS = ["Basics", "Sources", "Parameters"] as const;

const FREQUENCY_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

const AGENT_TYPE_LABELS: Record<AgentType, string> = {
  competitor: "Competitor",
  model_provider: "Model Provider",
  research: "Research",
  hf_benchmark: "HF Benchmark",
};

const WEEK_DAYS = [
  { key: "mon", label: "M" },
  { key: "tue", label: "T" },
  { key: "wed", label: "W" },
  { key: "thu", label: "T" },
  { key: "fri", label: "F" },
  { key: "sat", label: "S" },
  { key: "sun", label: "S" },
] as const;

interface ConfigParams {
  crawl_frequency: string;
  crawl_depth: number;
  keywords: string[];
}

export default function ConfigureRunPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Step 1
  const [runName, setRunName] = useState("");
  const [description, setDescription] = useState("");
  const [enableEmailAlert, setEnableEmailAlert] = useState(false);
  const [recipients, setRecipients] = useState<string[]>(() => {
    if (typeof window !== "undefined") {
      const storedEmail = localStorage.getItem("user_email");
      return storedEmail ? [storedEmail] : [];
    }
    return [];
  });
  const [recipientInput, setRecipientInput] = useState("");

  // Step 2
  const [sources, setSources] = useState<Source[]>([]);
  const [loadingSources, setLoadingSources] = useState(true);
  const [selectedSourceIds, setSelectedSourceIds] = useState<Set<string>>(
    new Set(),
  );
  const [sourceSearch, setSourceSearch] = useState("");
  const [agentFilter, setAgentFilter] = useState<string>("all");

  // Step 3
  const [params, setParams] = useState<ConfigParams>({
    crawl_frequency: "daily",
    crawl_depth: 0,
    keywords: [],
  });
  const [keywordInput, setKeywordInput] = useState("");
  const [codeMode, setCodeMode] = useState<"form" | "code">("form");
  const [codeLang, setCodeLang] = useState<"json" | "yaml">("json");
  const [codeText, setCodeText] = useState("");

  // Schedule state
  const [scheduleTime, setScheduleTime] = useState("09:00");
  const [scheduleDays, setScheduleDays] = useState<Set<string>>(
    new Set(["mon", "wed", "fri"]),
  );
  const [scheduleDates, setScheduleDates] = useState<Set<number>>(new Set([1]));

  function toggleDay(day: string) {
    setScheduleDays((prev) => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  }

  function toggleDate(date: number) {
    setScheduleDates((prev) => {
      const next = new Set(prev);
      if (next.has(date)) next.delete(date);
      else next.add(date);
      return next;
    });
  }

  function buildSchedule(): CrawlSchedule {
    const freq = params.crawl_frequency as CrawlSchedule["frequency"];
    const [h, m] = scheduleTime.split(":").map(Number);
    const now = new Date();
    now.setHours(h, m, 0, 0);
    const utcTime = `${String(now.getUTCHours()).padStart(2, "0")}:${String(now.getUTCMinutes()).padStart(2, "0")}`;

    let periods: string[] | null = null;
    if (freq === "weekly") {
      periods = Array.from(scheduleDays);
    } else if (freq === "monthly") {
      periods = Array.from(scheduleDates).sort((a, b) => a - b).map(String);
    }
    return { frequency: freq, time: utcTime, periods };
  }

  useEffect(() => {
    getSources().then((res) => {
      if (res.ok) {
        setSources(res.data);
        setSelectedSourceIds(new Set(res.data.map((s) => s.source_id)));
      }
      setLoadingSources(false);
    });
  }, []);

  function addRecipient() {
    const email = recipientInput.trim();
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (email && emailRegex.test(email) && !recipients.includes(email)) {
      setRecipients((prev) => [...prev, email]);
      setRecipientInput("");
    } else if (email && !emailRegex.test(email)) {
      toast.error("Invalid email format");
    }
  }

  function removeRecipient(email: string) {
    setRecipients((prev) => prev.filter((e) => e !== email));
  }

  const filteredSources = useMemo(() => {
    return sources.filter((s) => {
      const matchSearch =
        !sourceSearch ||
        s.display_name.toLowerCase().includes(sourceSearch.toLowerCase()) ||
        s.source_name.toLowerCase().includes(sourceSearch.toLowerCase());
      const matchAgent = agentFilter === "all" || s.agent_type === agentFilter;
      return matchSearch && matchAgent;
    });
  }, [sources, sourceSearch, agentFilter]);

  const allFilteredSelected = useMemo(() => {
    return (
      filteredSources.length > 0 &&
      filteredSources.every((s) => selectedSourceIds.has(s.source_id))
    );
  }, [filteredSources, selectedSourceIds]);

  function toggleSelectAll() {
    setSelectedSourceIds((prev) => {
      const next = new Set(prev);
      if (allFilteredSelected) {
        filteredSources.forEach((s) => next.delete(s.source_id));
      } else {
        filteredSources.forEach((s) => next.add(s.source_id));
      }
      return next;
    });
  }

  function toggleSource(id: string) {
    setSelectedSourceIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function addKeyword() {
    const kw = keywordInput.trim();
    if (kw && !params.keywords.includes(kw)) {
      setParams((p) => ({ ...p, keywords: [...p.keywords, kw] }));
    }
    setKeywordInput("");
  }

  function removeKeyword(kw: string) {
    setParams((p) => ({ ...p, keywords: p.keywords.filter((k) => k !== kw) }));
  }

  function serializeToCode(p: ConfigParams, lang?: "json" | "yaml"): string {
    const targetLang = lang ?? codeLang;
    if (targetLang === "json") {
      return JSON.stringify(
        {
          crawl_frequency: p.crawl_frequency,
          crawl_depth: p.crawl_depth,
          keywords: p.keywords,
        },
        null,
        2,
      );
    }
    let yaml = `crawl_frequency: ${p.crawl_frequency}\n`;
    yaml += `crawl_depth: ${p.crawl_depth}\n`;
    yaml += `keywords:\n`;
    if (p.keywords.length === 0) yaml += `  []\n`;
    else p.keywords.forEach((kw) => (yaml += `  - ${kw}\n`));
    return yaml;
  }

  function parseFromCode(text: string): ConfigParams | null {
    try {
      if (codeLang === "json") {
        const obj = JSON.parse(text);
        return {
          crawl_frequency: obj.crawl_frequency ?? "daily",
          crawl_depth: Number(obj.crawl_depth) || 0,
          keywords: Array.isArray(obj.keywords) ? obj.keywords.map(String) : [],
        };
      }
      const lines = text.split("\n").filter(Boolean);
      const result: ConfigParams = {
        crawl_frequency: "daily",
        crawl_depth: 0,
        keywords: [],
      };
      for (const line of lines) {
        if (line.startsWith("crawl_frequency:")) {
          result.crawl_frequency = line.split(":")[1].trim();
        } else if (line.startsWith("crawl_depth:")) {
          result.crawl_depth = Number(line.split(":")[1].trim()) || 0;
        } else if (line.trim().startsWith("- ")) {
          result.keywords.push(line.trim().slice(2));
        }
      }
      return result;
    } catch {
      return null;
    }
  }

  function handleCodeModeSwitch(mode: string) {
    if (mode === "code") {
      setCodeText(serializeToCode(params));
      setCodeMode("code");
    } else {
      if (codeText) {
        const parsed = parseFromCode(codeText);
        if (parsed) setParams(parsed);
      }
      setCodeMode("form");
    }
  }

  function handleCodeLangSwitch(lang: string) {
    const targetLang = lang as "json" | "yaml";
    if (codeText) {
      const parsed = parseFromCode(codeText);
      if (parsed) {
        setCodeLang(targetLang);
        setCodeText(serializeToCode(parsed, targetLang));
        return;
      }
    }
    setCodeLang(targetLang);
    setCodeText(serializeToCode(params, targetLang));
  }

  function canAdvance(): boolean {
    if (step === 0) return runName.trim().length > 0;
    if (step === 1) return selectedSourceIds.size > 0;
    return true;
  }

  async function handleSubmit(andTrigger: boolean) {
    let finalParams = params;
    if (codeMode === "code" && codeText) {
      const parsed = parseFromCode(codeText);
      if (parsed) finalParams = parsed;
      else {
        toast.error(
          "Invalid code. Please fix syntax errors before submitting.",
        );
        return;
      }
    }

    setSubmitting(true);
    const res = await createRun({
      run_name: runName.trim(),
      description: description.trim() || undefined,
      enable_email_alert: enableEmailAlert,
      email_recipients:
        enableEmailAlert && recipients.length > 0 ? recipients : undefined,
      sources: Array.from(selectedSourceIds),
      crawl_frequency: buildSchedule(),
      crawl_depth: finalParams.crawl_depth,
      keywords:
        finalParams.keywords.length > 0 ? finalParams.keywords : [],
      trigger_on_create: andTrigger,
    });

    if (!res.ok) {
      toast.error(res.error);
      setSubmitting(false);
      return;
    }

    if (andTrigger) {
      toast.success("Run created and triggered successfully.");
    } else {
      toast.success("Run created successfully.");
    }

    setSubmitting(false);
    router.push("/runs");
  }

  return (
    <div>
      <PageHeader
        title="Configure Run"
        description="Set up a new run configuration in 3 steps."
      />

      {/* Stepper */}
      <div className="mb-8 flex items-center justify-center">
        {STEPS.map((label, i) => (
          <Fragment key={label}>
            <div className="flex items-center gap-2">
              <button
                onClick={() => i < step && setStep(i)}
                disabled={i > step}
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-medium transition-colors",
                  i < step &&
                    "border-primary bg-primary text-primary-foreground cursor-pointer",
                  i === step && "border-primary bg-primary/10 text-primary",
                  i > step &&
                    "border-muted-foreground/30 text-muted-foreground",
                )}
              >
                {i < step ? <Check className="size-3.5" /> : i + 1}
              </button>
              <span
                className={cn(
                  "text-sm font-medium",
                  i === step ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-3 h-px w-10 shrink-0",
                  i < step ? "bg-primary" : "bg-border",
                )}
              />
            )}
          </Fragment>
        ))}
      </div>

      <motion.div
        key={step}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Step 1: Basics */}
        {step === 0 && (
          <Card>
            <CardContent className="space-y-6 py-6">
              <div className="space-y-2.5">
                <Label htmlFor="run-name">Run Name *</Label>
                <Input
                  id="run-name"
                  placeholder="e.g. Daily AI Scan"
                  maxLength={255}
                  value={runName}
                  onChange={(e) => setRunName(e.target.value)}
                />
              </div>
              <div className="space-y-3">
                <Label htmlFor="run-desc">Description</Label>
                <Textarea
                  id="run-desc"
                  placeholder="Optional description for this run configuration"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-4 rounded-md border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Enable Email Alerts</p>
                    <p className="text-xs text-muted-foreground">
                      Send digest results to configured recipients
                    </p>
                  </div>
                  <Switch
                    checked={enableEmailAlert}
                    onCheckedChange={setEnableEmailAlert}
                  />
                </div>

                {enableEmailAlert && (
                  <div className="space-y-3 pt-2 border-t">
                    <Label>Recipients</Label>
                    <div className="flex gap-2">
                      <Input
                        type="email"
                        placeholder="Add recipient email..."
                        value={recipientInput}
                        onChange={(e) => setRecipientInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addRecipient();
                          }
                        }}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addRecipient}
                      >
                        Add
                      </Button>
                    </div>
                    {recipients.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {recipients.map((email) => (
                          <span
                            key={email}
                            className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium"
                          >
                            {email}
                            <button
                              type="button"
                              onClick={() => removeRecipient(email)}
                              className="text-muted-foreground hover:text-foreground"
                            >
                              <X className="size-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Sources */}
        {step === 1 && (
          <Card>
            <CardContent className="space-y-4 py-6">
              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search sources..."
                    className="pl-9"
                    value={sourceSearch}
                    onChange={(e) => setSourceSearch(e.target.value)}
                  />
                </div>
                <Select value={agentFilter} onValueChange={setAgentFilter}>
                  <SelectTrigger className="w-full sm:w-48">
                    <SelectValue placeholder="All agent types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All agent types</SelectItem>
                    {(
                      Object.entries(AGENT_TYPE_LABELS) as [AgentType, string][]
                    ).map(([k, v]) => (
                      <SelectItem key={k} value={k}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {loadingSources ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  Loading sources...
                </p>
              ) : filteredSources.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No sources found.
                </p>
              ) : (
                <div className="rounded-md border">
                  <div className="flex items-center gap-3 border-b px-4 py-2.5 bg-muted/40">
                    <Checkbox
                      checked={allFilteredSelected}
                      onCheckedChange={toggleSelectAll}
                    />
                    <span className="text-xs font-medium text-muted-foreground">
                      {selectedSourceIds.size} of {sources.length} selected
                    </span>
                  </div>
                  <div className="max-h-72 overflow-y-auto">
                    {filteredSources.map((s) => (
                      <label
                        key={s.source_id}
                        className="flex cursor-pointer items-center gap-3 px-4 py-2.5 transition-colors hover:bg-muted/30"
                      >
                        <Checkbox
                          checked={selectedSourceIds.has(s.source_id)}
                          onCheckedChange={() => toggleSource(s.source_id)}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {s.display_name}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {s.url}
                          </p>
                        </div>
                        <StatusBadge variant="neutral">
                          {AGENT_TYPE_LABELS[s.agent_type]}
                        </StatusBadge>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 3: Parameters */}
        {step === 2 && (
          <Card>
            <CardContent className="space-y-8 py-6">
              <Tabs value={codeMode} onValueChange={handleCodeModeSwitch}>
                <TabsList>
                  <TabsTrigger value="form">Form</TabsTrigger>
                  <TabsTrigger value="code">Code</TabsTrigger>
                </TabsList>

                <TabsContent value="form" className="space-y-6 pt-4">
                  <div className="space-y-2.5">
                    <Label>Crawl Frequency</Label>
                    <Select
                      value={params.crawl_frequency}
                      onValueChange={(v) =>
                        setParams((p) => ({ ...p, crawl_frequency: v }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FREQUENCY_OPTIONS.map((o) => (
                          <SelectItem key={o.value} value={o.value}>
                            {o.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Schedule Time */}
                  <div className="space-y-2.5">
                    <Label htmlFor="schedule-time">Run Time</Label>
                    <Input
                      id="schedule-time"
                      type="time"
                      value={scheduleTime}
                      onChange={(e) => setScheduleTime(e.target.value)}
                      className="w-40"
                    />
                    <p className="text-xs text-muted-foreground">
                      What time should the run execute?
                    </p>
                  </div>

                  {/* Day-of-week (weekly) */}
                  {params.crawl_frequency === "weekly" && (
                    <div className="space-y-2.5">
                      <Label>Days of the Week</Label>
                      <div className="flex gap-1.5">
                        {WEEK_DAYS.map((d) => (
                          <button
                            key={d.key}
                            type="button"
                            onClick={() => toggleDay(d.key)}
                            className={cn(
                              "flex size-9 cursor-pointer items-center justify-center rounded-md border text-sm font-medium transition-colors",
                              scheduleDays.has(d.key)
                                ? "border-primary bg-primary text-primary-foreground"
                                : "border-input bg-background text-muted-foreground hover:bg-muted",
                            )}
                          >
                            {d.label}
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Selected:{" "}
                        {Array.from(scheduleDays).join(", ") || "none"}
                      </p>
                    </div>
                  )}

                  {/* Date-of-month (monthly) */}
                  {params.crawl_frequency === "monthly" && (
                    <div className="space-y-2.5">
                      <Label>Dates of the Month</Label>
                      <div className="inline-grid grid-cols-7 gap-1 rounded-lg border p-2">
                        {Array.from({ length: 31 }, (_, i) => i + 1).map(
                          (d) => (
                            <button
                              key={d}
                              type="button"
                              onClick={() => toggleDate(d)}
                              className={cn(
                                "flex size-9 cursor-pointer items-center justify-center rounded-md text-xs font-medium transition-colors",
                                scheduleDates.has(d)
                                  ? "bg-primary text-primary-foreground"
                                  : "text-muted-foreground hover:bg-muted",
                              )}
                            >
                              {d}
                            </button>
                          ),
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Selected:{" "}
                        {Array.from(scheduleDates)
                          .sort((a, b) => a - b)
                          .join(", ") || "none"}
                      </p>
                    </div>
                  )}

                  <div className="space-y-3">
                    <div className="flex items-center gap-1.5">
                      <Label htmlFor="crawl-depth">Crawl Depth</Label>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <CircleHelp className="size-3.5 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent
                          side="right"
                          className="max-w-xs text-xs leading-relaxed"
                        >
                          <p className="font-semibold mb-1">
                            Crawl Depth Levels
                          </p>
                          <p>
                            <strong>Level 0</strong> — Only the source URL
                            itself
                          </p>
                          <p>
                            <strong>Level 1</strong> — Source URL + URLs in its
                            RSS feed
                          </p>
                          <p>
                            <strong>Level 2</strong> — Level 1 + RSS URLs from
                            Level 1 pages
                          </p>
                          <p>
                            <strong>Level 3+</strong> — Continues recursively
                            per level
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                    <Input
                      id="crawl-depth"
                      type="number"
                      min={0}
                      max={5}
                      value={params.crawl_depth}
                      onChange={(e) =>
                        setParams((p) => ({
                          ...p,
                          crawl_depth: Number(e.target.value),
                        }))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      0 = source URL only, higher = follow more links (0–5)
                    </p>
                  </div>

                  <div className="space-y-3">
                    <Label>Keywords</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add a keyword..."
                        maxLength={50}
                        value={keywordInput}
                        onChange={(e) => setKeywordInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addKeyword();
                          }
                        }}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={addKeyword}
                      >
                        Add
                      </Button>
                    </div>
                    {params.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {params.keywords.map((kw) => (
                          <span
                            key={kw}
                            className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium"
                          >
                            {kw}
                            <button
                              onClick={() => removeKeyword(kw)}
                              className="text-muted-foreground hover:text-foreground"
                            >
                              <X className="size-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="code" className="space-y-3 pt-4">
                  <div className="flex gap-2">
                    <Button
                      variant={codeLang === "json" ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleCodeLangSwitch("json")}
                    >
                      JSON
                    </Button>
                    <Button
                      variant={codeLang === "yaml" ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleCodeLangSwitch("yaml")}
                    >
                      YAML
                    </Button>
                  </div>
                  <Textarea
                    className="font-mono text-sm min-h-48"
                    value={codeText}
                    onChange={(e) => setCodeText(e.target.value)}
                    spellCheck={false}
                  />
                  <p className="text-xs text-muted-foreground">
                    Edit parameters as {codeLang.toUpperCase()}. Values are
                    synced when switching back to Form.
                  </p>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </motion.div>

      {/* Navigation buttons */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="outline"
          onClick={() =>
            step === 0 ? router.push("/runs") : setStep(step - 1)
          }
          disabled={submitting}
        >
          <ArrowLeft className="mr-1.5 size-4" />
          {step === 0 ? "Cancel" : "Back"}
        </Button>

        <div className="flex gap-2">
          {step < 2 ? (
            <Button onClick={() => setStep(step + 1)} disabled={!canAdvance()}>
              Next
              <ArrowRight className="ml-1.5 size-4" />
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => handleSubmit(false)}
                disabled={submitting}
              >
                {submitting ? (
                  <Loader2 className="mr-1.5 size-4 animate-spin" />
                ) : (
                  <Check className="mr-1.5 size-4" />
                )}
                Create Run
              </Button>
              <Button onClick={() => handleSubmit(true)} disabled={submitting}>
                {submitting ? (
                  <Loader2 className="mr-1.5 size-4 animate-spin" />
                ) : (
                  <Play className="mr-1.5 size-4" />
                )}
                Create & Trigger
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
