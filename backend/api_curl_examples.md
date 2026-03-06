# Zentivra Backend API - cURL Examples & Response Reference

This file contains cURL requests with **both success and error responses** for every endpoint.
Use this as a contract reference when building UI components.

## Response Shape Convention

**Success responses** return the resource directly (object or array) with a 2xx status code.

**Error responses** always have this shape:

```json
{
  "detail": "Human-readable error message"
}
```

Except **422 Validation Errors**, which return:

```json
{
  "detail": [
    {
      "type": "error_type",
      "loc": ["body", "field_name"],
      "msg": "Human-readable field error",
      "input": "<the bad value>"
    }
  ]
}
```

**UI handling rule of thumb:**
- `4xx` errors: show `response.detail` (string) directly to the user.
- `422` errors: `response.detail` is an array -- map each item's `msg` to the field at `loc`.
- `5xx` errors: show a generic fallback like "Something went wrong. Please try again."
- Network failures (no response): show "Unable to reach the server."

## Setup

```bash
BASE_URL="http://localhost:8000"
```

---

## Health Endpoints

### 1) Root Health Check

```bash
curl -X GET "$BASE_URL/"
```

**Success (200):**

```json
{
  "name": "Zentivra - Frontier AI Radar",
  "version": "1.0.0",
  "status": "operational",
  "llm_provider": "groq",
  "email_configured": true
}
```

### 2) Detailed Health

```bash
curl -X GET "$BASE_URL/health"
```

**Success (200):**

```json
{
  "status": "healthy",
  "database": "connected",
  "llm_provider": "groq",
  "email_configured": true,
  "environment": "development"
}
```

### 3) Scheduler Status

```bash
curl -X GET "$BASE_URL/scheduler"
```

**Success (200):**

```json
{
  "running": true,
  "jobs": [
    {
      "id": "daily_digest",
      "name": "Daily AI Radar Digest",
      "next_run": "2026-03-06T06:00:00+00:00"
    }
  ]
}
```

---

## Sources API (`/api/sources`)

### 1) List Sources

```bash
curl -X GET "$BASE_URL/api/sources"
```

**Success (200):**

```json
[
  {
    "id": "e5b5adf6-f19f-4fbe-8f64-0aeecf0f4b2c",
    "name": "OpenAI Blog",
    "agent_type": "model_provider",
    "url": "https://openai.com/blog",
    "feed_url": "https://openai.com/blog/rss.xml",
    "css_selectors": null,
    "keywords": ["gpt", "api", "release"],
    "rate_limit_rpm": 10,
    "crawl_depth": 1,
    "enabled": true,
    "created_at": "2026-03-05T08:00:00+00:00",
    "updated_at": "2026-03-05T08:00:00+00:00"
  }
]
```

Returns an empty array `[]` when no sources exist (not an error).

### 2) List Sources (with filters)

```bash
curl -X GET "$BASE_URL/api/sources?agent_type=model_provider&enabled=true"
```

**Success (200):** same shape as above, filtered rows. Empty array if nothing matches.

**Error -- invalid `agent_type` value (422):**

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "agent_type"],
      "msg": "Input should be 'competitor', 'model_provider', 'research' or 'hf_benchmark'",
      "input": "invalid_type"
    }
  ]
}
```

### 3) Create Source

```bash
curl -X POST "$BASE_URL/api/sources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Anthropic News",
    "agent_type": "model_provider",
    "url": "https://www.anthropic.com/news",
    "feed_url": null,
    "css_selectors": {"article": ".news-item"},
    "keywords": ["claude", "model", "api"],
    "rate_limit_rpm": 10,
    "crawl_depth": 1,
    "enabled": true
  }'
