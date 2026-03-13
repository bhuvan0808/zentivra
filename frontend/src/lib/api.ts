import type {
  Source,
  SourceCreate,
  SourceUpdate,
  Run,
  RunCreate,
  RunUpdate,
  RunTriggerPayload,
  RunTriggerResponse,
  RunTrigger,
  RunTriggerRequest,
  TriggerRunResponse,
  Finding,
  FindingsStats,
  Snapshot,
  Digest,
  HealthStatus,
  SchedulerStatus,
  ApiResult,
  ApiValidationItem,
  FindingsQueryParams,
  SourcesQueryParams,
  AuthResponse,
  AuthUser,
  LoginPayload,
  SignupPayload,
  AgentLogSummary,
  LogPreview,
  DashboardKpi,
  DashboardCharts,
  DashboardTriggers,
  DashboardSources,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function buildUrl(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): string {
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

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
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

async function request<T>(
  url: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  try {
    const authHeaders = getAuthHeaders();
    const merged: RequestInit = {
      ...init,
      headers: {
        ...authHeaders,
        ...init?.headers,
      },
    };

    const res = await fetch(url, merged);

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        const currentPath = window.location.pathname;
        localStorage.removeItem("auth_token");
        window.location.href = `/?redirect=${encodeURIComponent(currentPath)}`;
      }
      return { ok: false, error: "Session expired" };
    }

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
    return {
      ok: false,
      error: "Unable to reach the server. Please check your connection.",
    };
  }
}

async function publicRequest<T>(
  url: string,
  init?: RequestInit,
): Promise<ApiResult<T>> {
  try {
    const res = await fetch(url, init);
    if (!res.ok) {
      const error = await extractError(res);
      return { ok: false, error };
    }
    const data = (await res.json()) as T;
    return { ok: true, data };
  } catch {
    return {
      ok: false,
      error: "Unable to reach the server. Please check your connection.",
    };
  }
}

// ── Auth (public endpoints) ──

