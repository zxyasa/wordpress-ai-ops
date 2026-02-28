from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import resolve_auth, resolve_site
from .exceptions import TargetNotFoundError, TaskValidationError
from .handlers import (
    handle_append_internal_links,
    handle_generate_topic_hub,
    handle_inject_schema_faq,
    handle_publish_post,
    handle_report_only,
    handle_set_meta,
    handle_upload_media,
    handle_update_post_or_page,
    handle_update_taxonomy_term,
)
from .models import Task, parse_task
from .quality_gate import evaluate_quality
from .storage import StateStore
from .target_resolver import resolve_target
from .task_templates import render_task_payload
from .ui_bridge import queue_ui_task
from .wp_client import WPClient


def _target_key(site_base: str, resource_type: str, resource_id: int) -> str:
    return f"{site_base}:{resource_type}:{resource_id}"


def _run_single_target(client: WPClient, task: Task, target_idx: int, store: StateStore, apply_changes: bool) -> dict:
    target = task.targets[target_idx]
    resource_type, resource = resolve_target(client, target)
    resource_id = int(resource["id"])
    key = _target_key(task.site.get("base_url", "unknown"), resource_type, resource_id)

    can_write, reason = store.allow_write(
        key,
        cooldown_hours=task.limits.cooldown_hours,
        max_write_per_target_7d=task.limits.max_write_per_target_7d,
    )
    if not can_write:
        return {"target": key, "status": "skipped", "reason": reason}

    before_content = None
    if isinstance(resource.get("content"), dict):
        before_content = resource.get("content", {}).get("raw") or resource.get("content", {}).get("rendered")
    store.write_snapshot(task.task_id, "before", key, resource, before_content)

    if task.task_type == "update_post_or_page":
        result = handle_update_post_or_page(resource, task.operations)
    elif task.task_type == "append_internal_links":
        result = handle_append_internal_links(resource, task.operations)
    elif task.task_type == "inject_schema_faq":
        result = handle_inject_schema_faq(resource, task.operations)
    elif task.task_type == "generate_topic_hub":
        result = handle_generate_topic_hub(resource, task.operations)
    elif task.task_type == "set_meta":
        result = handle_set_meta(resource, task.operations)
    elif task.task_type == "update_taxonomy_term":
        result = handle_update_taxonomy_term(task.operations)
    else:
        raise TaskValidationError(f"Unsupported executable task_type: {task.task_type}")

    if not result.changed:
        return {"target": key, "status": "noop", "warnings": result.warnings}

    # Content quality gate: on low score, downgrade writes to report_only-style result.
    if result.patch_payload.get("content"):
        quality = evaluate_quality(content=str(result.patch_payload["content"]), site=task.site)
        if not quality.get("passed", True):
            return {
                "target": key,
                "status": "downgraded_report_only",
                "reason": "quality_gate_failed",
                "quality": quality,
                "warnings": result.warnings,
                "diff_summary": result.diff_summary,
                "chars_delta": result.chars_delta,
            }

    if task.mode == "plan" or not apply_changes:
        return {
            "target": key,
            "status": "planned",
            "diff_summary": result.diff_summary,
            "warnings": result.warnings,
            "chars_delta": result.chars_delta,
        }

    updated = client.update_resource(resource_type, resource_id, result.patch_payload)
    after_content = None
    if isinstance(updated.get("content"), dict):
        after_content = updated.get("content", {}).get("raw") or updated.get("content", {}).get("rendered")
    store.write_snapshot(task.task_id, "after", key, updated, after_content)
    store.record_write(key)

    return {
        "target": key,
        "status": "updated",
        "warnings": result.warnings,
        "diff_summary": result.diff_summary,
        "chars_delta": result.chars_delta,
        "changed_fields": sorted(result.patch_payload.keys()),
    }


