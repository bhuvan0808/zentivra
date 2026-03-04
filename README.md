<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Alien%20Monster.png" alt="Alien Monster" width="60" height="60" />
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Satellite%20Antenna.png" alt="Satellite Antenna" width="60" height="60" />
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Rocket.png" alt="Rocket" width="60" height="60" />

# 🌊 ZENTIVRA : Frontier AI Radar

**Your Autonomous AI Intelligence Command Center**  
*Scanning the horizon for the next big leap in artificial intelligence.*

<br/>

[![Next.js](https://img.shields.io/badge/Frontend-Next.js_14-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Language-Python_3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Powered_by-Groq_Llama_3-F55036?style=for-the-badge&logo=meta)](https://groq.com/)

<br/>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=20&duration=3000&pause=1000&color=9C27B0&center=true&vCenter=true&width=600&lines=Autonomous+Multi-Agent+Pipeline;Real-time+AI+Industry+Monitoring;LLM-Powered+Insight+Extraction;State-of-the-Art+Deduplication+Engine" alt="Typing SVG" />
</p>

</div>

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Magic%20Wand.png" alt="Magic Wand" width="25" height="25" /> **Constantly Evolving. Always Learning.**

---

## 🌟 What is Zentivra?

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=400&size=16&duration=4000&pause=500&color=2196F3&width=800&lines=From+raw+internet+noise+to+high-signal+executive+briefings." alt="Subtitle typing" />
</p>

In the AI sector, a week is a year. New foundation models drop daily, pricing updates happen in real-time, and research breakthroughs are fleeting. **Zentivra** is an autonomous "radar" system designed to monitor, extract, deduplicate, rank, and summarize the absolute cutting edge of AI news so you never miss a beat.

<details open>
<summary><b>✨ Core Capabilities (Click to Expand)</b></summary>
<br/>

*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" width="20" height="20" /> **Multi-Agent Architecture**: Four specialized intelligent agents (*Competitor Watcher, Model Provider, Research Scout, HF Benchmark Tracker*) constantly monitor over 19+ diverse sources.
*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/High%20Voltage.png" width="20" height="20" /> **Intelligent Extraction**: Bypasses cookie banners and grabs pure, semantic content from unstructured HTML and XML feeds.
*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Brain.png" width="20" height="20" /> **LLM-Powered Summarization & Ranking**: Summarizes complex articles using **Groq (Llama-3.3-70B)** and ranks them using a weighted algorithm.
*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Stop%20Sign.png" width="20" height="20" /> **Advanced Deduplication Engine**: Uses local semantic hashing and similarity clustering so you only read a story once.
*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/E-Mail.png" width="20" height="20" /> **Automated Delivery**: Compiles daily findings into a stunning narrative-driven HTML/PDF digest, sent to your inbox.
*   <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Desktop%20Computer.png" width="20" height="20" /> **Premium Glassmorphic Dashboard**: A gorgeous, dark-mode Next.js UI containing dynamic metric charts.

</details>

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Gear.png" alt="Gear" width="45" height="45" />
  <h2>🏗️ System Architecture Flow</h2>
</div>

### 1. High-Level Pipeline Orchestration

Zentivra runs entirely locally. It schedules jobs, fetches the entire internet's daily AI news, structures it, and renders a Next.js UI using FastAPI and SQLite/PostgreSQL.

```mermaid
graph TD
    subgraph internet["🌐 Internet Sources"]
        RSS["RSS/XML Feeds"]
        Web["HTML Websites"]
        API["API Endpoints"]
    end

    subgraph backend["🤖 Zentivra Core Backend (FastAPI)"]
        FET["Fetcher & Proxy Engine"]
        EXT["Trafilatura Extractor"]
        CHG["SHA256 Change Detector"]
        
        subgraph agents["Agents Routing Layer"]
            CW["Competitor Agent"]
            MP["Provider Agent"]
            RS["Research Scout"]
            HF["Benchmark Tracker"]
        end
        
        SUM["Groq LLM Summarizer"]
        DDP["Semantic Dedup Engine"]
        RNK["Heuristic/LLM Ranker"]
    end

    subgraph frontend["🖥️ Zentivra Frontend"]
        UI["Next.js Glassmorphic Dashboard"]
        DB[("Database (SQLite / PostgreSQL)")]
    end

    subgraph delivery["📬 Delivery Layer"]
        CMP["Digest Narrative Compiler"]
        PDF["WeasyPrint PDF Generator"]
        EML["SendGrid SMTP"]
    end

    RSS & Web & API --> FET
    FET --> EXT --> CHG
    CHG --> CW & MP & RS & HF
    CW & MP & RS & HF --> SUM
    SUM --> DDP --> RNK
    RNK --> DB
    RNK --> CMP
    DB <--> UI
    CMP --> PDF & EML
```

### 2. The Extraction & Deduplication Engine

How does Zentivra deal with the exact same OpenAI announcement being posted on 20 different blogs? By utilizing a state-of-the-art canonicalization and clustering algorithm.

```mermaid
flowchart LR
    raw["Raw HTML DOM"] -->|Trafilatura Extract| text["Clean Semantic Text"]
    text --> clean["Canonicalize \n(Strip whitespace, tags)"]
    clean --> hash{"SHA256 Content Hash"}
    
    hash -->|Matches Previous Fetch?| drop("Drop: Unchanged")
    hash -->|Unique Text| llm["LLM Structured JSON\n(Summaries, Tags)"]
    
    llm --> sim["Cosine Similarity Clustering\n(Deduplication Phase)"]
    sim -->|Duplicate > 0.85| tag("Tag as Duplicate")
    sim -->|Unique Story| save("Save & Rank Finding")
    
    style drop fill:#f9cfcf,stroke:#333,stroke-width:2px
    style save fill:#cff9d4,stroke:#333,stroke-width:2px
```

### 3. The Relevancy Ranker

Information overload is deadly. Zentivra forces the LLM to output a 4-dimensional array score from 0-10, calculating a final `Impact Score %`.

```mermaid
pie title Impact Score Formula Weighting
    "Relevancy to Enterprise AI" : 35
    "Novelty / Breaking News" : 25
    "Source Credibility" : 20
    "Actionability" : 20
```

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Wrench.png" alt="Wrench" width="45" height="45" />
  <h2>🛠️ Quick Start Guide</h2>
</div>

### Prerequisites
- <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="15" height="15" /> Node.js (v18+)
- <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Check%20Mark%20Button.png" width="15" height="15" /> Python (3.11+)
- <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Key.png" width="15" height="15" /> API Keys: `Groq` (Recommended), `OpenRouter`, `Gemini`, or `OpenAI`

<details>
<summary><b>1️⃣ Backend Setup (FastAPI / Python)</b></summary>
<br/>

```bash
# Clone the repository
git clone https://github.com/bhuvan0808/zentivra.git
cd zentivra/backend

# Virtual Environment Setup
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Secrets
cp .env.example .env
# ✏️ Edit .env: Add your GROQ_API_KEY and OPENROUTER_API_KEY

# Fire up the engine! 🚀
python -m uvicorn app.main:app --reload --port 8000
```
</details>

<details>
<summary><b>2️⃣ Frontend Setup (Next.js / React)</b></summary>
<br/>

```bash
# Open a new terminal tab
cd frontend

# Install UI Dependencies
npm install

# Launch the Dashboard 🎨
npm run dev -- -p 3000
```
</details>

<br/>

### 🎉 You are Live!
Open your browser to [**http://localhost:3000**](http://localhost:3000) to access the Zentivra Command Center.

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Microscope.png" alt="Microscope" width="45" height="45" />
  <h2>🔬 Rigorous Testing Suite</h2>
</div>

Zentivra includes an industrial-grade **62-test `pytest` suite** covering the entire AI pipeline, ensuring 0 hallucinations and 99.9% uptime.

| Test Category | Description | Command |
| :--- | :--- | :--- |
| **Unit Tests** | Tests raw Parsing, HTML extraction logic, and math algorithms. (32 tests) | `pytest tests/test_unit.py` |
| **Integration** | Validates End-to-End data flows (Fetch → Extract → Rank) locally in memory. (11 tests) | `pytest tests/test_integration.py` |
| **Quality/Guardrails** | Defends against LLM hallucinations, blocks malformed JSON, and routes sub-tags. (19 tests) | `pytest tests/test_quality.py` |

<br/>

<details>
<summary><b>Run the entire Pipeline End-to-End:</b></summary>

```bash
cd backend
python test_e2e.py
```
*Executes a live fetch, triggers Groq Llama-3.3, processes a deduplication sequence, and renders a localized PDF Digest.*
</details>

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/File%20Folder.png" alt="Folder" width="45" height="45" />
  <h2>📂 Project Structure Hub</h2>
</div>

```text
zentivra/
├── backend/
│   ├── app/
│   │   ├── agents/      # 🧠 Specialized Agent Modules (Scouts, Trackers)
│   │   ├── core/        # ⚙️ Fetcher, Extractor, Dedup, Ranker, Summarizer 
│   │   ├── digest/      # 📄 Narrative Compiler and PDF Generator
│   │   ├── models/      # 🗄️ SQLAlchemy DB ORM
│   │   └── scheduler/   # ⏱️ APScheduler Orchestration Heartbeat
│   └── tests/           # 🧪 62-Test Pytest Suite
└── frontend/
    ├── src/
    │   ├── app/         # 💻 Next.js Pages (Runs, Sources, Digests, Explorer)
    │   ├── components/  # 🧩 Reusable React UI Components
    │   └── lib/         # 🔌 Backend API Client SDK
    └── public/          # 🖼️ Static Assets
```

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Handshake.png" alt="Handshake" width="50" height="50" />
  
  ### Built for speed. Designed for intelligence. Stay ahead of the Frontier.
  Contributions to improve the extraction efficiency, add LLM providers, or enhance the dashboard are welcome!  
  
  **License**: MIT 
</div>
