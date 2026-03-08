import { useState, useEffect, useCallback, useRef } from "react";
import {
  getAgents,
  getAgentLogs,
  getAgentSources,
} from "@/lib/agents-api";
import type {
  AgentInfo,
  AgentLogEntry,
  AgentSource,
} from "@/lib/agents-api";

export interface UseAgentsReturn {
  agents: AgentInfo[];
  loading: boolean;
  selectedAgent: string | null;
  setSelectedAgent: (key: string | null) => void;
  activeTab: "logs" | "sources";
  setActiveTab: (tab: "logs" | "sources") => void;
  logs: AgentLogEntry[];
  logsLoading: boolean;
  logsTrigger: string | null;
  totalLogLines: number;
  sources: AgentSource[];
  sourcesLoading: boolean;
  selectAgentLogs: (agentKey: string) => void;
  selectAgentSources: (agentKey: string) => void;
  refreshLogs: () => void;
}

/**
 * Custom hook for the Agents page.
 * Manages fetching agents status, live log streaming,
 * and crawl source viewing.
 *
 * Interacts with:
 * - GET /api/agents
 * - GET /api/agents/{key}/logs
 * - GET /api/agents/{key}/sources
 */
export function useAgents(): UseAgentsReturn {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"logs" | "sources">("logs");

  // Logs state
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsTrigger, setLogsTrigger] = useState<string | null>(null);
  const [totalLogLines, setTotalLogLines] = useState(0);

  // Sources state
  const [sources, setSources] = useState<AgentSource[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);

  const selectedAgentRef = useRef(selectedAgent);
  useEffect(() => {
    selectedAgentRef.current = selectedAgent;
  }, [selectedAgent]);

  // Fetch agents list
  const fetchAgents = useCallback(async () => {
    const res = await getAgents();
    if (res.ok) setAgents(res.data);
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

  // Fetch logs for the selected agent
  const fetchLogs = useCallback(async (agentKey: string) => {
    setLogsLoading(true);
    const res = await getAgentLogs(agentKey, undefined, 200);
    if (res.ok) {
      setLogs(res.data.entries);
      setLogsTrigger(res.data.trigger_id);
      setTotalLogLines(res.data.total_lines);
    }
    setLogsLoading(false);
  }, []);

  // Auto-refresh logs every 3s when an agent is running and selected
  useEffect(() => {
    if (!selectedAgent || activeTab !== "logs") return;

    const agent = agents.find((a) => a.key === selectedAgent);
    if (!agent || agent.status !== "running") return;

    const id = setInterval(() => {
      if (selectedAgentRef.current) {
        void fetchLogs(selectedAgentRef.current);
      }
    }, 3_000);

    return () => clearInterval(id);
  }, [selectedAgent, activeTab, agents, fetchLogs]);

  function selectAgentLogs(agentKey: string) {
    setSelectedAgent(agentKey);
    setActiveTab("logs");
    void fetchLogs(agentKey);
  }

  function selectAgentSources(agentKey: string) {
    setSelectedAgent(agentKey);
    setActiveTab("sources");
    setSourcesLoading(true);
    getAgentSources(agentKey).then((res) => {
      if (res.ok) setSources(res.data);
      setSourcesLoading(false);
    });
  }

  function refreshLogs() {
    if (selectedAgent) {
      void fetchLogs(selectedAgent);
    }
  }

  return {
    agents,
    loading,
    selectedAgent,
    setSelectedAgent,
    activeTab,
    setActiveTab,
    logs,
    logsLoading,
    logsTrigger,
    totalLogLines,
    sources,
    sourcesLoading,
    selectAgentLogs,
    selectAgentSources,
    refreshLogs,
  };
}
