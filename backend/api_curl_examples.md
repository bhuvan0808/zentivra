# Zentivra Backend API - cURL Examples & Response Reference

This file contains cURL requests with **success and error responses** for every endpoint.
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
- `401` errors: redirect to login page, preserve the current route for post-login navigation.
- `403` errors: show `response.detail` (account disabled, etc.).
- `4xx` errors: show `response.detail` (string) directly to the user.
- `422` errors: `response.detail` is an array -- map each item's `msg` to the field at `loc`.
- `5xx` errors: show a generic fallback like "Something went wrong. Please try again."
- Network failures (no response): show "Unable to reach the server."

## Setup

```bash
BASE_URL="http://localhost:8000"
```

---

## Auth API (`/api/auth`)

Auth endpoints are **public** -- no Authorization header required.

### 1) Signup

```bash
curl -X POST "$BASE_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kaustubh",
    "password": "securePass123",
    "display_name": "Kaustubh Paturi"
  }'
```

**Success (201):**

```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "kaustubh",
  "display_name": "Kaustubh Paturi",
  "auth_token": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "expires_at": "2026-03-05T14:30:00+00:00"
}
```

**Error -- username already taken (409):**

```json
{
  "detail": "Username already taken"
}
```

**Error -- validation failure (422):**

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 3 characters",
      "input": "ab"
    }
  ]
}
```

### 2) Login

```bash
curl -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kaustubh",
    "password": "securePass123"
  }'
```

**Success (200):**

```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "kaustubh",
  "display_name": "Kaustubh Paturi",
  "auth_token": "9c8d7e6f-5a4b-3c2d-1e0f-abcdef123456",
  "expires_at": "2026-03-05T14:30:00+00:00"
}
```

**Error -- invalid credentials (401):**

```json
{
  "detail": "Invalid username or password"
}
```

**Error -- account disabled (403):**

```json
{
  "detail": "Account is disabled"
}
```

### 3) Logout

```bash
curl -X POST "$BASE_URL/api/auth/logout" \
  -H "Authorization: Bearer f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

**Success (200):**

```json
{
  "message": "Logged out"
}
```

**Error -- missing or invalid token (401):**

```json
{
  "detail": "Invalid or expired session"
}
```

### 4) Get Current User

```bash
curl -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

**Success (200):**

```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "kaustubh",
  "display_name": "Kaustubh Paturi",
  "last_login": "2026-03-05T12:30:00+00:00",
  "created_at": "2026-03-05T08:00:00+00:00"
}
```

**Error -- expired session (401):**

```json
{
  "detail": "Session expired"
}
```

---

## Authorization Header (for all protected routes)

All endpoints below require the `Authorization` header:

```
Authorization: Bearer <auth_token>
```

If missing or invalid, the response is:

**Error -- missing header (422):**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "authorization"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**Error -- bad format (401):**

```json
{
  "detail": "Invalid authorization header format"
}
```

**Error -- expired or invalid token (401):**

```json
{
  "detail": "Invalid or expired session"
}
```

---

## Health Endpoints (public)

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

## Sources API (`/api/sources`) -- Protected

### 1) List Sources

```bash
curl -X GET "$BASE_URL/api/sources" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "source_id": "e5b5adf6-f19f-4fbe-8f64-0aeecf0f4b2c",
    "source_name": "openai-blog",
    "display_name": "OpenAI Blog",
    "agent_type": "model_provider",
    "url": "https://openai.com/blog",
    "is_enabled": true,
    "created_at": "2026-03-05T08:00:00+00:00",
    "updated_at": "2026-03-05T08:00:00+00:00"
  }
]
```

Returns empty array `[]` when no sources exist.

### 2) List Sources (with filters)

```bash
curl -X GET "$BASE_URL/api/sources?agent_type=model_provider&enabled=true" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):** same shape as above, filtered. Empty array if nothing matches.

**Error -- invalid agent_type (422):**

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
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "anthropic-news",
    "display_name": "Anthropic News",
    "agent_type": "model_provider",
    "url": "https://www.anthropic.com/news"
  }'
