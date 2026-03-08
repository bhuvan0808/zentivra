export type AgentType =
  | "competitor"
  | "model_provider"
  | "research"
  | "hf_benchmark";

export type FindingCategory =
  | "models"
  | "apis"
  | "pricing"
  | "benchmarks"
  | "safety"
  | "tooling"
  | "research"
  | "other";

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "partial"
  | "completed_empty";

export interface Source {
  readonly source_id: string;
  readonly source_name: string;
  readonly display_name: string;
  readonly agent_type: AgentType;
  readonly url: string;
  readonly is_enabled: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SourceCreate {
  source_name: string;
  display_name: string;
  agent_type: AgentType;
  url: string;
}

export interface SourceUpdate {
  source_name?: string;
  display_name?: string;
  agent_type?: AgentType;
  url?: string;
  is_enabled?: boolean;
}

export interface CrawlSchedule {
  readonly frequency: "daily" | "weekly" | "monthly";
  readonly time: string;
  readonly periods: string[] | null;
}

export interface Run {
  readonly run_id: string;
  readonly run_name: string;
  readonly description: string | null;
  readonly enable_pdf_gen: boolean;
  readonly enable_email_alert: boolean;
  readonly email_recipients: string[] | null;
  readonly sources: string[];
  readonly crawl_frequency: CrawlSchedule | null;
  readonly crawl_depth: number;
  readonly keywords: string[] | null;
  readonly is_enabled: boolean;
  readonly has_active_triggers: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface RunCreate {
  run_name: string;
  description?: string;
  enable_pdf_gen?: boolean;
  enable_email_alert?: boolean;
  email_recipients?: string[];
  sources: string[];
  crawl_frequency?: CrawlSchedule;
  crawl_depth: number;
  keywords?: string[];
  trigger_on_create?: boolean;
}

export interface RunUpdate {
  run_name?: string;
  description?: string;
  enable_pdf_gen?: boolean;
  enable_email_alert?: boolean;
  email_recipients?: string[];
  sources?: string[];
  crawl_frequency?: CrawlSchedule;
  crawl_depth?: number;
  keywords?: string[];
  is_enabled?: boolean;
}

export interface RunTriggerPayload {
  trigger_method?: string;
  max_sources_per_agent?: number;
}

export interface RunTriggerResponse {
  readonly run_trigger_id: string;
  readonly run_id: string;
  readonly message: string;
  readonly status: string;
}

export interface RunTrigger {
  readonly run_trigger_id: string;
  readonly run_id: string;
  readonly trigger_method: string;
  readonly status: RunStatus;
  readonly is_latest: boolean;
  readonly created_at: string;
  readonly updated_at: string;
  readonly findings_count: number;
  readonly snapshots_count: number;
  readonly digest_id?: string | null;
  readonly digest_status?: string | null;
  readonly pdf_url?: string | null;
  readonly html_url?: string | null;
}

export interface Snapshot {
  readonly snapshot_id: string;
  readonly source_name: string;
  readonly total_findings: number;
  readonly summary: string | null;
  readonly status: string;
  readonly created_at: string;
}

/** @deprecated Use RunTriggerPayload + triggerRunById instead */
export interface TriggerRunResponse {
  readonly run_id: string;
  readonly message: string;
  readonly status: string;
}

/** @deprecated Use RunTriggerPayload + triggerRunById instead */
export interface RunTriggerRequest {
  agent_types?: AgentType[];
  source_ids?: string[];
  recipients?: string[];
  max_sources_per_agent?: number;
}

export interface Finding {
  readonly finding_id: string;
  readonly content: string | null;
  readonly summary: string | null;
  readonly run_trigger_id: string | null;
  readonly src_url: string;
  readonly category: FindingCategory | null;
  readonly confidence: number;
  readonly created_at: string;
}

export interface FindingsStats {
  readonly total_findings: number;
  readonly by_category: Record<string, number>;
}

export interface Digest {
  readonly digest_id: string;
  readonly digest_name: string | null;
  readonly run_trigger_id: string | null;
  readonly pdf_path: string | null;
  readonly html_path: string | null;
  readonly status: string;
  readonly has_pdf: boolean;
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
  readonly frequency: string;
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

// ── Auth ──

export interface AuthResponse {
  readonly user_id: string;
  readonly username: string;
  readonly email: string;
  readonly display_name: string;
  readonly auth_token: string;
  readonly expires_at: string;
}

export interface AuthUser {
  readonly user_id: string;
  readonly username: string;
  readonly email: string;
  readonly display_name: string;
  readonly last_login: string | null;
  readonly created_at: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface SignupPayload {
  username: string;
  email: string;
  password: string;
  display_name: string;
}

export interface FindingsQueryParams {
  page?: number;
  page_size?: number;
  category?: FindingCategory;
  min_confidence?: number;
}

export interface SourcesQueryParams {
  agent_type?: AgentType;
  enabled?: boolean;
}

// ── Execution Logs ──

export interface AgentLogSummary {
  readonly agent_name: string;
  readonly file_size: number;
  readonly line_count: number;
}

export interface LogEntry {
  readonly ts: string;
  readonly trigger_id: string;
  readonly level: string;
  readonly agent: string | null;
  readonly step: string;
  readonly event: string;
  readonly [key: string]: unknown;
}

export interface LogPreview {
  readonly agent_name: string;
  readonly total_lines: number;
  readonly preview: LogEntry[];
}

// ── Dashboard ──

export interface DashboardKpi {
  readonly total_findings: number;
  readonly total_sources: number;
  readonly runs_overview: {
    readonly total_runs: number;
    readonly enabled_runs: number;
  };
}

export interface DashboardCharts {
  readonly confidence_distribution: {
    readonly high: number;
    readonly medium: number;
    readonly low: number;
  };
  readonly daily_findings: Array<{
    readonly date: string;
    readonly count: number;
  }>;
  readonly confidence_trend: Array<{
    readonly date: string;
    readonly avg_confidence: number | null;
  }>;
  readonly by_category: Record<string, number>;
  readonly by_agent_type: Record<string, number>;
}

export interface DashboardTriggers {
  readonly trigger_status_counts: Record<string, number>;
  readonly recent_triggers: Array<{
    readonly run_trigger_id: string;
    readonly run_name: string;
    readonly status: string;
    readonly findings_count: number;
    readonly snapshots_count: number;
    readonly created_at: string | null;
  }>;
}

export interface DashboardSources {
  readonly findings_by_source: Array<{
    readonly source_name: string;
    readonly display_name: string;
    readonly count: number;
  }>;
}
