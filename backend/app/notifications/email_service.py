"""
Email Notification Service - Send digest emails via SendGrid or SMTP.

Sends:
- Executive summary snippet as email body
- PDF attachment
- Link to web dashboard
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
    Email delivery service supporting SendGrid and SMTP.

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
        Send the daily digest email.

        Returns True if sent successfully, False otherwise.
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
        html_body = self._build_email_body(
            executive_summary, dashboard_url, pdf_path
        )

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
        """Send email via SendGrid API."""
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
        """Send email via SMTP (e.g., Gmail)."""
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
        """Build a nice HTML email body."""
        today = date.today().strftime("%B %d, %Y")

        # Convert markdown-ish text to basic HTML
        summary_html = executive_summary.replace("\n\n", "</p><p>").replace("\n", "<br>")
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