```

**Success (201):**

```json
{
  "id": "31e2c1b1-57dc-4b07-a660-2427f5d6b772",
  "name": "Anthropic News",
  "agent_type": "model_provider",
  "url": "https://www.anthropic.com/news",
  "feed_url": null,
  "css_selectors": {"article": ".news-item"},
  "keywords": ["claude", "model", "api"],
  "rate_limit_rpm": 10,
  "crawl_depth": 1,
  "enabled": true,
  "created_at": "2026-03-05T10:15:41.124000+00:00",
  "updated_at": "2026-03-05T10:15:41.124000+00:00"
}
```

**Error -- missing required field (422):**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

**Error -- name too short (422):**

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "name"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

**Error -- rate_limit_rpm out of range (422):**

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "rate_limit_rpm"],
      "msg": "Input should be greater than or equal to 1",
      "input": 0
    }
  ]
}
```

### 4) Get Source by ID

```bash
curl -X GET "$BASE_URL/api/sources/31e2c1b1-57dc-4b07-a660-2427f5d6b772"
```

**Success (200):** same shape as the create response above.

**Error -- not found (404):**

```json
{
  "detail": "Source not found"
}
```

### 5) Update Source

```bash
curl -X PUT "$BASE_URL/api/sources/31e2c1b1-57dc-4b07-a660-2427f5d6b772" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false,
    "rate_limit_rpm": 5
  }'
```

**Success (200):**

```json
{
  "id": "31e2c1b1-57dc-4b07-a660-2427f5d6b772",
  "name": "Anthropic News",
  "agent_type": "model_provider",
  "url": "https://www.anthropic.com/news",
  "feed_url": null,
  "css_selectors": {"article": ".news-item"},
  "keywords": ["claude", "model", "api"],
  "rate_limit_rpm": 5,
  "crawl_depth": 1,
  "enabled": false,
  "created_at": "2026-03-05T10:15:41.124000+00:00",
  "updated_at": "2026-03-05T10:18:10.332000+00:00"
}
```

**Error -- source not found (404):**

```json
{
  "detail": "Source not found"
}
```

