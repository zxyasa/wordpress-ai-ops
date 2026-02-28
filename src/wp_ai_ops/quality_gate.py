from __future__ import annotations

import re
from collections import Counter
from typing import Any


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"</p>|<br\s*/?>|\n{2,}", text, flags=re.IGNORECASE)
    out: list[str] = []
    for part in parts:
        clean = _strip_html(part).strip().lower()
        if clean:
            out.append(clean)
    return out


def evaluate_quality(*, content: str, site: dict[str, Any]) -> dict[str, Any]:
    policy = site.get("quality_policy") or {}
    threshold = int(policy.get("score_threshold", 70))
    max_exclamation = int(policy.get("max_exclamation", 4))
    min_chars = int(policy.get("min_chars", 120))
    forbidden_phrases = [str(x).strip().lower() for x in policy.get("forbidden_phrases", []) if str(x).strip()]
    required_brand_terms = [str(x).strip().lower() for x in policy.get("required_brand_terms", []) if str(x).strip()]

    plain = _strip_html(content)
    score = 100
    issues: list[str] = []

    if len(plain) < min_chars:
        score -= 20
        issues.append(f"content_too_short(<{min_chars})")

    exclamations = plain.count("!")
    if exclamations > max_exclamation:
        score -= 15
        issues.append(f"too_many_exclamations({exclamations}>{max_exclamation})")

    lower = plain.lower()
    for phrase in forbidden_phrases:
        if phrase in lower:
            score -= 15
            issues.append(f"forbidden_phrase:{phrase}")

    if required_brand_terms and not any(term in lower for term in required_brand_terms):
        score -= 20
        issues.append("missing_required_brand_term")

    paragraphs = _split_paragraphs(content)
    if paragraphs:
        counts = Counter(paragraphs)
        duplicates = sum(v - 1 for v in counts.values() if v > 1)
        if duplicates > 0:
            score -= min(30, duplicates * 10)
            issues.append(f"duplicate_paragraphs:{duplicates}")

    passed = score >= threshold
    return {
        "passed": passed,
        "score": max(0, score),
        "threshold": threshold,
        "issues": issues,
        "metrics": {
            "plain_chars": len(plain),
            "exclamation_count": exclamations,
            "paragraph_count": len(paragraphs),
        },
    }

