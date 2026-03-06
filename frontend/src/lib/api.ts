import type {
  Source,
  SourceCreate,
  SourceUpdate,
  Run,
  RunAgentActivity,
  RunAgentLog,
  RunAgentSummary,
  RunTriggerRequest,
  TriggerRunResponse,
  Finding,
  FindingsStats,
  Digest,
  HealthStatus,
  SchedulerStatus,
  ApiResult,
  ApiValidationItem,
  DisruptiveArticleRequest,
  DisruptiveArticleResponse,
  FindingsQueryParams,
  SourcesQueryParams,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = new URL(path, BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function extractError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (body.detail) {
      if (typeof body.detail === "string") {
        return body.detail;
      }
      if (Array.isArray(body.detail)) {
        return (body.detail as ApiValidationItem[])
          .map((item) => {
            const field = item.loc[item.loc.length - 1];
            return `${field}: ${item.msg}`;
          })
          .join(". ");
      }
    }
    return `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(url, init);
    if (!res.ok) {
      const error = await extractError(res);
      return { ok: false, error };
    }
    if (res.status === 204) {
      return { ok: true, data: undefined as unknown as T };
    }
    const data = (await res.json()) as T;
    return { ok: true, data };
  } catch {
    return { ok: false, error: "Unable to reach the server. Please check your connection." };
  }
}

// ── Health ──

export function getHealth(): Promise<ApiResult<HealthStatus>> {
  return request<HealthStatus>(buildUrl("/"));
}

export function getSchedulerStatus(): Promise<ApiResult<SchedulerStatus>> {
  return request<SchedulerStatus>(buildUrl("/scheduler"));
}

// ── Sources ──

export function getSources(params?: SourcesQueryParams): Promise<ApiResult<Source[]>> {
  return request<Source[]>(buildUrl("/api/sources", params as Record<string, string | boolean | undefined>));
}

export function getSource(id: string): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl(`/api/sources/${id}`));
}

export function createSource(data: SourceCreate): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl("/api/sources"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateSource(id: string, data: SourceUpdate): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl(`/api/sources/${id}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function deleteSource(id: string): Promise<ApiResult<void>> {
  return request<void>(buildUrl(`/api/sources/${id}`), { method: "DELETE" });
}

// ── Runs ──

export function getRuns(limit?: number): Promise<ApiResult<Run[]>> {
  return request<Run[]>(buildUrl("/api/runs", { limit }));
}

export function getRun(id: string): Promise<ApiResult<Run>> {
  return request<Run>(buildUrl(`/api/runs/${id}`));
}

export function triggerRun(payload?: RunTriggerRequest): Promise<ApiResult<TriggerRunResponse>> {
  return request<TriggerRunResponse>(buildUrl("/api/runs/trigger"), {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

export function getRunAgents(runId: string): Promise<ApiResult<RunAgentSummary[]>> {
  return request<RunAgentSummary[]>(buildUrl(`/api/runs/${runId}/agents`));
}

export function getRunAgentActivity(
  runId: string,
  agentType: string,
  limit = 200
): Promise<ApiResult<RunAgentActivity[]>> {
  return request<RunAgentActivity[]>(
    buildUrl(`/api/runs/${runId}/agents/${agentType}/activity`, { limit })
  );
}

export function getRunAgentLogs(
  runId: string,
  agentType: string,
  limit = 300
): Promise<ApiResult<RunAgentLog[]>> {
  return request<RunAgentLog[]>(
    buildUrl(`/api/runs/${runId}/agents/${agentType}/logs`, { limit })
  );
}

// ── Findings ──

export function getFindings(params?: FindingsQueryParams): Promise<ApiResult<Finding[]>> {
  return request<Finding[]>(
    buildUrl("/api/findings", params as Record<string, string | number | boolean | undefined>)
  );
}

export function getFindingsStats(): Promise<ApiResult<FindingsStats>> {
  return request<FindingsStats>(buildUrl("/api/findings/stats"));
}

export function getFinding(id: string): Promise<ApiResult<Finding>> {
  return request<Finding>(buildUrl(`/api/findings/${id}`));
}

// ── Digests ──

export function getDigests(limit?: number): Promise<ApiResult<Digest[]>> {
  return request<Digest[]>(buildUrl("/api/digests", { limit }));
}

export function getLatestDigest(): Promise<ApiResult<Digest>> {
  return request<Digest>(buildUrl("/api/digests/latest"));
}

export function getDigest(id: string): Promise<ApiResult<Digest>> {
  return request<Digest>(buildUrl(`/api/digests/${id}`));
}

export function getDigestPdfUrl(id: string): string {
  return buildUrl(`/api/digests/${id}/pdf`);
}

// ── Workflows ──

export function runDisruptiveArticle(
  payload: DisruptiveArticleRequest
): Promise<ApiResult<DisruptiveArticleResponse>> {
  return request<DisruptiveArticleResponse>(buildUrl("/api/workflows/disruptive-article"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getDisruptiveReportPdfUrl(reportId: string): string {
  return buildUrl(`/api/workflows/reports/${reportId}/pdf`);
}