**Error -- invalid field value (422):**

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "crawl_depth"],
      "msg": "Input should be greater than or equal to 1",
      "input": 0
    }
  ]
}
```

### 6) Delete Source

```bash
curl -X DELETE "$BASE_URL/api/sources/31e2c1b1-57dc-4b07-a660-2427f5d6b772" -i
```

**Success:** HTTP `204 No Content` (empty body).

**Error -- source not found (404):**

```json
{
  "detail": "Source not found"
}
```

---

## Runs API (`/api/runs`)

### 1) List Runs

```bash
curl -X GET "$BASE_URL/api/runs?limit=20"
```

**Success (200):**

```json
[
  {
    "id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
    "started_at": "2026-03-05T10:20:00.000000+00:00",
    "completed_at": "2026-03-05T10:23:44.000000+00:00",
    "status": "completed",
    "agent_statuses": {
      "competitor": "completed (6 findings)",
      "model_provider": "completed (4 findings)",
      "research": "completed (3 findings)",
      "hf_benchmark": "completed (2 findings)"
    },
    "total_findings": 15,
    "error_log": null,
    "log_path": "data/logs/8ef7675f-a7bb-4979-b736-53fa775f06a9.ndjson",
    "triggered_by": "manual"
  }
]
```

Returns empty array `[]` when no runs exist.

**`status` field values:** `"pending"`, `"running"`, `"completed"`, `"failed"`, `"partial"`

### 2) Get Run by ID

```bash
curl -X GET "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9"
```

**Success (200) -- while running:**

```json
{
  "id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
  "started_at": "2026-03-05T10:24:11.000000+00:00",
  "completed_at": null,
  "status": "running",
  "agent_statuses": {
    "competitor": "completed (5 findings)",
    "model_provider": "pending",
    "research": "pending",
    "hf_benchmark": "pending"
  },
  "total_findings": 0,
  "error_log": null,
  "log_path": "data/logs/8ef7675f-a7bb-4979-b736-53fa775f06a9.ndjson",
  "triggered_by": "manual"
}
```

**Success (200) -- failed run (no LLM configured):**

```json
{
  "id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
  "started_at": "2026-03-05T10:24:11.000000+00:00",
  "completed_at": "2026-03-05T10:24:55.000000+00:00",
  "status": "failed",
  "agent_statuses": null,
  "total_findings": 0,
  "error_log": "No LLM provider configured",
  "log_path": "data/logs/8ef7675f-a7bb-4979-b736-53fa775f06a9.ndjson",
  "triggered_by": "manual"
}
```

**Success (200) -- partial run (some agents failed):**

```json
{
  "id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
  "started_at": "2026-03-05T10:24:11.000000+00:00",
  "completed_at": "2026-03-05T10:28:33.000000+00:00",
  "status": "partial",
  "agent_statuses": {
    "competitor": "completed (6 findings)",
    "model_provider": "completed (4 findings)",
    "research": "failed: Timeout fetching arxiv RSS after 30s",
    "hf_benchmark": "completed (2 findings)"
  },
  "total_findings": 12,
  "error_log": null,
  "log_path": "data/logs/8ef7675f-a7bb-4979-b736-53fa775f06a9.ndjson",
  "triggered_by": "manual"
}
```

**Error -- not found (404):**

```json
{
  "detail": "Run not found"
}
```

### 3) Trigger Run

```bash
curl -X POST "$BASE_URL/api/runs/trigger"
```

**Success (202):**

```json
{
  "run_id": "2ac8d104-9a3e-4912-9690-b3576e909676",
  "message": "Run triggered successfully. Pipeline executing in background.",
  "status": "pending"
}
```

**Error -- another run is already active (409):**

```json
{
  "detail": "Run 8ef7675f-a7bb-4979-b736-53fa775f06a9 is already in progress."
}
```

### 4) Get Run Execution Logs

```bash
curl -X GET "$BASE_URL/api/runs/2ac8d104-9a3e-4912-9690-b3576e909676/logs"
```

With filters:

```bash
curl -X GET "$BASE_URL/api/runs/2ac8d104-9a3e-4912-9690-b3576e909676/logs?agent=competitor&level=ERROR&tail=50"
```

**Success (200):**

```json
[
  {
    "ts": "2026-03-05T10:20:01.123000+00:00",
    "run_id": "2ac8d104-9a3e-4912-9690-b3576e909676",
    "level": "INFO",
    "agent": null,
    "phase": "init",
    "event": "pipeline_run_start"
  },
  {
    "ts": "2026-03-05T10:20:01.234000+00:00",
    "run_id": "2ac8d104-9a3e-4912-9690-b3576e909676",
    "level": "INFO",
    "agent": "competitor",
    "phase": "fetch",
    "event": "url_fetched",
    "url": "https://openai.com/blog",
    "status_code": 200,
    "content_length": 48210,
    "method": "httpx",
    "progress": "1/3"
  },
  {
    "ts": "2026-03-05T10:20:05.567000+00:00",
    "run_id": "2ac8d104-9a3e-4912-9690-b3576e909676",
    "level": "INFO",
    "agent": "competitor",
    "phase": "finding",
    "event": "finding_created",
    "title": "OpenAI launches GPT-5 Turbo with native tool use",
    "confidence": 0.92,
    "category": "models"
  },
  {
    "ts": "2026-03-05T10:20:12.890000+00:00",
    "run_id": "2ac8d104-9a3e-4912-9690-b3576e909676",
    "level": "ERROR",
    "agent": "research",
    "phase": "error",
    "event": "url_processing_error",
    "url": "https://arxiv.org/rss/cs.CL",
    "error": "Timeout: connection timed out after 30s"
  }
]
```

Returns empty array `[]` when no log entries match the filters.

**Error -- run not found (404):**

```json
{
  "detail": "Run not found"
}
```

**Error -- no logs available (404):**

```json
{
  "detail": "No logs available for this run"
}
```

**Error -- log file missing from disk (404):**

```json
{
  "detail": "Log file not found on disk"
}
```

---

## Findings API (`/api/findings`)

### 1) List Findings

```bash
curl -X GET "$BASE_URL/api/findings?page=1&page_size=20"
```

**Success (200):**

```json
[
  {
    "id": "c7219ce4-15f8-4f53-ad74-c84ef86f7549",
    "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
    "source_id": "e5b5adf6-f19f-4fbe-8f64-0aeecf0f4b2c",
    "title": "Provider launched new multimodal model",
    "date_detected": "2026-03-05T10:21:40.000000+00:00",
    "source_url": "https://example.com/ai-news/new-model",
    "publisher": "Example AI",
    "category": "models",
    "summary_short": "New model supports image and text reasoning.",
    "summary_long": "Detailed summary of release, capabilities, and pricing details.",
    "why_it_matters": "Improves enterprise workflow automation quality and speed.",
    "evidence": {"claims": ["SOTA on benchmark X"]},
    "confidence": 0.91,
    "tags": ["model-release", "multimodal"],
    "entities": {"companies": ["Example AI"], "models": ["Model-X"], "datasets": []},
    "impact_score": 8.7,
    "is_duplicate": false,
    "cluster_id": null
  }
]
```

Returns empty array `[]` when no findings match.

**`category` field values:** `"models"`, `"apis"`, `"pricing"`, `"benchmarks"`, `"safety"`, `"tooling"`, `"research"`, `"other"`

### 2) List Findings (with filters + search)

```bash
curl -X GET "$BASE_URL/api/findings?category=models&min_confidence=0.7&search=multimodal&include_duplicates=false&page=1&page_size=10"
```

**Success (200):** same shape as above, filtered.

**Error -- invalid category (422):**

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "category"],
      "msg": "Input should be 'models', 'apis', 'pricing', 'benchmarks', 'safety', 'tooling', 'research' or 'other'",
      "input": "invalid"
    }
  ]
}
```

