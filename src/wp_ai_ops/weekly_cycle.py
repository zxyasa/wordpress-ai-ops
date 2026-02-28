from __future__ import annotations

import csv
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .batch_runner import run_task_batch
from .reporting import build_weekly_markdown


@dataclass
class OpportunityRow:
    url: str
    clicks: float
    impressions: float
    ctr: float
    position: float
    bounce_rate: float
    reasons: list[str]
    score: int


DEFAULT_WEEKLY_LIMIT_POLICY: dict[str, Any] = {
    "default": {"cooldown_hours": 24, "max_write_per_target": 3},
    "groups": {
        "homepage": {"cooldown_hours": 12, "max_write_per_target": 6},
        "core": {"cooldown_hours": 16, "max_write_per_target": 5},
        "service": {"cooldown_hours": 18, "max_write_per_target": 4},
        "other": {"cooldown_hours": 24, "max_write_per_target": 3},
    },
    "core_paths": ["/about/", "/services/", "/contact/", "/free-newcastle-business-audit/"],
    "service_path_patterns": [r".*-solutions/?$", r".*-newcastle/?$", r"^/services/.*"],
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def _normalize_path(raw_url: str) -> str:
    path = urlparse(raw_url).path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/" and not path.endswith("/"):
        path = f"{path}/"
    return path


def _classify_limit_group(url: str, policy: dict[str, Any]) -> str:
    path = _normalize_path(url)
    if path == "/":
        return "homepage"

    core_paths = {str(p).strip() for p in policy.get("core_paths", []) if str(p).strip()}
    if path in core_paths:
        return "core"

    service_patterns = [str(p) for p in policy.get("service_path_patterns", []) if str(p).strip()]
    for pattern in service_patterns:
        if re.search(pattern, path):
            return "service"

    return "other"


def _resolve_limits_for_url(site: dict[str, Any], url: str) -> tuple[dict[str, int], str]:
    override_policy = site.get("weekly_limits") or {}
    policy = _deep_merge(DEFAULT_WEEKLY_LIMIT_POLICY, override_policy)
    group = _classify_limit_group(url, policy)

    fallback = policy.get("default", {})
    override_groups = override_policy.get("groups") if isinstance(override_policy.get("groups"), dict) else {}
    policy_groups = policy.get("groups") if isinstance(policy.get("groups"), dict) else {}
    # If a group is not explicitly overridden, inherit from policy.default.
    # This keeps site-level "default" as the effective baseline.
    group_cfg = policy_groups.get(group, {}) if group in override_groups else {}
    cooldown = int(group_cfg.get("cooldown_hours", fallback.get("cooldown_hours", 24)))
    max_write = int(group_cfg.get("max_write_per_target", fallback.get("max_write_per_target", 3)))
    return {"cooldown_hours": cooldown, "max_write_per_target": max_write}, group


def _bootstrap_rows(site: dict[str, Any], *, top_n: int) -> list[OpportunityRow]:
    urls = site.get("bootstrap_urls") or []
    if not isinstance(urls, list):
        return []

    rows: list[OpportunityRow] = []
    for raw in urls:
        url = str(raw).strip()
        if not url:
            continue
        rows.append(
            OpportunityRow(
                url=url,
                clicks=0.0,
                impressions=0.0,
                ctr=0.0,
                position=99.0,
                bounce_rate=0.0,
                reasons=["no_gsc_data_bootstrap"],
                score=1,
            )
        )
        if len(rows) >= top_n:
            break
    return rows


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    raw = str(value).strip().replace("%", "")
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _normalize_rate(value: float) -> float:
    return value / 100.0 if value >= 1.0 else value


def _parse_ctr(value: Any) -> float:
    raw = str(value).strip()
    num = _to_float(raw, default=0.0)
    if "%" in raw:
        return num / 100.0
    return _normalize_rate(num)


def _read_gsc(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("url") or row.get("page") or "").strip()
            if not url:
                continue
            rows[url] = {
                "clicks": _to_float(row.get("clicks")),
                "impressions": _to_float(row.get("impressions")),
                "ctr": _parse_ctr(row.get("ctr")),
                "position": _to_float(row.get("position"), default=99.0),
            }
    return rows


def _read_ga(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = (row.get("url") or row.get("page") or "").strip()
            if not url:
                continue
            rows[url] = {
                "bounce_rate": _normalize_rate(
                    _to_float(row.get("bounce_rate", row.get("engagement_bounce_rate", 0.0)))
                )
            }
    return rows


def _score_row(url: str, gsc: dict, ga: dict) -> OpportunityRow:
    clicks = _to_float(gsc.get("clicks"))
    impressions = _to_float(gsc.get("impressions"))
    ctr = _to_float(gsc.get("ctr"))
    position = _to_float(gsc.get("position"), default=99.0)
    bounce_rate = _normalize_rate(_to_float(ga.get("bounce_rate"), default=0.0))

    score = 0
    reasons: list[str] = []

    if impressions >= 100 and ctr <= 0.02:
        score += 3
        reasons.append("high_impressions_low_ctr")
    if 5 <= position <= 15:
        score += 2
        reasons.append("rank_5_15")
    if bounce_rate >= 0.70:
        score += 2
        reasons.append("high_bounce")

    return OpportunityRow(
        url=url,
        clicks=clicks,
        impressions=impressions,
        ctr=ctr,
        position=position,
        bounce_rate=bounce_rate,
        reasons=reasons,
        score=score,
    )


def _build_update_task(site: dict, row: OpportunityRow, mode: str, limits: dict[str, int], limit_group: str) -> dict:
    intro_text = (
        "<p>This section was refreshed by WordPress AI Ops to improve click-through and first-screen clarity. "
        f"Signals: {', '.join(row.reasons)}.</p>"
    )

    faq_payload = {
        "faqs": [
            {
                "question": "What will I learn on this page?",
                "answer": "You will get a concise overview, practical steps, and links to related guides.",
            },
            {
                "question": "Who is this content for?",
                "answer": "Readers looking for a practical starting point and deeper follow-up resources.",
            },
            {
                "question": "What should I read next?",
                "answer": "Use the related links section for the next best article in the topic cluster.",
            },
        ],
        "inject_json_ld": True,
        "schema_slot": "AI_SLOT:SCHEMA",
    }

    return {
        "task_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "site": site,
        "task_type": "update_post_or_page",
        "priority": "high",
        "targets": [{"type": "page", "match": {"by": "url", "value": row.url}}],
        "operations": [
            {
                "op": "replace",
                "scope": "content",
                "selector": {"kind": "html_comment", "value": "AI_SLOT:INTRO"},
                "content": {"format": "html", "value": intro_text},
                "safety": {"max_chars_change": 1200, "dry_run_diff": True, "allow_full_replace": False},
            }
        ],
        "limits": limits,
        "notes": f"auto-cycle content refresh for {row.url} (limit_group={limit_group})",
        "_faq_operation": {
            "op": "replace",
            "scope": "content",
            "selector": {"kind": "html_comment", "value": "AI_SLOT:FAQ"},
            "content": {"format": "json", "value": faq_payload},
            "safety": {"max_chars_change": 1600, "dry_run_diff": True, "allow_full_replace": False},
        },
    }


def _build_faq_task(site: dict, row: OpportunityRow, mode: str, faq_op: dict, limits: dict[str, int], limit_group: str) -> dict:
    return {
        "task_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "site": site,
        "task_type": "inject_schema_faq",
        "priority": "medium",
        "targets": [{"type": "page", "match": {"by": "url", "value": row.url}}],
        "operations": [faq_op],
        "limits": limits,
        "notes": f"auto-cycle faq/schema refresh for {row.url} (limit_group={limit_group})",
    }


def _build_links_task(
    site: dict, row: OpportunityRow, mode: str, top_rows: list[OpportunityRow], limits: dict[str, int], limit_group: str
) -> dict:
    links: list[dict] = []
    for peer in top_rows:
        if peer.url == row.url:
            continue
        slug = peer.url.rstrip("/").split("/")[-1].replace("-", " ").strip() or "Related guide"
        links.append({"url": peer.url, "anchor": slug.title()})
        if len(links) >= 3:
            break

    return {
        "task_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "site": site,
        "task_type": "append_internal_links",
        "priority": "medium",
        "targets": [{"type": "page", "match": {"by": "url", "value": row.url}}],
        "operations": [
            {
                "op": "append",
                "scope": "content",
                "selector": {"kind": "html_comment", "value": "AI_SLOT:CTA"},
                "content": {"format": "json", "value": {"links": links}},
                "safety": {"max_chars_change": 1000, "dry_run_diff": True, "allow_full_replace": False},
            }
        ],
        "limits": limits,
        "notes": f"auto-cycle internal links refresh for {row.url} (limit_group={limit_group})",
    }


def _build_meta_task(site: dict, row: OpportunityRow, mode: str, limits: dict[str, int], limit_group: str) -> dict:
    slug = row.url.rstrip("/").split("/")[-1].replace("-", " ").strip() or "guide"
    title = f"{slug.title()} | Updated Guide"
    desc = f"Updated quick guide for {slug}. Clear answers, better structure, and next-step resources."
    keyword = slug

    return {
        "task_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "site": site,
        "task_type": "set_meta",
        "priority": "medium",
        "targets": [{"type": "page", "match": {"by": "url", "value": row.url}}],
        "operations": [
            {
                "op": "set_meta",
                "scope": "meta",
                "selector": {"kind": "html_comment", "value": "AI_SLOT:SCHEMA"},
                "content": {
                    "format": "json",
                    "value": {
                        "rank_math_title": title,
                        "rank_math_description": desc,
                        "rank_math_focus_keyword": keyword,
                    },
                },
                "safety": {"max_chars_change": 500, "dry_run_diff": True, "allow_full_replace": False},
            }
        ],
        "limits": limits,
        "notes": f"auto-cycle meta refresh for {row.url} (limit_group={limit_group})",
    }


def plan_weekly_from_csv(
    *,
    gsc_csv: Path,
    ga_csv: Path,
    site: dict,
    out_dir: Path,
    mode: str,
    top_n: int,
    include_meta: bool,
    state_dir: Path,
    execute: bool,
    confirm: bool,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    gsc_rows = _read_gsc(gsc_csv)
    ga_rows = _read_ga(ga_csv)
    merged_urls = sorted(set(gsc_rows.keys()) | set(ga_rows.keys()))

    scored = [_score_row(url, gsc_rows.get(url, {}), ga_rows.get(url, {})) for url in merged_urls]
    scored = [row for row in scored if row.score > 0]
    scored.sort(key=lambda r: (r.score, r.impressions, -r.ctr), reverse=True)

    selected = scored[:top_n]
    bootstrap_used = False
    if not selected:
        selected = _bootstrap_rows(site, top_n=top_n)
        bootstrap_used = bool(selected)

    tasks_dir = out_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    generated_tasks: list[Path] = []
    task_meta: list[dict] = []

    for row in selected:
        limits, limit_group = _resolve_limits_for_url(site, row.url)
        update_task = _build_update_task(site, row, mode, limits, limit_group)
        faq_op = update_task.pop("_faq_operation")

        bundle = [
            update_task,
            _build_faq_task(site, row, mode, faq_op, limits, limit_group),
            _build_links_task(site, row, mode, selected, limits, limit_group),
        ]
        if include_meta:
            bundle.append(_build_meta_task(site, row, mode, limits, limit_group))

        for task in bundle:
            task_path = tasks_dir / f"{task['task_id']}.json"
            task_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
            generated_tasks.append(task_path)
            task_meta.append({
                "task_id": task["task_id"],
                "task_type": task["task_type"],
                "target_url": row.url,
                "reasons": row.reasons,
            })

    execution_results: list[dict] = []
    if execute:
        batch_summary = run_task_batch(
            tasks_dir=tasks_dir,
            state_dir=state_dir,
            confirm=confirm,
            apply_changes=(mode == "execute"),
            continue_on_error=True,
        )
        execution_results = batch_summary.get("results", [])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {"gsc_csv": str(gsc_csv), "ga_csv": str(ga_csv)},
        "site": site,
        "bootstrap_used": bootstrap_used,
        "selected_pages": [
            {
                "url": row.url,
                "score": row.score,
                "reasons": row.reasons,
                "impressions": row.impressions,
                "clicks": row.clicks,
                "ctr": row.ctr,
                "position": row.position,
                "bounce_rate": row.bounce_rate,
            }
            for row in selected
        ],
        "generated_tasks": task_meta,
        "tasks_dir": str(tasks_dir),
        "execution_results": execution_results,
    }

    # Lightweight dashboard artifact for quick machine/human overview.
    from collections import Counter

    reason_counts = Counter()
    target_status = Counter()
    for row in execution_results:
        for item in row.get("results", []) if isinstance(row.get("results"), list) else []:
            target_status[str(item.get("status", "unknown"))] += 1
            reason = str(item.get("reason", "")).strip()
            if reason:
                reason_counts[reason] += 1
    dashboard = {
        "generated_at": report["generated_at"],
        "base_url": site.get("base_url"),
        "selected_pages": len(selected),
        "generated_tasks": len(task_meta),
        "execution_items": sum(target_status.values()),
        "target_status": dict(target_status),
        "skip_reasons_top": reason_counts.most_common(8),
        "bootstrap_used": bootstrap_used,
    }

    report_path = out_dir / "weekly_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = out_dir / "weekly_report.md"
    md_path.write_text(build_weekly_markdown(report), encoding="utf-8")
    (out_dir / "dashboard_summary.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