export function signup(
  payload: SignupPayload,
): Promise<ApiResult<AuthResponse>> {
  return publicRequest<AuthResponse>(buildUrl("/api/auth/signup"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function login(payload: LoginPayload): Promise<ApiResult<AuthResponse>> {
  return publicRequest<AuthResponse>(buildUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<ApiResult<{ message: string }>> {
  return request<{ message: string }>(buildUrl("/api/auth/logout"), {
    method: "POST",
  });
}

export function getMe(): Promise<ApiResult<AuthUser>> {
  return request<AuthUser>(buildUrl("/api/auth/me"));
}

// ── Health ──

export function getHealth(): Promise<ApiResult<HealthStatus>> {
  return request<HealthStatus>(buildUrl("/"));
}

export function getSchedulerStatus(): Promise<ApiResult<SchedulerStatus>> {
  return request<SchedulerStatus>(buildUrl("/scheduler"));
}

// ── Sources ──

export function getSources(
  params?: SourcesQueryParams,
): Promise<ApiResult<Source[]>> {
  return request<Source[]>(
    buildUrl(
      "/api/sources",
      params as Record<string, string | boolean | undefined>,
    ),
  );
}

export function getSource(sourceId: string): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl(`/api/sources/${sourceId}`));
}

export function createSource(data: SourceCreate): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl("/api/sources"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateSource(
  sourceId: string,
  data: SourceUpdate,
): Promise<ApiResult<Source>> {
  return request<Source>(buildUrl(`/api/sources/${sourceId}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function deleteSource(sourceId: string): Promise<ApiResult<void>> {
  return request<void>(buildUrl(`/api/sources/${sourceId}`), {
    method: "DELETE",
  });
}

// ── Runs ──

export function getRuns(limit?: number): Promise<ApiResult<Run[]>> {
  return request<Run[]>(buildUrl("/api/runs", { limit }));
}

export function getRun(runId: string): Promise<ApiResult<Run>> {
  return request<Run>(buildUrl(`/api/runs/${runId}`));
}

export function createRun(payload: RunCreate): Promise<ApiResult<Run>> {
  return request<Run>(buildUrl("/api/runs"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateRun(
  runId: string,
  payload: RunUpdate,
): Promise<ApiResult<Run>> {
  return request<Run>(buildUrl(`/api/runs/${runId}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteRun(runId: string): Promise<ApiResult<void>> {
  return request<void>(buildUrl(`/api/runs/${runId}`), { method: "DELETE" });
}

export function triggerRunById(
  runId: string,
  payload?: RunTriggerPayload,
): Promise<ApiResult<RunTriggerResponse>> {
  return request<RunTriggerResponse>(buildUrl(`/api/runs/${runId}/trigger`), {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

export function getRunTriggers(
  runId: string,
  limit?: number,
): Promise<ApiResult<RunTrigger[]>> {
  return request<RunTrigger[]>(
    buildUrl(`/api/runs/${runId}/triggers`, { limit }),
  );
}

export function getRunTrigger(
  triggerId: string,
): Promise<ApiResult<RunTrigger>> {
  return request<RunTrigger>(buildUrl(`/api/run-triggers/${triggerId}`));
}

export function getTriggerFindings(
  triggerId: string,
  limit?: number,
): Promise<ApiResult<Finding[]>> {
  return request<Finding[]>(
    buildUrl(`/api/run-triggers/${triggerId}/findings`, { limit }),
  );
}

export function getTriggerSnapshots(
  triggerId: string,
): Promise<ApiResult<Snapshot[]>> {
  return request<Snapshot[]>(
    buildUrl(`/api/run-triggers/${triggerId}/snapshots`),
  );
}

/** @deprecated Use triggerRunById instead */
export function triggerRun(
  payload?: RunTriggerRequest,
): Promise<ApiResult<TriggerRunResponse>> {
  return request<TriggerRunResponse>(buildUrl("/api/runs/trigger"), {
    method: "POST",
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

// ── Findings ──

export function getFindings(
  params?: FindingsQueryParams,
): Promise<ApiResult<Finding[]>> {
  return request<Finding[]>(
    buildUrl(
      "/api/findings",
      params as Record<string, string | number | boolean | undefined>,
    ),
  );
}

export function getFindingsStats(): Promise<ApiResult<FindingsStats>> {
  return request<FindingsStats>(buildUrl("/api/findings/stats"));
}

export function getFinding(findingId: string): Promise<ApiResult<Finding>> {
  return request<Finding>(buildUrl(`/api/findings/${findingId}`));
}

// ── Digests ──

export function getDigests(limit?: number): Promise<ApiResult<Digest[]>> {
  return request<Digest[]>(buildUrl("/api/digests", { limit }));
}

export function getLatestDigest(): Promise<ApiResult<Digest>> {
  return request<Digest>(buildUrl("/api/digests/latest"));
}

export function getDigest(digestId: string): Promise<ApiResult<Digest>> {
  return request<Digest>(buildUrl(`/api/digests/${digestId}`));
}

export function getDigestPdfUrl(digestId: string): string {
  return buildUrl(`/api/digests/${digestId}/pdf`);
}

export function getDigestHtmlUrl(digestId: string): string {
  return buildUrl(`/api/digests/${digestId}/html`);
}

export function sendDigestEmail(
  digestIds: string[],
  recipients: string[],
): Promise<ApiResult<{ sent: number; failed: number; details: object[] }>> {
  return request(buildUrl("/api/digests/send-email"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ digest_ids: digestIds, recipients }),
  });
}

// ── Execution Logs ──

export function getTriggerLogs(
  triggerId: string,
): Promise<ApiResult<AgentLogSummary[]>> {
  return request<AgentLogSummary[]>(
    buildUrl(`/api/run-triggers/${triggerId}/logs`),
  );
}

export function getTriggerLogPreview(
  triggerId: string,
  agentName: string,
  limit?: number,
): Promise<ApiResult<LogPreview>> {
  return request<LogPreview>(
    buildUrl(`/api/run-triggers/${triggerId}/logs/${agentName}/preview`, {
      limit,
    }),
  );
}

export function getTriggerLogDownloadUrl(
  triggerId: string,
  agentName: string,
): string {
  return buildUrl(`/api/run-triggers/${triggerId}/logs/${agentName}/download`);
}

// ── Dashboard ──

export function getDashboardKpi(): Promise<ApiResult<DashboardKpi>> {
  return request<DashboardKpi>(buildUrl("/api/dashboard/kpi"));
}

export function getDashboardCharts(): Promise<ApiResult<DashboardCharts>> {
  return request<DashboardCharts>(buildUrl("/api/dashboard/charts"));
}

export function getDashboardTriggers(): Promise<ApiResult<DashboardTriggers>> {
  return request<DashboardTriggers>(buildUrl("/api/dashboard/triggers"));
}

export function getDashboardSources(): Promise<ApiResult<DashboardSources>> {
  return request<DashboardSources>(buildUrl("/api/dashboard/sources"));
}

export async function downloadTriggerLog(
  triggerId: string,
  agentName: string,
): Promise<void> {
  const url = getTriggerLogDownloadUrl(triggerId, agentName);
  const authHeaders = getAuthHeaders();
  const res = await fetch(url, { headers: authHeaders });
  if (!res.ok) return;
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `${triggerId.slice(0, 8)}_${agentName}.ndjson`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(blobUrl);
}
