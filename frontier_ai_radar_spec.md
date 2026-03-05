# Frontier AI Radar – Daily Multi‑Agent Intelligence System

1. Product Overview

---

Goal:
Create a daily “Frontier AI Radar” that automatically tracks:

- Competitor releases (product/platform updates)
- Foundation model provider releases (model launches, API updates, pricing, evaluation claims)
- Latest research publications (LLMs / multimodal / agents / evaluation / alignment)
- Hugging Face benchmarking results (leaderboards, new SOTA claims, dataset/task trends)
- Produce an executive + technical digest as a PDF delivered by email.

Non‑Goals (Hackathon Scope):

- Training models
- Full web-scale crawling
- Real-time monitoring (daily batch is sufficient)

2. System Requirements

---

Functional Requirements

FR1 – Configurable sources per agent
Each agent reads a configuration file (YAML/JSON) listing:

- URLs (and optional RSS feeds / API endpoints)
- Crawl frequency (default daily)
- Crawl depth / include-exclude rules
- Parsing hints (CSS selectors, sitemap paths, “release notes” keywords)

FR2 – Robust extraction
System must handle:

- HTML pages
- RSS / Atom feeds
- PDF release notes (optional)
- “Changelog” pages with pagination

FR3 – Summarization
Each agent produces:

- Top updates (bullet list)
- What changed (before/after if detectable)
- Why it matters (impact summary)
- Confidence score + citations (source URLs)

FR4 – Deduplication and clustering

- Merge duplicates across sources
- Cluster by topic:
  Models, APIs, Pricing, Benchmarks, Safety, Tooling

FR5 – PDF generation
Daily PDF includes:

- Cover page with date and audience
- Executive summary (1 page)
- Deep dive sections:
  Competitors
  Model Providers
  Research
  HF Benchmarks
- Appendix with source links and snippets (optional)

FR6 – Email delivery
Send to:

- Primary user
- Configurable research distribution list

Email includes:

- Executive summary snippet
- PDF attachment
- Links to web dashboard

FR7 – Web UI
Minimal UI for hackathon scoring:

- Manage sources (add/edit URLs)
- Trigger run manually and see history
- Browse daily digests + search
- Per-agent logs and failures

## Non‑Functional Requirements

NFR1 Reliability

- Partial failure tolerant (one agent can fail without blocking digest)

NFR2 Observability

- Logs
- Metrics
- Trace per URL

NFR3 Rate limiting

- Respect robots.txt
- Throttle requests per domain

NFR4 Security

- Store secrets for email credentials and API keys securely

NFR5 Cost control

- Caching
- Incremental diffs
- Avoid re‑summarizing identical pages

3. High-Level Architecture

---

Components:

- Orchestrator (Scheduler + Run Manager)
- Agent Workers (4 crawlers + 1 compiler/sender)
- Fetcher Layer (HTTP + headless browser fallback)
- Extractor Layer (HTML to text, PDF to text, metadata)
- Change Detector (diff, fingerprinting, canonicalization)
- Summarizer (LLM summarization + structured output)
- Knowledge Store
  Raw snapshots
  Extracted text
  Structured findings
- Digest Compiler
- Ranking + narrative synthesis
- PDF Renderer
- Notification Service (Email)
- Web UI

Data Flow (Daily Run):
Scheduler → Run Manager → Agents 1–4 (parallel)
Agents produce findings → Deduplicate/Cluster → Digest Agent → PDF → Email

4. Agent Specifications

---

Shared Agent Interface

Inputs:

- run_id
- agent_config (URLs, rules, rate limits)
- since_timestamp (incremental scanning)

Outputs:
findings[] schema:

- title
- date_detected
- source_url
- publisher
- category
- summary_short
- summary_long
- why_it_matters
- evidence
- confidence
- tags
- entities (company/model/dataset)
- diff_hash

5. Agent #1 – Competitor Release Watcher

---

Purpose:
Track competitor sites (blogs, changelogs, docs release notes) and summarize releases.

