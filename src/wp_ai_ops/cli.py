from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import os

from .batch_runner import run_task_batch
from .consistency_scan import run_consistency_scan, write_consistency_markdown, write_fix_tasks
from .handoff import HandoffOptions, write_handoff
from .openclaw_consumer import prepare_openclaw_jobs
from .openclaw_http import dispatch_job_file, poll_job_status
from .reporting import write_weekly_markdown_from_json
from .rollback import rollback_task
from .task_runner import run_task
from .weekly_cycle import plan_weekly_from_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WordPress AI Ops runner")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run a single task JSON")
    run_parser.add_argument("--task", required=True, help="Task JSON path")
    run_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for snapshots/audit")
    run_parser.add_argument("--confirm", action="store_true", help="Confirm execution for requires_confirmation tasks")
    run_parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Do not write to WordPress even if task.mode is execute",
    )

    weekly_parser = subparsers.add_parser("plan-weekly", help="Generate weekly tasks from GSC/GA CSV")
    weekly_parser.add_argument("--gsc-csv", required=True, help="GSC CSV path")
    weekly_parser.add_argument("--ga-csv", required=True, help="GA CSV path")
    weekly_parser.add_argument("--out-dir", default="weekly-output", help="Output directory for tasks/report")
    weekly_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for execution")
    weekly_parser.add_argument("--base-url", required=True, help="Site base URL")
    weekly_parser.add_argument("--site-profile", default="", help="Optional site profile JSON with weekly_limits")
    weekly_parser.add_argument("--wp-api-base", default="", help="Optional WP API base, default derived from base-url")
    weekly_parser.add_argument("--auth-ref", default="", help="Auth env prefix, e.g. WP_MAIN")
    weekly_parser.add_argument("--mode", choices=["plan", "execute"], default="plan")
    weekly_parser.add_argument("--top-n", type=int, default=5)
    weekly_parser.add_argument("--include-meta", action="store_true")
    weekly_parser.add_argument("--execute", action="store_true", help="Execute generated tasks immediately")
    weekly_parser.add_argument("--confirm", action="store_true", help="Confirm execution when needed")

    batch_parser = subparsers.add_parser("run-batch", help="Run all task JSON files in a directory")
    batch_parser.add_argument("--tasks-dir", required=True, help="Directory containing *.json task files")
    batch_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for snapshots/audit")
    batch_parser.add_argument("--confirm", action="store_true", help="Confirm execution for requires_confirmation tasks")
    batch_parser.add_argument("--plan-only", action="store_true", help="Do not write to WordPress")
    batch_parser.add_argument("--continue-on-error", action="store_true", help="Continue when one task fails")

    report_parser = subparsers.add_parser("report-markdown", help="Render markdown report from weekly_report.json")
    report_parser.add_argument("--weekly-report-json", required=True, help="Path to weekly_report.json")
    report_parser.add_argument("--out", default="", help="Optional output markdown path")

    openclaw_parser = subparsers.add_parser("prepare-openclaw-jobs", help="Prepare OpenClaw job files from queue")
    openclaw_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory with queue file")
    openclaw_parser.add_argument("--out-dir", default="openclaw-jobs", help="Output directory for job files")
    openclaw_parser.add_argument("--limit", type=int, default=20, help="Max jobs to prepare")
    openclaw_parser.add_argument("--mark-claimed", action="store_true", help="Mark queue items as claimed")

    dispatch_parser = subparsers.add_parser("dispatch-openclaw", help="Submit a prepared OpenClaw job via HTTP API")
    dispatch_parser.add_argument("--job", required=True, help="Path to *.job.json")
    dispatch_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for dispatch logs")

    poll_parser = subparsers.add_parser("poll-openclaw", help="Poll OpenClaw job status via HTTP API")
    poll_parser.add_argument("--job-id", required=True, help="Remote job id")
    poll_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for poll logs")

    auto_parser = subparsers.add_parser("auto-weekly", help="Auto-fetch GSC data, run weekly cycle, notify via Telegram")
    auto_parser.add_argument("--base-url", required=True, help="Site base URL")
    auto_parser.add_argument("--gsc-property", default="", help="GSC property URL (e.g. sc-domain:example.com)")
    auto_parser.add_argument("--gsc-credentials", default="gsc_credentials.json", help="Path to GSC service account JSON")
    auto_parser.add_argument("--gsc-csv", default="", help="Manual GSC CSV path (skip API fetch)")
    auto_parser.add_argument("--ga-csv", default="", help="GA CSV path (optional, skipped if not provided)")
    auto_parser.add_argument("--out-dir", default="weekly-output", help="Output directory")
    auto_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory")
    auto_parser.add_argument("--site-profile", default="", help="Optional site profile JSON with weekly_limits")
    auto_parser.add_argument("--wp-api-base", default="", help="Optional WP API base")
    auto_parser.add_argument("--auth-ref", default="", help="Auth env prefix")
    auto_parser.add_argument("--mode", choices=["plan", "execute"], default="plan")
    auto_parser.add_argument("--top-n", type=int, default=5)
    auto_parser.add_argument("--include-meta", action="store_true")
    auto_parser.add_argument("--confirm", action="store_true")
    auto_parser.add_argument("--notify-telegram", action="store_true", help="Send report summary via Telegram")

    rollback_parser = subparsers.add_parser("rollback", help="Rollback changes by task_id snapshots")
    rollback_parser.add_argument("--original-task-id", required=True, help="Original task_id to rollback")
    rollback_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory with snapshots")
    rollback_parser.add_argument("--base-url", required=True, help="Site base URL")
    rollback_parser.add_argument("--wp-api-base", default="", help="Optional WP API base")
    rollback_parser.add_argument("--auth-ref", default="", help="Auth env prefix, e.g. WP_MAIN")

    handoff_parser = subparsers.add_parser("handoff", help="Write STATUS.md handoff from state/audit logs")
    handoff_parser.add_argument("--state-dir", default=".wp-ai-ops-state", help="State directory for snapshots/audit")
    handoff_parser.add_argument("--base-url", required=True, help="Site base URL")
    handoff_parser.add_argument("--out", default="STATUS.md", help="Output markdown path")
    handoff_parser.add_argument("--tail", type=int, default=30, help="Tail N audit log rows")

    scan_parser = subparsers.add_parser("consistency-scan", help="Scan site consistency and write report artifacts")
    scan_parser.add_argument("--base-url", required=True, help="Site base URL")
    scan_parser.add_argument("--wp-api-base", default="", help="Optional WP API base")
    scan_parser.add_argument("--auth-ref", default="", help="Auth env prefix, e.g. WP_MAIN")
    scan_parser.add_argument("--site-profile", default="", help="Path to site profile JSON")
    scan_parser.add_argument("--check-links", action="store_true", help="Check internal links with HEAD requests")
    scan_parser.add_argument("--max-link-checks", type=int, default=100, help="Maximum internal links to check")
    scan_parser.add_argument("--out-dir", default="consistency-output", help="Output directory")
    scan_parser.add_argument("--emit-fix-tasks", action="store_true", help="Generate fix task JSON files from findings")

    return parser


