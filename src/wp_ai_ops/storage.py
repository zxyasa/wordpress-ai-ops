from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class StateStore:
    state_dir: Path

    def __post_init__(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.executed_path = self.state_dir / "executed_tasks.json"
        self.limit_path = self.state_dir / "write_limits.json"
        self.audit_path = self.state_dir / "audit_log.jsonl"
        self.snapshots_dir = self.state_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_executed(self, task_id: str) -> bool:
        executed = self._read_json(self.executed_path, [])
        return task_id in executed

    def mark_executed(self, task_id: str) -> None:
        executed = self._read_json(self.executed_path, [])
        if task_id not in executed:
            executed.append(task_id)
            self._write_json(self.executed_path, executed)

    def allow_write(self, target_key: str, cooldown_hours: int, max_write_per_target_7d: int) -> tuple[bool, str]:
        now = datetime.now(timezone.utc)
        history = self._read_json(self.limit_path, {})
        timestamps = [datetime.fromisoformat(ts) for ts in history.get(target_key, [])]

        if timestamps:
            latest = max(timestamps)
            if now - latest < timedelta(hours=cooldown_hours):
                return False, f"cooldown active ({cooldown_hours}h)"

        recent_window = now - timedelta(days=7)
        recent = [ts for ts in timestamps if ts >= recent_window]
        if len(recent) >= max_write_per_target_7d:
            return False, f"7d write limit reached ({max_write_per_target_7d})"

        return True, "ok"

    def record_write(self, target_key: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        history = self._read_json(self.limit_path, {})
        history.setdefault(target_key, []).append(now)
        self._write_json(self.limit_path, history)

    def write_snapshot(self, task_id: str, stage: str, target_key: str, payload: dict, rendered: str | None = None) -> None:
        task_dir = self.snapshots_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        safe_target = target_key.replace("/", "_").replace(":", "_")
        manifest_path = task_dir / "manifest.json"
        manifest = self._read_json(manifest_path, {})
        manifest[safe_target] = target_key
        self._write_json(manifest_path, manifest)

        json_path = task_dir / f"{safe_target}.{stage}.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if rendered is not None:
            html_path = task_dir / f"{safe_target}.{stage}.rendered.html"
            html_path.write_text(rendered, encoding="utf-8")

    def append_audit(self, payload: dict) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
