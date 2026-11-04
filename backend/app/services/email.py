"""SMTP email. Returns a result; never reports success unless the SMTP server accepted the message."""
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    ok: bool
    provider_id: str | None = None
    error: str | None = None
    skipped: bool = False


def is_configured() -> bool:
    return bool(current_app.config.get("SMTP_HOST"))


def send_email(to: str, subject: str, text: str, html: str | None = None) -> SendResult:
    if not is_configured():
        return SendResult(False, error="SMTP not configured", skipped=True)
    cfg = current_app.config
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg["MAIL_FROM"], to, subject
    msg_id = make_msgid(domain=cfg["MAIL_FROM"].split("@")[-1].strip(" >") or None)
    msg["Message-ID"] = msg_id
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    try:
        context = ssl.create_default_context()
        if cfg["SMTP_USE_SSL"]:
            server = smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], context=context, timeout=20)
        else:
            server = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20)
        with server:
            if cfg["SMTP_USE_TLS"] and not cfg["SMTP_USE_SSL"]:
                server.starttls(context=context)
            if cfg["SMTP_USERNAME"]:
                server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
            refused = server.send_message(msg)
        if refused:
            return SendResult(False, error=f"Recipient refused: {refused}")
        return SendResult(True, provider_id=msg_id)
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Email to %s failed: %s", to, exc)
        return SendResult(False, error=str(exc)[:1000])