def _run_command(args: argparse.Namespace) -> dict:
    task_path = Path(args.task)
    state_dir = Path(args.state_dir)
    return run_task(
        task_path=task_path,
        state_dir=state_dir,
        confirm=args.confirm,
        apply_changes=not args.plan_only,
    )


def _weekly_command(args: argparse.Namespace) -> dict:
    site = {
        "base_url": args.base_url,
    }
    if args.site_profile:
        profile = json.loads(Path(args.site_profile).read_text(encoding="utf-8"))
        weekly_limits = profile.get("weekly_limits")
        if isinstance(weekly_limits, dict):
            site["weekly_limits"] = weekly_limits
        bootstrap_urls = profile.get("bootstrap_urls")
        if isinstance(bootstrap_urls, list):
            site["bootstrap_urls"] = bootstrap_urls
    if args.wp_api_base:
        site["wp_api_base"] = args.wp_api_base
    if args.auth_ref:
        site["auth_ref"] = args.auth_ref

    return plan_weekly_from_csv(
        gsc_csv=Path(args.gsc_csv),
        ga_csv=Path(args.ga_csv),
        site=site,
        out_dir=Path(args.out_dir),
        mode=args.mode,
        top_n=args.top_n,
        include_meta=args.include_meta,
        state_dir=Path(args.state_dir),
        execute=args.execute,
        confirm=args.confirm,
    )


def _rollback_command(args: argparse.Namespace) -> dict:
    site = {"base_url": args.base_url}
    if args.wp_api_base:
        site["wp_api_base"] = args.wp_api_base
    if args.auth_ref:
        site["auth_ref"] = args.auth_ref
    return rollback_task(
        original_task_id=args.original_task_id,
        state_dir=Path(args.state_dir),
        site_payload=site,
    )


