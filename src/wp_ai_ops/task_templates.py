from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .exceptions import TaskValidationError


_TEMPLATE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    cursor: Any = context
    for part in path.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            raise TaskValidationError(f"Template variable not found: {path}")
        cursor = cursor[part]
    return cursor


def _render_string(raw: str, context: dict[str, Any]) -> Any:
    matches = list(_TEMPLATE_PATTERN.finditer(raw))
    if not matches:
        return raw

    # If the full string is a single placeholder, preserve native type.
    if len(matches) == 1 and matches[0].span() == (0, len(raw)):
        return _resolve_path(context, matches[0].group(1))

    parts: list[str] = []
    last = 0
    for m in matches:
        parts.append(raw[last:m.start()])
        value = _resolve_path(context, m.group(1))
        if isinstance(value, (dict, list)):
            raise TaskValidationError(
                f"Template variable {m.group(1)} resolved to non-scalar in inline string context"
            )
        parts.append(str(value))
        last = m.end()
    parts.append(raw[last:])
    return "".join(parts)


def _render_obj(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return _render_string(value, context)
    if isinstance(value, list):
        return [_render_obj(v, context) for v in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, val in value.items():
            if key in {"site_profile", "site_profile_ref"}:
                continue
            out[key] = _render_obj(val, context)
        return out
    return value


def _read_profile_ref(task_path: Path, ref: str) -> dict[str, Any]:
    ref_path = Path(ref)
    if not ref_path.is_absolute():
        ref_path = (task_path.parent / ref_path).resolve()
    if not ref_path.exists():
        raise TaskValidationError(f"site_profile_ref not found: {ref_path}")
    try:
        payload = json.loads(ref_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise TaskValidationError(f"Invalid site_profile_ref JSON: {ref_path}") from exc
    if not isinstance(payload, dict):
        raise TaskValidationError("site_profile_ref must point to a JSON object")
    return payload


def render_task_payload(task_payload: dict[str, Any], *, task_path: Path) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    ref = task_payload.get("site_profile_ref")
    if ref:
        if not isinstance(ref, str):
            raise TaskValidationError("site_profile_ref must be a string path")
        profile = _read_profile_ref(task_path, ref)

    inline_profile = task_payload.get("site_profile")
    if inline_profile:
        if not isinstance(inline_profile, dict):
            raise TaskValidationError("site_profile must be a JSON object")
        profile = _deep_merge(profile, inline_profile)

    if not profile and "{{" not in json.dumps(task_payload, ensure_ascii=False):
        # Fast path: no template usage and no profile overlay.
        return {k: v for k, v in task_payload.items() if k not in {"site_profile", "site_profile_ref"}}

    context = _deep_merge({"site": task_payload.get("site", {})}, profile)
    rendered = _render_obj(task_payload, context)
    if not isinstance(rendered, dict):
        raise TaskValidationError("Rendered task payload must be an object")
    return rendered