```

**Success (201):**

```json
{
  "source_id": "31e2c1b1-57dc-4b07-a660-2427f5d6b772",
  "source_name": "anthropic-news",
  "display_name": "Anthropic News",
  "agent_type": "model_provider",
  "url": "https://www.anthropic.com/news",
  "is_enabled": true,
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
      "loc": ["body", "source_name"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### 4) Get Source by UUID

```bash
curl -X GET "$BASE_URL/api/sources/31e2c1b1-57dc-4b07-a660-2427f5d6b772" \
  -H "Authorization: Bearer <auth_token>"
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
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_enabled": false,
    "display_name": "Anthropic News (Paused)"
  }'
```

**Success (200):**

```json
{
  "source_id": "31e2c1b1-57dc-4b07-a660-2427f5d6b772",
  "source_name": "anthropic-news",
  "display_name": "Anthropic News (Paused)",
  "agent_type": "model_provider",
  "url": "https://www.anthropic.com/news",
  "is_enabled": false,
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

### 6) Delete Source

```bash
curl -X DELETE "$BASE_URL/api/sources/31e2c1b1-57dc-4b07-a660-2427f5d6b772" \
  -H "Authorization: Bearer <auth_token>" -i
```

**Success:** HTTP `204 No Content` (empty body).

**Error -- source not found (404):**

```json
{
  "detail": "Source not found"
}
```

---

## Runs API (`/api/runs`) -- Protected

### 1) List Runs

```bash
curl -X GET "$BASE_URL/api/runs?limit=20" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
    "run_name": "Daily AI Scan",
    "description": "Nightly crawl of all model provider sources",
    "enable_pdf_gen": true,
    "enable_email_alert": false,
    "sources": ["e5b5adf6-f19f-4fbe-8f64-0aeecf0f4b2c"],
    "crawl_frequency": "daily",
    "crawl_depth": 2,
    "keywords": ["gpt", "llama"],
    "is_enabled": true,
    "created_at": "2026-03-05T10:20:00+00:00",
    "updated_at": "2026-03-05T10:20:00+00:00"
  }
]
```

Returns empty array `[]` when no runs exist.

### 2) Create Run

```bash
curl -X POST "$BASE_URL/api/runs" \
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "run_name": "Weekly Research",
    "description": "Research scout sweep",
    "sources": ["e5b5adf6-f19f-4fbe-8f64-0aeecf0f4b2c"],
    "crawl_depth": 2,
    "keywords": ["reasoning", "agent"]
  }'
```

**Success (201):** same shape as list item above.

### 3) Get Run by UUID

```bash
curl -X GET "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):** same shape as list item above.

**Error -- not found (404):**

```json
{
  "detail": "Run not found"
}
```

### 4) Update Run

```bash
curl -X PUT "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9" \
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_enabled": false,
    "crawl_depth": 3
  }'
```

**Success (200):** full run object with updated fields.

### 5) Delete Run

```bash
curl -X DELETE "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9" \
  -H "Authorization: Bearer <auth_token>" -i
```

**Success:** HTTP `204 No Content` (empty body).

### 6) Trigger a Run

```bash
curl -X POST "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9/trigger" \
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_method": "manual",
    "max_sources_per_agent": 3
  }'
```

**Success (202):**

```json
{
  "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
  "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
  "message": "Run triggered successfully. Pipeline executing in background.",
  "status": "pending"
}
```

**Note:** The body is optional. If omitted, defaults to `trigger_method: "manual"`.

**Error -- run not found (404):**

```json
{
  "detail": "Run not found"
}
```

**Error -- run is disabled (400):**

```json
{
  "detail": "Run is disabled"
}
```

### 7) List Trigger History for a Run

```bash
curl -X GET "$BASE_URL/api/runs/8ef7675f-a7bb-4979-b736-53fa775f06a9/triggers?limit=10" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
    "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
    "trigger_method": "manual",
    "status": "completed",
    "is_latest": true,
    "created_at": "2026-03-05T11:00:00+00:00",
    "updated_at": "2026-03-05T11:05:00+00:00",
    "findings_count": 12,
    "snapshots_count": 5
  }
]
```

Returns empty array `[]` when no triggers exist for this run.

---

## Run Triggers API (`/api/run-triggers`) -- Protected

### 1) Get Trigger by UUID

