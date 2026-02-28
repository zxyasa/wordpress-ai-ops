"""Telegram notification via stdlib urllib (no extra dependencies)."""
from __future__ import annotations

import json
import urllib.request
import urllib.error

_MAX_MSG_LEN = 4000


def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send a message via Telegram Bot API.

    Long messages (>4000 chars) are automatically split into chunks.
    Returns *True* if all chunks were sent successfully.
    """
    chunks = _split_message(message)
    ok = True
    for chunk in chunks:
        if not _send_chunk(bot_token, chat_id, chunk):
            ok = False
    return ok


def _split_message(text: str) -> list[str]:
    if len(text) <= _MAX_MSG_LEN:
        return [text]
    parts: list[str] = []
    while text:
        if len(text) <= _MAX_MSG_LEN:
            parts.append(text)
            break
        # Try to split at a newline near the limit
        idx = text.rfind("\n", 0, _MAX_MSG_LEN)
        if idx == -1:
            idx = _MAX_MSG_LEN
        parts.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return parts


def _send_chunk(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False
