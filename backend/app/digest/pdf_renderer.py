"""
PDF Renderer - Generates PDF digests from HTML templates using WeasyPrint.

Renders the digest data into a professional PDF document with:
- Cover page with date and audience
- Executive summary
- Deep dive sections per agent/topic
- Appendix with source links
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.utils.logger import logger
from jinja2 import Environment, FileSystemLoader

from app.config import DIGESTS_DIR

from app.utils.logger import logger

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

        # Render HTML from template
        html_content = self._render_html(digest_data)

        # Convert HTML to PDF
        try:
            from weasyprint import HTML

            HTML(string=html_content).write_pdf(str(pdf_path))
            logger.info(
                "pdf_render_complete path=%s size_kb=%d",
                str(pdf_path),
                pdf_path.stat().st_size // 1024,
            )
        except ImportError:
            # Fallback: save as HTML if WeasyPrint is not available
            logger.warning("weasyprint_not_available fallback=html")
            html_path = output_dir / f"zentivra_digest_{digest_date}.html"
            html_path.write_text(html_content, encoding="utf-8")
            pdf_path = html_path
            logger.info("html_fallback_saved path=%s", str(pdf_path))
        except Exception as e:
            logger.error("pdf_render_error error=%s", str(e))
            # Save HTML as fallback
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
            "date_formatted": (
                digest_date.strftime("%B %d, %Y")
                if hasattr(digest_date, "strftime")
                else str(digest_date)
            ),
            "executive_summary": digest_data.get(
                "executive_summary", "No summary available."
            ),
            "sections": digest_data.get("sections", {}),
            "total_findings": digest_data.get("total_findings", 0),
            "duplicates_removed": digest_data.get("total_duplicates_removed", 0),
            "include_appendix": True,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        return template.render(**context)

    def render_html_only(self, digest_data: dict) -> str:
        """Render to HTML string only (useful for email body)."""
        return self._render_html(digest_data)
