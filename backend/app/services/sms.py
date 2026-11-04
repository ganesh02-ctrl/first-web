"""SMS via Twilio or a generic HTTP gateway. 'none' => always skipped, never reported as sent."""
import logging
import re

import requests
from flask import current_app

from app.services.email import SendResult

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    cfg = current_app.config
    provider = cfg.get("SMS_PROVIDER", "none")
    if provider == "twilio":
        return all([cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"], cfg["TWILIO_FROM_NUMBER"]])
    if provider == "http":
        return bool(cfg["SMS_HTTP_ENDPOINT"])
    return False


def normalize_number(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+"):
        return digits
    if len(digits) == 10:
        return current_app.config["SMS_DEFAULT_COUNTRY_CODE"] + digits
    return "+" + digits


def send_sms(to: str, message: str) -> SendResult:
    if not is_configured():
        return SendResult(False, error="SMS provider not configured", skipped=True)
    number = normalize_number(to)
    if not number:
        return SendResult(False, error="No phone number", skipped=True)
    cfg = current_app.config
    try:
        if cfg["SMS_PROVIDER"] == "twilio":
            sid = cfg["TWILIO_ACCOUNT_SID"]
            resp = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                data={"To": number, "From": cfg["TWILIO_FROM_NUMBER"], "Body": message[:1500]},
                auth=(sid, cfg["TWILIO_AUTH_TOKEN"]), timeout=20)
            if resp.status_code in (200, 201):
                return SendResult(True, provider_id=resp.json().get("sid"))
            return SendResult(False, error=f"Twilio HTTP {resp.status_code}: {resp.text[:500]}")
        headers = {"Content-Type": "application/json"}
        if cfg["SMS_HTTP_API_KEY"]:
            headers["Authorization"] = f"Bearer {cfg['SMS_HTTP_API_KEY']}"
        resp = requests.post(cfg["SMS_HTTP_ENDPOINT"], json={"to": number, "message": message[:1500]},
                             headers=headers, timeout=20)
        if 200 <= resp.status_code < 300:
            body = resp.json() if "json" in resp.headers.get("Content-Type", "") else {}
            return SendResult(True, provider_id=str(body.get("id") or body.get("message_id") or "") or None)
        return SendResult(False, error=f"SMS HTTP {resp.status_code}: {resp.text[:500]}")
    except requests.RequestException as exc:
        logger.warning("SMS to %s failed: %s", number, exc)
        return SendResult(False, error=str(exc)[:1000])
