/**
 * Agents API client module.
 *
 * Separate module to avoid merge conflicts with the main api.ts file.
 * Provides functions for the /api/agents endpoints.
 */

import type { ApiResult } from "./types";

// ── Types ────────────────────────────────────────────────────────────────

export interface AgentTriggerInfo {
  readonly trigger_id: string;
  readonly trigger_status: string;
  readonly created_at: string | null;
}

export interface AgentInfo {
  readonly key: string;
  readonly label: string;
  readonly description: string;
  readonly status: "running" | "idle";
  readonly sources_count: number;
  readonly recent_triggers: AgentTriggerInfo[];
}

export interface AgentLogEntry {
  readonly ts: string;
  readonly trigger_id: string;
  readonly level: string;
  readonly agent: string | null;
  readonly step: string;
  readonly event: string;
  readonly [key: string]: unknown;
}

export interface AgentLogsResponse {
  readonly agent_key: string;
  readonly trigger_id: string | null;
  readonly total_lines: number;
  readonly entries: AgentLogEntry[];
}

export interface AgentSource {
  readonly source_id: string;
  readonly source_name: string;
  readonly display_name: string;
  readonly url: string;
  readonly is_enabled: boolean;
}

// ── Request helper ───────────────────────────────────────────────────────

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function api<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { ...authHeaders(), ...init?.headers },
    });

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        window.location.href = `/?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
      return { ok: false, error: "Session expired" };
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = body.detail;
      return {
        ok: false,
        error:
          typeof detail === "string"
            ? detail
            : `Request failed (${res.status})`,
      };
    }

    if (res.status === 204) return { ok: true, data: undefined as unknown as T };
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, error: "Unable to reach the server." };
  }
}

// ── API functions ────────────────────────────────────────────────────────

export function getAgents(): Promise<ApiResult<AgentInfo[]>> {
  return api<AgentInfo[]>("/api/agents");
}

export function getAgentLogs(
  agentKey: string,
  triggerId?: string,
  limit?: number,
): Promise<ApiResult<AgentLogsResponse>> {
  const params = new URLSearchParams();
  if (triggerId) params.set("trigger_id", triggerId);
  if (limit) params.set("limit", String(limit));
  const qs = params.toString();
  return api<AgentLogsResponse>(
    `/api/agents/${agentKey}/logs${qs ? `?${qs}` : ""}`,
  );
}

export function getAgentSources(
  agentKey: string,
): Promise<ApiResult<AgentSource[]>> {
  return api<AgentSource[]>(`/api/agents/${agentKey}/sources`);
}
