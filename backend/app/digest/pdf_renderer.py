"""
PDF Renderer - Generates PDF digests from HTML templates using WeasyPrint.

Renders the digest data into a professional PDF document with:
- Cover page with date and audience
- Executive summary
- Deep dive sections per agent/topic
- Appendix with source links
"""

from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from app.utils.logger import logger
from jinja2 import Environment, FileSystemLoader

from app.config import DIGESTS_DIR

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


class PDFRenderer:
    """
    Render digest data into a PDF document.

    Usage:
        renderer = PDFRenderer()
        pdf_path = renderer.render(digest_data)
    """

    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    def render(
        self,
        digest_data: dict,
        output_dir: Optional[Path] = None,
    ) -> str:
        """
        Render digest data to a PDF file.

        Args:
            digest_data: Dict from DigestCompiler.compile()
            output_dir: Where to save the PDF (default: data/digests/)

        Returns:
            Absolute path to the generated PDF file
        """
        output_dir = output_dir or DIGESTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        digest_date = digest_data.get("date", datetime.now().date())
        filename = f"zentivra_digest_{digest_date}.pdf"
        pdf_path = output_dir / filename

        logger.info("pdf_render_start output=%s", str(pdf_path))
        prepared_digest = self._prepare_digest_data(digest_data)

        # Render HTML from template
        html_content = self._render_html(prepared_digest)

        # Convert HTML to PDF
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(str(pdf_path))
            logger.info("pdf_render_complete path=%s size_kb=%d", str(pdf_path), pdf_path.stat().st_size // 1024)
        except Exception as e:
            # Windows environments frequently miss WeasyPrint native libs.
            logger.warning("pdf_render_weasyprint_failed error=%s", str(e))
            try:
                self._render_with_fpdf(prepared_digest, pdf_path)
                logger.info(
                    "pdf_render_fpdf_fallback_complete path=%s size_kb=%d",
                    str(pdf_path),
                    pdf_path.stat().st_size // 1024,
                )
            except Exception as fallback_error:
                logger.error(
                    "pdf_render_fallback_error error=%s",
                    str(fallback_error),
                )
                html_path = output_dir / f"zentivra_digest_{digest_date}.html"
                html_path.write_text(html_content, encoding="utf-8")
                pdf_path = html_path

        return str(pdf_path)

    def _render_html(self, digest_data: dict) -> str:
        """Render the Jinja2 template with digest data."""
        template = self._env.get_template("digest.html")

        digest_date = digest_data.get("date", datetime.now().date())

        context = {
            "date": str(digest_date),
            "date_formatted": digest_date.strftime("%B %d, %Y") if hasattr(digest_date, "strftime") else str(digest_date),
            "executive_summary": digest_data.get("executive_summary", "No summary available."),
            "executive_summary_points": digest_data.get("executive_summary_points", []),
            "sections": digest_data.get("sections", {}),
            "total_findings": digest_data.get("total_findings", 0),
            "duplicates_removed": digest_data.get("total_duplicates_removed", 0),
            "include_appendix": True,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        return template.render(**context)

    def render_html_only(self, digest_data: dict) -> str:
        """Render to HTML string only (useful for email body)."""
        prepared_digest = self._prepare_digest_data(digest_data)
        return self._render_html(prepared_digest)

    def _prepare_digest_data(self, digest_data: dict) -> dict:
        """Normalize digest payload for both HTML and FPDF renderers."""
        prepared = dict(digest_data or {})
        prepared["executive_summary"] = self._clean_text(
            prepared.get("executive_summary") or "No summary available."
        )
        prepared["executive_summary_points"] = self._extract_points(
            prepared["executive_summary"],
            max_points=8,
        )
        prepared["sections"] = self._prepare_sections(prepared.get("sections", {}))
        return prepared

    def _prepare_sections(self, sections: dict[str, Any]) -> dict[str, dict]:
        """Add render-friendly fields (logo URL/domain/benchmark rows)."""
        prepared_sections: dict[str, dict] = {}
        for section_name, section_data in (sections or {}).items():
            data = dict(section_data or {})
            data["narrative"] = self._clean_text(data.get("narrative") or "")
            data["narrative_points"] = self._extract_points(
                data["narrative"],
                max_points=10,
            )
            findings = [self._prepare_finding(f) for f in data.get("findings", [])]
            data["findings"] = findings
            data["benchmark_rows"] = [
                finding
                for finding in findings
                if str(finding.get("category", "")).lower() == "benchmarks"
            ]
            prepared_sections[section_name] = data
        return prepared_sections

    def _prepare_finding(self, finding: dict) -> dict:
        """Add source/domain/logo fields used by templates and fallback PDF."""
        prepared = dict(finding or {})
        prepared["title"] = self._clean_text(prepared.get("title") or "Untitled")
        prepared["summary_short"] = self._clean_text(prepared.get("summary_short") or "")
        prepared["summary_long"] = self._clean_text(prepared.get("summary_long") or "")
        prepared["why_it_matters"] = self._clean_text(
            prepared.get("why_it_matters") or ""
        )
        prepared["what_changed"] = self._clean_text(
            prepared.get("what_changed") or ""
        )
        prepared["who_it_affects"] = self._clean_text(
            prepared.get("who_it_affects") or ""
        )
        prepared["publisher"] = self._clean_text(prepared.get("publisher") or "")
        prepared["category"] = self._clean_text(prepared.get("category") or "other")

        # Key numbers (list of strings)
        raw_numbers = prepared.get("key_numbers") or []
        if isinstance(raw_numbers, list):
            prepared["key_numbers"] = [self._clean_text(n) for n in raw_numbers if n]
        else:
            prepared["key_numbers"] = []

        # Entities
        raw_entities = prepared.get("entities") or {}
        if isinstance(raw_entities, dict):
            prepared["entities"] = {
                k: v for k, v in raw_entities.items() if v
            }
        else:
            prepared["entities"] = {}

        summary_basis = prepared["summary_short"] or prepared["summary_long"]
        prepared["summary_points"] = self._extract_points(summary_basis, max_points=4)
        prepared["why_points"] = self._extract_points(
            prepared["why_it_matters"],
            max_points=3,
        )

        # Scoring breakdown for visual bars
        prepared["relevance_score"] = float(prepared.get("relevance_score") or 0)
        prepared["novelty_score"] = float(prepared.get("novelty_score") or 0)
        prepared["credibility_score"] = float(prepared.get("credibility_score") or 0)
        prepared["actionability_score"] = float(prepared.get("actionability_score") or 0)

        source_url = self._strip_wrapping_quotes(str(prepared.get("source_url") or "").strip())
        prepared["source_url"] = source_url
        source_domain = self._extract_domain(source_url)
        prepared["source_domain"] = source_domain
        prepared["source_logo_url"] = (
            self._logo_url_for_domain(source_domain) if source_domain else None
        )
        return prepared

    def _strip_wrapping_quotes(self, value: str) -> str:
        """Remove matching single/double quotes around an entire string."""
        text = str(value or "").strip()
        quote_pairs = [('"', '"'), ("'", "'")]

        changed = True
        while changed and len(text) >= 2:
            changed = False
            for left, right in quote_pairs:
                if text.startswith(left) and text.endswith(right):
                    inner = text[len(left) : -len(right)].strip()
                    if inner:
                        text = inner
                        changed = True
                    break
        return text

    def _clean_text(self, value: object) -> str:
        """Normalize markdown-like text into clean report prose."""
        text = str(value or "")
        if not text:
            return ""

        text = unescape(text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace('\\"', '"').replace("\\'", "'")

        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"__(.*?)__", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        cleaned_lines: list[str] = []
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            line = re.sub(r"^\s*#{1,6}\s+", "", line)
            line = re.sub(r"^\s*[-*]+\s+", "", line)
            line = re.sub(r"^\s*\d+[.)]\s+", "", line)
            line = self._strip_wrapping_quotes(line)
            line = re.sub(r"\s+", " ", line).strip()
            if line:
                cleaned_lines.append(line)

        while cleaned_lines and cleaned_lines[0] == "":
            cleaned_lines.pop(0)
        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()

        cleaned = "\n".join(cleaned_lines)
        return self._strip_wrapping_quotes(cleaned.strip())

    def _extract_points(self, value: object, max_points: int = 8) -> list[str]:
        """Convert free-form text into concise point-by-point lines."""
        text = self._clean_text(value)
        if not text:
            return []

        points = [line.strip() for line in text.split("\n") if line.strip()]
        if len(points) <= 1:
            points = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+", text)
                if sentence.strip()
            ]

        deduped: list[str] = []
        seen: set[str] = set()
        for point in points:
            key = point.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(point)
            if len(deduped) >= max_points:
                break

        return deduped

    def _extract_domain(self, url: str) -> str:
        """Extract normalized domain from URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return ""

    def _logo_url_for_domain(self, domain: str) -> str:
        """Public favicon endpoint for source logos in HTML render."""
        return f"https://www.google.com/s2/favicons?domain={quote(domain)}&sz=64"

    def _safe_filename(self, value: str) -> str:
        """Convert arbitrary strings into filesystem-safe file names."""
        chars = [c if c.isalnum() or c in {"-", "_", "."} else "_" for c in value]
        safe = "".join(chars).strip("._")
        return safe or "source"

    def _download_logo_for_domain(self, domain: str, assets_dir: Path) -> Optional[Path]:
        """Download and cache favicon/logo for a source domain."""
        if not domain:
            return None

        assets_dir.mkdir(parents=True, exist_ok=True)
        target = assets_dir / f"{self._safe_filename(domain)}.png"
        if target.exists() and target.stat().st_size > 0:
            return target

        logo_url = self._logo_url_for_domain(domain)
        try:
            request = Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=5) as response:
                content = response.read()
            if not content:
                return None
            target.write_bytes(content)
            return target
        except Exception:
            return None

    def _render_with_fpdf(self, digest_data: dict, pdf_path: Path) -> None:
        """Fallback PDF generation with professional layout and benchmark table."""
        from fpdf import FPDF

        def safe_text(value: object) -> str:
            text = self._clean_text(value)
            return text.encode("latin-1", "replace").decode("latin-1")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        content_width = pdf.w - pdf.l_margin - pdf.r_margin

        def split_token_to_fit(token: str, max_width: float) -> list[str]:
            """Split an unbreakable token into chunks that fit the page width."""
            if not token:
                return [""]
            if pdf.get_string_width(token) <= max_width:
                return [token]

            chunks: list[str] = []
            remaining = token
            while remaining:
                if pdf.get_string_width(remaining) <= max_width:
                    chunks.append(remaining)
                    break

                lo, hi = 1, len(remaining)
                best = 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    candidate = remaining[:mid]
                    if pdf.get_string_width(candidate) <= max_width:
                        best = mid
                        lo = mid + 1
                    else:
                        hi = mid - 1

                chunks.append(remaining[:best])
                remaining = remaining[best:]

            return chunks

        def wrap_text(value: object, max_width: float) -> str:
            """Pre-wrap text so FPDF never receives an unrenderable line."""
            text = safe_text(value)
            output_lines: list[str] = []

            for raw_line in text.split("\n"):
                if not raw_line.strip():
                    output_lines.append("")
                    continue

                current = ""
                words = raw_line.split()
                for word in words:
                    pieces = split_token_to_fit(word, max_width)
                    for piece in pieces:
                        candidate = piece if not current else f"{current} {piece}"
                        if pdf.get_string_width(candidate) <= max_width:
                            current = candidate
                        else:
                            if current:
                                output_lines.append(current)
                            current = piece

                if current:
                    output_lines.append(current)

            if not output_lines:
                return ""
            return "\n".join(output_lines)

        def write_wrapped(
            value: object,
            line_height: float,
            *,
            x: Optional[float] = None,
            width: Optional[float] = None,
        ) -> None:
            target_x = pdf.l_margin if x is None else x
            target_width = content_width if width is None else width
            pdf.set_x(target_x)
            pdf.multi_cell(target_width, line_height, wrap_text(value, target_width))

        def ensure_space(height_needed: float) -> None:
            if pdf.get_y() + height_needed > (pdf.h - pdf.b_margin):
                pdf.add_page()

        def truncate(value: object, limit: int) -> str:
            text = safe_text(value)
            if len(text) <= limit:
                return text
            return f"{text[: max(0, limit - 1)]}…"

        def draw_benchmark_table(rows: list[dict]) -> None:
            if not rows:
                return

            ensure_space(20)
            pdf.set_font("Helvetica", "B", 11)
            write_wrapped("Benchmark Highlights", 6)
            pdf.ln(1)

            widths = [
                content_width * 0.52,
                content_width * 0.24,
                content_width * 0.12,
                content_width * 0.12,
            ]
            headers = ["Benchmark", "Source", "Conf", "Impact"]

            pdf.set_fill_color(245, 245, 245)
            pdf.set_draw_color(130, 130, 130)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "B", 8)
            for idx, header in enumerate(headers):
                pdf.cell(widths[idx], 7, header, border=1, ln=0, fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", size=8)
            for row in rows[:12]:
                ensure_space(7)
                confidence = int(float(row.get("confidence") or 0) * 100)
                impact = int(float(row.get("impact_score") or 0) * 100)
                row_values = [
                    truncate(row.get("title", "Untitled"), 50),
                    truncate(row.get("publisher") or row.get("source_domain") or "Unknown", 22),
                    f"{confidence}%",
                    f"{impact}%",
                ]
                for idx, value in enumerate(row_values):
                    pdf.cell(widths[idx], 6, value, border=1, ln=0)
                pdf.ln()
            pdf.ln(2)

        # Cover header (minimal monochrome)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_xy(pdf.l_margin, 14)
        pdf.cell(0, 8, "ZENTIVRA AI RADAR", ln=True)
        pdf.set_font("Helvetica", size=10)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, "Frontier AI Intelligence Digest", ln=True)
        pdf.set_draw_color(120, 120, 120)
        pdf.line(pdf.l_margin, pdf.get_y() + 1, pdf.w - pdf.r_margin, pdf.get_y() + 1)

        # Cover body
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        date_value = digest_data.get("date", datetime.now().date())
        pdf.set_font("Helvetica", "B", 14)
        write_wrapped(f"Digest Date: {date_value}", 8)
        pdf.set_font("Helvetica", size=10)
        write_wrapped(
            f"Total Findings: {digest_data.get('total_findings', 0)}  |  "
            f"Sections: {len(digest_data.get('sections', {}))}  |  "
            f"Duplicates Removed: {digest_data.get('total_duplicates_removed', 0)}",
            6,
        )
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 12)
        write_wrapped("Executive Summary", 7)
        pdf.ln(1)
        pdf.set_font("Helvetica", size=10)
        summary_points = digest_data.get("executive_summary_points", [])
        if summary_points:
            for point in summary_points[:10]:
                write_wrapped(f"- {point}", 4.8)
        else:
            write_wrapped(
                digest_data.get("executive_summary", "No executive summary."),
                4.8,
            )
        pdf.ln(3)

        # Section pages
        sections = digest_data.get("sections", {})
        for section_name, section_data in sections.items():
            pdf.add_page()

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "B", 13)
            count = int(section_data.get("count", len(section_data.get("findings", []))))
            write_wrapped(f"{section_name} ({count} findings)", 6)
            pdf.set_draw_color(140, 140, 140)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(2)

            narrative_points = section_data.get("narrative_points", [])
            if narrative_points:
                pdf.set_font("Helvetica", "B", 10)
                write_wrapped("Section Notes", 5.2)
                pdf.set_font("Helvetica", size=9)
                for point in narrative_points[:10]:
                    write_wrapped(f"- {point}", 4.5)
                pdf.ln(2)

            draw_benchmark_table(section_data.get("benchmark_rows", []))

            pdf.set_font("Helvetica", "B", 11)
            write_wrapped("Findings", 6)
            pdf.ln(1)

            findings = section_data.get("findings", [])
            for index, finding in enumerate(findings[:18], start=1):
                ensure_space(28)
                pdf.set_font("Helvetica", "B", 10)
                write_wrapped(f"{index}. {finding.get('title', 'Untitled')}", 4.8)

                confidence = int(float(finding.get("confidence") or 0) * 100)
                impact = int(float(finding.get("impact_score") or 0) * 100)
                domain = str(finding.get("source_domain") or "")
                publisher = finding.get("publisher") or domain or "Unknown source"
                category = finding.get("category", "other")
                meta_line = f"Source: {publisher}"
                score_line = (
                    f"Category: {category} | Confidence {confidence}% | Impact {impact}%"
                )
                pdf.set_font("Helvetica", size=8)
                write_wrapped(f"- {meta_line}", 4.2)
                write_wrapped(f"- {score_line}", 4.2)

                # Summary
                summary_points = (
                    finding.get("summary_points")
                    or self._extract_points(
                        finding.get("summary_short")
                        or finding.get("summary_long")
                        or "No summary available.",
                        max_points=4,
                    )
                )
                pdf.set_font("Helvetica", "B", 8)
                write_wrapped("Summary:", 4.2)
                pdf.set_font("Helvetica", size=9)
                for point in summary_points[:4]:
                    write_wrapped(f"  - {point}", 4.6)

                # Detailed Analysis
                summary_long = finding.get("summary_long") or ""
                if summary_long:
                    ensure_space(12)
                    pdf.set_font("Helvetica", "B", 8)
                    write_wrapped("Detailed Analysis:", 4.2)
                    pdf.set_font("Helvetica", size=8)
                    write_wrapped(truncate(summary_long, 600), 4.2)

                # What Changed
                what_changed = finding.get("what_changed") or ""
                if what_changed:
                    ensure_space(10)
                    pdf.set_font("Helvetica", "B", 8)
                    write_wrapped("What Changed:", 4.2)
                    pdf.set_font("Helvetica", size=8)
                    write_wrapped(truncate(what_changed, 400), 4.2)

                # Why It Matters
                why_points = (
                    finding.get("why_points")
                    or self._extract_points(finding.get("why_it_matters") or "", max_points=3)
                )
                if why_points:
                    pdf.set_font("Helvetica", "B", 8)
                    write_wrapped("Why It Matters:", 4.2)
                    pdf.set_font("Helvetica", size=8)
                    for point in why_points[:3]:
                        write_wrapped(f"  - {point}", 4.4)

                # Who It Affects
                who_it_affects = finding.get("who_it_affects") or ""
                if who_it_affects:
                    pdf.set_font("Helvetica", "B", 8)
                    write_wrapped("Who It Affects:", 4.2)
                    pdf.set_font("Helvetica", size=8)
                    write_wrapped(truncate(who_it_affects, 300), 4.2)

                # Key Numbers & Claims
                key_numbers = finding.get("key_numbers") or []
                if key_numbers:
                    pdf.set_font("Helvetica", "B", 8)
                    write_wrapped("Key Numbers & Claims:", 4.2)
                    pdf.set_font("Helvetica", size=8)
                    for num in key_numbers[:6]:
                        write_wrapped(f"  - {safe_text(num)}", 4.2)

                # Entity Badges
                entities = finding.get("entities") or {}
                entity_parts = []
                for etype, elist in entities.items():
                    if elist and isinstance(elist, list):
                        for e in elist[:4]:
                            entity_parts.append(f"{etype}: {e}")
                if entity_parts:
                    pdf.set_font("Helvetica", "I", 7)
                    write_wrapped(" | ".join(entity_parts[:8]), 3.8)

                # Score Breakdown
                rel = float(finding.get("relevance_score") or 0)
                nov = float(finding.get("novelty_score") or 0)
                cred = float(finding.get("credibility_score") or 0)
                act = float(finding.get("actionability_score") or 0)
                if any([rel, nov, cred, act]):
                    pdf.set_font("Helvetica", size=7)
                    score_text = (
                        f"Scores: Relevance {rel:.1f} | Novelty {nov:.1f} | "
                        f"Credibility {cred:.1f} | Actionability {act:.1f}"
                    )
                    write_wrapped(score_text, 3.6)

                source_url = finding.get("source_url") or ""
                if source_url:
                    pdf.set_font("Helvetica", size=7)
                    write_wrapped(f"Link: {source_url}", 3.6)

                pdf.set_draw_color(180, 180, 180)
                divider_y = pdf.get_y() + 1
                pdf.line(pdf.l_margin, divider_y, pdf.w - pdf.r_margin, divider_y)
                pdf.ln(3)

        pdf.output(str(pdf_path))
