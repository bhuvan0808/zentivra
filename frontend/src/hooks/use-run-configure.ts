import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { getSources, createRun } from "@/lib/api";
import type { Source, CrawlSchedule } from "@/lib/types";

export interface ConfigParams {
  crawl_frequency: string;
  crawl_depth: number;
  keywords: string[];
}

export const WEEK_DAYS = [
  { key: "mon", label: "M" },
  { key: "tue", label: "T" },
  { key: "wed", label: "W" },
  { key: "thu", label: "T" },
  { key: "fri", label: "F" },
  { key: "sat", label: "S" },
  { key: "sun", label: "S" },
] as const;

export interface UseRunConfigureReturn {
  step: number;
  setStep: (v: number | ((prev: number) => number)) => void;
  submitting: boolean;
  runName: string;
  setRunName: (v: string) => void;
  description: string;
  setDescription: (v: string) => void;
  enableEmailAlert: boolean;
  setEnableEmailAlert: (v: boolean) => void;
  recipients: string[];
  recipientInput: string;
  setRecipientInput: (v: string) => void;
  sources: Source[];
  loadingSources: boolean;
  selectedSourceIds: Set<string>;
  sourceSearch: string;
  setSourceSearch: (v: string) => void;
  agentFilter: string;
  setAgentFilter: (v: string) => void;
  params: ConfigParams;
  setParams: React.Dispatch<React.SetStateAction<ConfigParams>>;
  keywordInput: string;
  setKeywordInput: (v: string) => void;
  codeMode: "form" | "code";
  codeLang: "json" | "yaml";
  codeText: string;
  setCodeText: (v: string) => void;
  scheduleTime: string;
  setScheduleTime: (v: string) => void;
  scheduleDays: Set<string>;
  scheduleDates: Set<number>;
  filteredSources: Source[];
  allFilteredSelected: boolean;
  toggleDay: (day: string) => void;
  toggleDate: (date: number) => void;
  addRecipient: () => void;
  removeRecipient: (email: string) => void;
  toggleSelectAll: () => void;
  toggleSource: (id: string) => void;
  addKeyword: () => void;
  removeKeyword: (kw: string) => void;
  handleCodeModeSwitch: (mode: string) => void;
  handleCodeLangSwitch: (lang: string) => void;
  canAdvance: () => boolean;
  handleSubmit: (andTrigger: boolean) => Promise<void>;
  router: ReturnType<typeof useRouter>;
}

/**
 * Custom hook for the Runs Configure (wizard) page.
 * Manages multi-step form state, code/form syncing, and run creation.
 *
 * Interacts with:
 * - GET /api/sources
 * - POST /api/runs
 */
export function useRunConfigure(): UseRunConfigureReturn {
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

    setSubmitting(false);
    if (res.ok) {
      toast.success(
        andTrigger ? "Run created and triggered." : "Run created successfully.",
      );
      router.push("/runs");
    } else {
      toast.error(res.error);
    }
  }

  return {
    step,
    setStep,
    submitting,
    runName,
    setRunName,
    description,
    setDescription,
    enableEmailAlert,
    setEnableEmailAlert,
    recipients,
    recipientInput,
    setRecipientInput,
    sources,
    loadingSources,
    selectedSourceIds,
    sourceSearch,
    setSourceSearch,
    agentFilter,
    setAgentFilter,
    params,
    setParams,
    keywordInput,
    setKeywordInput,
    codeMode,
    codeLang,
    codeText,
    setCodeText,
    scheduleTime,
    setScheduleTime,
    scheduleDays,
    scheduleDates,
    filteredSources,
    allFilteredSelected,
    toggleDay,
    toggleDate,
    addRecipient,
    removeRecipient,
    toggleSelectAll,
    toggleSource,
    addKeyword,
    removeKeyword,
    handleCodeModeSwitch,
    handleCodeLangSwitch,
    canAdvance,
    handleSubmit,
    router,
  };
}