<div align="center">

# 🌊 Zentivra: Frontier AI Radar

**Your Autonomous AI Intelligence Command Center**

![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Python](https://img.shields.io/badge/Python-3.11-3776AB)
![Powered by Groq](https://img.shields.io/badge/Powered_by-Groq_Llama_3-F55036)

<p align="center">
  A multi-agent, scheduled pipeline that scours the internet for the fastest-moving AI developments, distills the noise, and delivers high-impact executive summaries.
</p>

</div>

---

## 🚀 What is Zentivra?

In the AI sector, a week is a year. New foundation models drop daily, pricing updates happen in real-time, and research breakthroughs are fleeting. **Zentivra** is an autonomous "radar" system designed to monitor, extract, deduplicate, rank, and summarize the absolute cutting edge of AI news so you never miss a beat.

### ✨ Core Features

*   🤖 **Multi-Agent Architecture**: Four specialized intelligent agents (Competitor Watcher, Model Provider, Research Scout, HF Benchmark Tracker) constantly monitor the ecosystem.
*   ⚡ **Intelligent Extraction**: Bypasses paywalls and cookie banners to grab pure, semantic content from unstructured HTML and complex RSS feeds.
*   🧠 **LLM-Powered Summarization & Ranking**: Summarizes complex articles using Groq (Llama-3.3-70B) and ranks them using a weighted algorithm (Novelty, Relevance, Credibility, Actionability).
*   🛑 **Advanced Deduplication**: Identifies overlapping news coverage using text-hash and semantic clustering to ensure you only read a story once.
*   📧 **Automated Delivery**: Compiles daily findings into a stunning narrative-driven HTML/PDF digest, sent directly to your inbox via SendGrid.
*   🖥️ **Premium Next.js Dashboard**: A gorgeous, dark-mode, glassmorphic UI to explore findings, manage sources, and review pipeline telemetry.

---

## 🏗️ System Architecture

Zentivra is built on a resilient, microservice-inspired architecture:

### 1. The Backend (Python / FastAPI)
*   **Orchestration**: `APScheduler` manages the daily pipeline heartbeat.
*   **Fetcher & Extractor**: Utilizes `httpx`, `BeautifulSoup4`, and `Trafilatura` for clean web scraping.
*   **LLM Engine**: Dynamic provider routing supporting Groq, OpenRouter, Gemini, OpenAI, and Anthropic.
*   **Storage**: SQLAlchemy + SQLite (production-ready for PostgreSQL swap).

### 2. The Frontend (Next.js / React)
*   **Design**: Zero-dependency vanilla CSS design system featuring deep space purples, fluid typography, and premium micro-interactions.
*   **Views**: Real-time Dashboard, Source Configuration Manager, Pipeline Run History, Findings Explorer, and Digest Archive.

---

## 🛠️ Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python (3.11+)
*   API Keys: Groq (Recommended), or OpenAI/Gemini/Anthropic/OpenRouter.

### 1. Clone the Repository
```bash
git clone https://github.com/bhuvan0808/zentivra.git
cd zentivra
```

### 2. Backend Setup
```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Or `.\venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your Groq/OpenRouter API keys and SendGrid credentials

# Run the backend server
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install

# Start the development server
npm run dev -- -p 3000
```

🌟 **Open your browser to `http://localhost:3000` to access the Zentivra Command Center.**

---

## 🧪 Testing

Zentivra includes a rigorous, 62-test `pytest` suite covering the entire pipeline.

```bash
cd backend
python -m pytest tests/ -v
```

*   **Unit Tests**: Verifies raw parsing, extraction logic, and math algorithms.
*   **Integration Tests**: Validates the end-to-end data flow (Fetch → Extract → Detect → Dedup → Rank) in memory.
*   **Quality Guardrails**: Ensures LLM responses don't hallucinate, handles malformed JSON, and validates routing logic.

---

## 📂 Project Structure

```bash
zentivra/
├── backend/
│   ├── app/
│   │   ├── agents/      # Specialized monitoring agents
│   │   ├── core/        # Fetcher, Extractor, Dedup, Ranker, Summarizer
│   │   ├── digest/      # Compiler and PDF Renderer
│   │   ├── models/      # SQLAlchemy Database Models
│   │   └── scheduler/   # APScheduler Orchestration
│   └── tests/           # Comprehensive Pytest Suite
└── frontend/
    ├── src/
    │   ├── app/         # Next.js App Router pages (Dashboard, Findings, etc.)
    │   ├── components/  # React reusable UI components
    │   └── lib/         # API Client SDK
    └── public/          # Static assets
```

---

## 🤝 Contributing

This project is tailored for specialized AI tracking, but contributions to improve the extraction efficiency, add new LLM providers, or enhance the Next.js UI are highly encouraged!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">
  <b>Built for speed. Designed for intelligence.</b><br>
  <i>Stay ahead of the Frontier.</i>
</div>