def _batch_command(args: argparse.Namespace) -> dict:
    return run_task_batch(
        tasks_dir=Path(args.tasks_dir),
        state_dir=Path(args.state_dir),
        confirm=args.confirm,
        apply_changes=not args.plan_only,
        continue_on_error=args.continue_on_error,
    )


def _report_markdown_command(args: argparse.Namespace) -> dict:
    out = Path(args.out) if args.out else None
    return write_weekly_markdown_from_json(
        weekly_report_json=Path(args.weekly_report_json),
        output_path=out,
    )


def _prepare_openclaw_jobs_command(args: argparse.Namespace) -> dict:
    return prepare_openclaw_jobs(
        state_dir=Path(args.state_dir),
        out_dir=Path(args.out_dir),
        limit=args.limit,
        mark_claimed=args.mark_claimed,
    )


def _dispatch_openclaw_command(args: argparse.Namespace) -> dict:
    return dispatch_job_file(Path(args.job), state_dir=Path(args.state_dir))


def _poll_openclaw_command(args: argparse.Namespace) -> dict:
    return poll_job_status(args.job_id, state_dir=Path(args.state_dir))


def _auto_weekly_command(args: argparse.Namespace) -> dict:
    import csv as _csv

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Resolve GSC CSV ---
    gsc_csv_path: Path
    if args.gsc_csv:
        gsc_csv_path = Path(args.gsc_csv)
    elif args.gsc_property:
        from .gsc_export import export_gsc_csv

        gsc_csv_path = out_dir / "gsc_auto.csv"
        export_gsc_csv(
            property_url=args.gsc_property,
            credentials_path=args.gsc_credentials,
            output_path=gsc_csv_path,
        )
    else:
        raise SystemExit("error: provide --gsc-csv or --gsc-property to supply GSC data")

    # --- 2. Resolve GA CSV (optional) ---
    if args.ga_csv:
        ga_csv_path = Path(args.ga_csv)
    else:
        ga_csv_path = out_dir / "ga_empty.csv"
        with ga_csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            writer.writerow(["url", "bounce_rate"])

    # --- 3. Run weekly cycle ---
    site: dict = {"base_url": args.base_url}
    if args.site_profile:
        profile = json.loads(Path(args.site_profile).read_text(encoding="utf-8"))
        weekly_limits = profile.get("weekly_limits")
        if isinstance(weekly_limits, dict):
            site["weekly_limits"] = weekly_limits
        bootstrap_urls = profile.get("bootstrap_urls")
        if isinstance(bootstrap_urls, list):
            site["bootstrap_urls"] = bootstrap_urls
    if args.wp_api_base:
        site["wp_api_base"] = args.wp_api_base
    if args.auth_ref:
        site["auth_ref"] = args.auth_ref

    report = plan_weekly_from_csv(
        gsc_csv=gsc_csv_path,
        ga_csv=ga_csv_path,
        site=site,
        out_dir=out_dir,
        mode=args.mode,
        top_n=args.top_n,
        include_meta=args.include_meta,
        state_dir=Path(args.state_dir),
        execute=(args.mode == "execute"),
        confirm=args.confirm,
    )

    # --- 4. Telegram notification ---
    if args.notify_telegram:
        bot_token = os.environ.get("TG_BOT_TOKEN", "")
        chat_id = os.environ.get("TG_CHAT_ID", "")
        if bot_token and chat_id:
            from .notify import send_telegram

            summary = _build_telegram_summary(report)
            send_telegram(bot_token, chat_id, summary)
            report["telegram_sent"] = True
        else:
            report["telegram_sent"] = False
            report["telegram_error"] = "TG_BOT_TOKEN or TG_CHAT_ID not set"

    # Persist notification status back into the weekly report artifact.
    report_path = out_dir / "weekly_report.json"
    if report_path.exists():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return report


