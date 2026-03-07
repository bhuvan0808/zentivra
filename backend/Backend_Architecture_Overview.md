# Zentivra Platform: Technical Architecture & Specification

## 1. Executive Summary

The Zentivra platform is a high-performance, asynchronous orchestration engine and interactive dashboard built to manage complex, multi-agent intelligence gathering pipelines. It serves as the central nervous system for the Frontier AI Radar, handling everything from scheduled crawl triggers and parallel AI agent execution to Large Language Model (LLM) powered digest generation and highly interactive, animated data visualization.

Built as a decoupled full-stack architecture featuring a **FastAPI** backend and a **Next.js 16 (App Router)** frontend, the system is designed to be highly concurrent, maintaining data integrity while presenting complex, real-time intelligence feeds to the end user in a premium, fluid interface.

---

## 2. Architectural Paradigm & Technology Stack

To achieve the scale and responsiveness required by a multi-agent system with heavy user interaction, the platform adheres to a modular, event-driven, full-stack architecture.

### The Backend (Orchestration Engine)

- **Framework**: FastAPI (Python 3.10+) for lightning-fast application serving, dependency injection, automatic OpenAPI validation, and native async support.
- **Database Layer**: SQLite integrated via SQLAlchemy 2.0 using the `aiosqlite` pure-python async driver. This ensures database I/O is non-blocking, maintaining API responsiveness even when agents flush thousands of findings back to disk.
- **Design Pattern**: Domain-Driven Repository/Service pattern.
  - _Repositories_ isolate raw database operations.
  - _Services_ contain the core business logic.
  - _Routers (API)_ strictly handle HTTP context and payload validation via Pydantic.

### The Frontend (User Dashboard & Control Plane)

- **Framework**: Next.js 16 utilizing the App Router paradigm (`(app)` and `(public)` directories) along with React 19 Server Components/Client Hooks.
- **Styling & Components**: Tailwind CSS v4 coupled with `shadcn/ui` for accessible, premium-looking, and modular UI components (e.g., Modals, Dialogs, Selects, Tables).
- **Animation & Visualization**: Smooth page transitions and dynamic UI updates powered by `framer-motion` and `gsap`, with highly reactive dashboards rendered via `recharts`.
- **API Integration**: Centralized API middleware (`lib/api.ts`) abstracting standard DOM `fetch` calls, securely injecting JWT tokens dynamically from client `localStorage`.

---

## 3. The Multi-Agent Execution Flow & User Interaction (`RUNS` lifecycle)

The absolute core of the platform is the **Runs Lifecycle**—coordinated by the backend `Orchestrator` but heavily driven and tracked by the frontend interactive UI.

### The 10-Step Execution Lifecycle

1. **Pipeline Configuration (UI)**: Users interact with a visually stunning, multi-step run configuration form built with React-Hook-Forms and `framer-motion`. Users define agent types, depth, schedules (weekly/monthly GUI selectors), email recipients, and dynamic sources.
2. **Run Execution Context Creation**: Triggered manually via the API or automatically via the Background Scheduler, a new `RUN_TRIGGERS` DB record is spawned, acting as the parent UUID reference constraint for everything generated in this cycle.
3. **Parallel Base Agent Invocation**:
   - `BaseAgent` instances (e.g., Anthropic, OpenAI, GitHub crawlers) are instantiated on the backend.
   - Using `asyncio.gather`, the orchestrator fires off multiple independent agents concurrently.
   - Every agent tracks its own `.ndjson` structured execution log natively to disk, which the frontend's Trigger Detail Dialog polls to show real-time stream execution outputs to the user natively without locking SQLite.
4. **BFS URL Fetching & Preprocessing**:
   - Core `Fetcher` and `Extractor` modules fetch URLs adhering to maximum configurable timeouts, bypassing unnecessary DOM tree noise via `preprocessor.py`.
5. **LLM Finding Extraction**:
   - Agents call local/cloud LLMs mapped with system prompts specific to their core function to extract intelligent `FINDINGS` (e.g., pricing updates).
   - Every finding is tagged with a _Confidence Score_ (0.0 to 1.0) to signify LLM hallucination resistance.
6. **Snapshot Creation**:
   - Every agent yields a `SNAPSHOT`—a frozen-in-time summary metrics dictionary of target results. In the UI, these are dynamically rendered inside animated Accordion containers grouping findings chronologically.
7. **Database Persistence**:
   - Findings and Snapshots are batch-inserted into the database within an asynchronous SQLAlchemy session `.commit()` bound inside the orchestrator.
8. **Digest Generation (LLM Pipeline)**:
   - The backend `digest_generator` kicks in, consuming _only_ high-status/high-confidence findings from snapshots.
   - It pre-chunks and summarizes contexts, piping them through a powerful LLM to weave together a cohesive Intelligence Digest natively written in Markdown.