```bash
curl -X GET "$BASE_URL/api/run-triggers/d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
{
  "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
  "run_id": "8ef7675f-a7bb-4979-b736-53fa775f06a9",
  "trigger_method": "manual",
  "status": "completed",
  "is_latest": true,
  "created_at": "2026-03-05T11:00:00+00:00",
  "updated_at": "2026-03-05T11:05:00+00:00",
  "findings_count": 12,
  "snapshots_count": 5
}
```

**Error -- not found (404):**

```json
{
  "detail": "Run trigger not found"
}
```

### 2) List Findings for a Trigger

```bash
curl -X GET "$BASE_URL/api/run-triggers/d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8/findings?limit=50" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "finding_id": "c7219ce4-15f8-4f53-ad74-c84ef86f7549",
    "content": "Full text content...",
    "summary": "New model supports image and text reasoning.",
    "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
    "src_url": "https://example.com/ai-news/new-model",
    "category": "models",
    "confidence": 0.91,
    "created_at": "2026-03-05T11:03:00+00:00"
  }
]
```

Returns empty array `[]` when no findings exist.

### 3) List Snapshots for a Trigger

```bash
curl -X GET "$BASE_URL/api/run-triggers/d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8/snapshots" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "snapshot_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source_name": "OpenAI Blog",
    "total_findings": 3,
    "summary": "model_provider: 3 findings from OpenAI Blog",
    "status": "completed",
    "created_at": "2026-03-05T11:03:00+00:00"
  }
]
```

Returns empty array `[]` when no snapshots exist.

---

## Findings API (`/api/findings`) -- Protected

### 1) List Findings

```bash
curl -X GET "$BASE_URL/api/findings?page=1&page_size=20" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "finding_id": "c7219ce4-15f8-4f53-ad74-c84ef86f7549",
    "content": "Full text content of the finding...",
    "summary": "New model supports image and text reasoning.",
    "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
    "src_url": "https://example.com/ai-news/new-model",
    "category": "models",
    "confidence": 0.91,
    "created_at": "2026-03-05T10:21:40+00:00"
  }
]
```

Returns empty array `[]` when no findings match.

### 2) List Findings (with filters)

```bash
curl -X GET "$BASE_URL/api/findings?category=models&min_confidence=0.7&page=1&page_size=10" \
  -H "Authorization: Bearer <auth_token>"
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

### 3) Findings Stats

```bash
curl -X GET "$BASE_URL/api/findings/stats" \
  -H "Authorization: Bearer <auth_token>"
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
  }
}
```

### 4) Get Finding by UUID

```bash
curl -X GET "$BASE_URL/api/findings/c7219ce4-15f8-4f53-ad74-c84ef86f7549" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):** same shape as list item above.

**Error -- not found (404):**

```json
{
  "detail": "Finding not found"
}
```

---

## Digests API (`/api/digests`) -- Protected

### 1) List Digests

```bash
curl -X GET "$BASE_URL/api/digests?limit=30" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):**

```json
[
  {
    "digest_id": "5f2f9ac8-8e63-4b95-8f41-7f53a2288b89",
    "run_trigger_id": "d3e4f5a6-b7c8-9d0e-f1a2-b3c4d5e6f7a8",
    "pdf_path": "data/digests/zentivra_digest_2026-03-05.pdf",
    "html_path": "data/digests/zentivra_digest_2026-03-05.html",
    "status": "completed",
    "created_at": "2026-03-05T10:24:05+00:00"
  }
]
```

Returns empty array `[]` when no digests exist.

### 2) Get Latest Digest

```bash
curl -X GET "$BASE_URL/api/digests/latest" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):** same shape as list item above (single object).

**Error -- no digests exist (404):**

```json
{
  "detail": "No digests found"
}
```

### 3) Get Digest by UUID

```bash
curl -X GET "$BASE_URL/api/digests/5f2f9ac8-8e63-4b95-8f41-7f53a2288b89" \
  -H "Authorization: Bearer <auth_token>"
```

**Success (200):** same shape as list item above.

**Error -- not found (404):**

```json
{
  "detail": "Digest not found"
}
```

### 4) Download Digest PDF

