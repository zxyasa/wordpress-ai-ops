from __future__ import annotations

from pathlib import Path

from .task_runner import run_task


def run_task_batch(
    *,
    tasks_dir: Path,
    state_dir: Path,
    confirm: bool,
    apply_changes: bool,
    continue_on_error: bool,
) -> dict:
    if not tasks_dir.exists() or not tasks_dir.is_dir():
        raise FileNotFoundError(f"tasks_dir not found: {tasks_dir}")

    task_files = sorted([p for p in tasks_dir.glob("*.json") if p.is_file()])
    results: list[dict] = []
    failed = 0

    for task_path in task_files:
        try:
            summary = run_task(task_path=task_path, state_dir=state_dir, confirm=confirm, apply_changes=apply_changes)
        except Exception as exc:
            summary = {
                "task_id": "",
                "status": "failed",
                "error": str(exc),
                "results": [],
                "errors": [{"error": str(exc)}],
            }
        summary["task_file"] = str(task_path)
        results.append(summary)
        if summary.get("status") in {"failed", "partial", "blocked"}:
            failed += 1
            if not continue_on_error:
                break

    success_count = sum(1 for summary in results if summary.get("status") == "success")
    status = "ok"
    if results:
        if success_count == 0:
            status = "failed"
        elif success_count < len(results):
            status = "partial"
        else:
            status = "success"

    return {
        "status": status,
        "tasks_dir": str(tasks_dir),
        "total": len(task_files),
        "executed": len(results),
        "failed_or_blocked": failed,
        "results": results,
    }