9. **Artifact Matrix Storage & Viewing**:
   - Markdown is formatted with HTML wrappers, styled precisely with inline CSS.
   - The frontend's dynamic URL routes (`/digests/[digest_id]`) fetch this processed HTML/PDF Blob via authorized GET requests and natively map it into an isolated HTML `iframe` padded carefully for optimal typography reading.
10. **Run Completion & Notifications**:

- Backend trigger execution status transitions to `completed` (or `partial`). The React frontend updates badges via intelligent local timestamp formatting (`lib/formatDate.ts`), mapping raw backend UTC to user-localized display times. Background email workers optionally dispatch the final PDF.

---

## 4. Directory Structure & Core Modules

### Backend Structure (`app/`)

- **`agents/`**: Contains `base_agent.py` and intelligent crawlers encapsulating specific scraping and LLM prompt logic for varying domains.
- **`api/` & `schemas/`**: The FastAPI routing layer interacting exactly with strict Pydantic v2 validation payloads.
- **`core/` & `digest/`**: Extraction internals and complex LLM context window mappers for artifact generation.
- **`repositories/` & `services/`**: Clean SQL abstractions handling complex JOINs asynchronously.
- **`models/`**: SQLAlchemy declarative base models mapping perfectly to the Zentivra Database Schemas.

### Frontend Structure (`src/`)

- **`app/(app)/`**: Protected routing segments (Dashboard, Runs, Sources, Findings). Requires valid JWT. Implements complex layout shifts using `framer-motion` layout animations.
- **`app/(public)/`**: Unauthenticated auth forms (Signin/Signup) performing payload formatting and securely stashing auth tokens and email profiles in local storage upon successful handshakes.
- **`components/`**: Clean UI boundaries matching atomic design:
  - Base `shadcn-ui` primitives (Button, Dropdown, Dialog with backdrop-blur enhancements).
  - Composed modules like `PageHeader`, `Sidebar`, and `StatusBadge`.
- **`lib/`**: Standalone API middleware `api.ts`, shared `types.ts` type definitions (syncing to FastAPI Pydantic equivalents), and formatting utility modules.

---

## 5. Security & Data Integrity

- **JWT & Stateless Authentication**: Users authenticate yielding stateless bearer tokens stored temporarily in `localStorage`. Next.js API interceptors attach the Bearer strings perfectly to `/app/(app)` fetch requests, bouncing invalid sessions to `/signin`.
- **Cascading SQLite Persistence**: SQLite `PRAGMA foreign_keys = ON` natively ensures pipeline deletions cascade downwards safely resolving orphaned datasets.
- **Out-of-band NDJSON Logging**: Execution telemetry skips the relational database entirely, writing to `.ndjson` disk logs. The Next.js frontend fetches these through isolated API scopes, guaranteeing dashboard stability even during massive data crawls.

---

## 6. Challenges Faced & Engineering Triumphs

Building a robust full-stack multi-agent orchestration engine within massive operational constraints presented significant hurdles:

1. **Async Database Deadlocks vs React Render Thrashing**:
   _Challenge_: When multiple parallel Python coroutines completed simultaneously dumping thousands of findings, SQLite locked up, causing frontend dashboard API calls to sequentially time out or trigger cascading error toasts.
   _Solution (Backend)_: Switched cleanly to pure async connections (`aiosqlite`) blocking bulk transactions inside strict repository scopes.
   _Solution (Frontend)_: Implemented optimized `useEffect` boundaries and debouncing on table requests to prevent `setState` render spirals while waiting for heavy data payload responses.
2. **Graceful Handling of Unpredictable Agent Failures**:
   _Challenge_: A single target website dropping connection shouldn't crash a massive intelligence run.
   _Solution_: The Backend orchestrator implements resilient nested `try/except` bounds that catch timeouts and yield a `partial` execution sequence. The Frontend handles this beautifully natively, rendering `Warning` chips and ensuring visually accurate user expectations with yellow status badges.
3. **LLM Context Window Saturation & UI Render limits**:
   _Challenge_: Digest generation overflowed local context maps, and streaming 100+ findings crashed the dynamic UI lists visually.
   _Solution_: Backend implemented intermediate LLM summarizing and dynamically thresholded `Confidence Scores`. Frontend `runs` modals implement native CSS container containment (`overflow-x-auto`) scrolling while limiting execution log previews tightly to the Top 10 to preserve stable DOM performance globally.

---

## 7. Contributors

This unified Next.js + FastAPI full-stack architecture was proudly designed and developed by:

- **Boddu Bhuvan**
- **Kaustubh Paturi**
- **Srinivasulu Kethavath**
