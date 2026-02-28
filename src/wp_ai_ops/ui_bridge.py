from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def queue_ui_task(*, state_dir: Path, task_payload: dict) -> dict:
    queue_path = state_dir / "openclaw_queue.jsonl"
    state_dir.mkdir(parents=True, exist_ok=True)

    item = {
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued",
        "requires_confirmation": True,
        "requires_ui": True,
        "task_id": task_payload.get("task_id"),
        "task_type": task_payload.get("task_type"),
        "site": task_payload.get("site", {}),
        "targets": task_payload.get("targets", []),
        "operations": task_payload.get("operations", []),
        "required_artifacts": ["step_screenshots", "change_summary"],
    }

    with queue_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return {
        "status": "queued_ui_bridge",
        "queue_file": str(queue_path),
        "task_id": item["task_id"],
        "requires_confirmation": True,
        "required_artifacts": item["required_artifacts"],
    }
