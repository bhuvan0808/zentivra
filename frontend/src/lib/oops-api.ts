/**
 * Oops (Disruptive Article) API client module.
 *
 * Separate module to avoid merge conflicts with the main api.ts file.
 * Provides functions for the /api/workflows/disruptive-article endpoint.
 */

import type { ApiResult } from "./types";

// ── Types ────────────────────────────────────────────────────────────────

export interface OopsRequest {
  url: string;
  recipient_email: string;
  title?: string;
}

export interface OopsResponse {
  readonly report_id: string;
  readonly findings_count: number;
  readonly email_sent: boolean;
  readonly pdf_path: string | null;
  readonly pdf_download_url: string | null;
  readonly agents_used: string[];
  readonly message: string;
}

export interface OopsReportSummary {
  readonly report_id: string;
  readonly url: string;
  readonly title: string | null;
  readonly recipient_email: string;
  readonly findings_count: number;
  readonly email_sent: boolean;
  readonly agents_used: string[];
  readonly executive_summary: string;
  readonly created_at: string | null;
  readonly pdf_download_url: string;
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

export function submitOopsReport(
  payload: OopsRequest,
): Promise<ApiResult<OopsResponse>> {
  return api<OopsResponse>("/api/workflows/disruptive-article", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getOopsReportPdfUrl(reportId: string): string {
  return `${BASE_URL}/api/workflows/reports/${reportId}/pdf`;
}

export function getReportHistory(): Promise<ApiResult<OopsReportSummary[]>> {
  return api<OopsReportSummary[]>("/api/workflows/reports");
}
