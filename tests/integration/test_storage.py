from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from wp_ai_ops.storage import StateStore


class TestIsExecutedMarkExecuted:
    def test_not_executed_initially(self, tmp_path):
        store = StateStore(tmp_path / "state")
        assert store.is_executed("t1") is False

    def test_mark_and_check(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.mark_executed("t1")
        assert store.is_executed("t1") is True

    def test_idempotent_mark(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.mark_executed("t1")
        store.mark_executed("t1")
        data = json.loads(store.executed_path.read_text())
        assert data.count("t1") == 1


class TestAllowWrite:
    def test_first_write_allowed(self, tmp_path):
        store = StateStore(tmp_path / "state")
        ok, reason = store.allow_write("key1", cooldown_hours=24, max_write_per_target_7d=3)
        assert ok is True
        assert reason == "ok"

    def test_cooldown_active(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.record_write("key1")
        ok, reason = store.allow_write("key1", cooldown_hours=24, max_write_per_target_7d=3)
        assert ok is False
        assert "cooldown" in reason

    def test_7day_limit(self, tmp_path):
        store = StateStore(tmp_path / "state")
        # Write 3 times with timestamps within 7 days but outside cooldown
        now = datetime.now(timezone.utc)
        history = {
            "key1": [
                (now - timedelta(hours=48)).isoformat(),
                (now - timedelta(hours=36)).isoformat(),
                (now - timedelta(hours=25)).isoformat(),
            ]
        }
        store._write_json(store.limit_path, history)
        ok, reason = store.allow_write("key1", cooldown_hours=24, max_write_per_target_7d=3)
        assert ok is False
        assert "7d write limit" in reason

    def test_expired_cooldown_allowed(self, tmp_path):
        store = StateStore(tmp_path / "state")
        now = datetime.now(timezone.utc)
        history = {"key1": [(now - timedelta(hours=25)).isoformat()]}
        store._write_json(store.limit_path, history)
        ok, reason = store.allow_write("key1", cooldown_hours=24, max_write_per_target_7d=3)
        assert ok is True


class TestWriteSnapshot:
    def test_directory_structure(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.write_snapshot("t1", "before", "example.com:post:42", {"id": 42})
        task_dir = store.snapshots_dir / "t1"
        assert task_dir.exists()
        assert (task_dir / "manifest.json").exists()
        assert (task_dir / "example.com_post_42.before.json").exists()

    def test_manifest_content(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.write_snapshot("t1", "before", "example.com:post:42", {"id": 42})
        manifest = json.loads((store.snapshots_dir / "t1" / "manifest.json").read_text())
        assert manifest["example.com_post_42"] == "example.com:post:42"

    def test_json_and_html_files(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.write_snapshot("t1", "after", "key1", {"id": 1}, rendered="<p>Hello</p>")
        task_dir = store.snapshots_dir / "t1"
        assert (task_dir / "key1.after.json").exists()
        assert (task_dir / "key1.after.rendered.html").exists()
        assert (task_dir / "key1.after.rendered.html").read_text() == "<p>Hello</p>"


class TestAppendAudit:
    def test_jsonl_format(self, tmp_path):
        store = StateStore(tmp_path / "state")
        store.append_audit({"event": "test", "value": 1})
        store.append_audit({"event": "test", "value": 2})
        lines = store.audit_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["value"] == 1
        assert json.loads(lines[1])["value"] == 2
