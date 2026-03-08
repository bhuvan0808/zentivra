"""
Email Notification Service — sends digest emails via SendGrid or SMTP.

Post-processing component: runs after the digest pipeline has produced
HTML/PDF. Delivers notifications containing:
- Executive summary snippet as HTML email body
- PDF attachment (when available)
- Link to web dashboard

SendGrid vs SMTP fallback:
- Primary: SendGrid API when SENDGRID_API_KEY is configured and valid.
- Fallback: If SendGrid is configured but fails (API error, network, etc.),
  the service automatically falls back to SMTP when SMTP settings are present.
- SMTP-only: When SendGrid is not configured, SMTP is used directly.
"""

import smtplib
from datetime import date
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from app.utils.logger import logger

from app.config import settings


class EmailService:
    """
    Email delivery service supporting SendGrid (primary) and SMTP (fallback).

    Provider selection:
    1. If SendGrid API key is set and valid → use SendGrid.
    2. If SendGrid fails and SMTP is configured → fall back to SMTP.
    3. If only SMTP is configured → use SMTP directly.
    4. If neither is configured → return False and log error.

    Usage:
        service = EmailService()
        await service.send_digest_email(
            recipients=["user@example.com"],
            subject="Zentivra AI Radar — 2024-01-15",
            executive_summary="Today's key findings...",
            pdf_path="/path/to/digest.pdf",
        )
    """

    async def send_digest_email(
        self,
        recipients: list[str],
        subject: str,
        executive_summary: str,
        pdf_path: Optional[str] = None,
        dashboard_url: str = "http://localhost:3000",
    ) -> bool:
        """
        Send the daily digest email to recipients.

        Normalizes and deduplicates recipients, builds HTML body, and sends
        via SendGrid or SMTP (with fallback as documented in module docstring).
        Skips send if no recipients or email is not configured.

        Args:
            recipients: List of email addresses.
            subject: Email subject line.
            executive_summary: Summary text for the email body.
            pdf_path: Optional path to PDF attachment.
            dashboard_url: Link to web dashboard in the email.

        Returns:
            True if sent successfully, False otherwise.
        """
        normalized_recipients = [
            r.strip().lower() for r in recipients if isinstance(r, str) and r.strip()
        ]
        # Preserve insertion order while removing duplicates.
        normalized_recipients = list(dict.fromkeys(normalized_recipients))

        if not normalized_recipients:
            logger.warning("no_email_recipients")
            return False

        if not settings.has_email_configured:
            logger.warning("email_not_configured")
            return False

        # Build HTML email body
        html_body = self._build_email_body(executive_summary, dashboard_url, pdf_path)

        try:
            use_sendgrid = bool(
                settings.sendgrid_api_key
                and settings.sendgrid_api_key != "your-sendgrid-api-key-here"
            )
            use_smtp = bool(settings.smtp_host)

            if use_sendgrid:
                sent = await self._send_via_sendgrid(
                    normalized_recipients, subject, html_body, pdf_path
                )
                if sent:
                    return True
                # Fall back to SMTP when SendGrid is configured but unavailable.
                if use_smtp:
                    logger.warning("sendgrid_failed_falling_back_to_smtp")
                    return await self._send_via_smtp(
                        normalized_recipients, subject, html_body, pdf_path
                    )
                return False

            if use_smtp:
                return await self._send_via_smtp(
                    normalized_recipients, subject, html_body, pdf_path
                )

            logger.error("no_email_provider_configured")
            return False

        except Exception as e:
            logger.error("email_send_error error=%s", str(e))
            return False

    async def _send_via_sendgrid(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        pdf_path: Optional[str],
    ) -> bool:
        """
        Send email via SendGrid API.

        Attaches PDF if pdf_path exists. Returns True for status 200/201/202.
        Returns False on ImportError (sendgrid not installed) or API/network errors.
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import (
                Attachment,
                ContentId,
                Disposition,
                FileContent,
                FileName,
                FileType,
                Mail,
            )
            import base64

            message = Mail(
                from_email=settings.email_from,
                to_emails=recipients,
                subject=subject,
                html_content=html_body,
            )

            # Attach PDF
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    pdf_data = base64.b64encode(f.read()).decode()

                attachment = Attachment(
                    FileContent(pdf_data),
                    FileName(Path(pdf_path).name),
                    FileType("application/pdf"),
                    Disposition("attachment"),
                )
                message.attachment = attachment

            sg = SendGridAPIClient(settings.sendgrid_api_key)
            response = sg.send(message)

            logger.info(
                "email_sent_sendgrid recipients=%d status=%d",
                len(recipients),
                response.status_code,
            )
            return response.status_code in (200, 201, 202)

        except ImportError:
            logger.error("sendgrid_not_installed")
            return False
        except Exception as e:
            logger.error("sendgrid_error error=%s", str(e))
            return False

    async def _send_via_smtp(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        pdf_path: Optional[str],
    ) -> bool:
        """
        Send email via SMTP (e.g., Gmail, custom mail server).

        Uses SMTP_SSL or SMTP with optional STARTTLS. Attaches PDF if pdf_path
        exists. Normalizes Gmail app passwords (removes spaces) when applicable.
        Returns False on connection/auth/send errors.
        """
        try:
            msg = MIMEMultipart("mixed")
            msg["From"] = settings.email_from
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            # HTML body
            msg.attach(MIMEText(html_body, "html"))

            # PDF attachment
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=Path(pdf_path).name,
                    )
                    msg.attach(pdf_attachment)

            # Send
            smtp_cls = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
            with smtp_cls(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as server:
                if not settings.smtp_use_ssl and settings.smtp_use_tls:
                    server.starttls()

                if settings.smtp_user:
                    smtp_password = (settings.smtp_password or "").strip()
                    smtp_host = (settings.smtp_host or "").lower()
                    # Gmail app passwords are often copied with spaces; normalize safely.
                    if "gmail.com" in smtp_host and " " in smtp_password:
                        compact = "".join(smtp_password.split())
                        if compact:
                            smtp_password = compact
                    server.login(settings.smtp_user.strip(), smtp_password)

                server.send_message(msg)

            logger.info(
                "email_sent_smtp recipients=%d host=%s",
                len(recipients),
                settings.smtp_host,
            )
            return True

        except Exception as e:
            logger.error("smtp_error error=%s", str(e))
            return False

    def _build_email_body(
        self,
        executive_summary: str,
        dashboard_url: str,
        pdf_path: Optional[str],
    ) -> str:
        """
        Build HTML email body with executive summary and dashboard CTA.

        Converts markdown-style newlines to HTML. Includes styled header,
        summary block, and footer. pdf_path is unused but kept for API consistency.
        """
        today = date.today().strftime("%B %d, %Y")

        # Convert markdown-ish text to basic HTML
        summary_html = executive_summary.replace("\n\n", "</p><p>").replace(
            "\n", "<br>"
        )
        if not summary_html.startswith("<p>"):
            summary_html = f"<p>{summary_html}</p>"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a2e; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 24px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; }}
                .header p {{ margin: 4px 0 0; opacity: 0.9; }}
                .content {{ background: #fff; padding: 24px; border: 1px solid #e0e4ef; }}
                .summary {{ background: #f8f9ff; border-left: 4px solid #667eea;
                           padding: 16px; margin: 16px 0; border-radius: 0 6px 6px 0; }}
                .cta {{ display: inline-block; background: #667eea; color: white;
                       padding: 10px 24px; text-decoration: none; border-radius: 6px;
                       font-weight: 600; margin: 16px 0; }}
                .footer {{ text-align: center; padding: 16px; color: #888; font-size: 12px;
                          border-top: 1px solid #e0e4ef; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ZENTIVRA</h1>
                    <p>Frontier AI Radar — {today}</p>
                </div>
                <div class="content">
                    <h2>Executive Summary</h2>
                    <div class="summary">
                        {summary_html}
                    </div>
                    <p>The full digest is attached as a PDF.</p>
                    <a href="{dashboard_url}" class="cta">View Dashboard →</a>
                </div>
                <div class="footer">
                    <p>Generated by Zentivra AI Radar</p>
                    <p>You're receiving this because you're on the research distribution list.</p>
                </div>
            </div>
        </body>
        </html>
        """
