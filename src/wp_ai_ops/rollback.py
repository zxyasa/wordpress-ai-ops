from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import resolve_auth, resolve_site
from .storage import StateStore
from .wp_client import WPClient


def pre_run_snapshot(
    *,
    task_id: str,
    targets: list[dict],
    site_payload: dict,
    state_dir: Path,
) -> dict:
    """Proactively snapshot WP resources BEFORE a bulk task runs.

    Useful for scripted batch operations that want a pre-flight safety net
    independent of the task_runner's built-in before-snapshot.

    Args:
        task_id:      Identifier for the pending task (used as snapshot dir name).
        targets:      List of target dicts from the task JSON:
                      [{"type": "post", "match": {"by": "id", "value": 123}}, ...]
        site_payload: Site config dict with auth_ref / base_url.
        state_dir:    Path to the state directory (same as used by task_runner).

    Returns:
        {"task_id": str, "snapshots_taken": int, "errors": list[dict]}
    """
    site = resolve_site(site_payload)
    auth = resolve_auth(site.auth_ref)
    client = WPClient(site.wp_api_base, auth.username, auth.app_password)
    store = StateStore(state_dir)

    snapshots_taken = 0
    errors: list[dict] = []

    for target in targets:
        resource_type = target.get("type", "post")
        match = target.get("match", {})
        by = match.get("by", "")
        value = match.get("value")

        if not value:
            continue

        try:
            if by == "id":
                resource_id = int(value)
                resource = client.get_resource(resource_type, resource_id)
            else:
                # For slug/url matches: resolve via list query
                params: dict = {}
                if by == "slug":
                    params["slug"] = str(value)
                elif by == "url":
                    slug = str(value).rstrip("/").split("/")[-1]
                    params["slug"] = slug
                else:
                    errors.append({"target": target, "error": f"unsupported match.by={by}"})
                    continue

                rows = client.list_resources(resource_type, params=params)
                if not rows:
                    errors.append({"target": target, "error": f"no resource found matching {by}={value}"})
                    continue
                resource = rows[0]
                resource_id = resource["id"]

            key = f"{site.auth_ref}:{resource_type}:{resource_id}"
            before_content = (
                resource.get("content", {}).get("raw")
                or resource.get("content", {}).get("rendered")
            )
            store.write_snapshot(task_id, "before", key, resource, before_content)
            snapshots_taken += 1

        except Exception as exc:
            errors.append({"target": target, "error": str(exc)})

    return {
        "task_id": task_id,
        "snapshots_taken": snapshots_taken,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _load_manifest(task_dir: Path) -> dict[str, str]:
    manifest_path = task_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    # Backward compatibility for older snapshots without manifest.
    mapping: dict[str, str] = {}
    for path in task_dir.glob("*.before.json"):
        safe_target = path.name.removesuffix(".before.json")
        mapping[safe_target] = safe_target
    return mapping


def _extract_resource_ref(target_key: str) -> tuple[str, int]:
    parts = target_key.rsplit(":", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid target key: {target_key}")
    resource_type = parts[1]
    resource_id = int(parts[2])
    return resource_type, resource_id


def _build_rollback_payload(before: dict) -> dict:
    payload: dict = {}
    for field in ("title", "excerpt", "content", "meta", "description", "slug", "status"):
        value = before.get(field)
        if value is None:
            continue
        if isinstance(value, dict) and "raw" in value:
            payload[field] = value.get("raw")
        elif isinstance(value, dict) and "rendered" in value and field == "content":
            payload[field] = value.get("rendered")
        else:
            payload[field] = value
    return payload


def rollback_task(*, original_task_id: str, state_dir: Path, site_payload: dict) -> dict:
    store = StateStore(state_dir)
    task_dir = store.snapshots_dir / original_task_id
    if not task_dir.exists():
        raise FileNotFoundError(f"Snapshot directory not found: {task_dir}")

    site = resolve_site(site_payload)
    auth = resolve_auth(site.auth_ref)
    client = WPClient(site.wp_api_base, auth.username, auth.app_password)

    manifest = _load_manifest(task_dir)
    rollback_task_id = str(uuid.uuid4())
    results: list[dict] = []
    errors: list[dict] = []

    for safe_target, target_key in manifest.items():
        before_path = task_dir / f"{safe_target}.before.json"
        if not before_path.exists():
            continue

        try:
            before = json.loads(before_path.read_text(encoding="utf-8"))
            resource_type, resource_id = _extract_resource_ref(target_key)
            patch_payload = _build_rollback_payload(before)
            if not patch_payload:
                results.append({"target": target_key, "status": "skipped", "reason": "empty rollback payload"})
                continue
            updated = client.update_resource(resource_type, resource_id, patch_payload)
            rendered = updated.get("content", {}).get("rendered") if isinstance(updated.get("content"), dict) else None
            store.write_snapshot(rollback_task_id, "after", target_key, updated, rendered)
            store.record_write(target_key)
            results.append(
                {
                    "target": target_key,
                    "status": "rolled_back",
                    "changed_fields": sorted(patch_payload.keys()),
                }
            )
        except Exception as exc:
            errors.append({"target": target_key, "error": str(exc)})

    summary = {
        "task_id": rollback_task_id,
        "task_type": "rollback",
        "original_task_id": original_task_id,
        "status": "partial" if errors and results else ("failed" if errors else "ok"),
        "results": results,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    store.append_audit(summary)
    if summary["status"] == "ok":
        store.mark_executed(rollback_task_id)
    return summary
