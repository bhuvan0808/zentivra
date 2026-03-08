import { useState, useEffect } from "react";
import { toast } from "sonner";
import { updateRun, getSources } from "@/lib/api";
import type { Run, Source, CrawlSchedule } from "@/lib/types";

const WEEK_DAYS = [
  { key: "mon", label: "M" },
  { key: "tue", label: "T" },
  { key: "wed", label: "W" },
  { key: "thu", label: "T" },
  { key: "fri", label: "F" },
  { key: "sat", label: "S" },
  { key: "sun", label: "S" },
] as const;

function parseCrawlSchedule(schedule: CrawlSchedule | null) {
  const freq = schedule?.frequency ?? "daily";
  const time = schedule?.time ? utcToLocalInput(schedule.time) : "09:00";
  let days = new Set(["mon", "wed", "fri"]);
  let dates = new Set([1]);

  if (freq === "weekly" && schedule?.periods) {
    days = new Set(schedule.periods);
  }
  if (freq === "monthly" && schedule?.periods) {
    dates = new Set(schedule.periods.map(Number).filter(Boolean));
  }

  return { freq, time, days, dates };
}

function utcToLocalInput(utcTime: string): string {
  const [h, m] = utcTime.split(":").map(Number);
  const now = new Date();
  now.setUTCHours(h, m, 0, 0);
  return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

function localToUtc(localTime: string): string {
  const [h, m] = localTime.split(":").map(Number);
  const now = new Date();
  now.setHours(h, m, 0, 0);
  return `${String(now.getUTCHours()).padStart(2, "0")}:${String(now.getUTCMinutes()).padStart(2, "0")}`;
}

export interface UseRunEditReturn {
  runName: string;
  setRunName: (v: string) => void;
  description: string;
  setDescription: (v: string) => void;
  enableEmailAlert: boolean;
  setEnableEmailAlert: (v: boolean) => void;
  recipients: string[];
  recipientInput: string;
  setRecipientInput: (v: string) => void;
  crawlFrequency: CrawlSchedule["frequency"];
  setCrawlFrequency: (v: CrawlSchedule["frequency"]) => void;
  scheduleTime: string;
  setScheduleTime: (v: string) => void;
  scheduleDays: Set<string>;
  scheduleDates: Set<number>;
  crawlDepth: number;
  setCrawlDepth: (v: number) => void;
  keywords: string[];
  keywordInput: string;
  setKeywordInput: (v: string) => void;
  saving: boolean;
  allSources: Source[];
  selectedSourceIds: Set<string>;
  sourceSearch: string;
  setSourceSearch: (v: string) => void;
  agentFilter: string;
  setAgentFilter: (v: string) => void;
  loadingSources: boolean;
  filteredSources: Source[];
  toggleSource: (id: string) => void;
  toggleDay: (day: string) => void;
  toggleDate: (date: number) => void;
  addRecipient: () => void;
  removeRecipient: (email: string) => void;
  handleSave: () => Promise<void>;
  addKeyword: () => void;
  removeKeyword: (kw: string) => void;
  WEEK_DAYS: typeof WEEK_DAYS;
}

/**
 * Custom hook for the RunEditDialog component.
 * Manages form state, schedule encoding/decoding, and source filtering.
 *
 * Interacts with:
 * - GET /api/sources
 * - PUT /api/runs/{id}
 */
export function useRunEdit(
  run: Run,
  onClose: () => void,
  onSaved: (updated: Run) => void,
): UseRunEditReturn {
  const parsed = parseCrawlSchedule(run.crawl_frequency);

  const [runName, setRunName] = useState(run.run_name);
  const [description, setDescription] = useState(run.description ?? "");
  const [enableEmailAlert, setEnableEmailAlert] = useState(
    run.enable_email_alert,
  );
  const [recipients, setRecipients] = useState<string[]>(
    run.email_recipients ?? [],
  );
  const [recipientInput, setRecipientInput] = useState("");
  const [crawlFrequency, setCrawlFrequency] = useState(parsed.freq);
  const [scheduleTime, setScheduleTime] = useState(parsed.time);
  const [scheduleDays, setScheduleDays] = useState<Set<string>>(parsed.days);
  const [scheduleDates, setScheduleDates] = useState<Set<number>>(parsed.dates);
  const [crawlDepth, setCrawlDepth] = useState(run.crawl_depth);
  const [keywords, setKeywords] = useState<string[]>(run.keywords ?? []);
  const [keywordInput, setKeywordInput] = useState("");
  const [saving, setSaving] = useState(false);

  const [allSources, setAllSources] = useState<Source[]>([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState<Set<string>>(
    new Set(run.sources ?? []),
  );
  const [sourceSearch, setSourceSearch] = useState("");
  const [agentFilter, setAgentFilter] = useState("all");
  const [loadingSources, setLoadingSources] = useState(true);

  useEffect(() => {
    getSources().then((res) => {
      if (res.ok) setAllSources(res.data);
      setLoadingSources(false);
    });
  }, []);

  const filteredSources = allSources.filter((s) => {
    const matchSearch =
      !sourceSearch ||
      s.display_name.toLowerCase().includes(sourceSearch.toLowerCase()) ||
      s.source_name.toLowerCase().includes(sourceSearch.toLowerCase());
    const matchAgent = agentFilter === "all" || s.agent_type === agentFilter;
    return matchSearch && matchAgent;
  });

  function toggleSource(id: string) {
    setSelectedSourceIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

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
    const utcTime = localToUtc(scheduleTime);
    let periods: string[] | null = null;
    if (crawlFrequency === "weekly") {
      periods = Array.from(scheduleDays);
    } else if (crawlFrequency === "monthly") {
      periods = Array.from(scheduleDates)
        .sort((a, b) => a - b)
        .map(String);
    }
    return {
      frequency: crawlFrequency as CrawlSchedule["frequency"],
      time: utcTime,
      periods,
    };
  }

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

  function addKeyword() {
    const kw = keywordInput.trim();
    if (kw && !keywords.includes(kw)) {
      setKeywords((prev) => [...prev, kw]);
      setKeywordInput("");
    }
  }

  function removeKeyword(kw: string) {
    setKeywords((prev) => prev.filter((k) => k !== kw));
  }

  async function handleSave() {
    if (!runName.trim()) {
      toast.error("Run name is required.");
      return;
    }
    setSaving(true);
    const res = await updateRun(run.run_id, {
      run_name: runName.trim(),
      description: description.trim() || undefined,
      enable_email_alert: enableEmailAlert,
      email_recipients:
        enableEmailAlert && recipients.length > 0 ? recipients : undefined,
      crawl_frequency: buildSchedule(),
      crawl_depth: crawlDepth,
      keywords: keywords.length > 0 ? keywords : [],
      sources: Array.from(selectedSourceIds),
    });
    setSaving(false);
    if (res.ok) {
      toast.success("Run updated.");
      onSaved(res.data);
    } else {
      toast.error(res.error);
    }
  }

  return {
    runName,
    setRunName,
    description,
    setDescription,
    enableEmailAlert,
    setEnableEmailAlert,
    recipients,
    recipientInput,
    setRecipientInput,
    crawlFrequency,
    setCrawlFrequency,
    scheduleTime,
    setScheduleTime,
    scheduleDays,
    scheduleDates,
    crawlDepth,
    setCrawlDepth,
    keywords,
    keywordInput,
    setKeywordInput,
    saving,
    allSources,
    selectedSourceIds,
    sourceSearch,
    setSourceSearch,
    agentFilter,
    setAgentFilter,
    loadingSources,
    filteredSources,
    toggleSource,
    toggleDay,
    toggleDate,
    addRecipient,
    removeRecipient,
    handleSave,
    addKeyword,
    removeKeyword,
    WEEK_DAYS,
  };
}
