# Dashboard API Requirements

## Overview

The dashboard has 13 tiles across 6 rows. We need multiple independent API endpoints so each section can load progressively. This document describes what each tile displays and what data it needs.

---

## Dashboard Layout

```
Row 1: [Total Findings] [Sources Monitored] [Total Runs] [Latest Digest]
Row 2: [Upcoming Runs (table)]               [Confidence Distribution (radial chart)]
Row 3: [Daily Findings (area chart)]         [Confidence Trend (line chart)]
Row 4: [Findings by Category (pie chart)]    [Trigger Outcomes (donut chart)]
Row 5: [Top Sources (bar chart)]             [Agent Performance (bar chart)]
Row 6: [Recent Activity (list)]
```

---

## Tile Breakdown

### Row 1: KPI Cards

Tiles 1, 2, and 3 are related -- all simple counts. They should come from a single endpoint.

#### Tile 1: Total Findings
- **Displays:** Total count of all findings in the system.
- **I need:** `total_findings: number`

#### Tile 2: Sources Monitored
- **Displays:** Total count of all sources.
- **I need:** `total_sources: number`

#### Tile 3: Total Runs
- **Displays:** Total number of runs (large number) and how many are enabled (subtitle).
- **I need:**
  - `runs_overview.total_runs: number`
  - `runs_overview.enabled_runs: number`

#### Tile 4: Latest Digest
- **Displays:** The date of the most recent digest, its status (as a badge), and a PDF download icon. The download icon is only shown if a PDF is available for this digest. On click, the PDF is downloaded using the digest ID.
- **I need:**
  - `digest_id: string` -- used to construct the PDF download URL
  - `status: string` -- shown as a badge (e.g., "completed")
  - `created_at: string` -- shown as the digest date
  - `has_pdf: boolean` -- whether a PDF is available for download
- **Existing endpoint:** `GET /api/digests/latest` already provides this. Just need `has_pdf` instead of (or in addition to) `pdf_path`, since the FE doesn't use the path itself.

---

### Row 2: Upcoming Runs + Confidence Distribution

These two tiles are unrelated and come from different endpoints.

#### Tile 5: Upcoming Runs (table)
- **Displays:** A table of the next 3 upcoming scheduled runs. Columns: serial number, run name, frequency, next run time (shown as both relative like "in 2h 30m" and absolute like "Mar 6, 2026 06:00").
- **I need:** An array of scheduled jobs, each with:
  - `id: string`
  - `name: string` -- the run/job name
  - `frequency: string` -- the schedule frequency (e.g., `"daily"`, `"weekly"`, `"monthly"`). Currently the scheduler response only has `id`, `name`, and `next_run` -- the FE is guessing frequency from the job name, which is fragile.
  - `next_run: string` -- ISO 8601 datetime of the next scheduled execution
- **Existing endpoint:** `GET /scheduler` -- needs the `frequency` field added.

#### Tile 6: Confidence Distribution (radial bar chart)
- **Displays:** A half-circle radial bar chart with 3 bars representing finding counts in confidence buckets: High (>0.7), Medium (0.3-0.7), Low (<0.3).
- **I need:**
  - `confidence_distribution.high: number`
  - `confidence_distribution.medium: number`
  - `confidence_distribution.low: number`

---

### Row 3: Daily Findings + Confidence Trend

Tiles 7 and 8 are related -- both are time-series data over the last 30 days, grouped by date.

#### Tile 7: Daily Findings (area chart)
- **Displays:** An area chart showing the number of findings created per day.
- **I need:** An array sorted ascending by date. Days with no findings should have `count: 0` (so the chart has a continuous x-axis).
  ```json
  "daily_findings": [
    { "date": "2026-02-28", "count": 12 },
    { "date": "2026-03-01", "count": 18 },
    { "date": "2026-03-02", "count": 0 },
    { "date": "2026-03-03", "count": 7 }
  ]
  ```

#### Tile 8: Confidence Trend (line chart)
- **Displays:** A line chart showing the average confidence score per day. Y-axis is 0 to 1 (displayed as 0% to 100%).
- **I need:** An array sorted ascending by date. Days with no findings can have `avg_confidence: null` -- the FE filters those out.
  ```json
  "confidence_trend": [
    { "date": "2026-02-28", "avg_confidence": 0.72 },
    { "date": "2026-03-01", "avg_confidence": 0.65 },
    { "date": "2026-03-02", "avg_confidence": null },
    { "date": "2026-03-03", "avg_confidence": 0.81 }
  ]
  ```

---

### Row 4: Findings by Category + Trigger Outcomes

Tiles 9 and 10 are unrelated, but both are lightweight aggregations.

#### Tile 9: Findings by Category (donut chart)
- **Displays:** A donut chart showing how many findings belong to each category. Center label shows total count.
- **I need:** A key-value map of category name to count.
  ```json
  "by_category": {
    "models": 42,
    "apis": 28,
    "research": 15,
    "benchmarks": 8
  }
  ```

#### Tile 10: Trigger Outcomes (donut chart)
- **Displays:** A donut chart showing how many triggers ended in each status. Center label shows total trigger count.
- **I need:** A key-value map of trigger status to count. Include all statuses even if count is 0.
  ```json
  "trigger_status_counts": {
    "completed": 42,
    "failed": 5,
    "partial": 3,
    "completed_empty": 8,
    "running": 1,
    "pending": 0
  }
  ```
