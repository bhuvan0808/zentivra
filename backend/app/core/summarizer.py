"""Summarizer — LLM-powered content summarization and finding generation.

Fourth stage of the pipeline: fetch -> extract -> preprocess -> summarize -> dedup -> rank.

Supports Groq (fastest), OpenRouter, Gemini, OpenAI, and Anthropic as LLM providers.
Extracts structured findings from raw text with guardrails (confidence, citations).
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from app.utils.logger import logger

from app.config import settings


@dataclass
class SummaryResult:
    """Structured summary produced by the LLM.

    Attributes:
        title: Concise title for the finding.
        summary_short: 2-3 sentence summary.
        summary_long: Detailed summary.
        why_it_matters: Why this matters to AI practitioners.
        what_changed: What specifically changed.
        who_it_affects: Target audience.
        key_numbers: List of metrics/numbers mentioned.
        confidence: 0.0-1.0 confidence score.
        category: One of models, apis, pricing, benchmarks, safety, tooling, research, other.
        tags: Categorization tags.
        entities: Dict with companies, models, datasets.
        evidence: Citations, source URLs.
        success: True if summarization succeeded.
        error: Error message if success=False.
    """

    title: str = ""
    summary_short: str = ""  # 2-3 sentence summary
    summary_long: str = ""  # Detailed summary
    why_it_matters: str = ""
    what_changed: str = ""
    who_it_affects: str = ""
    key_numbers: list[str] = field(default_factory=list)
    confidence: float = 0.5
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    entities: dict = field(default_factory=dict)  # companies, models, datasets
    evidence: dict = field(default_factory=dict)  # citations, source URLs
    success: bool = True
    error: Optional[str] = None


# ── Prompt Templates ─────────────────────────────────────────────────────────

SUMMARIZE_PROMPT = """You are an AI intelligence analyst for a Frontier AI Radar system.
Analyze the following content and extract a structured summary.

CONTENT SOURCE: {source_name} ({source_url})
CONTENT TYPE: {content_type}

─── CONTENT TO ANALYZE ───
{content}
───────────────────────────

Extract the following as valid JSON:
{{
  "title": "A clear, concise title for the finding (max 100 chars)",
  "summary_short": "2-3 sentence summary of the key development",
  "summary_long": "Detailed summary (3-5 paragraphs) covering all important details",
  "why_it_matters": "Why this matters to AI practitioners, researchers, or businesses",
  "what_changed": "What specifically changed or was announced (before/after if detectable)",
  "who_it_affects": "Who is affected by this change (developers, enterprises, researchers, etc.)",
  "key_numbers": ["List of any numbers, metrics, or claims mentioned"],
  "confidence": 0.0 to 1.0 confidence that this is a real, significant update,
  "category": one of ["models", "apis", "pricing", "benchmarks", "safety", "tooling", "research", "other"],
  "tags": ["relevant", "tags", "for", "categorization"],
  "entities": {{
    "companies": ["Company names mentioned"],
    "models": ["Model names mentioned"],
    "datasets": ["Dataset names mentioned"]
  }}
}}

RULES:
- ALWAYS include citations. Never invent benchmark scores or metrics.
- Assign confidence based on evidence quality: 0.9+ for official announcements, 0.5-0.8 for blog posts, 0.3-0.5 for rumors/speculation.
- Be precise with numbers and version strings.
- If the content is not about AI/ML/LLM developments, set confidence to 0.1.
- Return ONLY valid JSON, no markdown formatting.
"""

RANK_PROMPT = """Score the following AI finding on four dimensions (each 1-10):

FINDING:
Title: {title}
Summary: {summary}
Category: {category}
Source: {source}

Score each dimension:
1. RELEVANCE: How relevant is this to AI practitioners and the industry? (1=irrelevant, 10=critical)
2. NOVELTY: How new/unique is this? (1=old news, 10=breakthrough)
3. CREDIBILITY: How trustworthy is the source and claims? (1=rumor, 10=official announcement with evidence)
4. ACTIONABILITY: How actionable is this? (1=FYI only, 10=requires immediate response)