def _build_telegram_summary(report: dict) -> str:
    from collections import Counter

    lines = ["*Weekly SEO Report*", ""]
    pages = report.get("selected_pages", [])
    if pages:
        lines.append(f"Selected {len(pages)} pages:")
        for p in pages:
            reasons = ", ".join(p.get("reasons", []))
            lines.append(f"  - {p['url']}  (score {p['score']}, {reasons})")
    else:
        lines.append("No pages met the scoring threshold.")

    tasks = report.get("generated_tasks", [])
    lines.append(f"\nGenerated {len(tasks)} tasks.")

    results = report.get("execution_results", [])
    if results:
        ok = sum(1 for r in results if r.get("status") == "ok")
        lines.append(f"Executed: {ok}/{len(results)} succeeded.")
        reason_counts = Counter()
        for r in results:
            for item in r.get("results", []) if isinstance(r.get("results"), list) else []:
                reason = str(item.get("reason", "")).strip()
                if reason:
                    reason_counts[reason] += 1
        if reason_counts:
            lines.append("")
            lines.append("Top skip reasons:")
            for reason, count in reason_counts.most_common(3):
                lines.append(f"  - {reason}: {count}")

    lines.append("")
    if report.get("selected_pages"):
        lines.append("Next: review pages with repeated skip reasons and tune group limits.")
    else:
        lines.append("Next: data still low; keep bootstrap mode and continue indexing.")

    return "\n".join(lines)


def _handoff_command(args: argparse.Namespace) -> dict:
    out = write_handoff(
        HandoffOptions(
            state_dir=Path(args.state_dir),
            base_url=args.base_url,
            out_path=Path(args.out),
            tail=int(args.tail),
        )
    )
    return {"status": "ok", "out": str(out)}


def _consistency_scan_command(args: argparse.Namespace) -> dict:
    site = {"base_url": args.base_url}
    if args.wp_api_base:
        site["wp_api_base"] = args.wp_api_base
    if args.auth_ref:
        site["auth_ref"] = args.auth_ref

    report = run_consistency_scan(
        site_payload=site,
        site_profile_path=args.site_profile or None,
        check_links=bool(args.check_links),
        max_link_checks=int(args.max_link_checks),
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = report.get("timestamp", "").replace(":", "").replace("-", "")
    json_path = out_dir / f"consistency_scan_{ts}.json"
    md_path = out_dir / f"consistency_scan_{ts}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_consistency_markdown(report, md_path)
    report["artifacts"] = {"json": str(json_path), "markdown": str(md_path)}
    if args.emit_fix_tasks:
        fix_meta = write_fix_tasks(
            report=report,
            profile=json.loads(Path(args.site_profile).read_text(encoding="utf-8")) if args.site_profile else {},
            out_dir=out_dir / "fix_tasks",
        )
        report["artifacts"]["fix_tasks"] = fix_meta
    return report


def main() -> None:
    # Backward-compatible fallback: support legacy call without explicit subcommand.
    argv = sys.argv[1:]
    if "--task" in argv and (
        not argv
        or argv[0]
        not in {
            "run",
            "plan-weekly",
            "run-batch",
            "rollback",
            "report-markdown",
            "prepare-openclaw-jobs",
            "dispatch-openclaw",
            "poll-openclaw",
            "auto-weekly",
            "handoff",
            "consistency-scan",
        }
    ):
        legacy = argparse.ArgumentParser(add_help=False)
        legacy.add_argument("--task", required=True)
        legacy.add_argument("--state-dir", default=".wp-ai-ops-state")
        legacy.add_argument("--confirm", action="store_true")
        legacy.add_argument("--plan-only", action="store_true")
        legacy_args = legacy.parse_args(argv)
        summary = run_task(
            task_path=Path(legacy_args.task),
            state_dir=Path(legacy_args.state_dir),
            confirm=legacy_args.confirm,
            apply_changes=not legacy_args.plan_only,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        summary = _run_command(args)
    elif args.command == "plan-weekly":
        summary = _weekly_command(args)
    elif args.command == "run-batch":
        summary = _batch_command(args)
    elif args.command == "report-markdown":
        summary = _report_markdown_command(args)
    elif args.command == "prepare-openclaw-jobs":
        summary = _prepare_openclaw_jobs_command(args)
    elif args.command == "dispatch-openclaw":
        summary = _dispatch_openclaw_command(args)
    elif args.command == "poll-openclaw":
        summary = _poll_openclaw_command(args)
    elif args.command == "auto-weekly":
        summary = _auto_weekly_command(args)
    elif args.command == "rollback":
        summary = _rollback_command(args)
    elif args.command == "handoff":
        summary = _handoff_command(args)
    elif args.command == "consistency-scan":
        summary = _consistency_scan_command(args)
    else:
        parser.error(f"Unknown command: {args.command}")
        return

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
