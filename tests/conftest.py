from __future__ import annotations

import pytest

from wp_ai_ops.models import (
    ContentSpec,
    LimitSpec,
    Operation,
    SafetySpec,
    SelectorSpec,
    TargetSpec,
    MatchSpec,
    Task,
)


@pytest.fixture
def sample_html_with_slots():
    return (
        "<h1>Hello</h1>\n"
        "<!-- AI_SLOT:INTRO -->\n"
        "<p>Old intro</p>\n"
        "<!-- /AI_SLOT:INTRO -->\n"
        "<p>Body text</p>\n"
        "<!-- AI_SLOT:FAQ -->\n"
        "<!-- /AI_SLOT:FAQ -->\n"
        "<!-- AI_SLOT:CTA -->\n"
        "<!-- /AI_SLOT:CTA -->\n"
        "<!-- AI_SLOT:SCHEMA -->\n"
        "<!-- /AI_SLOT:SCHEMA -->"
    )


@pytest.fixture
def sample_wp_resource(sample_html_with_slots):
    return {
        "id": 42,
        "title": {"rendered": "Test Page"},
        "slug": "test-page",
        "content": {"raw": sample_html_with_slots, "rendered": sample_html_with_slots},
        "status": "publish",
    }


@pytest.fixture
def sample_operation_replace():
    return Operation(
        op="replace",
        scope="content",
        selector=SelectorSpec(kind="html_comment", value="AI_SLOT:INTRO"),
        content=ContentSpec(format="html", value="<p>New intro</p>"),
        safety=SafetySpec(),
    )


@pytest.fixture
def sample_task_payload():
    return {
        "task_id": "test-001",
        "task_type": "update_post_or_page",
        "site": {"base_url": "https://example.com"},
        "targets": [{"type": "page", "match": {"by": "id", "value": 42}}],
        "operations": [
            {
                "op": "replace",
                "scope": "content",
                "selector": {"kind": "html_comment", "value": "AI_SLOT:INTRO"},
                "content": {"format": "html", "value": "<p>New intro</p>"},
                "safety": {"max_chars_change": 2000},
            }
        ],
    }


@pytest.fixture
def sample_gsc_csv(tmp_path):
    path = tmp_path / "gsc.csv"
    path.write_text(
        "url,clicks,impressions,ctr,position\n"
        "https://example.com/page-a,10,500,0.02,8\n"
        "https://example.com/page-b,5,200,0.025,12\n"
        "https://example.com/page-c,1,50,0.02,25\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sample_ga_csv(tmp_path):
    path = tmp_path / "ga.csv"
    path.write_text(
        "url,bounce_rate\n"
        "https://example.com/page-a,75\n"
        "https://example.com/page-b,40\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("WP_USERNAME", "testuser")
    monkeypatch.setenv("WP_APP_PASSWORD", "testpass")
    monkeypatch.setenv("WP_BASE_URL", "https://example.com")
    monkeypatch.setenv("WP_API_BASE", "https://example.com/wp-json/wp/v2")
