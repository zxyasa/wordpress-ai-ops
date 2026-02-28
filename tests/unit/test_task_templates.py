from __future__ import annotations

import json

import pytest

from wp_ai_ops.exceptions import TaskValidationError
from wp_ai_ops.task_templates import render_task_payload


def test_render_task_payload_with_profile_ref(tmp_path):
    profile_path = tmp_path / "site_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "site": {
                    "base_url": "https://example.com",
                    "phone_display": "02 40755307",
                    "phone_tel": "0240755307",
                }
            }
        ),
        encoding="utf-8",
    )

    task_path = tmp_path / "task.json"
    payload = {
        "task_id": "t1",
        "task_type": "update_post_or_page",
        "site_profile_ref": "site_profile.json",
        "site": {"base_url": "{{site.base_url}}"},
        "targets": [{"type": "page", "match": {"by": "id", "value": 1}}],
        "operations": [
            {
                "op": "replace",
                "scope": "content",
                "selector": {"kind": "regex", "value": "x"},
                "content": {"format": "text", "value": "tel:{{site.phone_tel}} / {{site.phone_display}}"},
            }
        ],
    }

    rendered = render_task_payload(payload, task_path=task_path)
    assert rendered["site"]["base_url"] == "https://example.com"
    assert rendered["operations"][0]["content"]["value"] == "tel:0240755307 / 02 40755307"
    assert "site_profile_ref" not in rendered


def test_render_task_payload_missing_variable_raises(tmp_path):
    task_path = tmp_path / "task.json"
    payload = {
        "task_id": "t1",
        "task_type": "report_only",
        "notes": "Phone {{site.phone_display}}",
    }
    with pytest.raises(TaskValidationError, match="Template variable not found"):
        render_task_payload(payload, task_path=task_path)