- **Possible statuses:** `completed`, `failed`, `partial`, `completed_empty`, `running`, `pending`

---

### Row 5: Top Sources + Agent Performance

Both are horizontal bar charts comparing counts across a dimension.

#### Tile 11: Top Sources by Findings (horizontal bar chart)
- **Displays:** Which sources produced the most findings. Y-axis shows source display names.
- **I need:** An array of top 5-8 sources, sorted descending by count. Both slug and display name are needed.
  ```json
  "findings_by_source": [
    { "source_name": "openai-blog", "display_name": "OpenAI Blog", "count": 87 },
    { "source_name": "arxiv-ml", "display_name": "ArXiv ML Feed", "count": 54 },
    { "source_name": "hf-papers", "display_name": "HuggingFace Papers", "count": 31 }
  ]
  ```

#### Tile 12: Agent Performance (horizontal bar chart)
- **Displays:** How many findings each agent type produced. Y-axis shows agent type names.
- **I need:** A key-value map of agent type to finding count.
  ```json
  "by_agent_type": {
    "openai_agent": 45,
    "anthropic_agent": 38,
    "google_agent": 22,
    "meta_agent": 15
  }
  ```

---

### Row 6: Recent Activity

#### Tile 13: Recent Activity (list)
- **Displays:** The last 10 trigger executions across all runs. Each entry shows: status badge, run name, trigger ID, findings count, snapshots count, and timestamp.
- **I need:** An array of the last 10 triggers, sorted descending by created_at.
  ```json
  "recent_triggers": [
    {
      "run_trigger_id": "uuid-1",
      "run_name": "Daily AI Scan",
      "status": "completed",
      "findings_count": 23,
      "snapshots_count": 5,
      "created_at": "2026-03-05T06:00:00Z"
    }
  ]
  ```
- **Possible statuses:** `completed`, `failed`, `partial`, `completed_empty`, `running`, `pending`

---

## Proposed API Endpoints

| Endpoint | Tiles Served | Data Fields |
|---|---|---|
| `GET /api/dashboard/kpi` | Tiles 1, 2, 3 | `total_findings`, `total_sources`, `runs_overview` |
| `GET /api/dashboard/charts` | Tiles 6, 7, 8, 9, 12 | `confidence_distribution`, `daily_findings`, `confidence_trend`, `by_category`, `by_agent_type` |
| `GET /api/dashboard/triggers` | Tiles 10, 13 | `trigger_status_counts`, `recent_triggers` |
| `GET /api/dashboard/sources` | Tile 11 | `findings_by_source` |
| `GET /api/digests/latest` | Tile 4 | Existing endpoint (needs `has_pdf` field) |
| `GET /scheduler` | Tile 5 | Existing endpoint (needs `frequency` field per job) |

The FE will call each endpoint independently with separate loading states -- no `Promise.all`.

---

## Expected Response Shapes

### `GET /api/dashboard/kpi`

```json
{
  "total_findings": 156,
  "total_sources": 12,
  "runs_overview": {
    "total_runs": 8,
    "enabled_runs": 6
  }
}
```

### `GET /api/dashboard/charts`

```json
{
  "confidence_distribution": {
    "high": 89,
    "medium": 45,
    "low": 22
  },
  "daily_findings": [
    { "date": "2026-02-28", "count": 12 },
    { "date": "2026-03-01", "count": 18 }
  ],
  "confidence_trend": [
    { "date": "2026-02-28", "avg_confidence": 0.72 },
    { "date": "2026-03-01", "avg_confidence": 0.65 }
  ],
  "by_category": {
    "models": 42,
    "apis": 28,
    "research": 15,
    "benchmarks": 8
  },
  "by_agent_type": {
    "openai_agent": 45,
    "anthropic_agent": 38,
    "google_agent": 22
  }
}
```

### `GET /api/dashboard/triggers`

```json
{
  "trigger_status_counts": {
    "completed": 42,
    "failed": 5,
    "partial": 3,
    "completed_empty": 8,
    "running": 1,
    "pending": 0
  },
  "recent_triggers": [
    {
      "run_trigger_id": "uuid-1",
      "run_name": "Daily AI Scan",
      "status": "completed",
      "findings_count": 23,
      "snapshots_count": 5,
      "created_at": "2026-03-05T06:00:00Z"
    }
  ]
}
```

### `GET /api/dashboard/sources`

```json
{
  "findings_by_source": [
    { "source_name": "openai-blog", "display_name": "OpenAI Blog", "count": 87 },
    { "source_name": "arxiv-ml", "display_name": "ArXiv ML Feed", "count": 54 }
  ]
}
```

### `GET /api/digests/latest` (existing)

```json
{
  "digest_id": "uuid",
  "digest_name": "Daily Digest 2026-03-05",
  "status": "completed",
  "has_pdf": true,
  "created_at": "2026-03-05T06:00:00Z"
}
```

### `GET /scheduler` (existing)

```json
{
  "running": true,
  "jobs": [
    {
      "id": "daily_digest",
      "name": "Daily AI Radar Digest",
      "frequency": "daily",
      "next_run": "2026-03-06T06:00:00+00:00"
    }
  ]
}
```
