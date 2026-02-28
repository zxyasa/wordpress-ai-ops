from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urljoin, urlparse

from .config import resolve_auth, resolve_site
from .wp_client import WPClient

EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RX = re.compile(r"""https?://[^\s"'<>]+|href=["']([^"']+)["']""")

DEFAULT_RESOURCE_BASES = ["pages", "posts", "ux-blocks", "template-parts"]
DEFAULT_REQUIRED_SLOTS = {
    "pages": ["AI_SLOT:INTRO", "AI_SLOT:CTA", "AI_SLOT:SCHEMA"],
    "posts": [],
    "ux-blocks": [],
    "template-parts": [],
}
DEFAULT_REQUIRE_SCHEMA = {
    "pages": True,
    "posts": False,
    "ux-blocks": False,
    "template-parts": False,
}
DEFAULT_CONTACT_CHECK_BASES = ["pages", "ux-blocks"]


def _load_site_profile(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    profile_path = Path(path)
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _normalize_scan_policy(profile: dict[str, Any]) -> dict[str, Any]:
    raw = profile.get("scan_policy") if isinstance(profile.get("scan_policy"), dict) else {}
    required_slots = dict(DEFAULT_REQUIRED_SLOTS)
    require_schema = dict(DEFAULT_REQUIRE_SCHEMA)

    raw_slots = raw.get("required_slots")
    if isinstance(raw_slots, dict):
        for key, value in raw_slots.items():
            if isinstance(value, list):
                required_slots[str(key)] = [str(v) for v in value if isinstance(v, str) and v.strip()]

    raw_schema = raw.get("require_schema")
    if isinstance(raw_schema, dict):
        for key, value in raw_schema.items():
            require_schema[str(key)] = bool(value)

    link_bases = raw.get("link_check_resource_bases")
    if not isinstance(link_bases, list):
        link_bases = DEFAULT_RESOURCE_BASES
    email_bases = raw.get("email_check_resource_bases")
    if not isinstance(email_bases, list):
        email_bases = DEFAULT_CONTACT_CHECK_BASES
    phone_bases = raw.get("phone_check_resource_bases")
    if not isinstance(phone_bases, list):
        phone_bases = DEFAULT_CONTACT_CHECK_BASES

    resource_bases = raw.get("resource_bases")
    if not isinstance(resource_bases, list):
        resource_bases = DEFAULT_RESOURCE_BASES

    ignored_resources = raw.get("ignored_resources")
    if not isinstance(ignored_resources, list):
        ignored_resources = []

    return {
        "required_slots": required_slots,
        "require_schema": require_schema,
        "link_check_resource_bases": [str(x) for x in link_bases],
        "email_check_resource_bases": [str(x) for x in email_bases],
        "phone_check_resource_bases": [str(x) for x in phone_bases],
        "resource_bases": [str(x) for x in resource_bases],
        "ignored_resources": ignored_resources,
    }


def _resource_ignored(item: dict[str, Any], policy: dict[str, Any]) -> bool:
    for spec in policy.get("ignored_resources", []):
        if not isinstance(spec, dict):
            continue
        rb = spec.get("rest_base")
        slug = spec.get("slug")
        rid = spec.get("id")
        if rb and str(rb) != str(item.get("rest_base")):
            continue
        if slug and str(slug) != str(item.get("slug")):
            continue
        if rid is not None and int(rid) != int(item.get("id")):
            continue
        return True
    return False


def _extract_links(content: str, base_url: str) -> list[str]:
    links: list[str] = []
    for m in URL_RX.finditer(content):
        value = m.group(1) or m.group(0)
        value = value.strip()
        if not value:
            continue
        if value.startswith("#") or value.startswith("mailto:") or value.startswith("tel:"):
            continue
        if value.startswith("/"):
            value = urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))
        if value.startswith("http://") or value.startswith("https://"):
            links.append(value)
    return sorted(set(links))


def _check_link(url: str, timeout_s: int = 8) -> tuple[bool, int | None, str]:
    try:
        req = urlrequest.Request(url, method="HEAD")
        with urlrequest.urlopen(req, timeout=timeout_s) as resp:
            status = int(getattr(resp, "status", 0) or 0)
        return (200 <= status < 400), status, ""
    except urlerror.HTTPError as e:
        return False, e.code, str(e)
    except Exception as e:  # noqa: BLE001
        return False, None, str(e)


