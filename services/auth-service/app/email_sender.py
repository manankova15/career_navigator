"""
Lightweight SMTP sender for transactional emails (password reset).

Synchronous smtplib is wrapped in `asyncio.run_in_executor` so that a slow
SMTP server does not block the FastAPI event loop.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings

logger = logging.getLogger(__name__)


def _from_address() -> str:
    return settings.smtp_from_address or settings.smtp_username


def _send_sync(to_address: str, subject: str, body: str, html_body: str) -> None:
    from_addr = _from_address()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{from_addr}>"
    msg["To"] = to_address

    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(from_addr, [to_address], msg.as_string())
    logger.info("Email sent to %s subject=%r", to_address, subject)


async def send_email(to_address: str, subject: str, body: str, html_body: str) -> bool:
    """Send email asynchronously. Returns True if the SMTP call succeeded."""
    if not settings.smtp_host or not _from_address():
        logger.warning("SMTP not configured, skipping email to %s", to_address)
        return False
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync, to_address, subject, body, html_body)
        return True
    except Exception as exc:  # pragma: no cover — depends on external SMTP
        logger.error("Failed to send email to %s: %s", to_address, exc)
        return False


def build_password_reset_email(full_name: str, new_password: str) -> tuple[str, str, str]:
    """Returns (subject, plain_body, html_body) for the password reset email."""
    subject = "Career Navigator — восстановление пароля"
    plain = (
        f"Здравствуйте, {full_name or 'пользователь'}!\n\n"
        f"Мы получили запрос на восстановление пароля для вашей учётной записи "
        f"в Career Navigator.\n\n"
        f"Ваш временный пароль: {new_password}\n\n"
        f"Войдите с этим паролем и обязательно смените его в настройках профиля.\n\n"
        f"Если вы не запрашивали восстановление — просто проигнорируйте это письмо.\n"
    )
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; color: #0F172A;">
      <h2 style="margin: 0 0 16px; color: #4F46E5;">Восстановление пароля</h2>
      <p>Здравствуйте, <strong>{full_name or 'пользователь'}</strong>!</p>
      <p>Мы получили запрос на восстановление пароля для вашей учётной записи в&nbsp;Career&nbsp;Navigator.</p>
      <p>Ваш временный пароль:</p>
      <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 12px; padding: 16px 20px; font-family: 'SF Mono', Menlo, monospace; font-size: 18px; font-weight: 700; letter-spacing: 0.04em; color: #4338CA; text-align: center;">
        {new_password}
      </div>
      <p style="margin-top: 16px;">Войдите с этим паролем и&nbsp;обязательно смените его в&nbsp;настройках профиля.</p>
      <p style="color: #64748B; font-size: 13px;">Если вы не запрашивали восстановление — просто проигнорируйте это письмо.</p>
    </div>
    """
    return subject, plain, html
