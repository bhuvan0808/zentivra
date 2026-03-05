export type AgentType = "competitor" | "model_provider" | "research" | "hf_benchmark";

export type FindingCategory = "models" | "apis" | "pricing" | "benchmarks" | "safety" | "tooling" | "research" | "other";

export type RunStatus = "pending" | "running" | "completed" | "failed" | "partial";

export interface Source {
  readonly id: string;
  readonly name: string;
  readonly agent_type: AgentType;
  readonly url: string;
  readonly feed_url: string | null;
  readonly css_selectors: Record<string, string> | null;
  readonly keywords: string[];
  readonly rate_limit_rpm: number;
  readonly crawl_depth: number;
  readonly enabled: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SourceCreate {
  name: string;
  agent_type: AgentType;
  url: string;
  feed_url?: string | null;
  css_selectors?: Record<string, string> | null;
  keywords?: string[];
  rate_limit_rpm?: number;
  crawl_depth?: number;
  enabled?: boolean;
}

export interface SourceUpdate {
  name?: string;
  agent_type?: AgentType;
  url?: string;
  feed_url?: string | null;
  css_selectors?: Record<string, string> | null;
  keywords?: string[];
  rate_limit_rpm?: number;
  crawl_depth?: number;
  enabled?: boolean;
}

export interface Run {
  readonly id: string;
  readonly started_at: string;
  readonly completed_at: string | null;
  readonly status: RunStatus;
  readonly agent_statuses: Record<string, string> | null;
  readonly total_findings: number;
  readonly error_log: string | null;
  readonly triggered_by: string;
}

export interface TriggerRunResponse {
  readonly run_id: string;
  readonly message: string;
  readonly status: string;
}

export interface Finding {
  readonly id: string;
  readonly run_id: string;
  readonly source_id: string;
  readonly title: string;
  readonly date_detected: string;
  readonly source_url: string;
  readonly publisher: string;
  readonly category: FindingCategory;
  readonly summary_short: string;
  readonly summary_long: string;
  readonly why_it_matters: string;
  readonly evidence: { claims: string[] };
  readonly confidence: number;
  readonly tags: string[];
  readonly entities: {
    companies: string[];
    models: string[];
    datasets: string[];
  };
  readonly impact_score: number;
  readonly is_duplicate: boolean;
  readonly cluster_id: string | null;
}

export interface FindingsStats {
  readonly total_findings: number;
  readonly by_category: Record<string, number>;
  readonly avg_impact_score: number;
}

export interface Digest {
  readonly id: string;
  readonly run_id: string;
  readonly date: string;
  readonly executive_summary: string;
  readonly pdf_path: string;
  readonly email_sent: boolean;
  readonly sent_at: string | null;
  readonly recipients: string[];
  readonly total_findings: number;
  readonly created_at: string;
}

export interface HealthStatus {
  readonly name: string;
  readonly version: string;
  readonly status: string;
  readonly llm_provider: string;
  readonly email_configured: boolean;
}

export interface DetailedHealth {
  readonly status: string;
  readonly database: string;
  readonly llm_provider: string;
  readonly email_configured: boolean;
  readonly environment: string;
}

export interface SchedulerJob {
  readonly id: string;
  readonly name: string;
  readonly next_run: string;
}

export interface SchedulerStatus {
  readonly running: boolean;
  readonly jobs: SchedulerJob[];
}

export type ApiValidationItem = {
  readonly type: string;
  readonly loc: string[];
  readonly msg: string;
  readonly input: unknown;
};

export type ApiResult<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly error: string };

export interface FindingsQueryParams {
  page?: number;
  page_size?: number;
  category?: FindingCategory;
  min_confidence?: number;
  search?: string;
  include_duplicates?: boolean;
}

export interface SourcesQueryParams {
  agent_type?: AgentType;
  enabled?: boolean;
}