**Error -- min_confidence out of range (422):**

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "min_confidence"],
      "msg": "Input should be less than or equal to 1",
      "input": 5.0
    }
  ]
}
```

### 3) Findings Stats

```bash
curl -X GET "$BASE_URL/api/findings/stats"
```

**Success (200):**

```json
{
  "total_findings": 32,
  "by_category": {
    "models": 14,
    "apis": 7,
    "research": 6,
    "benchmarks": 5
  },
  "avg_impact_score": 6.842
}
```

**Success (200) -- no findings yet:**

```json
{
  "total_findings": 0,
  "by_category": {},
  "avg_impact_score": 0.0
}
```

Stats with optional run filter:

```bash
curl -X GET "$BASE_URL/api/findings/stats?run_id=8ef7675f-a7bb-4979-b736-53fa775f06a9"
```

### 4) Get Finding by ID

```bash
curl -X GET "$BASE_URL/api/findings/c7219ce4-15f8-4f53-ad74-c84ef86f7549"
```

**Success (200):** same shape as the list item above.

**Error -- not found (404):**

```json
{
  "detail": "Finding not found"
}
```

---

## Digests API (`/api/digests`)

### 1) List Digests

```bash
curl -X GET "$BASE_URL/api/digests?limit=30"
```

**Success (200):**

```json
[
  {
    "id": "5f2f9ac8-8e63-4b95-8f41-7f53a2288b89",
    "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
    "date": "2026-03-05",
    "executive_summary": "Major model updates and benchmark movements detected.",
    "pdf_path": "output/digests/zentivra_digest_2026-03-05.pdf",
    "email_sent": true,
    "sent_at": "2026-03-05T10:24:18.000000+00:00",
    "recipients": ["cto@company.com", "strategy@company.com"],
    "total_findings": 15,
    "created_at": "2026-03-05T10:24:05.000000+00:00"
  }
]
```

Returns empty array `[]` when no digests exist.

### 2) Get Latest Digest

```bash
curl -X GET "$BASE_URL/api/digests/latest"
```

**Success (200):** same shape as the list item above (single object, not array).

**Error -- no digests exist yet (404):**

```json
{
  "detail": "No digests found"
}
```

### 3) Get Digest by ID

```bash
curl -X GET "$BASE_URL/api/digests/5f2f9ac8-8e63-4b95-8f41-7f53a2288b89"
```

**Success (200):** same shape as the list item above.

**Error -- not found (404):**

```json
{
  "detail": "Digest not found"
}
```

### 4) Download Digest PDF

```bash
curl -X GET "$BASE_URL/api/digests/5f2f9ac8-8e63-4b95-8f41-7f53a2288b89/pdf" \
  --output zentivra_digest.pdf
