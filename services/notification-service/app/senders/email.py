"""
SMTP email sender.

Runs synchronous smtplib in a thread-pool executor so it doesn't block
the FastAPI event loop.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings

logger = logging.getLogger(__name__)


def _send_sync(to_address: str, subject: str, body: str, html_body: str) -> None:
    """Blocking SMTP send — must be called in a thread executor."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_address}>"
    msg["To"] = to_address

    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_address, [to_address], msg.as_string())
    logger.info("Email sent to %s subject=%r", to_address, subject)


async def send_email(to_address: str, subject: str, body: str, html_body: str) -> None:
    """Async wrapper: runs SMTP in a thread pool so it never blocks the loop."""
    if not settings.smtp_host or not settings.smtp_from_address:
        logger.warning("SMTP not configured, skipping email to %s", to_address)
        return
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to_address, subject, body, html_body)
