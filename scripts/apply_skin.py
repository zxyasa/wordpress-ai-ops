"""
Apply a visual skin to a WordPress site.

Usage:
  python scripts/apply_skin.py --site newcastlehub --skin newcastlehub-mothers-day --dry-run
  python scripts/apply_skin.py --site newcastlehub --skin newcastlehub-mothers-day --live
  python scripts/apply_skin.py --site newcastlehub --rollback --live
  python scripts/apply_skin.py --site sweetsworld  --skin default --dry-run

⚠️  LIVE MODE SAFETY PROTOCOL:
  1. Snapshot is MANDATORY before any write (auto-enforced, cannot be skipped)
  2. Diff between current values and new values is shown before writing
  3. THREE interactive confirmations required before any live write:
       Confirm 1: "You are about to write to a LIVE PRODUCTION site."
       Confirm 2: "Snapshot has been taken. Confirm you have reviewed the diff."
       Confirm 3: "FINAL WARNING — type the site hostname to confirm."
  4. Rollback also requires confirmation before executing

Environment variables (loaded automatically from sites/<site_id>/.env):
  WP_BASE_URL             WordPress site URL
  WP_USERNAME             WordPress username
  WP_APP_PASSWORD         WordPress application password
  WP_THEME_OPTIONS_TOKEN  PHP bridge token (needed for Flatsome write/snapshot/rollback)

Skin files are resolved in order:
  1. sites/<site_id>/skins/<skin_name>.md
  2. agents/sweetsworld-seo-agent/design-system/skins/<skin_name>.md
  3. SKIN_DIR env var (if set)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Allow running as  python scripts/apply_skin.py  from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from wp_ai_ops.skin_manager import FLATSOME_TOKEN_MAP, SkinManager  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # agents/
_SITES_DIR = _REPO_ROOT / "agents" / "sweetsworld-seo-agent" / "sites"
_DEFAULT_SKIN_DIR = _REPO_ROOT / "agents" / "sweetsworld-seo-agent" / "design-system" / "skins"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_site_env(site_id: str) -> None:
    """Load sites/<site_id>/.env into os.environ (does not overwrite existing vars)."""
    env_file = _SITES_DIR / site_id / ".env"
    if not env_file.exists():
        print(f"ERROR: No .env found for site '{site_id}' at {env_file}", file=sys.stderr)
        sys.exit(1)
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _resolve_skin_path(skin_name: str, site_id: str) -> Path:
    # 1. Per-site skins dir
    site_skin = _SITES_DIR / site_id / "skins" / f"{skin_name}.md"
    if site_skin.exists():
        return site_skin
    # 2. Shared design-system skins
    shared_skin = _DEFAULT_SKIN_DIR / f"{skin_name}.md"
    if shared_skin.exists():
        return shared_skin
    # 3. SKIN_DIR override
    if "SKIN_DIR" in os.environ:
        override = Path(os.environ["SKIN_DIR"]) / f"{skin_name}.md"
        if override.exists():
            return override
    # Not found — show available
    print(f"ERROR: Skin '{skin_name}' not found.", file=sys.stderr)
    print(f"Available skins:", file=sys.stderr)
    for d in [_SITES_DIR / site_id / "skins", _DEFAULT_SKIN_DIR]:
        if d.exists():
            for f in sorted(d.glob("*.md")):
                print(f"  {f.stem}  ({d})", file=sys.stderr)
    sys.exit(1)


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"ERROR: Environment variable {name} is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def _confirm(prompt: str, expected: str | None = None) -> None:
    """
    Interactive confirmation gate.
    If expected is set, the user must type that exact string.
    Otherwise they must type 'yes'.
    """
    if expected:
        answer = input(f"\n{prompt}\nType exactly [{expected}] to continue: ").strip()
        if answer != expected:
            print("Aborted — input did not match. No changes made.")
            sys.exit(0)
    else:
        answer = input(f"\n{prompt}\nType 'yes' to continue: ").strip().lower()
        if answer != "yes":
            print("Aborted. No changes made.")
            sys.exit(0)


def _print_diff(current: dict, incoming: dict) -> None:
    """Print a side-by-side diff of values being changed."""
    mapped_keys = set(FLATSOME_TOKEN_MAP.values()) | {"color_checkout"}
    relevant_current = {k: v for k, v in current.items() if k in mapped_keys}

    print("\n" + "=" * 70)
    print("  DIFF — values that will change on the live site")
    print("=" * 70)
    print(f"  {'Flatsome key':<30} {'CURRENT (live)':<20} {'NEW (skin)'}")
    print(f"  {'-'*30} {'-'*20} {'-'*20}")

    has_changes = False
    for fkey, new_val in incoming.items():
        cur_val = relevant_current.get(fkey, "(not set)")
        marker = "  " if cur_val == new_val else "→ "
        print(f"{marker} {fkey:<30} {str(cur_val):<20} {new_val}")
        if cur_val != new_val:
            has_changes = True

    if not has_changes:
        print("  (no changes — new values are identical to current)")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply a visual skin to a WordPress site",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--site", metavar="SITE_ID", default="sweetsworld",
                        help="Site ID matching sites/<site_id>/.env (default: sweetsworld)")
    parser.add_argument("--skin", metavar="NAME", help="Skin name (e.g. default, newcastlehub-mothers-day)")
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Actually write to WordPress — requires 3 interactive confirmations",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing (this is the default behaviour)",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        default=False,
        help="Restore the most recent snapshot",
    )
    parser.add_argument(
        "--snapshot-path",
        metavar="PATH",
        default=None,
        help="Specific snapshot file to rollback to (default: most recent)",
    )
    parser.add_argument(
        "--state-dir",
        metavar="DIR",
        default=".wp-ai-ops-state",
        help="Directory for snapshots (default: .wp-ai-ops-state)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Skip interactive confirmations (CI mode — use with extreme caution)",
    )

    args = parser.parse_args()

    if args.rollback and args.skin:
        parser.error("--rollback and --skin cannot be used together")
    if not args.rollback and not args.skin:
        parser.error("Either --skin NAME or --rollback is required")

    # Load site-specific .env BEFORE reading any env vars
    _load_site_env(args.site)

    dry_run = not args.live

    if dry_run:
        print("=" * 60)
        print("  DRY-RUN MODE  (pass --live to actually write)")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  ⚠️   LIVE MODE — WRITES TO PRODUCTION SITE   ⚠️")
        print("=" * 60)

    wp_base_url    = _require_env("WP_BASE_URL")
    wp_username    = _require_env("WP_USERNAME")
    wp_app_password = _require_env("WP_APP_PASSWORD")

    # Extract hostname for final confirmation
    from urllib.parse import urlparse
    hostname = urlparse(wp_base_url).hostname or wp_base_url

    manager = SkinManager(
        wp_base_url=wp_base_url,
        wp_username=wp_username,
        wp_app_password=wp_app_password,
        dry_run=dry_run,
        state_dir=args.state_dir,
    )

    # ------------------------------------------------------------------ ROLLBACK
    if args.rollback:
        snap_path = args.snapshot_path or manager.latest_snapshot_path()
        if snap_path is None:
            print("ERROR: No snapshots found. Nothing to rollback.", file=sys.stderr)
            sys.exit(1)

        print(f"\nRollback target: {snap_path}")

        if not dry_run:
            if not args.yes:
                _confirm(
                    f"⚠️  ROLLBACK will overwrite LIVE theme options on [{hostname}].\n"
                    f"   Snapshot: {snap_path}\n"
                    f"   A safety snapshot of the CURRENT state will be saved first.",
                )
            else:
                print("  [--yes] Skipping rollback confirmation.")

        manager.rollback(snap_path)
        print("Rollback complete." if not dry_run else "[DRY-RUN] Rollback simulated.")
        return

    # ------------------------------------------------------------------ APPLY SKIN
    skin_path = _resolve_skin_path(args.skin, args.site)
    print(f"\nLoading skin: {skin_path.name}  ({skin_path})")
    skin_tokens = manager.load_skin(str(skin_path))

    colour_tokens = {k: v for k, v in skin_tokens.items() if k.startswith("color_")}
    print(f"  Loaded {len(skin_tokens)} tokens ({len(colour_tokens)} colour tokens)")

    # ── CONFIRMATION 1 (live only) ────────────────────────────────────────────
    if not dry_run and not args.yes:
        _confirm(
            f"⚠️  CONFIRMATION 1 of 3\n"
            f"   You are about to write to a LIVE PRODUCTION site: [{hostname}]\n"
            f"   Skin: {args.skin}\n"
            f"   A snapshot will be taken automatically BEFORE any write."
        )

    # ── STEP 1: Mandatory snapshot ─────────────────────────────────────────────
    print("\nStep 1 — Taking snapshot of current settings (MANDATORY before any write)...")
    snap_path = manager.snapshot()
    print(f"  Snapshot saved: {snap_path}")

    # ── Read current values for diff (live only) ──────────────────────────────
    if not dry_run:
        from wp_ai_ops.skin_manager import FLATSOME_TOKEN_MAP as _TOKEN_MAP
        import json as _json
        snap_data = _json.loads(Path(snap_path).read_text(encoding="utf-8"))
        current_options = snap_data.get("flatsome_options", {})

        # Build the "incoming" dict the same way apply() would
        incoming: dict[str, str] = {}
        for token, value in skin_tokens.items():
            fkey = _TOKEN_MAP.get(token)
            if fkey:
                incoming[fkey] = value
        if "color_alert" in incoming:
            incoming.setdefault("color_checkout", incoming["color_alert"])

        _print_diff(current_options, incoming)

        # ── CONFIRMATION 2 ────────────────────────────────────────────────────
        if not args.yes:
            _confirm(
                "⚠️  CONFIRMATION 2 of 3\n"
                "   Snapshot confirmed. You have reviewed the diff above.\n"
                "   The changes shown will be written to the live database."
            )

    # ── STEP 2: Apply Flatsome options ────────────────────────────────────────
    print("\nStep 2 — Applying Flatsome theme options...")
    if not dry_run and not args.yes:
        # ── CONFIRMATION 3 — type the hostname ───────────────────────────────
        _confirm(
            f"⚠️  CONFIRMATION 3 of 3  — FINAL WARNING\n"
            f"   This is the last chance to abort.\n"
            f"   After this, changes will be written to [{hostname}].",
            expected=hostname,
        )

    manager.apply(skin_tokens)

    # ── STEP 3: Custom CSS ────────────────────────────────────────────────────
    custom_css = skin_tokens.get("custom_css", "")
    if custom_css:
        print("\nStep 3 — Applying custom CSS...")
        try:
            manager.apply_custom_css(custom_css)
        except RuntimeError as _css_err:
            print(f"  ⚠️  Custom CSS write failed: {_css_err}")
            print("  Paste the following CSS manually in WP Admin → Appearance → Additional CSS:")
            print("  " + "-" * 60)
            for line in custom_css.splitlines():
                print(f"  {line}")
            print("  " + "-" * 60)
            print("  Continuing with remaining steps...")
    else:
        print("\nStep 3 — No custom_css block in skin — skipping.")

    # ── STEP 4: Normalize hardcoded colors in page/post/block content ─────────
    color_replacements = skin_tokens.get("color_replacements", {})
    if color_replacements:
        print("\nStep 4 — Normalizing hardcoded colors in content...")
        manager.normalize_content_colors(color_replacements)
    else:
        print("\nStep 4 — No color_replacements in skin — skipping.")

    # ── STEP 5: Replace background images in content ──────────────────────────
    image_replacements = skin_tokens.get("image_replacements", {})
    if image_replacements:
        print("\nStep 5 — Replacing background images in content...")
        manager.normalize_content_images(image_replacements)
    else:
        print("\nStep 5 — No image_replacements in skin — skipping.")

    print("\n✅ Done.")
    if dry_run:
        print("   Re-run with --live to apply for real.")
    else:
        print(f"   Snapshot (for rollback): {snap_path}")
        print(f"   To undo: python scripts/apply_skin.py --rollback --live")


if __name__ == "__main__":
    main()