```

**Success (200):** binary PDF file (`Content-Type: application/pdf`).

**Error -- digest not found (404):**

```json
{
  "detail": "Digest not found"
}
```

**Error -- PDF not generated yet (404):**

```json
{
  "detail": "PDF not yet generated for this digest"
}
```

**Error -- PDF file missing from disk (404):**

```json
{
  "detail": "PDF file not found on disk"
}
```

---

## Config API (`/api/config`)

### Get Current Config

```bash
curl http://localhost:8000/api/config/
```

**Success (200):**

```json
{
  "config": {
    "crawl": {
      "max_pages_per_domain": 50,
      "request_timeout_seconds": 30,
      "max_concurrent_urls": 5,
      "respect_robots_txt": true
    },
    "schedule": {
      "run_time": "06:00",
      "timezone": "Asia/Kolkata",
      "enabled": true
    },
    "llm": {
      "default_provider": "groq",
      "default_model": "llama-3.3-70b-versatile",
      "agents": {
        "competitor": { "provider": "groq", "model": "llama-3.3-70b-versatile" },
        "model_provider": { "provider": "gemini", "model": "gemini-2.0-flash-lite" },
        "research": { "provider": "groq", "model": "llama-3.3-70b-versatile" },
        "hf_benchmark": { "provider": "gemini", "model": "gemini-2.0-flash-lite" }
      }
    },
    "deduplication": {
      "similarity_threshold": 0.85,
      "min_confidence": 0.3
    },
    "ranking": {
      "relevance_weight": 0.35,
      "novelty_weight": 0.25,
      "credibility_weight": 0.2,
      "actionability_weight": 0.2
    },
    "digest": {
      "max_findings_per_section": 15,
      "include_appendix": true
    },
    "notifications": {
      "email_recipients": [],
      "send_on_empty": false
    }
  },
  "updated_at": "2026-03-05T10:30:00Z"
}
```

> **Note:** If no config has been saved yet, the response returns all defaults with `"updated_at": null`.

---

### Update Config (JSON Body)

```bash
curl -X PUT http://localhost:8000/api/config/ \
  -H "Content-Type: application/json" \
  -d '{
    "crawl": {
      "max_pages_per_domain": 100,
      "request_timeout_seconds": 45
    },
    "llm": {
      "default_provider": "gemini",
      "default_model": "gemini-2.0-flash-lite",
      "agents": {
        "competitor": { "provider": "groq", "model": "llama-3.3-70b-versatile" },
        "research": { "provider": "gemini", "model": "gemini-2.0-flash-lite" }
      }
    },
    "deduplication": {
      "similarity_threshold": 0.90
    }
  }'