def _is_internal(url: str, base_url: str) -> bool:
    u = urlparse(url)
    b = urlparse(base_url)
    return u.netloc == b.netloc


def _iter_rest_base(client: WPClient, rest_base: str) -> list[dict]:
    rows: list[dict] = []
    page = 1
    while True:
        try:
            data = client._request(  # noqa: SLF001
                "GET",
                rest_base,
                params={
                    "context": "edit",
                    "per_page": 100,
                    "page": page,
                    "_fields": "id,slug,link,content,modified",
                },
            )
        except Exception:
            break
        if not isinstance(data, list) or not data:
            break
        rows.extend(data)
        page += 1
    return rows


def _target_type_for_rest_base(rest_base: str) -> str:
    mapping = {
        "pages": "page",
        "posts": "post",
        "ux-blocks": "ux-blocks",
        "menu-items": "menu-items",
        "template-parts": "template-parts",
    }
    return mapping.get(rest_base, rest_base)


def _schema_snippet(base_url: str, site_name: str) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": base_url.rstrip("/") + "/",
    }
    return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False) + "</script>"


def _merge_ops_by_target(findings: list[dict[str, Any]], *, profile: dict[str, Any], base_url: str) -> list[dict[str, Any]]:
    target_ops: dict[tuple[str, int], dict[str, Any]] = {}
    site_info = profile.get("site") if isinstance(profile.get("site"), dict) else {}
    configured_email = str(site_info.get("email") or "").strip()
    configured_phone = str(site_info.get("phone_display") or "").strip()
    configured_phone_tel = str(site_info.get("phone_tel") or "").strip()
    site_name = str(site_info.get("name") or urlparse(base_url).netloc)

    for f in findings:
        res = f.get("resource") or {}
        rest_base = str(res.get("rest_base") or "")
        rid = int(res.get("id") or 0)
        slug = str(res.get("slug") or "")
        if not rest_base or rid <= 0:
            continue

        key = (rest_base, rid)
        entry = target_ops.setdefault(
            key,
            {
                "resource": {"rest_base": rest_base, "id": rid, "slug": slug},
                "operations": [],
                "_seen": set(),
                "_ensure_slots": set(),
            },
        )

        kind = f.get("kind")
        if kind == "deprecated_email" and configured_email:
            msg = str(f.get("message", ""))
            old = msg.split(":", 1)[1].strip() if ":" in msg else ""
            if old:
                tag = ("email", old)
                if tag not in entry["_seen"]:
                    entry["_seen"].add(tag)
                    entry["operations"].append(
                        {
                            "op": "replace",
                            "scope": "content",
                            "selector": {"kind": "regex", "value": re.escape(old)},
                            "content": {"format": "text", "value": configured_email},
                            "safety": {"max_chars_change": 300, "dry_run_diff": True, "allow_full_replace": True},
                        }
                    )
        elif kind == "deprecated_phone" and configured_phone:
            msg = str(f.get("message", ""))
            old = msg.split(":", 1)[1].strip() if ":" in msg else ""
            if old:
                if configured_phone_tel:
                    tag_tel = ("phone_tel", old)
                    if tag_tel not in entry["_seen"]:
                        entry["_seen"].add(tag_tel)
                        entry["operations"].append(
                            {
                                "op": "replace",
                                "scope": "content",
                                "selector": {"kind": "regex", "value": re.escape(f"tel:{old}")},
                                "content": {"format": "text", "value": f"tel:{configured_phone_tel}"},
                                "safety": {"max_chars_change": 300, "dry_run_diff": True, "allow_full_replace": True},
                            }
                        )
                tag_phone = ("phone", old)
                if tag_phone not in entry["_seen"]:
                    entry["_seen"].add(tag_phone)
                    entry["operations"].append(
                        {
                            "op": "replace",
                            "scope": "content",
                            "selector": {"kind": "regex", "value": re.escape(old)},
                            "content": {"format": "text", "value": configured_phone},
                            "safety": {"max_chars_change": 300, "dry_run_diff": True, "allow_full_replace": True},
                        }
                    )
        elif kind == "missing_slot":
            marker = str(f.get("message", "")).replace("Missing slot marker:", "").strip()
            if marker:
                entry["_ensure_slots"].add(marker)
        elif kind == "missing_schema":
            # Add schema content into AI_SLOT:SCHEMA. If slot is missing, ensure_slots op is added below.
            tag_schema = ("schema", "AI_SLOT:SCHEMA")
            if tag_schema not in entry["_seen"]:
                entry["_seen"].add(tag_schema)
                entry["_ensure_slots"].add("AI_SLOT:SCHEMA")
                entry["operations"].append(
                    {
                        "op": "replace",
                        "scope": "content",
                        "selector": {"kind": "html_comment", "value": "AI_SLOT:SCHEMA"},
                        "content": {"format": "html", "value": _schema_snippet(base_url, site_name)},
                        "safety": {"max_chars_change": 1800, "dry_run_diff": True, "allow_full_replace": False},
                    }
                )

    tasks: list[dict[str, Any]] = []
    for _, entry in sorted(target_ops.items(), key=lambda x: (x[0][0], x[0][1])):
        ensure_slots = sorted(entry["_ensure_slots"])
        operations = []
        if ensure_slots:
            operations.append(
                {
                    "op": "ensure_slots",
                    "scope": "content",
                    "selector": {"kind": "html_comment", "value": "AI_SLOT:INTRO"},
                    "content": {"format": "json", "value": {"slots": ensure_slots}},
                    "safety": {"max_chars_change": 1600, "dry_run_diff": True, "allow_full_replace": True},
                }
            )
        operations.extend(entry["operations"])
        if not operations:
            continue
        res = entry["resource"]
        tasks.append(
            {
                "task_id": f"consistency-fix-{res['rest_base']}-{res['id']}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "mode": "execute",
                "site": {"base_url": base_url},
                "task_type": "update_post_or_page",
                "requires_confirmation": True,
                "priority": "high",
                "limits": {"cooldown_hours": 0, "max_write_per_target": 10},
                "notes": f"Auto-generated consistency fixes for {res['rest_base']}:{res['id']}:{res['slug']}",
                "targets": [
                    {
                        "type": _target_type_for_rest_base(res["rest_base"]),
                        "match": {"by": "id", "value": res["id"]},
                    }
                ],
                "operations": operations,
            }
        )
    return tasks


