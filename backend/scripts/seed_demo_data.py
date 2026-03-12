"""
Seed demo data for all users.

Populates shared sources, runs, triggers, findings, snapshots, digests,
digest_snapshots, and agent_logs so every user sees meaningful dashboard
metrics and populated pages.

Usage:
    cd backend
    python -m scripts.seed_demo_data

Idempotent: skips users that already have a "Daily Competitor Scan" run.
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func  # noqa: E402
from app.database import engine, async_session  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.source import Source  # noqa: E402
from app.models.run import Run  # noqa: E402
from app.models.run_trigger import RunTrigger  # noqa: E402
from app.models.finding import Finding  # noqa: E402
from app.models.snapshot import Snapshot  # noqa: E402
from app.models.digest import Digest  # noqa: E402
from app.models.digest_snapshot import DigestSnapshot  # noqa: E402
from app.models.agent_log import AgentLog  # noqa: E402

random.seed(42)

NOW = datetime.now(timezone.utc)

# ── Shared sources to ensure exist (user_id=0) ──────────────────────────

SHARED_SOURCES = [
    # Competitor Release Watcher
    {"source_name": "openai_news", "display_name": "OpenAI Product Releases", "agent_type": "competitor", "url": "https://openai.com/news/product-releases/"},
    {"source_name": "anthropic_news", "display_name": "Anthropic News", "agent_type": "competitor", "url": "https://www.anthropic.com/news"},
    {"source_name": "cohere_blog", "display_name": "Cohere Blog", "agent_type": "competitor", "url": "https://cohere.com/blog"},
    {"source_name": "perplexity_hub", "display_name": "Perplexity Hub", "agent_type": "competitor", "url": "https://www.perplexity.ai/hub"},
    {"source_name": "mistral_news", "display_name": "Mistral News", "agent_type": "competitor", "url": "https://mistral.ai/news"},
    
    # Foundation Model Provider Updates
    {"source_name": "deepmind_blog", "display_name": "DeepMind Blog", "agent_type": "model_provider", "url": "https://deepmind.google/blog/"},
    {"source_name": "nvidia_blogs", "display_name": "NVIDIA Blogs", "agent_type": "model_provider", "url": "https://blogs.nvidia.com/"},
    {"source_name": "microsoft_ai_news", "display_name": "Microsoft AI News", "agent_type": "model_provider", "url": "https://news.microsoft.com/source/topics/ai/"},
    {"source_name": "stability_research", "display_name": "Stability AI Research", "agent_type": "model_provider", "url": "https://stability.ai/research"},
    
    # Research Publication Scout
    {"source_name": "arxiv_llm", "display_name": "arXiv LLM Search", "agent_type": "research", "url": "https://arxiv.org/search/?query=llm&searchtype=all&source=header"},
    {"source_name": "semantic_scholar_llm", "display_name": "Semantic Scholar LLM", "agent_type": "research", "url": "https://www.semanticscholar.org/search?q=llm&sort=pub-date"},
    {"source_name": "hf_trending_papers", "display_name": "HF Trending Papers", "agent_type": "research", "url": "https://huggingface.co/papers/trending"},
    {"source_name": "allenai_research", "display_name": "AllenAI Research", "agent_type": "research", "url": "https://allenai.org/research"},
    
    # Hugging Face Benchmarks & Model Trends
    {"source_name": "hf_models", "display_name": "HF Models", "agent_type": "hf_benchmark", "url": "https://huggingface.co/models"},
    {"source_name": "hf_models_trending", "display_name": "HF Trending Models", "agent_type": "hf_benchmark", "url": "https://huggingface.co/models?sort=trending"},
    {"source_name": "hf_open_llm_leaderboard", "display_name": "HF Open LLM Leaderboard", "agent_type": "hf_benchmark", "url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/"},
    {"source_name": "hf_datasets", "display_name": "HF Datasets", "agent_type": "hf_benchmark", "url": "https://huggingface.co/datasets"},
]

# ── Finding templates per agent type ─────────────────────────────────────

FINDING_TEMPLATES = {
    "competitor": [
        {"summary": "OpenAI announces GPT-5 with enhanced reasoning capabilities and 1M token context window.", "category": "announcement", "confidence": 0.92},
        {"summary": "Google DeepMind releases Gemini Ultra 2.0 with native multimodal understanding.", "category": "release", "confidence": 0.88},
        {"summary": "Anthropic introduces Claude 4.5 Opus with improved agentic capabilities.", "category": "model_release", "confidence": 0.95},
        {"summary": "Meta open-sources Llama 4 with 400B parameters, claiming SOTA on benchmarks.", "category": "release", "confidence": 0.85},
        {"summary": "Microsoft partners with Mistral AI for enterprise Azure integration.", "category": "partnership", "confidence": 0.78},
        {"summary": "Cohere launches Command R+ with improved RAG performance.", "category": "release", "confidence": 0.72},
        {"summary": "xAI announces Grok-3 with real-time web access and code execution.", "category": "announcement", "confidence": 0.65},
        {"summary": "Amazon invests $4B in Anthropic, deepening AI partnership.", "category": "partnership", "confidence": 0.90},
        {"summary": "OpenAI reduces GPT-4o pricing by 50% for API customers.", "category": "pricing", "confidence": 0.88},
        {"summary": "Google introduces AI Overviews in Search, impacting SEO landscape.", "category": "announcement", "confidence": 0.75},
    ],
    "model_provider": [
        {"summary": "OpenAI API adds structured outputs with guaranteed JSON schema compliance.", "category": "api_update", "confidence": 0.94},
        {"summary": "Anthropic doubles Claude API rate limits for all tiers.", "category": "api_update", "confidence": 0.87},
        {"summary": "Groq achieves 800 tokens/sec inference with custom LPU chips.", "category": "benchmark", "confidence": 0.82},
        {"summary": "Together AI launches serverless fine-tuning API for Llama models.", "category": "api_update", "confidence": 0.70},
        {"summary": "OpenAI deprecates text-davinci-003, migrating users to GPT-4o-mini.", "category": "api_update", "confidence": 0.91},
        {"summary": "Anthropic introduces tool use streaming for real-time agent applications.", "category": "release", "confidence": 0.86},
        {"summary": "Replicate adds A100 GPU support, reducing inference costs by 30%.", "category": "pricing", "confidence": 0.63},
        {"summary": "Fireworks AI achieves sub-100ms latency for Mixtral-8x22B inference.", "category": "benchmark", "confidence": 0.77},
    ],
    "research": [
        {"summary": "New paper introduces 'Chain-of-Draft' prompting, reducing token usage by 60% vs Chain-of-Thought.", "category": "research_paper", "confidence": 0.89},
        {"summary": "DeepSeek-V3 paper reveals MoE architecture achieving GPT-4 level at 1/10th cost.", "category": "research_paper", "confidence": 0.84},
        {"summary": "RLHF alternatives: DPO and KTO show comparable alignment with simpler training.", "category": "research_paper", "confidence": 0.76},
        {"summary": "Scaling laws for retrieval-augmented generation established in new CMU study.", "category": "research_paper", "confidence": 0.71},
        {"summary": "Visual language models achieve new SOTA on document understanding benchmarks.", "category": "benchmark", "confidence": 0.80},
        {"summary": "Constitutional AI 2.0: Self-improving alignment without human feedback.", "category": "research_paper", "confidence": 0.68},
        {"summary": "Sparse attention mechanisms reduce transformer memory by 4x with minimal quality loss.", "category": "research_paper", "confidence": 0.73},
    ],
    "hf_benchmark": [
        {"summary": "Claude 3.5 Sonnet tops Arena ELO ratings with 1290 score, surpassing GPT-4o.", "category": "benchmark", "confidence": 0.93},
        {"summary": "Qwen2.5-72B achieves #1 on Open LLM Leaderboard among open-weight models.", "category": "benchmark", "confidence": 0.90},
        {"summary": "Llama 3.1 405B closes gap with GPT-4 on MMLU, scoring 88.6%.", "category": "benchmark", "confidence": 0.86},
        {"summary": "New coding benchmark HumanEval+ reveals GPT-4o at 92.1% pass@1.", "category": "benchmark", "confidence": 0.88},
        {"summary": "Phi-3 Mini 3.8B outperforms Llama 2 7B on reasoning tasks.", "category": "benchmark", "confidence": 0.81},
        {"summary": "Gemma 2 27B shows surprising strength on multilingual benchmarks.", "category": "benchmark", "confidence": 0.79},
    ],
}

# ── Run definitions ──────────────────────────────────────────────────────

RUN_DEFINITIONS = [
    {
        "run_name": "Daily Competitor Scan",
        "description": "Monitors competitor blogs and announcements daily at 6 AM IST.",
        "agent_types": ["competitor"],
        "crawl_frequency": {"frequency": "daily", "time": "06:00", "periods": None},
        "keywords": ["AI", "LLM", "GPT", "Claude", "Gemini"],
    },
    {
        "run_name": "API Provider Updates",
        "description": "Tracks model provider API changes and new releases weekly.",
        "agent_types": ["model_provider"],
        "crawl_frequency": {"frequency": "weekly", "time": "09:00", "periods": ["mon", "wed", "fri"]},
        "keywords": ["API", "model", "release", "pricing"],
    },
    {
        "run_name": "Research & Benchmarks",
        "description": "Scans arxiv papers and HF leaderboards for research insights.",
        "agent_types": ["research", "hf_benchmark"],
        "crawl_frequency": {"frequency": "daily", "time": "08:00", "periods": None},
        "keywords": ["transformer", "benchmark", "SOTA", "scaling"],
    },
    {
        "run_name": "Full Intelligence Sweep",
        "description": "Comprehensive scan across all agent types for weekly executive digest.",
        "agent_types": ["competitor", "model_provider", "research", "hf_benchmark"],
        "crawl_frequency": {"frequency": "weekly", "time": "07:00", "periods": ["mon", "thu"]},
        "keywords": ["AI", "LLM", "benchmark", "release"],
    },
]

# Trigger statuses to cycle through (mostly completed for rich dashboard data)
TRIGGER_STATUSES = [
    "completed", "completed", "completed", "completed",
    "partial", "completed", "failed", "completed",
    "completed", "completed", "partial", "completed",
]


def _make_log_entries(agent_key: str, trigger_id: str, num_findings: int, base_time: datetime, num_sources: int = 2) -> list[dict]:
    """Generate realistic agent log entries matching the real pipeline format.

    Fields: ts (ISO timestamp), level (INFO/WARNING/ERROR), step (module), event (action).
    Simulates: pipeline → source_resolution → fetch → extract → preprocess → summarize per source.
    """
    entries: list[dict] = []
    t = base_time
    _s = lambda d: (t + d).isoformat()  # noqa: E731

    # Pipeline start
    entries.append({"ts": _s(timedelta(0)), "level": "INFO", "step": "pipeline", "event": "agent_start"})
    entries.append({"ts": _s(timedelta(seconds=1)), "level": "INFO", "step": "pipeline", "event": "agent_run_start"})

    offset = 2  # seconds elapsed
    for src_idx in range(num_sources):
        # Source processing cycle
        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "source_resolution", "event": "source_processing_start"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "fetch", "event": "urls_discovered"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "fetch", "event": "fetch_start"})
        fetch_duration = random.randint(5, 15)
        offset += fetch_duration

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "fetch", "event": "fetch_done"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "extract", "event": "extract_start"})
        extract_duration = random.randint(3, 12)
        offset += extract_duration

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "extract", "event": "extract_done"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "preprocess", "event": "preprocess_start"})
        offset += random.randint(1, 3)

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "preprocess", "event": "preprocess_done"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "summarize", "event": "summarize_start"})
        summarize_duration = random.randint(3, 8)
        offset += summarize_duration

        # Occasionally fail summarize (like real logs show)
        if src_idx == num_sources - 1 and random.random() < 0.25:
            entries.append({"ts": _s(timedelta(seconds=offset)), "level": "WARNING", "step": "summarize", "event": "summarize_failed"})
        else:
            entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "summarize", "event": "summarize_done"})
        offset += 1

        entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "source_resolution", "event": "source_processing_complete"})
        offset += 1

    # Pipeline complete
    entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "pipeline", "event": "agent_run_complete"})
    offset += 1
    entries.append({"ts": _s(timedelta(seconds=offset)), "level": "INFO", "step": "pipeline", "event": "agent_complete"})

    return entries


def _make_failed_log_entries(agent_key: str, base_time: datetime) -> list[dict]:
    """Generate log entries for a failed agent run."""
    _s = lambda d: (base_time + d).isoformat()  # noqa: E731
    return [
        {"ts": _s(timedelta(0)), "level": "INFO", "step": "pipeline", "event": "agent_start"},
        {"ts": _s(timedelta(seconds=1)), "level": "INFO", "step": "pipeline", "event": "agent_run_start"},
        {"ts": _s(timedelta(seconds=2)), "level": "INFO", "step": "source_resolution", "event": "source_processing_start"},
        {"ts": _s(timedelta(seconds=3)), "level": "INFO", "step": "fetch", "event": "urls_discovered"},
        {"ts": _s(timedelta(seconds=4)), "level": "INFO", "step": "fetch", "event": "fetch_start"},
        {"ts": _s(timedelta(seconds=20)), "level": "ERROR", "step": "fetch", "event": "fetch_failed"},
        {"ts": _s(timedelta(seconds=21)), "level": "ERROR", "step": "source_resolution", "event": "source_processing_failed"},
        {"ts": _s(timedelta(seconds=22)), "level": "ERROR", "step": "pipeline", "event": "agent_run_failed"},
        {"ts": _s(timedelta(seconds=23)), "level": "ERROR", "step": "pipeline", "event": "agent_complete"},
    ]


async def seed():
    print("=== Zentivra Demo Data Seeder ===\n")

    async with async_session() as db:
        # ── 1. Fetch target user only ────────────────────────────────
        TARGET_EMAIL = "bhuvanboddu08@gmail.com"
        result = await db.execute(
            select(User).where(User.email == TARGET_EMAIL)
        )
        target_user = result.scalar_one_or_none()
        if not target_user:
            print(f"ERROR: User '{TARGET_EMAIL}' not found.")
            return
        users = [target_user]

        print(f"Seeding for: {target_user.username} (id={target_user.id})")

        # ── 2. Ensure shared sources exist ───────────────────────────
        result = await db.execute(
            select(Source.source_name).where(Source.user_id == 0)
        )
        existing_names = {row[0] for row in result.all()}

        new_sources = []
        for s in SHARED_SOURCES:
            if s["source_name"] not in existing_names:
                new_sources.append(Source(user_id=0, **s))

        if new_sources:
            db.add_all(new_sources)
            await db.flush()
            print(f"Created {len(new_sources)} new shared sources.")
        else:
            print("All shared sources already exist.")

        # Re-fetch all shared sources (need integer IDs and UUIDs)
        result = await db.execute(
            select(Source).where(Source.user_id == 0, Source.is_enabled == True)  # noqa: E712
        )
        shared_sources = result.scalars().all()
        sources_by_type: dict[str, list[Source]] = {}
        for s in shared_sources:
            sources_by_type.setdefault(s.agent_type, []).append(s)

        print(f"Sources by type: { {k: len(v) for k, v in sources_by_type.items()} }")

        # ── 3. Seed per user ─────────────────────────────────────────
        for user in users:
            uid = user.id
            print(f"\n--- User '{user.username}' (id={uid}) ---")

            # Idempotency: skip if demo runs already exist
            result = await db.execute(
                select(func.count(Run.id))
                .where(Run.user_id == uid)
                .where(Run.run_name == "Daily Competitor Scan")
            )
            if (result.scalar() or 0) > 0:
                print("  Demo data already exists, skipping.")
                continue

            status_idx = 0
            total_triggers = 0
            total_findings = 0
            total_snapshots = 0
            total_digests = 0

            # ── Create runs ──────────────────────────────────────────
            runs: list[tuple[Run, list[str]]] = []
            for defn in RUN_DEFINITIONS:
                agent_types = defn["agent_types"]
                source_ids = []
                for at in agent_types:
                    for s in sources_by_type.get(at, []):
                        source_ids.append(s.source_id)

                run = Run(
                    user_id=uid,
                    run_name=defn["run_name"],
                    description=defn["description"],
                    enable_pdf_gen=True,
                    enable_email_alert=False,
                    sources=source_ids,
                    crawl_frequency=defn["crawl_frequency"],
                    crawl_depth=1,
                    keywords=defn.get("keywords"),
                    is_enabled=True,
                    created_at=NOW - timedelta(days=35),
                )
                db.add(run)
                runs.append((run, agent_types))

            await db.flush()
            print(f"  Created {len(runs)} runs.")

            # ── Create triggers + children ───────────────────────────
            # Distribute triggers evenly across last 30 days
            for run, agent_types in runs:
                num_triggers = 3
                for t_idx in range(num_triggers):
                    # Spread: day 2, 12, 22 for first run; day 4, 14, 24 for second, etc.
                    run_offset = runs.index((run, agent_types))
                    days_ago = 2 + (t_idx * 10) + (run_offset * 2)
                    days_ago = min(days_ago, 29)
                    trigger_time = NOW - timedelta(days=days_ago, hours=random.randint(5, 10))

                    status = TRIGGER_STATUSES[status_idx % len(TRIGGER_STATUSES)]
                    status_idx += 1
                    is_latest = (t_idx == num_triggers - 1)

                    trigger = RunTrigger(
                        run_id=run.id,
                        trigger_method="cron" if t_idx < num_triggers - 1 else "manual",
                        status=status,
                        is_latest=is_latest,
                        created_at=trigger_time,
                        updated_at=trigger_time + timedelta(minutes=random.randint(5, 15)),
                    )
                    db.add(trigger)
                    await db.flush()
                    total_triggers += 1

                    # No children for failed triggers
                    if status == "failed":
                        for at in agent_types:
                            log = AgentLog(
                                user_id=uid,
                                trigger_id=trigger.run_trigger_id,
                                agent_key=at,
                                entries=_make_failed_log_entries(at, trigger_time),
                                total_lines=9,
                                created_at=trigger_time,
                            )
                            db.add(log)
                        continue

                    # ── Findings ──────────────────────────────────────
                    trigger_findings: list[tuple[Finding, str]] = []
                    for at in agent_types:
                        templates = FINDING_TEMPLATES.get(at, [])
                        n = min(random.randint(2, 4), len(templates))
                        chosen = random.sample(templates, n)

                        for tmpl in chosen:
                            conf = tmpl["confidence"] + random.uniform(-0.1, 0.1)
                            conf = round(max(0.05, min(0.99, conf)), 2)

                            src_urls = [s.url for s in sources_by_type.get(at, [])]
                            src_url = random.choice(src_urls) if src_urls else f"https://example.com/{at}"

                            finding = Finding(
                                user_id=uid,
                                run_trigger_id=trigger.id,
                                content=(
                                    f"Detailed analysis: {tmpl['summary']} "
                                    f"This development signals a significant shift in the "
                                    f"{at.replace('_', ' ')} landscape and warrants strategic attention."
                                ),
                                summary=tmpl["summary"],
                                src_url=src_url,
                                category=tmpl["category"],
                                confidence=conf,
                                created_at=trigger_time + timedelta(minutes=random.randint(3, 10)),
                            )
                            db.add(finding)
                            trigger_findings.append((finding, at))
                            total_findings += 1

                    await db.flush()

                    # ── Snapshots (one per source) ────────────────────
                    trigger_snapshots: list[Snapshot] = []
                    for at in agent_types:
                        at_findings = [f for f, a in trigger_findings if a == at]
                        at_sources = sources_by_type.get(at, [])
                        for i, source in enumerate(at_sources):
                            # Distribute findings across sources
                            per_source = len(at_findings) // max(1, len(at_sources))
                            if i < len(at_findings) % max(1, len(at_sources)):
                                per_source += 1
                            per_source = max(per_source, 1 if at_findings else 0)

                            snap_status = "completed"
                            if status == "partial" and i == len(at_sources) - 1:
                                snap_status = "failed"

                            snap = Snapshot(
                                run_trigger_id=trigger.id,
                                source_id=source.id,
                                total_findings=per_source,
                                summary=f"Crawled {source.display_name}: extracted {per_source} relevant findings.",
                                status=snap_status,
                                created_at=trigger_time + timedelta(minutes=2),
                            )
                            db.add(snap)
                            trigger_snapshots.append(snap)
                            total_snapshots += 1

                    await db.flush()

                    # ── Digest ────────────────────────────────────────
                    if trigger_findings:
                        digest = Digest(
                            user_id=uid,
                            run_trigger_id=trigger.id,
                            digest_name=f"{run.run_name} — {trigger_time.strftime('%b %d, %Y')}",
                            status="completed",
                            created_at=trigger_time + timedelta(minutes=12),
                        )
                        db.add(digest)
                        await db.flush()
                        total_digests += 1

                        # Link digest to snapshots
                        for snap in trigger_snapshots:
                            ds = DigestSnapshot(
                                digest_id=digest.id,
                                snapshot_id=snap.id,
                                created_at=trigger_time + timedelta(minutes=12),
                            )
                            db.add(ds)

                    # ── Agent logs ─────────────────────────────────────
                    for at in agent_types:
                        at_count = len([f for f, a in trigger_findings if a == at])
                        n_src = len(sources_by_type.get(at, []))
                        log_entries = _make_log_entries(at, trigger.run_trigger_id, at_count, trigger_time, num_sources=max(n_src, 1))
                        log = AgentLog(
                            user_id=uid,
                            trigger_id=trigger.run_trigger_id,
                            agent_key=at,
                            entries=log_entries,
                            total_lines=len(log_entries),
                            created_at=trigger_time,
                        )
                        db.add(log)

            await db.flush()
            print(
                f"  Created: {total_triggers} triggers, {total_findings} findings, "
                f"{total_snapshots} snapshots, {total_digests} digests"
            )

        await db.commit()
        print("\n=== Demo data seeding complete! ===")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
