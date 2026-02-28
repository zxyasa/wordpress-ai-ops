from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class HandoffOptions:
    state_dir: Path
    base_url: str
    out_path: Path
    tail: int = 30


def _read_jsonl_tail(path: Path, n: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    tail = lines[-n:] if n > 0 else lines
    out: list[dict[str, Any]] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _extract_recent_changes(audit_rows: list[dict[str, Any]], base_url: str) -> list[str]:
    items: list[str] = []
    for row in audit_rows[::-1]:
        task_id = row.get("task_id", "")
        status = row.get("status", "")
        ts = row.get("timestamp", "")
        results = row.get("results") or []
        if not task_id or not status:
            continue
        if status not in {"ok", "created", "updated"} and not (isinstance(results, list) and results):
            continue

        # Collect per-target summaries when present.
        if isinstance(results, list) and results:
            for r in results:
                if not isinstance(r, dict):
                    continue
                target = str(r.get("target", ""))
                r_status = str(r.get("status", ""))
                if not target.startswith(base_url):
                    # target key includes base_url; keep it anyway if it looks like one of our keys.
                    pass
                changed_fields = r.get("changed_fields")
                cf = ""
                if isinstance(changed_fields, list) and changed_fields:
                    cf = f" fields={','.join(map(str, changed_fields))}"
                items.append(f"- {ts} task={task_id} {r_status} target={target}{cf}")
        else:
            items.append(f"- {ts} task={task_id} status={status}")
        if len(items) >= 20:
            break
    return items[::-1]


def write_handoff(opts: HandoffOptions) -> Path:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    audit_path = opts.state_dir / "audit_log.jsonl"
    executed_path = opts.state_dir / "executed_tasks.json"
    write_limits_path = opts.state_dir / "write_limits.json"

    audit_tail = _read_jsonl_tail(audit_path, opts.tail)
    recent_changes = _extract_recent_changes(audit_tail, opts.base_url)

    executed_count = 0
    if executed_path.exists():
        try:
            executed = json.loads(executed_path.read_text(encoding="utf-8"))
            if isinstance(executed, dict):
                executed_count = len(executed.keys())
        except Exception:
            pass

    lines: list[str] = []
    lines.append(f"# Project Status ({now})")
    lines.append("")
    lines.append("## Environment")
    lines.append(f"- base_url: `{opts.base_url}`")
    lines.append(f"- state_dir: `{opts.state_dir}`")
    lines.append("- auth: use local `.env` / secret manager (do not paste passwords into chat)")
    lines.append("")
    lines.append("## State Files")
    lines.append(f"- audit_log: `{audit_path}`")
    lines.append(f"- executed_tasks: `{executed_path}` (count={executed_count})")
    lines.append(f"- write_limits: `{write_limits_path}`")
    lines.append("")
    lines.append("## Recent Changes (from audit_log tail)")
    if recent_changes:
        lines.extend(recent_changes)
    else:
        lines.append("- (none found)")
    lines.append("")
    lines.append("## Next Actions (suggested)")
    lines.append("1. Run plan-only before any write:")
    lines.append("   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --plan-only`")
    lines.append("2. Execute after confirmation:")
    lines.append("   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --confirm`")
    lines.append("3. Rollback if needed:")
    lines.append("   - `PYTHONPATH=src python3 -m wp_ai_ops.cli rollback --original-task-id <task_id> --state-dir .wp-ai-ops-state-live --base-url https://newcastlehub.info`")
    lines.append("4. One-click next run:")
    lines.append("   - `cd /Users/michaelzhao/agents/apps/wordpress-ai-ops && ./scripts/run_auto_weekly_newcastle.sh`")
    lines.append("")

    opts.out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return opts.out_path