Return ONLY valid JSON:
{{
  "relevance": score,
  "novelty": score,
  "credibility": score,
  "actionability": score,
  "reasoning": "Brief explanation of scores"
}}
"""


class Summarizer:
    """
    LLM-powered summarizer that supports multiple providers.

    Usage:
        summarizer = Summarizer()
        result = await summarizer.summarize(text, source_name, source_url)
        scores = await summarizer.rank(title, summary, category, source)
    """

    def __init__(self, provider: str | None = None, model: str | None = None):
        """Initialize with provider (groq, openrouter, gemini, openai, anthropic) and optional model override."""
        self._provider = provider or settings.active_llm_provider
        self._model_override = model
        logger.info("summarizer_init provider=%s", self._provider)

    def _resolve_model(self) -> str:
        """Return the model name for the active provider, preferring explicit override."""
        if self._model_override:
            return self._model_override
        model_map = {
            "groq": settings.groq_model,
            "openrouter": settings.openrouter_model,
            "gemini": settings.gemini_model,
            "openai": settings.openai_model,
            "anthropic": settings.anthropic_model,
        }
        return model_map.get(self._provider, "")

    async def summarize(
        self,
        content: str,
        source_name: str = "",
        source_url: str = "",
        content_type: str = "web page",
        max_content_length: int = 15000,
    ) -> SummaryResult:
        """
        Summarize content using the configured LLM provider.

        Args:
            content: Raw text to summarize
            source_name: Name of the source (e.g., "OpenAI Blog")
            source_url: URL of the source
            content_type: Type of content (web page, RSS entry, research paper)
            max_content_length: Max characters to send to LLM

        Returns:
            SummaryResult with structured fields
        """
        if not content or len(content.strip()) < 50:
            return SummaryResult(
                success=False,
                error="Content too short to summarize",
                confidence=0.0,
            )

        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[Content truncated...]"

        prompt = SUMMARIZE_PROMPT.format(
            source_name=source_name,
            source_url=source_url,
            content_type=content_type,
            content=content,
        )

        try:
            response_text = await self._call_llm(prompt)
            result = self._parse_summary_response(response_text)
            result.evidence = {"source_url": source_url, "source_name": source_name}
            return result

        except Exception as e:
            logger.error("summarize_error error=%s source=%s", str(e), source_name)
            return SummaryResult(
                success=False,
                error=str(e),
                confidence=0.0,
            )

    async def rank(
        self,
        title: str,
        summary: str,
        category: str,
        source: str,
    ) -> dict:
        """Score a finding on relevance, novelty, credibility, actionability.

        Returns dict with relevance, novelty, credibility, actionability (1-10),
        impact_score (0-1), and reasoning. On error, returns default scores (5 each).
        """
        prompt = RANK_PROMPT.format(
            title=title,
            summary=summary,
            category=category,
            source=source,
        )

        try:
            response_text = await self._call_llm(prompt)
            scores = self._parse_json_response(response_text)

            # Compute impact score using spec weights
            impact = (
                0.35 * scores.get("relevance", 5)
                + 0.25 * scores.get("novelty", 5)
                + 0.20 * scores.get("credibility", 5)
                + 0.20 * scores.get("actionability", 5)
            ) / 10.0  # Normalize to 0-1

            scores["impact_score"] = round(impact, 3)
            return scores

        except Exception as e:
            logger.error("rank_error error=%s title=%s", str(e), title)
            return {
                "relevance": 5,
                "novelty": 5,
                "credibility": 5,
                "actionability": 5,
                "impact_score": 0.5,
                "reasoning": f"Default scores — ranking failed: {e}",
            }

    async def generate_narrative(
        self,
        findings_by_section: dict[str, list[dict]],
    ) -> dict[str, str]:
        """
        Generate narrative text for each section of the digest.

        Args:
            findings_by_section: Dict of section_name -> list of finding dicts

        Returns:
            Dict of section_name -> narrative text
        """
        narratives = {}

        for section, findings in findings_by_section.items():
            if not findings:
                narratives[section] = "No significant updates in this area today."
                continue

            findings_text = "\n".join(
                f"- {f.get('title', 'Untitled')}: {f.get('summary_short', '')}"
                for f in findings[:15]
            )

            prompt = f"""You are writing the "{section}" section of a daily AI intelligence digest.

Write a coherent 2-4 paragraph narrative summarizing these findings. Use a professional,
analytical tone appropriate for technical leadership. Highlight the most impactful items first.

FINDINGS:
{findings_text}

Write the narrative directly (no preamble, no markdown headers). Keep it concise but insightful."""

            try:
                narrative = await self._call_llm(prompt)
                narratives[section] = narrative.strip()
            except Exception as e:
                logger.error("narrative_error section=%s error=%s", section, str(e))
                narratives[section] = f"Error generating narrative: {e}"

        return narratives

    async def generate_digest_title(
        self,
        findings: list[dict],
    ) -> str:
        """Generate a short, descriptive title for the digest based on top findings.

        Uses LLM; falls back to first finding title or 'AI Radar Digest' on error.
        """
        if not findings:
            return "AI Radar Digest"

        top = findings[:5]
        bullets = "\n".join(
            f"- {f.get('title', '')} ({f.get('category', 'other')})" for f in top
        )

        prompt = f"""Given these top AI findings from today, generate a short digest title (max 8 words).
