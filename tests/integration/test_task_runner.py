from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wp_ai_ops.storage import StateStore


def _write_task(tmp_path: Path, payload: dict) -> Path:
    task_path = tmp_path / f"{payload['task_id']}.json"
    task_path.write_text(json.dumps(payload), encoding="utf-8")
    return task_path


def _base_payload(**overrides):
    base = {
        "task_id": "test-001",
        "task_type": "update_post_or_page",
        "site": {"base_url": "https://example.com", "wp_api_base": "https://example.com/wp-json/wp/v2"},
        "targets": [{"type": "page", "match": {"by": "id", "value": 42}}],
        "operations": [
            {
                "op": "replace",
                "scope": "content",
                "selector": {"kind": "html_comment", "value": "AI_SLOT:INTRO"},
                "content": {"format": "html", "value": "<p>Updated</p>"},
                "safety": {"max_chars_change": 2000},
            }
        ],
    }
    base.update(overrides)
    return base


def _mock_wp_resource():
    return {
        "id": 42,
        "title": {"rendered": "Test Page"},
        "content": {
            "raw": (
                "<h1>Hello</h1>\n"
                "<!-- AI_SLOT:INTRO -->\n<p>Old</p>\n<!-- /AI_SLOT:INTRO -->"
            ),
            "rendered": (
                "<h1>Hello</h1>\n"
                "<!-- AI_SLOT:INTRO -->\n<p>Old</p>\n<!-- /AI_SLOT:INTRO -->"
            ),
        },
    }


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("WP_USERNAME", "testuser")
    monkeypatch.setenv("WP_APP_PASSWORD", "testpass")


class TestTaskRunnerFullFlow:
    def test_execute_update(self, tmp_path, mock_env):
        payload = _base_payload()
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        updated_resource = dict(_mock_wp_resource())
        updated_resource["content"]["raw"] = "<h1>Hello</h1>\n<!-- AI_SLOT:INTRO -->\n<p>Updated</p>\n<!-- /AI_SLOT:INTRO -->"

        with patch("wp_ai_ops.task_runner.WPClient") as MockClient:
            instance = MockClient.return_value
            instance.get_resource.return_value = _mock_wp_resource()
            instance.update_resource.return_value = updated_resource

            from wp_ai_ops.task_runner import run_task
            result = run_task(task_path, state_dir)

        assert result["status"] == "ok"
        assert result["task_id"] == "test-001"
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == "updated"

    def test_idempotent_skip(self, tmp_path, mock_env):
        payload = _base_payload()
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        store = StateStore(state_dir)
        store.mark_executed("test-001")

        from wp_ai_ops.task_runner import run_task
        result = run_task(task_path, state_dir)
        assert result["status"] == "skipped"
        assert result["reason"] == "idempotent_skip"

    def test_cooldown_block(self, tmp_path, mock_env):
        payload = _base_payload()
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        store = StateStore(state_dir)
        store.record_write("https://example.com:page:42")

        with patch("wp_ai_ops.task_runner.WPClient") as MockClient:
            instance = MockClient.return_value
            instance.get_resource.return_value = _mock_wp_resource()

            from wp_ai_ops.task_runner import run_task
            result = run_task(task_path, state_dir)

        assert result["status"] == "ok"
        assert result["results"][0]["status"] == "skipped"
        assert "cooldown" in result["results"][0]["reason"]

    def test_plan_mode(self, tmp_path, mock_env):
        payload = _base_payload(mode="plan")
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        with patch("wp_ai_ops.task_runner.WPClient") as MockClient:
            instance = MockClient.return_value
            instance.get_resource.return_value = _mock_wp_resource()

            from wp_ai_ops.task_runner import run_task
            result = run_task(task_path, state_dir)

        assert result["status"] == "ok"
        assert result["results"][0]["status"] == "planned"
        # Plan mode should NOT mark as executed
        store = StateStore(state_dir)
        assert store.is_executed("test-001") is False

    def test_requires_ui(self, tmp_path, mock_env):
        payload = _base_payload(requires_ui=True)
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        from wp_ai_ops.task_runner import run_task
        result = run_task(task_path, state_dir)
        assert result["status"] == "queued_ui_bridge"

    def test_report_only(self, tmp_path, mock_env):
        payload = {
            "task_id": "report-001",
            "task_type": "report_only",
            "site": {"base_url": "https://example.com", "wp_api_base": "https://example.com/wp-json/wp/v2"},
            "notes": "weekly check",
        }
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        from wp_ai_ops.task_runner import run_task
        result = run_task(task_path, state_dir)
        assert result["status"] == "ok"
        assert "weekly check" in result["result"]


class TestTaskRunnerErrors:
    def test_target_not_found(self, tmp_path, mock_env):
        payload = _base_payload()
        payload["targets"][0]["match"]["by"] = "slug"
        payload["targets"][0]["match"]["value"] = "nonexistent"
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        with patch("wp_ai_ops.task_runner.WPClient") as MockClient:
            instance = MockClient.return_value
            instance.list_resources.return_value = []

            from wp_ai_ops.task_runner import run_task
            result = run_task(task_path, state_dir)

        assert result["status"] == "failed"
        assert len(result["errors"]) == 1

    def test_safety_violation(self, tmp_path, mock_env):
        payload = _base_payload()
        payload["operations"][0]["content"]["value"] = "<p>" + "x" * 5000 + "</p>"
        payload["operations"][0]["safety"]["max_chars_change"] = 100
        task_path = _write_task(tmp_path, payload)
        state_dir = tmp_path / "state"

        with patch("wp_ai_ops.task_runner.WPClient") as MockClient:
            instance = MockClient.return_value
            instance.get_resource.return_value = _mock_wp_resource()

            from wp_ai_ops.task_runner import run_task
            result = run_task(task_path, state_dir)

        assert result["status"] == "failed"
        assert len(result["errors"]) == 1
