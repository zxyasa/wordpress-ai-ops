from __future__ import annotations

import json

from wp_ai_ops.consistency_scan import _extract_links, run_consistency_scan, write_consistency_markdown, write_fix_tasks


def test_extract_links_filters_mailto_tel_and_hash():
    html = """
    <a href="/contact/">Contact</a>
    <a href="https://example.com/a">A</a>
    <a href="#hero">Hero</a>
    <a href="mailto:hello@example.com">Mail</a>
    <a href="tel:0240755307">Call</a>
    """
    links = _extract_links(html, "https://example.com")
    assert "https://example.com/contact/" in links
    assert "https://example.com/a" in links
    assert all(not x.startswith("mailto:") for x in links)
    assert all(not x.startswith("tel:") for x in links)


def test_run_consistency_scan_finds_expected_issues(monkeypatch, tmp_path):
    profile = {
        "site": {
            "email": "hello@newcastlehub.info",
            "phone_display": "02 40755307",
        },
        "deprecated_emails": ["admin@newcastlehub.com"],
        "deprecated_phones": ["0493027766"],
    }
    profile_path = tmp_path / "site_profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    monkeypatch.setenv("WP_USERNAME", "u")
    monkeypatch.setenv("WP_APP_PASSWORD", "p")

    class FakeWPClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def _request(self, method, path, *, params=None, **_kwargs):
            assert method == "GET"
            page = int((params or {}).get("page", 1))
            if page > 1:
                return []
            if path == "pages":
                return [
                    {
                        "id": 28,
                        "slug": "contact",
                        "link": "https://example.com/contact/",
                        "content": {
                            "raw": "<p>Phone: 0493027766</p><p>Email: admin@newcastlehub.com</p>",
                        },
                    }
                ]
            return []

    monkeypatch.setattr("wp_ai_ops.consistency_scan.WPClient", FakeWPClient)

    report = run_consistency_scan(
        site_payload={"base_url": "https://example.com", "wp_api_base": "https://example.com/wp-json/wp/v2"},
        site_profile_path=str(profile_path),
        check_links=False,
    )

    kinds = [f["kind"] for f in report["findings"]]
    assert "deprecated_email" in kinds
    assert "deprecated_phone" in kinds
    assert "missing_slot" in kinds
    assert "missing_schema" in kinds


def test_write_consistency_markdown(tmp_path):
    report = {
        "timestamp": "2026-02-16T00:00:00+00:00",
        "site": {"base_url": "https://example.com"},
        "summary": {"findings_total": 1, "errors": 1, "warnings": 0, "link_checks": 0},
        "findings": [
            {
                "kind": "deprecated_phone",
                "severity": "error",
                "resource": {"rest_base": "pages", "id": 1, "slug": "home"},
                "message": "Deprecated phone found",
            }
        ],
    }
    out = tmp_path / "report.md"
    write_consistency_markdown(report, out)
    content = out.read_text(encoding="utf-8")
    assert "Consistency Scan Report" in content
    assert "deprecated_phone" in content


def test_write_fix_tasks_generates_task_files(tmp_path):
    report = {
        "timestamp": "2026-02-16T00:00:00+00:00",
        "site": {"base_url": "https://example.com"},
        "findings": [
            {
                "kind": "deprecated_email",
                "severity": "error",
                "resource": {"rest_base": "pages", "id": 28, "slug": "contact"},
                "message": "Deprecated email found: admin@example.com",
            },
            {
                "kind": "missing_slot",
                "severity": "warn",
                "resource": {"rest_base": "pages", "id": 28, "slug": "contact"},
                "message": "Missing slot marker: AI_SLOT:SCHEMA",
            },
            {
                "kind": "missing_schema",
                "severity": "warn",
                "resource": {"rest_base": "pages", "id": 28, "slug": "contact"},
                "message": "Missing JSON-LD schema block",
            },
        ],
    }
    profile = {"site": {"email": "hello@example.com", "name": "Example"}}
    meta = write_fix_tasks(report=report, profile=profile, out_dir=tmp_path / "fix")
    assert meta["tasks_count"] >= 1
    manifest = json.loads((tmp_path / "fix" / "fix_tasks_manifest.json").read_text(encoding="utf-8"))
    assert manifest["tasks_count"] >= 1
