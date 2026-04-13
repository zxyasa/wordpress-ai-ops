from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .exceptions import TaskValidationError


@dataclass
class MatchSpec:
    by: str
    value: Any


@dataclass
class TargetSpec:
    type: str
    match: MatchSpec


@dataclass
class SafetySpec:
    max_chars_change: int = 2000
    dry_run_diff: bool = True
    allow_full_replace: bool = False
    forbid_remove: list[str] = field(default_factory=lambda: ["ux_", "<script", "<style"])


@dataclass
class ContentSpec:
    format: str
    value: Any


@dataclass
class SelectorSpec:
    kind: str = "html_comment"
    value: str = "AI_SLOT:INTRO"


@dataclass
class Operation:
    op: str
    scope: str
    selector: SelectorSpec
    content: ContentSpec
    safety: SafetySpec


@dataclass
class LimitSpec:
    cooldown_hours: int = 24
    max_write_per_target_7d: int = 3


@dataclass
class Task:
    task_id: str
    created_at: str
    mode: str
    site: dict
    task_type: str
    targets: list[TargetSpec]
    operations: list[Operation]
    requires_confirmation: bool = False
    requires_ui: bool = False
    priority: str = "medium"
    rollback: dict = field(default_factory=lambda: {"enabled": True, "strategy": "local_snapshot"})
    limits: LimitSpec = field(default_factory=LimitSpec)
    notes: str = ""


SUPPORTED_TASK_TYPES = {
    "update_post_or_page",
    "append_internal_links",
    "append_faq",
    "inject_schema_faq",
    "generate_topic_hub",
    "set_meta",
    "update_taxonomy_term",
    "publish_post",
    "upload_media",
    "report_only",
}


def _parse_target(raw: dict) -> TargetSpec:
    match = raw.get("match") or {}
    if "by" not in match or "value" not in match:
        raise TaskValidationError("targets[].match must include by and value")
    return TargetSpec(type=raw.get("type", "post"), match=MatchSpec(by=match["by"], value=match["value"]))


def _parse_operation(raw: dict) -> Operation:
    selector = raw.get("selector") or {}
    selector_spec = SelectorSpec(
        kind=selector.get("kind", selector.get("type", "html_comment")),
        value=selector.get("value", "AI_SLOT:INTRO"),
    )
    content = raw.get("content") or {}
    content_spec = ContentSpec(format=content.get("format", "html"), value=content.get("value", ""))

    safety = raw.get("safety") or {}
    safety_spec = SafetySpec(
        max_chars_change=int(safety.get("max_chars_change", 2000)),
        dry_run_diff=bool(safety.get("dry_run_diff", True)),
        allow_full_replace=bool(safety.get("allow_full_replace", False)),
        forbid_remove=list(safety.get("forbid_remove", ["ux_", "<script", "<style"])),
    )

    return Operation(
        op=raw.get("op", "replace"),
        scope=raw.get("scope", "content"),
        selector=selector_spec,
        content=content_spec,
        safety=safety_spec,
    )


def parse_task(payload: dict) -> Task:
    if "task_id" not in payload:
        raise TaskValidationError("task_id is required")
    if "task_type" not in payload:
        raise TaskValidationError("task_type is required")
    if payload["task_type"] not in SUPPORTED_TASK_TYPES:
        raise TaskValidationError(f"Unsupported task_type: {payload['task_type']}")
    targets = payload.get("targets") or []
    if payload["task_type"] not in {"report_only", "publish_post", "upload_media"} and not targets:
        raise TaskValidationError("targets must not be empty")

    operations = payload.get("operations") or []

    created_at = payload.get("created_at") or datetime.now(timezone.utc).isoformat()
    limits = payload.get("limits") or {}
    return Task(
        task_id=payload["task_id"],
        created_at=created_at,
        mode=payload.get("mode", "execute"),
        site=payload.get("site") or {},
        task_type=payload["task_type"],
        targets=[_parse_target(t) for t in targets],
        operations=[_parse_operation(op) for op in operations],
        requires_confirmation=bool(payload.get("requires_confirmation", False)),
        requires_ui=bool(payload.get("requires_ui", False)),
        priority=payload.get("priority", "medium"),
        rollback=payload.get("rollback") or {"enabled": True, "strategy": "local_snapshot"},
        limits=LimitSpec(
            cooldown_hours=int(limits.get("cooldown_hours", 24)),
            max_write_per_target_7d=int(limits.get("max_write_per_target", limits.get("max_write_per_target_7d", 3))),
        ),
        notes=payload.get("notes", ""),
    )
