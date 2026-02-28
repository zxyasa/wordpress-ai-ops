from __future__ import annotations

import difflib
import re

from .exceptions import SafetyViolationError
from .models import Operation


def _slot_marker(slot_name: str) -> str:
    return f"<!-- {slot_name} -->"


def apply_slot_replace(content: str, slot_name: str, new_html: str) -> str:
    start_marker = _slot_marker(slot_name)
    end_marker = _slot_marker(f"/{slot_name}")

    if start_marker in content and end_marker in content:
        pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
        replacement = f"{start_marker}\n{new_html}\n{end_marker}"
        return re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    if start_marker in content:
        insertion = f"{start_marker}\n{new_html}\n{end_marker}"
        return content.replace(start_marker, insertion, 1)

    raise SafetyViolationError(f"Missing AI slot marker: {slot_name}")


def ensure_slot_markers(content: str, slot_names: list[str]) -> str:
    # Insert missing slot markers as HTML comments. This is intentionally minimal and
    # should not affect Flatsome/shortcodes rendering.
    to_add: list[str] = []
    for slot in slot_names:
        start_marker = _slot_marker(slot)
        end_marker = _slot_marker(f"/{slot}")
        if start_marker in content and end_marker in content:
            continue
        if start_marker in content and end_marker not in content:
            # Add missing end marker right after the start marker.
            content = content.replace(start_marker, f"{start_marker}{end_marker}", 1)
            continue
        if start_marker not in content and end_marker in content:
            # Edge case: end exists without start; add a start marker before end.
            content = content.replace(end_marker, f"{start_marker}{end_marker}", 1)
            continue
        to_add.append(f"{start_marker}{end_marker}")

    if not to_add:
        return content
    prefix = "\n".join(to_add) + "\n"
    return prefix + content


def _apply_regex_op(before_content: str, operation: Operation) -> str:
    pattern = str(operation.selector.value)
    new = str(operation.content.value)
    try:
        rx = re.compile(pattern, flags=re.DOTALL)
    except re.error as e:
        raise SafetyViolationError(f"Invalid regex selector: {e}") from e

    m = rx.search(before_content)
    if not m:
        raise SafetyViolationError("Regex selector did not match any content")

    if operation.op == "replace":
        return rx.sub(new, before_content, count=1)
    if operation.op == "append":
        # Insert right after the first match.
        return before_content[: m.end()] + new + before_content[m.end() :]
    if operation.op == "prepend":
        # Insert right before the first match.
        return before_content[: m.start()] + new + before_content[m.start() :]
    raise SafetyViolationError(f"Unsupported regex op: {operation.op}")


def apply_operation_to_content(before_content: str, operation: Operation) -> tuple[str, str]:
    selector_kind = (operation.selector.kind or "html_comment").lower()
    slot_name = operation.selector.value
    if operation.op not in {"replace", "append", "prepend", "ensure_slots"}:
        raise SafetyViolationError(f"Unsupported content op for MVP: {operation.op}")

    if operation.op == "ensure_slots":
        raw = operation.content.value
        if isinstance(raw, dict):
            slots = raw.get("slots", [])
        else:
            slots = raw
        if not isinstance(slots, list) or not all(isinstance(s, str) and s for s in slots):
            raise SafetyViolationError("ensure_slots requires content.value as list[str] or {slots:[...]}")
        after_content = ensure_slot_markers(before_content, slots)
    elif selector_kind in {"regex", "re"}:
        after_content = _apply_regex_op(before_content, operation)
    elif selector_kind in {"html_comment", "comment"}:
        if operation.op == "replace":
            after_content = apply_slot_replace(before_content, slot_name, str(operation.content.value))
        else:
            existing = ""
            start_marker = _slot_marker(slot_name)
            end_marker = _slot_marker(f"/{slot_name}")
            pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
            match = re.search(pattern, before_content, flags=re.DOTALL)
            if match:
                existing = match.group(1).strip()

            if operation.op == "append":
                next_content = (existing + "\n" + str(operation.content.value)).strip()
            else:
                next_content = (str(operation.content.value) + "\n" + existing).strip()

            after_content = apply_slot_replace(before_content, slot_name, next_content)
    else:
        raise SafetyViolationError(f"Unsupported selector.kind: {operation.selector.kind}")

    diff = "\n".join(
        difflib.unified_diff(
            before_content.splitlines(),
            after_content.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )
    return after_content, diff


def validate_content_change(before: str, after: str, operation: Operation) -> None:
    safety = operation.safety
    delta = abs(len(after) - len(before))
    if delta > safety.max_chars_change:
        raise SafetyViolationError(
            f"chars changed {delta} > max_chars_change {safety.max_chars_change}"
        )

    for token in safety.forbid_remove:
        if token in before and token not in after:
            raise SafetyViolationError(f"forbid_remove token lost: {token}")

    if operation.op != "ensure_slots":
        selector_kind = (operation.selector.kind or "html_comment").lower()
        if selector_kind in {"html_comment", "comment"}:
            if not safety.allow_full_replace and before.strip() and after.strip() and before.strip() != after.strip():
                # For comment-slot ops, enforce slot marker still present post update.
                slot_marker = _slot_marker(operation.selector.value)
                if slot_marker not in after:
                    raise SafetyViolationError("slot marker missing after update")
