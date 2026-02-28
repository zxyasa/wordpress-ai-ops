from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_weekly_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Weekly AI Ops Report")
    lines.append("")
    lines.append(f"Generated At: {report.get('generated_at', datetime.now(timezone.utc).isoformat())}")
    lines.append("")

    site = report.get("site", {})
    lines.append("## Scope")
    lines.append(f"- Base URL: {site.get('base_url', 'N/A')}")
    if site.get("auth_ref"):
        lines.append(f"- Auth Ref: {site.get('auth_ref')}")
    lines.append("")

    selected = report.get("selected_pages", [])
    lines.append("## Opportunity Pages")
    if not selected:
        lines.append("- None")
    else:
        for row in selected:
            reasons = ", ".join(row.get("reasons", [])) or "none"
            lines.append(
                f"- {row.get('url')} | score={row.get('score')} | impressions={row.get('impressions')} "
                f"| ctr={_fmt_pct(float(row.get('ctr', 0.0)))} | position={row.get('position')} "
                f"| bounce={_fmt_pct(float(row.get('bounce_rate', 0.0)))} | reasons={reasons}"
            )
    lines.append("")

    tasks = report.get("generated_tasks", [])
    lines.append("## Generated Tasks")
    lines.append(f"- Total: {len(tasks)}")
    task_counts: dict[str, int] = {}
    for task in tasks:
        t = task.get("task_type", "unknown")
        task_counts[t] = task_counts.get(t, 0) + 1
    for task_type in sorted(task_counts.keys()):
        lines.append(f"- {task_type}: {task_counts[task_type]}")
    lines.append("")

    results = report.get("execution_results", [])
    if results:
        lines.append("## Execution Results")
        ok = sum(1 for r in results if r.get("status") == "ok")
        partial = sum(1 for r in results if r.get("status") == "partial")
        failed = sum(1 for r in results if r.get("status") == "failed")
        blocked = sum(1 for r in results if r.get("status") == "blocked")
        queued_ui = sum(1 for r in results if r.get("status") == "queued_ui_bridge")
        lines.append(f"- ok={ok}, partial={partial}, failed={failed}, blocked={blocked}, queued_ui={queued_ui}")
        target_status = Counter()
        reason_counts = Counter()
        for row in results:
            for item in row.get("results", []) if isinstance(row.get("results"), list) else []:
                target_status[str(item.get("status", "unknown"))] += 1
                reason = str(item.get("reason", "")).strip()
                if reason:
                    reason_counts[reason] += 1
        if target_status:
            lines.append(f"- target_status: {dict(target_status)}")
        if reason_counts:
            lines.append("- skip/top reasons:")
            for reason, count in reason_counts.most_common(5):
                lines.append(f"  - {reason}: {count}")
        lines.append("")

    lines.append("## Next Week Suggestions")
    selected = report.get("selected_pages", [])
    if not selected:
        lines.append("- GSC data still low; keep bootstrap mode enabled and monitor indexing coverage.")
    else:
        lines.append("- Prioritize pages with repeated skip reasons by relaxing limits only for specific groups.")
        lines.append("- Review downgraded_report_only items and tune quality_policy thresholds/brand terms.")
    lines.append("")

    lines.append("## Artifacts")
    lines.append(f"- Tasks Dir: {report.get('tasks_dir', 'N/A')}")
    lines.append(f"- JSON Report: weekly_report.json")
    lines.append(f"- Markdown Report: weekly_report.md")
    lines.append("")

    return "\n".join(lines) + "\n"


def write_weekly_markdown_from_json(*, weekly_report_json: Path, output_path: Path | None = None) -> dict:
    report = json.loads(weekly_report_json.read_text(encoding="utf-8"))
    md = build_weekly_markdown(report)
    target = output_path or weekly_report_json.with_suffix(".md")
    target.write_text(md, encoding="utf-8")
    return {
        "status": "ok",
        "source": str(weekly_report_json),
        "output": str(target),
        "chars": len(md),
    }
