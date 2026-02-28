from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def prepare_openclaw_jobs(*, state_dir: Path, out_dir: Path, limit: int, mark_claimed: bool) -> dict:
    queue_path = state_dir / "openclaw_queue.jsonl"
    rows = _load_jsonl(queue_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared = 0
    jobs: list[str] = []

    for row in rows:
        if prepared >= limit:
            break
        if row.get("status") != "queued":
            continue

        task_id = str(row.get("task_id") or "unknown")
        job = {
            "job_id": f"openclaw-{task_id}",
            "prepared_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_confirmation",
            "requires_confirmation": True,
            "requires_ui": True,
            "task": {
                "task_id": row.get("task_id"),
                "task_type": row.get("task_type"),
                "site": row.get("site", {}),
                "targets": row.get("targets", []),
                "operations": row.get("operations", []),
            },
            "required_artifacts": row.get("required_artifacts", ["step_screenshots", "change_summary"]),
            "checklist": [
                "Open target and capture before screenshot",
                "Apply requested UI changes",
                "Capture after screenshot",
                "Record change summary",
                "Wait for confirmation before publish",
            ],
        }
        job_path = out_dir / f"{task_id}.job.json"
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        jobs.append(str(job_path))
        prepared += 1

        if mark_claimed:
            row["status"] = "claimed"
            row["claimed_at"] = datetime.now(timezone.utc).isoformat()

    if mark_claimed and rows:
        _write_jsonl(queue_path, rows)

    return {
        "status": "ok",
        "queue_file": str(queue_path),
        "prepared": prepared,
        "jobs": jobs,
        "marked_claimed": mark_claimed,
    }
