import { useState, useEffect, useCallback, useRef } from "react";
import {
  getAgents,
  getAgentLogs,
  getAgentSources,
} from "@/lib/agents-api";
import type {
  AgentInfo,
  AgentTriggerInfo,
  AgentLogEntry,
  AgentSource,
} from "@/lib/agents-api";

// Static fallback so cards always render even when the API is unreachable
const STATIC_AGENTS: AgentInfo[] = [
  {
    key: "competitor",
    label: "Competitor Watcher",
    description:
      "Monitors competitor announcements, releases, and strategic moves.",
    status: "idle",
    sources_count: 0,
    recent_triggers: [],
  },
  {
    key: "model_provider",
    label: "Model Provider Watcher",
    description:
      "Tracks LLM provider updates, new model releases, and API changes.",
    status: "idle",
    sources_count: 0,
    recent_triggers: [],
  },
  {
    key: "research",
    label: "Research Scout",
    description:
      "Scans research publications, arXiv papers, and technical blogs.",
    status: "idle",
    sources_count: 0,
    recent_triggers: [],
  },
  {
    key: "hf_benchmark",
    label: "HF Benchmark Tracker",
    description: "Monitors Hugging Face leaderboards and benchmark results.",
    status: "idle",
    sources_count: 0,
    recent_triggers: [],
  },
];

export interface UseAgentsReturn {
  agents: AgentInfo[];
  loading: boolean;
  selectedAgent: string | null;
  setSelectedAgent: (key: string | null) => void;
  logs: AgentLogEntry[];
  logsLoading: boolean;
  selectedTrigger: AgentTriggerInfo | null;
  setSelectedTrigger: (t: AgentTriggerInfo | null) => void;
  totalLogLines: number;
  sources: AgentSource[];
  sourcesLoading: boolean;
  selectAgentLogs: (agentKey: string) => void;
  fetchLogsForTrigger: (agentKey: string, triggerId: string) => void;
  openCrawlSources: (agentKey: string) => void;
  refreshLogs: () => void;
}

/**
 * Custom hook for the Agents page.
 * Always returns 4 agent cards (static fallback).
 * Merges live API data when available.
 * Supports selecting past run triggers to view their logs.
 */
export function useAgents(): UseAgentsReturn {
  const [agents, setAgents] = useState<AgentInfo[]>(STATIC_AGENTS);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Logs state
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [selectedTrigger, setSelectedTrigger] =
    useState<AgentTriggerInfo | null>(null);
  const [totalLogLines, setTotalLogLines] = useState(0);

  // Sources state (for View Crawl)
  const [sources, setSources] = useState<AgentSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  const selectedAgentRef = useRef(selectedAgent);
  useEffect(() => {
    selectedAgentRef.current = selectedAgent;
  }, [selectedAgent]);

  // Fetch agents list — merge API data on top of static cards
  const fetchAgents = useCallback(async () => {
    const res = await getAgents();
    if (res.ok && res.data.length > 0) {
      setAgents(res.data);
    }
    // If API fails, STATIC_AGENTS stays — cards always visible
    setLoading(false);
  }, []);

  useEffect(() => {
    void fetchAgents();
  }, [fetchAgents]);

  // Poll agents every 10s for status updates
  useEffect(() => {
    const id = setInterval(() => void fetchAgents(), 10_000);
    return () => clearInterval(id);
  }, [fetchAgents]);

  // Fetch logs for a specific trigger
  const fetchLogs = useCallback(
    async (agentKey: string, triggerId?: string) => {
      setLogsLoading(true);
      const res = await getAgentLogs(agentKey, triggerId, 200);
      if (res.ok) {
        setLogs(res.data.entries);
        setTotalLogLines(res.data.total_lines);
      } else {
        setLogs([]);
        setTotalLogLines(0);
      }
      setLogsLoading(false);
    },
    [],
  );

  // Auto-refresh logs every 3s when an agent is running and selected
  useEffect(() => {
    if (!selectedAgent) return;

    const agent = agents.find((a) => a.key === selectedAgent);
    if (!agent || agent.status !== "running") return;

    const id = setInterval(() => {
      if (selectedAgentRef.current) {
        void fetchLogs(
          selectedAgentRef.current,
          selectedTrigger?.trigger_id,
        );
      }
    }, 3_000);

    return () => clearInterval(id);
  }, [selectedAgent, agents, fetchLogs, selectedTrigger]);

  function selectAgentLogs(agentKey: string) {
    setSelectedAgent(agentKey);
    // Auto-select the first (latest) trigger
    const agent = agents.find((a) => a.key === agentKey);
    const first = agent?.recent_triggers[0] ?? null;
    setSelectedTrigger(first);
    void fetchLogs(agentKey, first?.trigger_id);
  }

  function fetchLogsForTrigger(agentKey: string, triggerId: string) {
    const agent = agents.find((a) => a.key === agentKey);
    const trigger =
      agent?.recent_triggers.find((t) => t.trigger_id === triggerId) ?? null;
    setSelectedTrigger(trigger);
    void fetchLogs(agentKey, triggerId);
  }

  function openCrawlSources(agentKey: string) {
    // Fetch sources then open the first URL in a new tab
    setSourcesLoading(true);
    getAgentSources(agentKey).then((res) => {
      if (res.ok) {
        setSources(res.data);
        // Open the first enabled source URL
        const first = res.data.find((s) => s.is_enabled);
        if (first) {
          window.open(first.url, "_blank", "noopener,noreferrer");
        }
      }
      setSourcesLoading(false);
    });
  }

  function refreshLogs() {
    if (selectedAgent) {
      void fetchLogs(selectedAgent, selectedTrigger?.trigger_id);
    }
  }

  return {
    agents,
    loading,
    selectedAgent,
    setSelectedAgent,
    logs,
    logsLoading,
    selectedTrigger,
    setSelectedTrigger,
    totalLogLines,
    sources,
    sourcesLoading,
    selectAgentLogs,
    fetchLogsForTrigger,
    openCrawlSources,
    refreshLogs,
  };
}
