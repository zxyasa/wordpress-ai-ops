from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _write_task_file(tasks_dir: Path, task_id: str, task_type: str = "report_only") -> Path:
    payload = {
        "task_id": task_id,
        "task_type": task_type,
        "site": {"base_url": "https://example.com", "wp_api_base": "https://example.com/wp-json/wp/v2"},
        "notes": f"task {task_id}",
    }
    path = tasks_dir / f"{task_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestBatchRunner:
    def test_all_succeed(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WP_USERNAME", "u")
        monkeypatch.setenv("WP_APP_PASSWORD", "p")

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        _write_task_file(tasks_dir, "t1")
        _write_task_file(tasks_dir, "t2")

        state_dir = tmp_path / "state"

        from wp_ai_ops.batch_runner import run_task_batch
        result = run_task_batch(
            tasks_dir=tasks_dir,
            state_dir=state_dir,
            confirm=False,
            apply_changes=True,
            continue_on_error=True,
        )
        assert result["status"] == "ok"
        assert result["total"] == 2
        assert result["executed"] == 2
        assert result["failed_or_blocked"] == 0

    def test_partial_failure_continue(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WP_USERNAME", "u")
        monkeypatch.setenv("WP_APP_PASSWORD", "p")

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        _write_task_file(tasks_dir, "t1")

        # Write an invalid task that will fail
        bad_path = tasks_dir / "t2.json"
        bad_path.write_text('{"invalid": true}', encoding="utf-8")

        _write_task_file(tasks_dir, "t3")

        state_dir = tmp_path / "state"

        from wp_ai_ops.batch_runner import run_task_batch
        result = run_task_batch(
            tasks_dir=tasks_dir,
            state_dir=state_dir,
            confirm=False,
            apply_changes=True,
            continue_on_error=True,
        )
        assert result["status"] == "partial"
        assert result["executed"] == 3
        assert result["failed_or_blocked"] >= 1

    def test_stop_on_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("WP_USERNAME", "u")
        monkeypatch.setenv("WP_APP_PASSWORD", "p")

        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()

        # First file is invalid
        bad_path = tasks_dir / "a_first.json"
        bad_path.write_text('{"bad": true}', encoding="utf-8")

        _write_task_file(tasks_dir, "b_second")

        state_dir = tmp_path / "state"

        from wp_ai_ops.batch_runner import run_task_batch
        result = run_task_batch(
            tasks_dir=tasks_dir,
            state_dir=state_dir,
            confirm=False,
            apply_changes=True,
            continue_on_error=False,
        )
        assert result["executed"] == 1  # stopped after first failure
        assert result["failed_or_blocked"] == 1

    def test_empty_dir(self, tmp_path):
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        state_dir = tmp_path / "state"

        from wp_ai_ops.batch_runner import run_task_batch
        result = run_task_batch(
            tasks_dir=tasks_dir,
            state_dir=state_dir,
            confirm=False,
            apply_changes=True,
            continue_on_error=True,
        )
        assert result["status"] == "ok"
        assert result["total"] == 0
        assert result["executed"] == 0

    def test_missing_dir(self, tmp_path):
        from wp_ai_ops.batch_runner import run_task_batch
        with pytest.raises(FileNotFoundError):
            run_task_batch(
                tasks_dir=tmp_path / "nonexistent",
                state_dir=tmp_path / "state",
                confirm=False,
                apply_changes=True,
                continue_on_error=True,
            )
