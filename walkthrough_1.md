# Zentivra — Build Walkthrough

## Phases 1-5: Backend Complete ✅

### What's Built

| Phase | Components | Status |
|---|---|---|
| **Phase 1** | FastAPI + SQLAlchemy + Config + 12 API endpoints | ✅ |
| **Phase 2** | Fetcher, Extractor, Change Detector, Summarizer, Dedup, Ranker | ✅ |
| **Phase 3** | BaseAgent + 4 Agents (Competitor, Model Provider, Research, HF Benchmark) | ✅ |
| **Phase 4** | Digest Compiler + PDF/HTML Renderer + Email Service | ✅ |
| **Phase 5** | Orchestrator (parallel agents) + APScheduler (daily cron) | ✅ |

### LLM Providers Supported

| Provider | Model | Status |
|---|---|---|
| **Groq** (active) | `llama-3.3-70b-versatile` | ✅ Tested |
| OpenRouter | `meta-llama/llama-3.3-70b-instruct` | ✅ Configured |
| Gemini | `gemini-2.0-flash-lite` | ⚠️ Rate-limited on free tier |
| OpenAI | `gpt-4o-mini` | Ready (needs key) |
| Anthropic | `claude-sonnet-4-20250514` | Ready (needs key) |

---

## End-to-End Test Results

**All 8 pipeline steps passed with Groq (Llama 3.3 70B):**

| Step | Component | Result |
|---|---|---|
| 1. Fetch | [fetcher.py](file:///c:/Bhuvan/zentivra/backend/app/core/fetcher.py) → httpx | Fetched OpenAI blog page |
| 2. Extract | [extractor.py](file:///c:/Bhuvan/zentivra/backend/app/core/extractor.py) → trafilatura | Extracted text + title |
| 3. Change Detect | [change_detector.py](file:///c:/Bhuvan/zentivra/backend/app/core/change_detector.py) | First fetch marked as changed |
| 4. Summarize | [summarizer.py](file:///c:/Bhuvan/zentivra/backend/app/core/summarizer.py) → Groq API | Structured JSON summary returned |
| 5. Rank | [ranker.py](file:///c:/Bhuvan/zentivra/backend/app/core/ranker.py) → Groq API | **Impact: 77.5%**, Category: models |
| 6. Dedup | [dedup.py](file:///c:/Bhuvan/zentivra/backend/app/core/dedup.py) | 1 duplicate detected and removed |
| 7. Compile | [compiler.py](file:///c:/Bhuvan/zentivra/backend/app/digest/compiler.py) | Sections + narratives generated |
| 8. Output | [pdf_renderer.py](file:///c:/Bhuvan/zentivra/backend/app/digest/pdf_renderer.py) | HTML digest at [data/digests/zentivra_digest_2026-03-05.html](file:///c:/Bhuvan/zentivra/backend/data/digests/zentivra_digest_2026-03-05.html) |

### Files Created in Phase 2-5

**Core Pipeline** (`app/core/`):
- [rate_limiter.py](file:///c:/Bhuvan/zentivra/backend/app/core/rate_limiter.py) — Per-domain token bucket
- [fetcher.py](file:///c:/Bhuvan/zentivra/backend/app/core/fetcher.py) — httpx + Playwright + robots.txt
- [extractor.py](file:///c:/Bhuvan/zentivra/backend/app/core/extractor.py) — trafilatura + BeautifulSoup + RSS
- [change_detector.py](file:///c:/Bhuvan/zentivra/backend/app/core/change_detector.py) — SHA256 hashing + diffing
- [summarizer.py](file:///c:/Bhuvan/zentivra/backend/app/core/summarizer.py) — 5-provider LLM with retry
- [dedup.py](file:///c:/Bhuvan/zentivra/backend/app/core/dedup.py) — Hash + semantic similarity
- [ranker.py](file:///c:/Bhuvan/zentivra/backend/app/core/ranker.py) — Impact scoring formula

**Agent Workers** (`app/agents/`):
- [base_agent.py](file:///c:/Bhuvan/zentivra/backend/app/agents/base_agent.py) — Shared pipeline interface
- [competitor_watcher.py](file:///c:/Bhuvan/zentivra/backend/app/agents/competitor_watcher.py)
- [model_provider_watcher.py](file:///c:/Bhuvan/zentivra/backend/app/agents/model_provider_watcher.py)
- [research_scout.py](file:///c:/Bhuvan/zentivra/backend/app/agents/research_scout.py)
- [hf_benchmark_tracker.py](file:///c:/Bhuvan/zentivra/backend/app/agents/hf_benchmark_tracker.py)

**Digest & Delivery** (`app/digest/`, `app/notifications/`):
- [compiler.py](file:///c:/Bhuvan/zentivra/backend/app/digest/compiler.py) — Full compilation pipeline
- [pdf_renderer.py](file:///c:/Bhuvan/zentivra/backend/app/digest/pdf_renderer.py) — Jinja2 + WeasyPrint
- [digest.html](file:///c:/Bhuvan/zentivra/backend/app/digest/templates/digest.html) — PDF template
- [email_service.py](file:///c:/Bhuvan/zentivra/backend/app/notifications/email_service.py) — SendGrid + SMTP

**Orchestration** (`app/scheduler/`):
- [orchestrator.py](file:///c:/Bhuvan/zentivra/backend/app/scheduler/orchestrator.py) — Run manager
- [scheduler.py](file:///c:/Bhuvan/zentivra/backend/app/scheduler/scheduler.py) — APScheduler cron

### Next: Phase 6 — Web UI (Next.js)
