from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Any

from .exceptions import SafetyViolationError
from .models import Operation, Task
from .safety import apply_operation_to_content, validate_content_change


@dataclass
class HandlerResult:
    changed: bool
    patch_payload: dict
    warnings: list[str]
    diff_summary: str
    chars_delta: int


def _extract_rendered_content(resource: dict) -> str:
    content = resource.get("content")
    if isinstance(content, dict):
        # Prefer raw when available (context=edit) to avoid modifying already-rendered HTML.
        return content.get("raw") or content.get("rendered", "")
    return ""


def _extract_slot_body(content: str, slot_name: str) -> str:
    start = f"<!-- {slot_name} -->"
    end = f"<!-- /{slot_name} -->"
    pattern = re.escape(start) + r"(.*?)" + re.escape(end)
    m = re.search(pattern, content, flags=re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def _run_content_operations(before_content: str, operations: list[Operation]) -> tuple[str, list[str], str, int]:
    after_content = before_content
    warnings: list[str] = []
    combined_diff: list[str] = []

    for operation in operations:
        if operation.scope != "content":
            # Non-content ops (e.g. set_fields) are handled elsewhere.
            continue
        if (operation.selector.kind or "html_comment").lower() not in {"html_comment", "comment", "regex", "re"}:
            raise SafetyViolationError(f"Unsupported selector.kind: {operation.selector.kind}")

        next_content, diff = apply_operation_to_content(after_content, operation)
        validate_content_change(after_content, next_content, operation)
        after_content = next_content
        combined_diff.append(diff)

    return after_content, warnings, "\n\n".join([d for d in combined_diff if d]), len(after_content) - len(before_content)


def handle_update_post_or_page(before: dict, operations: list[Operation]) -> HandlerResult:
    before_content = _extract_rendered_content(before)
    # Two kinds of updates are supported:
    # - content slot/regex edits (scope=content)
    # - field updates like status/slug/title (op=set_fields, scope=fields)
    after_content, warnings, diff_summary, chars_delta = _run_content_operations(before_content, operations)

    field_patch: dict[str, Any] = {}
    for operation in operations:
        if operation.op != "set_fields" or operation.scope != "fields":
            continue
        if operation.content.format != "json" or not isinstance(operation.content.value, dict):
            raise SafetyViolationError("set_fields requires content.format=json and value object")

        allowed_fields = {"status", "title", "slug", "excerpt"}
        patch = {k: v for k, v in operation.content.value.items() if k in allowed_fields}
        if not patch:
            raise SafetyViolationError("set_fields has no allowed fields (status/title/slug/excerpt)")

        if "status" in patch:
            status = str(patch["status"]).strip().lower()
            if status not in {"draft", "publish", "private", "pending"}:
                raise SafetyViolationError(f"Unsupported status: {status}")
            patch["status"] = status

        approx_chars = sum(len(str(v)) for v in patch.values())
        if approx_chars > operation.safety.max_chars_change:
            raise SafetyViolationError(
                f"set_fields chars changed {approx_chars} > max_chars_change {operation.safety.max_chars_change}"
            )

        field_patch.update(patch)

    changed = (after_content != before_content) or bool(field_patch)
    if not changed:
        return HandlerResult(False, {}, warnings, "", 0)

    payload: dict[str, Any] = {
        "modified_gmt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if after_content != before_content:
        payload["content"] = after_content
    payload.update(field_patch)

    return HandlerResult(True, payload, warnings, diff_summary, chars_delta)


def handle_append_internal_links(before: dict, operations: list[Operation]) -> HandlerResult:
    if not operations:
        raise SafetyViolationError("append_internal_links requires operations")

    before_content = _extract_rendered_content(before)
    derived_ops: list[Operation] = []
    warnings: list[str] = []

    for operation in operations:
        if operation.scope != "content":
            warnings.append(f"skip non-content op: {operation.scope}")
            continue

        slot_body = _extract_slot_body(before_content, operation.selector.value)
        existing_urls = set(re.findall(r"https?://[^\s\"']+", slot_body))

        links_payload = operation.content.value
        if isinstance(links_payload, dict):
            links_payload = links_payload.get("links", [])
        if not isinstance(links_payload, list):
            raise SafetyViolationError("append_internal_links content.value must be list or {links:[]}")

        new_lines: list[str] = []
        inserted = 0
        for item in links_payload:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            anchor = str(item.get("anchor", "")).strip() or "Read more"
            if not url or url in existing_urls:
                continue
            existing_urls.add(url)
            new_lines.append(f'<a href="{escape(url)}">{escape(anchor)}</a>')
            inserted += 1
            if inserted >= 3:
                break

        if not new_lines:
            warnings.append(f"no new links inserted for slot {operation.selector.value}")
            continue

        html = "<p>Related reads: " + " | ".join(new_lines) + "</p>"
        derived_ops.append(
            Operation(
                op="append",
                scope="content",
                selector=operation.selector,
                content=operation.content.__class__(format="html", value=html),
                safety=operation.safety,
            )
        )

    merged_ops = derived_ops if derived_ops else []
    after_content, run_warnings, diff_summary, chars_delta = _run_content_operations(before_content, merged_ops)
    warnings.extend(run_warnings)

    if after_content == before_content:
        return HandlerResult(False, {}, warnings, "", 0)

    payload = {
        "content": after_content,
        "modified_gmt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return HandlerResult(True, payload, warnings, diff_summary, chars_delta)


def _build_faq_html(faqs: list[dict]) -> str:
    blocks: list[str] = [
        "<style>"
        ".ai-faq-accordion details{margin:0 0 18px;border:1px solid #dfe5ee;border-radius:12px;background:#fff;overflow:hidden}"
        ".ai-faq-accordion summary{cursor:pointer;list-style:none;padding:16px 18px;font-weight:700;line-height:1.6}"
        ".ai-faq-accordion summary::-webkit-details-marker{display:none}"
        ".ai-faq-accordion details[open] summary{border-bottom:1px solid #e8edf5}"
        ".ai-faq-accordion p{margin:0;padding:16px 18px 18px;line-height:1.8;color:#334155}"
        "</style>",
        "<div class=\"ai-faq-accordion\">",
    ]
    for item in faqs:
        q = escape(str(item.get("question", "")))
        a = escape(str(item.get("answer", "")))
        if not q or not a:
            continue
        blocks.append(f"<details><summary><strong>{q}</strong></summary><p>{a}</p></details>")
    blocks.append("</div>")
    return "\n".join(blocks)


def _build_faq_json_ld(faqs: list[dict]) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": str(item.get("question", "")),
                "acceptedAnswer": {"@type": "Answer", "text": str(item.get("answer", ""))},
            }
            for item in faqs
            if item.get("question") and item.get("answer")
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False) + "</script>"


def handle_inject_schema_faq(before: dict, operations: list[Operation]) -> HandlerResult:
    before_content = _extract_rendered_content(before)
    derived_ops: list[Operation] = []
    warnings: list[str] = []

    for operation in operations:
        data = operation.content.value
        if not isinstance(data, dict):
            raise SafetyViolationError("inject_schema_faq content.value must be json object")

        faqs = data.get("faqs") or []
        if not isinstance(faqs, list) or len(faqs) < 1:
            raise SafetyViolationError("inject_schema_faq requires at least one faq")
        faqs = faqs[:6]

        faq_html = _build_faq_html(faqs)
        derived_ops.append(
            Operation(
                op="replace",
                scope="content",
                selector=operation.selector,
                content=operation.content.__class__(format="html", value=faq_html),
                safety=operation.safety,
            )
        )

        if data.get("inject_json_ld", False):
            schema_slot = str(data.get("schema_slot", "AI_SLOT:SCHEMA"))
            schema_html = _build_faq_json_ld(faqs)
            derived_ops.append(
                Operation(
                    op="replace",
                    scope="content",
                    selector=operation.selector.__class__(kind="html_comment", value=schema_slot),
                    content=operation.content.__class__(format="html", value=schema_html),
                    safety=operation.safety,
                )
            )

    after_content, run_warnings, diff_summary, chars_delta = _run_content_operations(before_content, derived_ops)
    warnings.extend(run_warnings)

    if after_content == before_content:
        return HandlerResult(False, {}, warnings, "", 0)

    payload = {
        "content": after_content,
        "modified_gmt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return HandlerResult(True, payload, warnings, diff_summary, chars_delta)


def handle_generate_topic_hub(before: dict, operations: list[Operation]) -> HandlerResult:
    before_content = _extract_rendered_content(before)
    derived_ops: list[Operation] = []

    for operation in operations:
        data = operation.content.value
        if not isinstance(data, dict):
            raise SafetyViolationError("generate_topic_hub content.value must be json object")

        hub_title = escape(str(data.get("hub_title", "Topic Hub")))
        items = data.get("items") or []
        if not isinstance(items, list) or not items:
            raise SafetyViolationError("generate_topic_hub requires items[]")

        lines = [f"<section class=\"ai-topic-hub\"><h2>{hub_title}</h2><ol>"]
        for item in items[:20]:
            if not isinstance(item, dict):
                continue
            title = escape(str(item.get("title", "Untitled")))
            url = escape(str(item.get("url", "#")))
            summary = escape(str(item.get("summary", "")))
            if summary:
                lines.append(f"<li><a href=\"{url}\">{title}</a><p>{summary}</p></li>")
            else:
                lines.append(f"<li><a href=\"{url}\">{title}</a></li>")
        lines.append("</ol></section>")
        html = "\n".join(lines)

        derived_ops.append(
            Operation(
                op="replace",
                scope="content",
                selector=operation.selector,
                content=operation.content.__class__(format="html", value=html),
                safety=operation.safety,
            )
        )

    after_content, warnings, diff_summary, chars_delta = _run_content_operations(before_content, derived_ops)

    if after_content == before_content:
        return HandlerResult(False, {}, warnings, "", 0)

    payload = {
        "content": after_content,
        "modified_gmt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return HandlerResult(True, payload, warnings, diff_summary, chars_delta)


def handle_update_taxonomy_term(operations: list[Operation]) -> HandlerResult:
    if not operations:
        raise SafetyViolationError("update_taxonomy_term requires operations")
    op = operations[0]
    desc = str(op.content.value)
    if len(desc) > op.safety.max_chars_change:
        raise SafetyViolationError(
            f"term_description chars {len(desc)} > max_chars_change {op.safety.max_chars_change}"
        )
    return HandlerResult(
        changed=True,
        patch_payload={"description": desc},
        warnings=[],
        diff_summary="term description updated",
        chars_delta=len(desc),
    )


def handle_publish_post(operations: list[Operation]) -> HandlerResult:
    if not operations:
        raise SafetyViolationError("publish_post requires operations")
    op = operations[0]
    if not isinstance(op.content.value, dict):
        raise SafetyViolationError("publish_post content.value must be json object")
    payload = dict(op.content.value)
    allowed_fields = {
        "type",
        "status",
        "title",
        "content",
        "excerpt",
        "slug",
        "categories",
        "tags",
        "featured_media",
        "meta",
    }
    filtered = {k: v for k, v in payload.items() if k in allowed_fields}
    if not filtered.get("title") or not filtered.get("content"):
        raise SafetyViolationError("publish_post requires title and content")
    if "status" not in filtered:
        filtered["status"] = "draft"

    chars_delta = len(str(filtered.get("title", ""))) + len(str(filtered.get("content", "")))
    if chars_delta > op.safety.max_chars_change:
        raise SafetyViolationError(
            f"publish_post chars {chars_delta} > max_chars_change {op.safety.max_chars_change}"
        )

    return HandlerResult(
        changed=True,
        patch_payload=filtered,
        warnings=[],
        diff_summary=f"publish_post fields: {', '.join(sorted(filtered.keys()))}",
        chars_delta=chars_delta,
    )


def handle_upload_media(operations: list[Operation]) -> HandlerResult:
    if not operations:
        raise SafetyViolationError("upload_media requires operations")
    op = operations[0]
    if not isinstance(op.content.value, dict):
        raise SafetyViolationError("upload_media content.value must be json object")
    payload = dict(op.content.value)
    if "file_path" not in payload:
        raise SafetyViolationError("upload_media requires file_path")
    return HandlerResult(
        changed=True,
        patch_payload=payload,
        warnings=[],
        diff_summary="upload_media payload prepared",
        chars_delta=len(str(payload.get("file_path", ""))),
    )


def handle_set_meta(before: dict, operations: list[Operation]) -> HandlerResult:
    meta_updates: dict[str, Any] = {}
    warnings: list[str] = []

    for operation in operations:
        if operation.op != "set_meta" or operation.scope != "meta":
            warnings.append(f"skip non-meta operation: {operation.op}/{operation.scope}")
            continue
        if operation.content.format != "json" or not isinstance(operation.content.value, dict):
            raise SafetyViolationError("set_meta requires content.format=json and value object")

        new_chars = sum(len(str(v)) for v in operation.content.value.values())
        if new_chars > operation.safety.max_chars_change:
            raise SafetyViolationError(
                f"meta chars changed {new_chars} > max_chars_change {operation.safety.max_chars_change}"
            )
        meta_updates.update(operation.content.value)

    if not meta_updates:
        return HandlerResult(False, {}, warnings, "", 0)

    return HandlerResult(
        changed=True,
        patch_payload={"meta": meta_updates},
        warnings=warnings,
        diff_summary=f"meta keys updated: {', '.join(sorted(meta_updates.keys()))}",
        chars_delta=sum(len(str(v)) for v in meta_updates.values()),
    )


def handle_report_only(task: Task) -> HandlerResult:
    note = task.notes or "report_only mode"
    return HandlerResult(
        changed=False,
        patch_payload={},
        warnings=[],
        diff_summary=f"report_only: {note}",
        chars_delta=0,
    )
