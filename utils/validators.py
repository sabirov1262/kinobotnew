from __future__ import annotations

import re


HTTPS_RE = re.compile(r"^https://[^\s]+$", re.IGNORECASE)
TELEGRAM_USERNAME_RE = re.compile(r"^@[A-Za-z0-9_]{5,}$")
TELEGRAM_ID_RE = re.compile(r"^-100\d{6,}$")
TELEGRAM_TME_RE = re.compile(r"^https://t\.me/(?:\+)?[A-Za-z0-9_+/=-]+$", re.IGNORECASE)


def is_https_url(text: str) -> bool:
    return bool(HTTPS_RE.match(text.strip()))


def classify_subscription_value(value: str) -> str | None:
    value = value.strip()
    if TELEGRAM_USERNAME_RE.match(value) or TELEGRAM_ID_RE.match(value) or TELEGRAM_TME_RE.match(value):
        return "telegram"
    if value.startswith("https://t.me/+"):
        return "private"
    if is_https_url(value):
        return "external"
    return None
