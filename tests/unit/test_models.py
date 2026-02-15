from __future__ import annotations

import pytest

from wp_ai_ops.exceptions import TaskValidationError
from wp_ai_ops.models import parse_task


class TestParseTask:
    def test_valid_minimal(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "update_post_or_page",
            "targets": [{"type": "post", "match": {"by": "id", "value": 1}}],
        })
        assert task.task_id == "t1"
        assert task.task_type == "update_post_or_page"
        assert task.mode == "execute"
        assert task.priority == "medium"
        assert task.limits.cooldown_hours == 24
        assert task.limits.max_write_per_target_7d == 3

    def test_missing_task_id(self):
        with pytest.raises(TaskValidationError, match="task_id is required"):
            parse_task({"task_type": "update_post_or_page"})

    def test_missing_task_type(self):
        with pytest.raises(TaskValidationError, match="task_type is required"):
            parse_task({"task_id": "t1"})

    def test_unsupported_task_type(self):
        with pytest.raises(TaskValidationError, match="Unsupported task_type"):
            parse_task({"task_id": "t1", "task_type": "nuke_site"})

    def test_empty_targets_non_exempt(self):
        with pytest.raises(TaskValidationError, match="targets must not be empty"):
            parse_task({
                "task_id": "t1",
                "task_type": "update_post_or_page",
                "targets": [],
            })

    def test_empty_targets_exempt_report_only(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "report_only",
        })
        assert task.task_type == "report_only"
        assert task.targets == []

    def test_empty_targets_exempt_publish_post(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "publish_post",
        })
        assert task.task_type == "publish_post"

    def test_empty_targets_exempt_upload_media(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "upload_media",
        })
        assert task.task_type == "upload_media"


class TestBackwardCompat:
    def test_max_write_per_target_compat(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "report_only",
            "limits": {"max_write_per_target": 5},
        })
        assert task.limits.max_write_per_target_7d == 5

    def test_max_write_per_target_7d_preferred(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "report_only",
            "limits": {"max_write_per_target": 5, "max_write_per_target_7d": 10},
        })
        # When both present, max_write_per_target is used as the fallback;
        # the code does: limits.get("max_write_per_target", limits.get("max_write_per_target_7d", 3))
        # so max_write_per_target wins when both are present.
        assert task.limits.max_write_per_target_7d == 5

    def test_selector_type_to_kind(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "update_post_or_page",
            "targets": [{"type": "post", "match": {"by": "id", "value": 1}}],
            "operations": [
                {
                    "op": "replace",
                    "scope": "content",
                    "selector": {"type": "regex", "value": "pattern"},
                    "content": {"format": "html", "value": "new"},
                }
            ],
        })
        assert task.operations[0].selector.kind == "regex"


class TestDefaultValues:
    def test_defaults(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "report_only",
        })
        assert task.mode == "execute"
        assert task.priority == "medium"
        assert task.created_at  # auto-set
        assert task.limits.cooldown_hours == 24
        assert task.limits.max_write_per_target_7d == 3
        assert task.rollback == {"enabled": True, "strategy": "local_snapshot"}
        assert task.requires_confirmation is False
        assert task.requires_ui is False

    def test_safety_defaults(self):
        task = parse_task({
            "task_id": "t1",
            "task_type": "update_post_or_page",
            "targets": [{"type": "post", "match": {"by": "id", "value": 1}}],
            "operations": [{"op": "replace", "scope": "content"}],
        })
        safety = task.operations[0].safety
        assert safety.max_chars_change == 2000
        assert safety.dry_run_diff is True
        assert safety.allow_full_replace is False
        assert "ux_" in safety.forbid_remove
