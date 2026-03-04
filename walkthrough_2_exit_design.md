# Zentivra — Build Walkthrough

## All 6 Phases Complete (34/34 items)

### Architecture Overview

```mermaid
graph TB
    subgraph Frontend
        UI[Next.js Web UI :3000]
    end
    subgraph Backend
        API[FastAPI :8000]
        SCH[APScheduler]
        ORC[Orchestrator]
    end
    subgraph Agents
        CW[Competitor Watcher]
        MP[Model Provider Watcher]
        RS[Research Scout]
        HF[HF Benchmark Tracker]
    end
    subgraph Pipeline
        FET[Fetcher] --> EXT[Extractor] --> CHG[Change Detector] --> SUM[Summarizer]
        SUM --> DDP[Dedup] --> RNK[Ranker]
    end
    subgraph Delivery
        CMP[Digest Compiler] --> PDF[PDF Renderer]
        CMP --> EML[Email Service]
    end
    UI --> API
    SCH --> ORC
    ORC --> CW & MP & RS & HF
    CW & MP & RS & HF --> FET
    RNK --> CMP
```

---

## Phase 6: Web UI Screenshots

### Sources Manager
![Sources page showing 19 configured sources with agent-type filters](/C:/Users/BodduBhuvan/.gemini/antigravity/brain/e1db781a-02b9-4995-82c5-d1aacd83e4d0/sources_page_1772657938983.png)

### Findings Explorer
![Findings explorer with search and category filters](/C:/Users/BodduBhuvan/.gemini/antigravity/brain/e1db781a-02b9-4995-82c5-d1aacd83e4d0/findings_page_1772657951833.png)

---

## E2E Test (Groq — Llama 3.3 70B)

| Step | Component | Result |
|---|---|---|
| Fetch | httpx → OpenAI blog | Content fetched |
| Extract | trafilatura | Text + title extracted |
| Change Detect | SHA256 | First fetch flagged |
| Summarize | Groq API | Structured JSON summary |
| Rank | Groq API | **Impact: 77.5%** |
| Dedup | Hash match | 1 duplicate removed |
| Compile | DigestCompiler | Sections + narratives |
| Output | PDFRenderer | [zentivra_digest_2026-03-05.html](file:///c:/Bhuvan/zentivra/backend/data/digests/zentivra_digest_2026-03-05.html) |

---

## Testing Suite

The project includes a comprehensive 62-test pytest suite covering the entire pipeline:

1. **Unit Tests (32 tests)**: Covers Extractor, ChangeDetector, DedupEngine, Ranker, PDFs, and Agent sub-type logic.
2. **Integration Tests (11 tests)**: End-to-end component chains (fetch → extract → detect → dedup → rank) and database model consistency.
3. **Quality Tests (19 tests)**: Validates LLM outputs (JSON parsing, malformed data, short content rejection), agent route inference, and settings edges.

All tests run locally with `pytest` without requiring live API keys.

---

## How to Run

```bash
# Backend (terminal 1)
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend
npm run dev -- -p 3000
```

Open **http://localhost:3000** for the dashboard.