def write_fix_tasks(
    *,
    report: dict[str, Any],
    profile: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = out_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    tasks = _merge_ops_by_target(findings=report.get("findings", []), profile=profile, base_url=report["site"]["base_url"])
    written = 0
    task_paths: list[str] = []
    for task in tasks:
        path = tasks_dir / f"{task['task_id']}.json"
        path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        task_paths.append(str(path))
        written += 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site": report.get("site", {}),
        "source_report_timestamp": report.get("timestamp"),
        "tasks_count": written,
        "tasks": task_paths,
    }
    manifest_path = out_dir / "fix_tasks_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"tasks_dir": str(tasks_dir), "manifest": str(manifest_path), "tasks_count": written}


def run_consistency_scan(
    *,
    site_payload: dict[str, Any],
    site_profile_path: str | None = None,
    check_links: bool = False,
    max_link_checks: int = 100,
) -> dict[str, Any]:
    site = resolve_site(site_payload)
    auth = resolve_auth(site.auth_ref)
    client = WPClient(site.wp_api_base, auth.username, auth.app_password)
    profile = _load_site_profile(site_profile_path)
    policy = _normalize_scan_policy(profile)
    now = datetime.now(timezone.utc).isoformat()

    base_url = site.base_url.rstrip("/")
    site_info = profile.get("site") if isinstance(profile.get("site"), dict) else {}
    configured_email = str(site_info.get("email") or "").strip()
    configured_phone_display = str(site_info.get("phone_display") or "").strip()
    deprecated_emails = [e for e in (profile.get("deprecated_emails") or []) if isinstance(e, str)]
    deprecated_phones = [p for p in (profile.get("deprecated_phones") or []) if isinstance(p, str)]

    findings: list[dict[str, Any]] = []
    checked_links = 0

    for rest_base in policy["resource_bases"]:
        for row in _iter_rest_base(client, rest_base):
            content_obj = row.get("content") if isinstance(row.get("content"), dict) else {}
            content = (content_obj.get("raw") or content_obj.get("rendered") or "") if content_obj else ""
            item = {
                "rest_base": rest_base,
                "id": row.get("id"),
                "slug": row.get("slug"),
                "link": row.get("link"),
            }
            if _resource_ignored(item, policy):
                continue

            for marker in policy["required_slots"].get(rest_base, []):
                if marker not in content:
                    findings.append(
                        {
                            "kind": "missing_slot",
                            "severity": "warn",
                            "resource": item,
                            "message": f"Missing slot marker: {marker}",
                        }
                    )

            if policy["require_schema"].get(rest_base, False):
                if '<script type="application/ld+json">' not in content:
                    findings.append(
                        {
                            "kind": "missing_schema",
                            "severity": "warn",
                            "resource": item,
                            "message": "Missing JSON-LD schema block",
                        }
                    )

            if rest_base in policy["email_check_resource_bases"] and configured_email:
                emails = set(EMAIL_RX.findall(content))
                if emails and configured_email not in emails:
                    findings.append(
                        {
                            "kind": "email_mismatch",
                            "severity": "warn",
                            "resource": item,
                            "message": f"Configured email not found: {configured_email}",
                            "emails_found": sorted(emails),
                        }
                    )

            for old in deprecated_emails:
                if old and old in content:
                    findings.append(
                        {
                            "kind": "deprecated_email",
                            "severity": "error",
                            "resource": item,
                            "message": f"Deprecated email found: {old}",
                        }
                    )

            for old in deprecated_phones:
                if old and old in content:
                    findings.append(
                        {
                            "kind": "deprecated_phone",
                            "severity": "error",
                            "resource": item,
                            "message": f"Deprecated phone found: {old}",
                        }
                    )

            if rest_base in policy["phone_check_resource_bases"] and configured_phone_display:
                if configured_phone_display not in content and ("tel:" in content or "Phone" in content or "phone" in content):
                    findings.append(
                        {
                            "kind": "phone_mismatch",
                            "severity": "warn",
                            "resource": item,
                            "message": f"Configured display phone not found: {configured_phone_display}",
                        }
                    )

            if check_links and rest_base in policy["link_check_resource_bases"] and checked_links < max_link_checks:
                for url in _extract_links(content, base_url):
                    if checked_links >= max_link_checks:
                        break
                    if not _is_internal(url, base_url):
                        continue
                    checked_links += 1
                    ok, status, err = _check_link(url)
                    if not ok:
                        findings.append(
                            {
                                "kind": "dead_link",
                                "severity": "error",
                                "resource": item,
                                "message": f"Broken internal link: {url}",
                                "status": status,
                                "error": err,
                            }
                        )

    errors = [f for f in findings if f["severity"] == "error"]
    warns = [f for f in findings if f["severity"] == "warn"]
    return {
        "status": "ok",
        "timestamp": now,
        "site": {
            "base_url": base_url,
            "wp_api_base": site.wp_api_base,
        },
        "policy": policy,
        "summary": {
            "findings_total": len(findings),
            "errors": len(errors),
            "warnings": len(warns),
            "link_checks": checked_links,
        },
        "findings": findings,
    }


def write_consistency_markdown(report: dict[str, Any], output_path: Path) -> Path:
    summary = report.get("summary", {})
    lines = [
        "# Consistency Scan Report",
        "",
        f"- Time: {report.get('timestamp', '')}",
        f"- Site: {report.get('site', {}).get('base_url', '')}",
        f"- Findings: {summary.get('findings_total', 0)}",
        f"- Errors: {summary.get('errors', 0)}",
        f"- Warnings: {summary.get('warnings', 0)}",
        f"- Internal links checked: {summary.get('link_checks', 0)}",
        "",
        "## Findings",
    ]
    for item in report.get("findings", []):
        res = item.get("resource", {})
        lines.append(
            f"- [{item.get('severity')}] {item.get('kind')} "
            f"({res.get('rest_base')}:{res.get('id')}:{res.get('slug')}) - {item.get('message')}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path