The title should capture the most significant theme. No quotes, no punctuation at the end.

FINDINGS:
{bullets}

Return ONLY the title, nothing else."""

        try:
            title = (await self._call_llm(prompt)).strip().strip("\"'.")
            if title and len(title) <= 100:
                return title
        except Exception as e:
            logger.error("digest_title_error error=%s", str(e))

        # Fallback: derive from top finding title
        top_title = top[0].get("title", "")
        if top_title:
            return top_title[:80]
        return "AI Radar Digest"

    async def generate_executive_summary(
        self,
        section_narratives: dict[str, str],
        total_findings: int,
    ) -> str:
        """Generate a one-page executive summary from section narratives.

        Returns error message string on LLM failure.
        """
        sections_text = "\n\n".join(
            f"**{section}**:\n{narrative}"
            for section, narrative in section_narratives.items()
        )

        prompt = f"""Write a concise executive summary (max 300 words) for today's AI intelligence digest.

TOTAL FINDINGS TODAY: {total_findings}

SECTION SUMMARIES:
{sections_text}

Write a crisp, executive-level summary highlighting the top 3-5 most important developments.
Focus on: what happened, why it matters, and what to watch for. No preamble."""

        try:
            return (await self._call_llm(prompt)).strip()
        except Exception as e:
            logger.error("executive_summary_error error=%s", str(e))
            return f"Executive summary generation failed: {e}"

    # ── LLM Provider Implementations ──────────────────────────────────────

    async def _call_llm(self, prompt: str) -> str:
        """Route to the configured LLM provider. Raises RuntimeError if none configured."""
        if self._provider == "groq":
            return await self._call_groq(prompt)
        elif self._provider == "openrouter":
            return await self._call_openrouter(prompt)
        elif self._provider == "gemini":
            return await self._call_gemini(prompt)
        elif self._provider == "openai":
            return await self._call_openai(prompt)
        elif self._provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            raise RuntimeError(
                f"No LLM provider configured. Set GROQ_API_KEY, OPENROUTER_API_KEY, "
                f"GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file."
            )

    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API with retry/backoff for rate limits and timeouts."""
        import asyncio
        import re
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        timeout_seconds = max(1, int(settings.llm_timeout_seconds))

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=self._resolve_model(),
                        contents=prompt,
                    ),
                    timeout=timeout_seconds,
                )
                return response.text or ""
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "gemini_timeout_retry timeout=%d wait=%d attempt=%d",
                        timeout_seconds,
                        wait,
                        attempt + 1,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise TimeoutError(
                    f"Gemini request timed out after {timeout_seconds} seconds"
                )
            except Exception as e:
                error_str = str(e)
                # Check for rate-limit / retryDelay
                delay_match = re.search(
                    r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)", error_str
                )
                if delay_match and attempt < max_retries - 1:
                    delay = int(delay_match.group(1))
                    logger.warning(
                        "gemini_rate_limit retry_delay=%d attempt=%d",
                        delay,
                        attempt + 1,
                    )
                    await asyncio.sleep(delay + 2)  # Wait the suggested delay + buffer
                elif attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "gemini_error_retry error=%s wait=%d", error_str[:100], wait
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API. Raises on HTTP error."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._resolve_model(),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API. Raises on HTTP error."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self._resolve_model(),
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API (fast inference). Raises on HTTP error."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._resolve_model(),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API (multi-model gateway). Raises on HTTP error."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://zentivra.local",
                    "X-Title": "Zentivra AI Radar",
                },
                json={
                    "model": self._resolve_model(),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    # ── Response Parsing ──────────────────────────────────────────────────

    def _parse_summary_response(self, response: str) -> SummaryResult:
        """Parse JSON response from LLM into SummaryResult. Returns empty fields on parse failure."""
        data = self._parse_json_response(response)

        return SummaryResult(
            title=data.get("title", ""),
            summary_short=data.get("summary_short", ""),
            summary_long=data.get("summary_long", ""),
            why_it_matters=data.get("why_it_matters", ""),
            what_changed=data.get("what_changed", ""),
            who_it_affects=data.get("who_it_affects", ""),
            key_numbers=data.get("key_numbers", []),
            confidence=float(data.get("confidence", 0.5)),
            category=data.get("category", "other"),
            tags=data.get("tags", []),
            entities=data.get("entities", {}),
        )

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks. Returns {} on failure."""
        response = response.strip()

        # Remove markdown code block wrappers if present
        if response.startswith("```"):
            lines = response.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            response = "\n".join(lines)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            logger.error("json_parse_error response_preview=%s", response[:200])
            return {}