```

**Success (200):**

```json
{
  "config": {
    "crawl": {
      "max_pages_per_domain": 100,
      "request_timeout_seconds": 45,
      "max_concurrent_urls": 5,
      "respect_robots_txt": true
    },
    "schedule": {
      "run_time": "06:00",
      "timezone": "Asia/Kolkata",
      "enabled": true
    },
    "llm": {
      "default_provider": "gemini",
      "default_model": "gemini-2.0-flash-lite",
      "agents": {
        "competitor": { "provider": "groq", "model": "llama-3.3-70b-versatile" },
        "research": { "provider": "gemini", "model": "gemini-2.0-flash-lite" }
      }
    },
    "deduplication": {
      "similarity_threshold": 0.9,
      "min_confidence": 0.3
    },
    "ranking": {
      "relevance_weight": 0.35,
      "novelty_weight": 0.25,
      "credibility_weight": 0.2,
      "actionability_weight": 0.2
    },
    "digest": {
      "max_findings_per_section": 15,
      "include_appendix": true
    },
    "notifications": {
      "email_recipients": [],
      "send_on_empty": false
    }
  },
  "updated_at": "2026-03-05T11:00:00Z"
}
```

**Failure — invalid value (422):**

```json
{
  "detail": [
    {
      "loc": ["body", "crawl", "max_pages_per_domain"],
      "msg": "Input should be greater than or equal to 1",
      "type": "greater_than_equal",
      "input": -5
    }
  ]
}
```

---

### Upload Config File (JSON or YAML)

```bash
curl -X POST http://localhost:8000/api/config/upload \
  -F "file=@config.yaml"
```

**Success (200):** Same response shape as PUT — full config with defaults filled in.

**Failure — invalid YAML (422):**

```json
{
  "detail": "Invalid YAML: mapping values are not allowed here ..."
}
```

**Failure — invalid JSON (422):**

```json
{
  "detail": "Invalid JSON: Expecting ',' delimiter at line 5"
}
```

**Failure — unsupported format (422):**

```json
{
  "detail": "Unsupported file format: 'txt'. Use .json, .yaml, or .yml"
}
```

---

## Error Reference (for UI developers)

### How to parse errors in the frontend

```javascript
async function apiCall(url, options = {}) {
  try {
    const res = await fetch(url, options);

    if (res.ok) {
      if (res.status === 204) return null;       // DELETE success
      return await res.json();                    // normal success
    }

    // 4xx / 5xx
    const err = await res.json();

    if (res.status === 422 && Array.isArray(err.detail)) {
      // Validation error -- join field messages
      const messages = err.detail.map(e => e.msg);
      throw new Error(messages.join(". "));
    }

    // 400, 404, 409, etc. -- detail is a string
    throw new Error(err.detail || "Something went wrong");

  } catch (e) {
    if (e instanceof TypeError) {
      // Network error -- fetch itself failed
      throw new Error("Unable to reach the server. Is the backend running?");
    }
    throw e;
  }
}
```

### Complete error detail messages by endpoint

| Endpoint | Status | `detail` message |
|---|---|---|
| `GET /api/sources/{id}` | 404 | `"Source not found"` |
| `PUT /api/sources/{id}` | 404 | `"Source not found"` |
| `DELETE /api/sources/{id}` | 404 | `"Source not found"` |
| `GET /api/runs/{id}` | 404 | `"Run not found"` |
| `POST /api/runs/trigger` | 409 | `"Run {id} is already in progress."` |
| `GET /api/runs/{id}/logs` | 404 | `"Run not found"` |
| `GET /api/runs/{id}/logs` | 404 | `"No logs available for this run"` |
| `GET /api/runs/{id}/logs` | 404 | `"Log file not found on disk"` |
| `GET /api/findings/{id}` | 404 | `"Finding not found"` |
| `GET /api/digests/latest` | 404 | `"No digests found"` |
| `GET /api/digests/{id}` | 404 | `"Digest not found"` |
| `GET /api/digests/{id}/pdf` | 404 | `"Digest not found"` |
| `GET /api/digests/{id}/pdf` | 404 | `"PDF not yet generated for this digest"` |
| `GET /api/digests/{id}/pdf` | 404 | `"PDF file not found on disk"` |
| `PUT /api/config/` | 422 | Validation error (e.g. out-of-range value) |
| `POST /api/config/upload` | 422 | `"Invalid JSON: ..."` or `"Invalid YAML: ..."` |
| `POST /api/config/upload` | 422 | `"Unsupported file format: '...'. Use .json, .yaml, or .yml"` |
| Any `POST`/`PUT` with bad body | 422 | `[{loc, msg, type, input}, ...]` (array) |
| Any unhandled server error | 500 | `{"detail": "Internal Server Error"}` |