Inputs:

- competitor name
- release URLs
- RSS feeds
- CSS selectors
- keywords
- domain rate limit

Logic:

- Discover pages (RSS → sitemap → crawl)
- Fetch page content
- Extract canonical text and metadata
- Detect changes via diff
- Summarize changes
- Rank impact (GA/pricing/API/security mentions)

6. Agent #2 – Foundation Model Provider Release Watcher

---

Tracks:

- Model releases
- API updates
- Pricing changes
- Evaluation claims

Outputs include:

- Model version
- Modalities
- Context length
- Tool use features
- Pricing
- Safety updates
- Benchmark claims

Optional:
Create verification tasks for benchmark claims.

7. Agent #3 – Research Publication Scout

---

Sources:

- arXiv queries (CS.CL, CS.LG, stat.ML)
- Semantic Scholar queries
- OpenReview conferences
- Curated research lab blogs

Outputs:

- Core contribution
- Novelty vs prior work
- Practical implications
- Relevance score

Relevance Factors:

- New benchmarks
- Data-centric techniques
- Agent workflows
- Multimodal reasoning
- Safety/alignment research

8. Agent #4 – Hugging Face Benchmark Tracker

---

Tracks:

- HF leaderboards
- Trending models
- Evaluation datasets
- New SOTA claims

Outputs:

- Leaderboard movements
- Task improvements
- Model family trends
- Reproducibility notes

9. Final Agent – Digest Compiler

---

Steps:

- Deduplicate findings
- Cluster by topic and entity
- Rank by impact
- Generate narrative
- Create executive summary
- Render PDF
- Send email notification

10. Configuration Design

---

Global config:

- run_time
- timezone
- max_pages_per_domain
- default_rate_limit
- email_recipients

Agents config:

- competitors
- model providers
- research queries
- HF benchmarks

11. Orchestration and Scheduling

---

Use scheduler:

- Cron
- Airflow
- Dagster
- Prefect
- Temporal

Retry strategy:

- Per‑URL retries with exponential backoff
- Domain‑level circuit breaker

12. Storage and Data Model

---

Tables/collections:

- sources
- snapshots
- extractions
- findings
- runs
- digests

Caching:
Skip summarization if content hash unchanged.

13. Summarization Contract

---

Prompt concept:
“Summarize this release note and extract:

- What changed
- Why it matters
- Who it affects
- Numbers/claims
- Source citation”

Guardrails:

- Always include citations
- Do not invent benchmark scores
- Assign confidence levels

14. Ranking and Scoring

---

Impact Score Formula:

Impact =
0.35_Relevance +
0.25_Novelty +
0.20_Credibility +
0.20_Actionability

15. Web UI

---

Pages:

- Dashboard
- Sources manager
- Runs history
- Findings explorer
- Digest archive

Bonus:

- “What changed” diff viewer
- SOTA leaderboard chart
- Entity heatmap

16. Security and Compliance

---

- Respect robots.txt
- Rate limit crawling
- Store secrets securely
- Avoid scraping behind authentication unless permitted
- Redact any detected PII

17. Testing and Evaluation

---

Unit tests:

- HTML extraction
- Date parsing
- Dedup hashing
- PDF rendering

Integration tests:

- Full pipeline with test corpus
- Failure injection

Quality tests:

- Hallucination checks
- Evidence verification

18. Deliverables

---

- Multi‑agent pipeline
- Configurable sources
- Daily scheduler
- Dedup + ranking
- PDF digest
- Email distribution
- Web UI
- Observability

20. Suggested Tech Stack

---

Orchestrator:

- Prefect
- Dagster
- Temporal

Crawler:

- httpx
- readability
- Playwright fallback

Parsing:

- BeautifulSoup
- trafilatura

Storage:

- PostgreSQL
- S3 object storage

Embeddings:

- local embedding model or API

PDF:

- ReportLab
- WeasyPrint

Email:

- SMTP
- SendGrid

UI:

- Next.js + FastAPI
- Streamlit (fast demo)
