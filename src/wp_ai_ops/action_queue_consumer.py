"""Action Queue Consumer — dispatches auto-executable actions from the Command Center.

Reads a growth-graph ActionQueue JSON and dispatches auto-executable items
directly through the wp-ai-ops task_runner, skipping Telegram approval for
low-risk automated actions.

Called by the auto-weekly cycle or a dedicated scheduled job.

Usage:
    python -m wp_ai_ops.action_queue_consumer --queue /path/to/queue.json
    python -m wp_ai_ops.action_queue_consumer --site sweetsworld --auto
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# No-touch rules runtime check
# ---------------------------------------------------------------------------

_NO_TOUCH_RULES_PATH = (
    Path(__file__).parents[3] / "website-os" / "registries" / "no_touch_rules.yaml"
)


def _load_no_touch_rules() -> Optional[Dict[str, Any]]:
    """Load no_touch_rules.yaml. Returns None if file not found or yaml unavailable."""
    if not _NO_TOUCH_RULES_PATH.exists():
        logger.debug("no_touch_rules.yaml not found at %s — skipping safety check", _NO_TOUCH_RULES_PATH)
        return None
    try:
        import yaml  # type: ignore
        with open(_NO_TOUCH_RULES_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed — no_touch_rules check skipped")
        return None
    except Exception as exc:
        logger.warning("Failed to load no_touch_rules.yaml: %s", exc)
        return None


def _is_no_touch_target(
    wp_task: Dict[str, Any],
    no_touch_rules: Dict[str, Any],
) -> tuple:
    """Check whether a task's target is protected by no_touch_rules.

    Returns (blocked: bool, reason: str).
    """
    import fnmatch

    site_id = (wp_task.get("site") or {}).get("auth_ref", "sweetsworld")
    targets = wp_task.get("targets", [])

    global_rules = no_touch_rules.get("global", {})
    site_rules = (no_touch_rules.get("sites") or {}).get(site_id, {})

    protected_url_patterns = [
        r.get("pattern", "") for r in global_rules.get("protected_url_patterns", [])
    ]
    protected_slugs = {
        entry.get("slug", ""): entry.get("reason", "protected")
        for entry in site_rules.get("protected_slugs", [])
    }
    content_area_patterns: List[str] = []
    for area in site_rules.get("protected_content_areas", []):
        if "url" in area:
            content_area_patterns.append(area["url"])
        for pat in area.get("url_patterns", []):
            content_area_patterns.append(pat)

    for target in targets:
        match = target.get("match", {})
        by = match.get("by", "")
        value = str(match.get("value", ""))

        if not value:
            continue

        # Check slug-based targets
        if by == "slug":
            if value in protected_slugs:
                return True, f"slug '{value}' is protected: {protected_slugs[value]}"

        # Check URL-based targets
        if by in ("url", "id"):
            for pat in protected_url_patterns:
                # Normalise: treat /product-category/* as a path prefix match
                if pat.endswith("*"):
                    prefix = pat[:-1]
                    if value.startswith(prefix) or f"/{value}".startswith(prefix):
                        return True, f"URL matches protected pattern '{pat}'"
                elif fnmatch.fnmatch(value, pat):
                    return True, f"URL matches protected pattern '{pat}'"

            for pat in content_area_patterns:
                if fnmatch.fnmatch(value, pat):
                    return True, f"URL matches protected content area '{pat}'"

    # Check operations for protected fields
    protected_fields = {
        f.get("field", ""): f.get("reason", "protected")
        for f in global_rules.get("protected_fields", [])
    }
    for op in wp_task.get("operations", []):
        scope = op.get("scope", "")
        if scope in protected_fields:
            reason = protected_fields[scope]
            # slug and post_status have exceptions — only block if explicitly writing
            return True, f"operation scope '{scope}' is a protected field: {reason}"

    return False, ""


def load_queue_json(queue_path: str) -> Dict[str, Any]:
    with open(queue_path, encoding="utf-8") as f:
        return json.load(f)


def dispatch_auto_items(
    queue_json: Dict[str, Any],
    state_dir: str = ".wp-ai-ops-state-live",
    dry_run: bool = True,
    confirm: bool = False,
) -> Dict[str, Any]:
    """Dispatch auto-executable items from a serialised ActionQueue dict.

    Returns {dispatched, skipped, errors}.
    """
    items = queue_json.get("items", [])
    results = {"dispatched": 0, "skipped": 0, "errors": []}

    auto_items = [i for i in items if i.get("auto_executable", False)]
    logger.info(f"Queue has {len(items)} total items, {len(auto_items)} auto-executable")

    # Load no_touch_rules once for the entire batch
    no_touch_rules = _load_no_touch_rules()

    for item in auto_items:
        wp_task = item.get("wp_task_json")
        if not wp_task:
            logger.warning(
                "Skipping auto-executable item with no wp_task_json: id=%s title=%s",
                item.get("action_id") or item.get("id"),
                item.get("title") or item.get("description", ""),
            )
            results["skipped"] += 1
            continue

        # ── No-touch safety check ──────────────────────────────────────────
        if no_touch_rules:
            blocked, reason = _is_no_touch_target(wp_task, no_touch_rules)
            if blocked:
                logger.warning(
                    "BLOCKED by no_touch_rules: id=%s reason=%s",
                    item.get("action_id") or item.get("id"),
                    reason,
                )
                results["skipped"] += 1
                continue

        # Write task to a temp file and dispatch via task_runner
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="cmd_center_task_", delete=False
        ) as tf:
            json.dump(wp_task, tf, indent=2, ensure_ascii=False)
            task_path = tf.name

        try:
            from wp_ai_ops.task_runner import run_task

            result = run_task(
                task_path=Path(task_path),
                state_dir=Path(state_dir),
                confirm=confirm,
                apply_changes=not dry_run,
            )

            if result.get("status") == "ok":
                results["dispatched"] += 1
                logger.info(f"Dispatched: {item.get('action_id')} — {item.get('description', '')[:60]}")
            elif result.get("status") == "skipped":
                results["skipped"] += 1
                logger.info(
                    "Skipped: %s — %s",
                    item.get("action_id"),
                    result.get("reason", "unknown"),
                )
            else:
                results["errors"].append({
                    "action_id": item.get("action_id"),
                    "error": result.get("reason") or result.get("status", "unknown"),
                })
                logger.warning(
                    "Failed: %s — %s",
                    item.get("action_id"),
                    result.get("reason") or result.get("status", "unknown"),
                )
        except Exception as exc:
            results["errors"].append({"action_id": item.get("action_id"), "error": str(exc)})
            logger.error(f"Error dispatching {item.get('action_id')}: {exc}")
        finally:
            try:
                os.unlink(task_path)
            except OSError:
                pass

    return results


def build_and_dispatch(
    site_id: str = "sweetsworld",
    registry_path: Optional[str] = None,
    graph_db_path: Optional[str] = None,
    state_dir: str = ".wp-ai-ops-state-live",
    dry_run: bool = True,
    observe_only: bool = False,
    output_queue_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the action queue from the graph and immediately dispatch auto items.

    Returns {queue_stats, dispatch_results}.
    """
    try:
        growth_graph_src = str(
            Path(__file__).parent.parent.parent.parent / "growth-graph" / "src"
        )
        if growth_graph_src not in sys.path:
            sys.path.insert(0, growth_graph_src)
        from growth_graph.command_center import build_action_queue
    except ImportError as exc:
        logger.error(f"growth-graph not available: {exc}")
        return {"error": "growth_graph_not_available"}

    queue = build_action_queue(
        site_id=site_id,
        registry_path=registry_path,
        graph_db_path=graph_db_path,
        observe_only=observe_only,
    )

    # Optionally save queue to file for audit
    if output_queue_path:
        with open(output_queue_path, "w", encoding="utf-8") as f:
            f.write(queue.to_json())
        logger.info(f"Queue saved → {output_queue_path}")

    if observe_only:
        logger.info("observe_only=True — skipping dispatch")
        return {"queue_stats": queue.stats, "dispatch_results": None, "observe_only": True}

    queue_dict = json.loads(queue.to_json())
    dispatch_results = dispatch_auto_items(
        queue_dict, state_dir=state_dir, dry_run=dry_run
    )

    return {
        "queue_stats": queue.stats,
        "dispatch_results": dispatch_results,
        "telegram_summary": queue.telegram_summary(),
    }


def main() -> None:
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Dispatch auto-executable actions from the Command Center")
    parser.add_argument("--site", default="sweetsworld")
    parser.add_argument("--queue", default=None, help="Path to pre-built queue JSON (skip graph build)")
    parser.add_argument("--state-dir", default=".wp-ai-ops-state-live")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="Disable dry-run and actually write to WP")
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--output", default=None, help="Save queue JSON to this path")
    args = parser.parse_args()

    dry_run = not args.live

    if args.queue:
        queue_json = load_queue_json(args.queue)
        results = dispatch_auto_items(queue_json, state_dir=args.state_dir, dry_run=dry_run)
        print(json.dumps(results, indent=2))
    else:
        results = build_and_dispatch(
            site_id=args.site,
            state_dir=args.state_dir,
            dry_run=dry_run,
            observe_only=args.observe_only,
            output_queue_path=args.output,
        )
        if "telegram_summary" in results:
            print(results["telegram_summary"])
        print(json.dumps({k: v for k, v in results.items() if k != "telegram_summary"}, indent=2))


if __name__ == "__main__":
    main()
