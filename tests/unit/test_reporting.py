from __future__ import annotations

from wp_ai_ops.reporting import build_weekly_markdown


class TestBuildWeeklyMarkdown:
    def test_full_report(self):
        report = {
            "generated_at": "2024-01-15T12:00:00Z",
            "site": {"base_url": "https://example.com", "auth_ref": "MY_SITE"},
            "selected_pages": [
                {
                    "url": "https://example.com/page-a",
                    "score": 7,
                    "reasons": ["high_impressions_low_ctr", "rank_5_15"],
                    "impressions": 500,
                    "clicks": 10,
                    "ctr": 0.02,
                    "position": 8,
                    "bounce_rate": 0.75,
                }
            ],
            "generated_tasks": [
                {"task_type": "update_post_or_page"},
                {"task_type": "inject_schema_faq"},
            ],
            "tasks_dir": "/tmp/tasks",
            "execution_results": [
                {"status": "ok"},
                {"status": "failed"},
            ],
        }
        md = build_weekly_markdown(report)
        assert "# Weekly AI Ops Report" in md
        assert "Generated At: 2024-01-15T12:00:00Z" in md
        assert "Base URL: https://example.com" in md
        assert "Auth Ref: MY_SITE" in md
        assert "page-a" in md
        assert "score=7" in md
        assert "Total: 2" in md
        assert "ok=1" in md
        assert "failed=1" in md

    def test_empty_sections(self):
        report = {
            "generated_at": "2024-01-15T12:00:00Z",
            "site": {},
            "selected_pages": [],
            "generated_tasks": [],
            "tasks_dir": "/tmp/tasks",
        }
        md = build_weekly_markdown(report)
        assert "- None" in md
        assert "Total: 0" in md

    def test_without_execution_results(self):
        report = {
            "generated_at": "2024-01-15T12:00:00Z",
            "site": {"base_url": "https://example.com"},
            "selected_pages": [],
            "generated_tasks": [],
            "tasks_dir": "/tmp/tasks",
        }
        md = build_weekly_markdown(report)
        assert "## Execution Results" not in md

    def test_with_execution_results(self):
        report = {
            "generated_at": "2024-01-15T12:00:00Z",
            "site": {},
            "selected_pages": [],
            "generated_tasks": [],
            "tasks_dir": "/tmp/tasks",
            "execution_results": [
                {"status": "ok"},
                {"status": "ok"},
                {"status": "partial"},
                {"status": "blocked"},
                {"status": "queued_ui_bridge"},
            ],
        }
        md = build_weekly_markdown(report)
        assert "## Execution Results" in md
        assert "ok=2" in md
        assert "partial=1" in md
        assert "blocked=1" in md
        assert "queued_ui=1" in md