def _run_create_task(client: WPClient, task: Task, store: StateStore, apply_changes: bool) -> dict:
    if task.task_type == "publish_post":
        result = handle_publish_post(task.operations)
        if task.mode == "plan" or not apply_changes:
            return {
                "target": f"{task.site.get('base_url', 'unknown')}:post:new",
                "status": "planned",
                "diff_summary": result.diff_summary,
                "warnings": result.warnings,
                "chars_delta": result.chars_delta,
            }
        # Allow publish_post to create either a post or a page by passing payload.type.
        payload = dict(result.patch_payload)
        content_type = str(payload.pop("type", "post") or "post").strip().lower()
        if content_type not in {"post", "page"}:
            raise TaskValidationError(f"publish_post unsupported type: {content_type}")
        created = client.create_resource(content_type, payload)
        if not isinstance(created, dict) or "id" not in created:
            raise TaskValidationError("publish_post failed: missing created post id")
        key = _target_key(task.site.get("base_url", "unknown"), content_type, int(created["id"]))
        rendered = created.get("content", {}).get("rendered") if isinstance(created.get("content"), dict) else None
        store.write_snapshot(task.task_id, "after", key, created, rendered)
        store.record_write(key)
        return {
            "target": key,
            "status": "created",
            "warnings": result.warnings,
            "diff_summary": result.diff_summary,
            "chars_delta": result.chars_delta,
            "changed_fields": sorted(result.patch_payload.keys()),
        }

    if task.task_type == "upload_media":
        result = handle_upload_media(task.operations)
        payload = result.patch_payload
        if task.mode == "plan" or not apply_changes:
            return {
                "target": f"{task.site.get('base_url', 'unknown')}:media:new",
                "status": "planned",
                "diff_summary": result.diff_summary,
                "warnings": result.warnings,
                "chars_delta": result.chars_delta,
            }
        media = client.upload_media(
            str(payload["file_path"]),
            title=payload.get("title"),
            alt_text=payload.get("alt_text"),
        )
        if not isinstance(media, dict) or "id" not in media:
            raise TaskValidationError("upload_media failed: missing media id")
        media_key = _target_key(task.site.get("base_url", "unknown"), "media", int(media["id"]))
        store.write_snapshot(task.task_id, "after", media_key, media, None)
        store.record_write(media_key)

        updates: list[str] = []
        if payload.get("set_as_featured") and payload.get("target_post_id"):
            updated_post = client.update_resource(
                "post",
                int(payload["target_post_id"]),
                {"featured_media": int(media["id"])},
            )
            post_key = _target_key(task.site.get("base_url", "unknown"), "post", int(payload["target_post_id"]))
            rendered = (
                updated_post.get("content", {}).get("rendered")
                if isinstance(updated_post.get("content"), dict)
                else None
            )
            store.write_snapshot(task.task_id, "after", post_key, updated_post, rendered)
            store.record_write(post_key)
            updates.append(f"featured_media set on post {payload['target_post_id']}")

        return {
            "target": media_key,
            "status": "created",
            "warnings": result.warnings,
            "diff_summary": "; ".join([result.diff_summary] + updates) if updates else result.diff_summary,
            "chars_delta": result.chars_delta,
            "changed_fields": ["media"],
        }

    raise TaskValidationError(f"Unsupported create-only task_type: {task.task_type}")


def run_task(task_path: Path, state_dir: Path, *, confirm: bool = False, apply_changes: bool = True) -> dict:
    started = time.time()
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    payload = render_task_payload(payload, task_path=task_path)
    task = parse_task(payload)
    site = resolve_site(task.site)
    task.site.setdefault("base_url", site.base_url)

    store = StateStore(state_dir)
    now = datetime.now(timezone.utc).isoformat()

    if store.is_executed(task.task_id):
        summary = {
            "task_id": task.task_id,
            "status": "skipped",
            "reason": "idempotent_skip",
            "timestamp": now,
        }
        store.append_audit(summary)
        return summary

    if task.requires_ui:
        queued = queue_ui_task(state_dir=state_dir, task_payload=payload)
        summary = {
            "task_id": task.task_id,
            "status": queued["status"],
            "reason": "requires_ui=true queued for optional_openclaw_bridge",
            "bridge": queued,
            "timestamp": now,
        }
        store.append_audit(summary)
        return summary

    # Confirmation is required only for writes. Plan-only previews should not be blocked.
    if task.requires_confirmation and not confirm and apply_changes and task.mode != "plan":
        summary = {
            "task_id": task.task_id,
            "status": "blocked",
            "reason": "requires_confirmation=true, pass --confirm",
            "timestamp": now,
        }
        store.append_audit(summary)
        return summary

    if task.task_type == "report_only":
        result = handle_report_only(task)
        summary = {
            "task_id": task.task_id,
            "status": "ok",
            "mode": task.mode,
            "result": result.diff_summary,
            "timestamp": now,
        }
        store.mark_executed(task.task_id)
        store.append_audit(summary)
        return summary

    auth = resolve_auth(site.auth_ref)
    client = WPClient(site.wp_api_base, auth.username, auth.app_password)

    results: list[dict] = []
    errors: list[dict] = []
    create_only_types = {"publish_post", "upload_media"}
    if task.task_type in create_only_types:
        try:
            results.append(_run_create_task(client, task, store, apply_changes=apply_changes))
        except (TaskValidationError, TargetNotFoundError, Exception) as exc:
            errors.append({"target": {}, "error": str(exc)})
    else:
        for idx in range(len(task.targets)):
            try:
                results.append(_run_single_target(client, task, idx, store, apply_changes=apply_changes))
            except (TaskValidationError, TargetNotFoundError, Exception) as exc:
                target_hint = asdict(task.targets[idx]) if idx < len(task.targets) else {}
                errors.append({"target": target_hint, "error": str(exc)})

    status = "partial" if errors and results else ("failed" if errors else "ok")
    # Idempotency should reflect actual writes. Plan-only (apply_changes=False) must not consume the task_id.
    if status == "ok" and apply_changes and task.mode != "plan":
        store.mark_executed(task.task_id)

    summary = {
        "task_id": task.task_id,
        "status": status,
        "mode": task.mode,
        "results": results,
        "errors": errors,
        "duration_ms": int((time.time() - started) * 1000),
        "timestamp": now,
    }
    store.append_audit(summary)
    return summary