```bash
curl -X GET "$BASE_URL/api/digests/5f2f9ac8-8e63-4b95-8f41-7f53a2288b89/pdf" \
  -H "Authorization: Bearer <auth_token>" \
  --output zentivra_digest.pdf
```

**Success (200):** binary PDF file (`Content-Type: application/pdf`).

**Error -- digest not found (404):**

```json
{
  "detail": "Digest not found"
}
```

**Error -- PDF not generated (404):**

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

## Config API (`/api/config`) -- Protected

### Get Current Config

```bash
curl -X GET "$BASE_URL/api/config/" \
  -H "Authorization: Bearer <auth_token>"
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
        "model_provider": { "provider": "gemini", "model": "gemini-2.0-flash-lite" }
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

### Update Config (JSON Body)

```bash
curl -X PUT "$BASE_URL/api/config/" \
  -H "Authorization: Bearer <auth_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "crawl": { "max_pages_per_domain": 100 },
    "llm": { "default_provider": "gemini" }
  }'
```

**Success (200):** full config with defaults filled in.

### Upload Config File

```bash
curl -X POST "$BASE_URL/api/config/upload" \
  -H "Authorization: Bearer <auth_token>" \
  -F "file=@config.yaml"
```

**Success (200):** same shape as GET.

**Error -- invalid YAML (422):**

```json
{
  "detail": "Invalid YAML: mapping values are not allowed here ..."
}
```

**Error -- unsupported format (422):**

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
  const token = localStorage.getItem("auth_token");
  if (token) {
    options.headers = {
      ...options.headers,
      "Authorization": `Bearer ${token}`,
    };
  }

  try {
    const res = await fetch(url, options);

    if (res.ok) {
      if (res.status === 204) return null;
      return await res.json();
    }

    const err = await res.json();

    if (res.status === 401) {
      // Session expired or invalid -- redirect to login
      const currentPath = window.location.pathname;
      localStorage.removeItem("auth_token");
      window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      throw new Error(err.detail || "Session expired");
    }

    if (res.status === 422 && Array.isArray(err.detail)) {
      const messages = err.detail.map(e => e.msg);
      throw new Error(messages.join(". "));
    }

    throw new Error(err.detail || "Something went wrong");

  } catch (e) {
    if (e instanceof TypeError) {
      throw new Error("Unable to reach the server. Is the backend running?");
    }
    throw e;
  }
}
```

### Complete error detail messages by endpoint

| Endpoint | Status | `detail` message |
|---|---|---|
| `POST /api/auth/signup` | 409 | `"Username already taken"` |
| `POST /api/auth/login` | 401 | `"Invalid username or password"` |
| `POST /api/auth/login` | 403 | `"Account is disabled"` |
| Any protected route | 401 | `"Invalid or expired session"` |
| Any protected route | 401 | `"Session expired"` |
| Any protected route | 401 | `"Invalid authorization header format"` |
| Any protected route | 401 | `"Missing auth token"` |
| `GET /api/sources/{id}` | 404 | `"Source not found"` |
| `PUT /api/sources/{id}` | 404 | `"Source not found"` |
| `DELETE /api/sources/{id}` | 404 | `"Source not found"` |
| `GET /api/runs/{id}` | 404 | `"Run not found"` |
| `POST /api/runs/{id}/trigger` | 404 | `"Run not found"` |
| `POST /api/runs/{id}/trigger` | 400 | `"Run is disabled"` |
| `GET /api/run-triggers/{id}` | 404 | `"Run trigger not found"` |
| `GET /api/findings/{id}` | 404 | `"Finding not found"` |
| `GET /api/digests/latest` | 404 | `"No digests found"` |
| `GET /api/digests/{id}` | 404 | `"Digest not found"` |
| `GET /api/digests/{id}/pdf` | 404 | `"PDF not yet generated for this digest"` |
| `GET /api/digests/{id}/pdf` | 404 | `"PDF file not found on disk"` |
| `POST /api/config/upload` | 422 | `"Invalid JSON: ..."` / `"Invalid YAML: ..."` |
| `POST /api/config/upload` | 422 | `"Unsupported file format: '...'"` |
| Any `POST`/`PUT` with bad body | 422 | `[{loc, msg, type, input}, ...]` (array) |
| Any unhandled server error | 500 | `"Internal server error"` |
