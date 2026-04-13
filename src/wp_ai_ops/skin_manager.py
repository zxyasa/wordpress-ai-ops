"""
SkinManager — read a design-system skin file and apply it to WordPress/Flatsome.

Flatsome stores its theme options as a PHP-serialized array under the
wp_options row with option_name='theme_mods_flatsome-child'.
The WP REST API does NOT expose wp_options directly, so we use two mechanisms:

  1. /wp-json/wp/v2/settings  — for the handful of core settings exposed there
     (e.g. custom_css via the Customizer).
  2. A server-side PHP bridge endpoint (same pattern as wp-seo-meta.php) that
     can read/write arbitrary wp_options rows — to be implemented as
     wp-theme-options.php on the server.

✅  Flatsome option key names
All keys in FLATSOME_TOKEN_MAP are CONFIRMED against the live sweetsworld.com.au
theme_mods_flatsome-child row (queried 2026-04-08 via SSH + PHP dump).
Live values at time of confirmation are noted in comments.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Flatsome option key mapping
# key   = skin token name (as defined in design-system/skins/*.md)
# value = confirmed Flatsome option key in theme_mods_flatsome-child
#
# All keys confirmed 2026-04-08 via SSH PHP dump of live sweetsworld.com.au.
# Live values at confirmation shown in comments.
# option_name in wp_options: 'theme_mods_flatsome-child'
# ---------------------------------------------------------------------------
FLATSOME_TOKEN_MAP: dict[str, str] = {
    # Primary brand colour — live: #2596be
    "color_primary":        "color_primary",
    # CTA accent (alert/urgency) — live: #dc0f67
    "color_cta_accent":     "color_alert",
    # Checkout button accent — live: #dc0f67 (same as alert; update both together)
    # "color_cta_accent" already maps color_alert; color_checkout mirrors it:
    # handled separately in _build_flatsome_patch()
    # Navigation text colour — live: #334862
    "color_text_primary":   "type_nav_color",
    # Navigation hover colour — live: #000000
    "color_primary_dark":   "type_nav_color_hover",
    # Nav bar background — live: #ffffff
    "color_card_bg":        "nav_position_bg",
    # Header shop strip background — live: #81d8d0
    "color_gallery_bg":     "header_shop_bg_color",
    # Footer background — live: #000000
    "color_card_border":    "footer_2_bg_color",
}

# Keys that can be written via /wp-json/wp/v2/settings (standard WP REST API).
# Confirmed 2026-04-08: html_custom_css is written via this endpoint.
WP_SETTINGS_TOKEN_MAP: dict[str, str] = {
    # custom CSS is injected here rather than via the PHP bridge
    # (no skin token needed — SkinManager.apply_custom_css() handles it directly)
}


class SkinManager:
    """Apply a visual skin (colour tokens) to a WordPress + Flatsome site."""

    SNAPSHOT_DIR = ".wp-ai-ops-state/skin_snapshots"

    def __init__(
        self,
        wp_base_url: str,
        wp_username: str,
        wp_app_password: str,
        dry_run: bool = True,
        state_dir: str | None = None,
    ) -> None:
        self.wp_base_url = wp_base_url.rstrip("/")
        self.wp_username = wp_username
        self.wp_app_password = wp_app_password
        self.dry_run = dry_run

        # Snapshot directory relative to cwd unless overridden
        self._snapshot_dir = Path(state_dir or self.SNAPSHOT_DIR)

        import base64
        token = base64.b64encode(
            f"{wp_username}:{wp_app_password}".encode()
        ).decode("ascii")
        self._auth_header = f"Basic {token}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_skin(self, skin_path: str) -> dict[str, Any]:
        """Parse a skin .md file and return a flat dict of token→value.

        The special key 'color_replacements' is returned as a nested dict
        mapping old_hex → new_value (used by normalize_content_colors).
        """
        path = Path(skin_path)
        if not path.exists():
            raise FileNotFoundError(f"Skin file not found: {skin_path}")
        return _parse_skin_file(path)

    def snapshot(self) -> str:
        """
        Read current Flatsome options via the PHP bridge and write a snapshot.
        Returns the snapshot file path.

        NOTE: Requires the wp-theme-options.php bridge to be deployed on the
        server.  Falls back to a minimal stub snapshot if the bridge is not
        available (so the script can still run in dry-run mode).
        """
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self._snapshot_dir / f"snapshot_{ts}.json"

        current = self._read_flatsome_options()
        snapshot_data = {
            "timestamp": ts,
            "wp_base_url": self.wp_base_url,
            "flatsome_options": current,
        }

        if self.dry_run:
            logger.info("[DRY-RUN] Would write snapshot to %s", path)
            logger.info("[DRY-RUN] Snapshot content: %s", json.dumps(snapshot_data, indent=2))
        else:
            path.write_text(json.dumps(snapshot_data, indent=2), encoding="utf-8")
            logger.info("Snapshot written to %s", path)

        return str(path)

    def apply(self, skin_tokens: dict[str, str]) -> None:
        """
        Map skin tokens to Flatsome option keys and write them.

        Only tokens present in FLATSOME_TOKEN_MAP are written.
        All keys in FLATSOME_TOKEN_MAP are confirmed against the live DB
        (sweetsworld.com.au, 2026-04-08).

        In live mode, requires wp-theme-options.php bridge on the server.
        """
        mapped: dict[str, str] = {}
        for token, value in skin_tokens.items():
            flatsome_key = FLATSOME_TOKEN_MAP.get(token)
            if flatsome_key is None:
                continue  # Not a Flatsome colour token — skip silently
            mapped[flatsome_key] = value

        # color_checkout mirrors color_alert (both confirmed as #dc0f67 on live site)
        if "color_alert" in mapped:
            mapped.setdefault("color_checkout", mapped["color_alert"])

        if self.dry_run:
            print("\n[DRY-RUN] Flatsome option writes (keys confirmed 2026-04-08):")
            print(f"  {'Skin token':<30} {'Flatsome key':<25} {'Value'}")
            print(f"  {'-'*30} {'-'*25} {'-'*15}")
            for fkey, value in mapped.items():
                token = next((t for t, k in FLATSOME_TOKEN_MAP.items() if k == fkey), fkey)
                print(f"  {token:<30} {fkey:<25} {value}")
            if "color_checkout" in mapped and "color_checkout" not in FLATSOME_TOKEN_MAP.values():
                print(f"  {'(mirrors color_alert)':<30} {'color_checkout':<25} {mapped['color_checkout']}")
            print()
            return

        self._write_flatsome_options(mapped)

    def rollback(self, snapshot_path: str) -> None:
        """Restore Flatsome options from a snapshot file."""
        path = Path(snapshot_path)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        flatsome_options = data.get("flatsome_options", {})

        if self.dry_run:
            print(f"\n[DRY-RUN] Would restore {len(flatsome_options)} Flatsome options from:")
            print(f"  {snapshot_path}")
            print(f"  Timestamp: {data.get('timestamp', 'unknown')}")
            return

        # Live rollback: write back via PHP bridge
        self._write_flatsome_options(flatsome_options)
        logger.info("Rollback complete from snapshot %s", snapshot_path)

    def apply_custom_css(self, css: str) -> None:
        """
        Write custom CSS to WordPress Additional CSS.

        Primary method: Code Snippets API — deploys a temporary PHP snippet that
        calls wp_update_custom_css_post(), triggers it, then deletes the snippet.
        This is reliable on sites where /wp-json/wp/v2/settings silently ignores
        the 'custom_css' field (e.g. sites without the Customizer REST endpoint).

        Fallback: POST /wp-json/wp/v2/settings { "custom_css": <css> }
        """
        if self.dry_run:
            print("\n[DRY-RUN] Would write custom CSS via Code Snippet bridge:")
            print(f"  custom_css length: {len(css)} chars")
            print("  Preview (first 300 chars):")
            print(f"  {css[:300]}")
            return

        try:
            self._apply_css_via_code_snippet(css)
            return
        except RuntimeError as exc:
            logger.warning("Code Snippets CSS injection failed: %s — falling back to /wp/v2/settings", exc)

        # Fallback: WP settings endpoint (silently ignored on some sites)
        url = f"{self.wp_base_url}/wp-json/wp/v2/settings"
        payload = json.dumps({"custom_css": css}, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=payload,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read())
            logger.info("custom_css written via settings (%d chars). Response keys: %s",
                        len(css), list(result.keys()))
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Failed to write custom_css: {exc.code} {body[:400]}") from exc

    def _apply_css_via_code_snippet(self, css: str) -> None:
        """
        Deploy a temporary Code Snippet that calls wp_update_custom_css_post(),
        trigger a WP request so it runs, then delete the snippet.

        Uses PHP nowdoc syntax so no escaping is needed for the CSS content.
        """
        import time as _time

        # Pick a nowdoc marker that won't appear in the CSS
        marker = "WPAIOPSCSS_END"
        if marker in css:
            marker = "WPAIOPSCSS_BLOCK_TERMINUS"

        php_code = (
            "<?php\n"
            f"$css = <<<'{marker}'\n"
            f"{css}\n"
            f"{marker};\n"
            "wp_update_custom_css_post( $css, array( 'stylesheet' => get_stylesheet() ) );\n"
        )

        snippets_url = f"{self.wp_base_url}/wp-json/code-snippets/v1/snippets"

        # Step 1: Create snippet (active=true → runs on next WP init)
        payload = json.dumps({
            "name": "wp-ai-ops: inject skin CSS (auto-delete)",
            "code": php_code,
            "active": True,
            "scope": "global",
        }, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            snippets_url,
            data=payload,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                snippet_data = json.loads(resp.read())
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Code Snippets API unavailable or rejected: {exc.code} {body[:400]}"
            ) from exc

        snippet_id = snippet_data.get("id")
        if not snippet_id:
            raise RuntimeError(f"Code Snippets API: no id in response: {snippet_data}")

        logger.info("Created snippet id=%s — triggering WP init to run it...", snippet_id)

        # Step 2: Trigger a WordPress request so the active snippet runs
        _time.sleep(0.5)
        trigger_url = f"{self.wp_base_url}/wp-json/wp/v2/types"
        try:
            trigger_req = urlrequest.Request(
                trigger_url, headers={"Authorization": self._auth_header}
            )
            with urlrequest.urlopen(trigger_req, timeout=10) as resp:
                resp.read()
        except Exception as _exc:
            logger.warning("Trigger request failed (snippet may still have run): %s", _exc)

        _time.sleep(0.5)

        # Step 3: Delete the snippet (CSS is now in DB; snippet is no longer needed)
        delete_url = f"{self.wp_base_url}/wp-json/code-snippets/v1/snippets/{snippet_id}"
        delete_req = urlrequest.Request(
            delete_url,
            headers={"Authorization": self._auth_header},
            method="DELETE",
        )
        try:
            with urlrequest.urlopen(delete_req, timeout=10) as resp:
                resp.read()
            logger.info("Snippet id=%s deleted. Custom CSS written (%d chars).", snippet_id, len(css))
        except Exception as exc:
            logger.warning(
                "Failed to delete snippet id=%s: %s  — CSS was written, delete manually if needed.",
                snippet_id, exc,
            )

    def normalize_content_colors(self, color_replacements: dict[str, str]) -> None:
        """
        Scan all pages, posts, and ux-blocks for hardcoded hex colors and replace them.

        color_replacements: {old_hex: new_value, ...}
        In dry-run mode, prints what would change without writing.
        In live mode, updates each affected post via the WP REST API.
        """
        if not color_replacements:
            print("\n[INFO] No color_replacements in skin — skipping content normalization.")
            return

        print(f"\n  Replacements to apply: {color_replacements}")
        post_types = ["pages", "posts", "ux-blocks"]
        total_hits = 0

        for post_type in post_types:
            posts = self._fetch_all_posts(post_type)
            print(f"  Scanning {len(posts)} {post_type}...")

            for post in posts:
                post_id = post["id"]
                raw_content = post.get("content", {})
                if isinstance(raw_content, dict):
                    content = raw_content.get("raw", "")
                else:
                    content = raw_content or ""

                new_content = content
                changes: list[str] = []
                for old_hex, new_val in color_replacements.items():
                    count = new_content.count(old_hex)
                    if count > 0:
                        new_content = new_content.replace(old_hex, new_val)
                        changes.append(f"{old_hex} → {new_val} ({count}×)")

                if not changes:
                    continue

                title_raw = post.get("title", {})
                title = (title_raw.get("rendered", "") if isinstance(title_raw, dict)
                         else title_raw) or f"ID {post_id}"
                print(f"    [{post_type}:{post_id}] {title[:60]}")
                for c in changes:
                    print(f"      {c}")
                total_hits += 1

                if not self.dry_run:
                    self._update_post_content(post_type, post_id, new_content)

        if self.dry_run:
            print(f"\n[DRY-RUN] Would update {total_hits} item(s).")
        else:
            print(f"\n  Updated {total_hits} item(s).")

    def latest_snapshot_path(self) -> str | None:
        """Return the most recent snapshot path, or None if no snapshots exist."""
        if not self._snapshot_dir.exists():
            return None
        snapshots = sorted(self._snapshot_dir.glob("snapshot_*.json"))
        if not snapshots:
            return None
        return str(snapshots[-1])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def normalize_content_images(self, image_replacements: dict[str, str]) -> None:
        """
        Replace WP media attachment IDs in page/post/ux-block content and featured_media.

        image_replacements: {"old_attachment_id": "new_attachment_id", ...}

        Handles two storage patterns:
          1. Flatsome UX Builder:  bg="OLD_ID"  →  bg="NEW_ID"  (in raw content)
          2. Page featured image:  featured_media field via REST API  (if old ID matches)

        Reversible: apply the default skin with reverse mappings to restore.
        """
        if not image_replacements:
            print("\n[INFO] No image_replacements in skin — skipping image normalization.")
            return

        print(f"\n  Image replacements: {image_replacements}")
        post_types = ["pages", "posts", "ux-blocks"]
        total_updated = 0

        for post_type in post_types:
            posts = self._fetch_all_posts(post_type)
            print(f"  Scanning {len(posts)} {post_type}...")

            for post in posts:
                post_id = post["id"]
                raw_content = post.get("content", {})
                content = raw_content.get("raw", "") if isinstance(raw_content, dict) else raw_content or ""

                title_raw = post.get("title", {})
                title = (title_raw.get("rendered", "") if isinstance(title_raw, dict)
                         else title_raw) or f"ID {post_id}"

                # 1. Replace bg="OLD_ID" shortcode attribute AND direct URL references
                new_content = content
                content_changes: list[str] = []
                for old_id, new_id in image_replacements.items():
                    # Pattern A: Flatsome shortcode  bg="ID"
                    old_attr = f'bg="{old_id}"'
                    new_attr = f'bg="{new_id}"'
                    count_a = new_content.count(old_attr)
                    if count_a > 0:
                        new_content = new_content.replace(old_attr, new_attr)
                        content_changes.append(f'bg="{old_id}" → bg="{new_id}" ({count_a}×)')

                    # Pattern B: direct URL in src= or url()
                    old_url, old_w, old_h = self._get_attachment_info(old_id)
                    new_url, new_w, new_h = self._get_attachment_info(new_id)
                    if old_url and new_url:
                        count_b = new_content.count(old_url)
                        if count_b > 0:
                            new_content = new_content.replace(old_url, new_url)
                            old_fname = old_url.split("/")[-1]
                            new_fname = new_url.split("/")[-1]
                            content_changes.append(f'URL {old_fname} → {new_fname} ({count_b}×)')
                            # Fix width/height attributes in <img> tags if dimensions differ
                            if old_w and old_h and new_w and new_h and (old_w, old_h) != (new_w, new_h):
                                import re as _re
                                dim_pattern = (
                                    r'(width=")' + str(old_w) + r'("\s+height=")' + str(old_h) + r'"'
                                    r'|'
                                    r'(height=")' + str(old_h) + r'("\s+width=")' + str(old_w) + r'"'
                                )
                                new_content_dim = _re.sub(
                                    dim_pattern,
                                    lambda m: (
                                        f'width="{new_w}" height="{new_h}"'
                                        if m.group(0).startswith('width')
                                        else f'height="{new_h}" width="{new_w}"'
                                    ),
                                    new_content,
                                )
                                if new_content_dim != new_content:
                                    new_content = new_content_dim
                                    content_changes.append(
                                        f'  img dimensions: {old_w}×{old_h} → {new_w}×{new_h}'
                                    )

                if content_changes:
                    print(f"    [{post_type}:{post_id}] {title[:50]}")
                    for c in content_changes:
                        print(f"      {c}")
                    total_updated += 1
                    if not self.dry_run:
                        self._update_post_content(post_type, post_id, new_content)

                # 2. Check featured_media
                current_featured = post.get("featured_media", 0)
                if current_featured and str(current_featured) in image_replacements:
                    new_featured = int(image_replacements[str(current_featured)])
                    print(f"    [{post_type}:{post_id}] {title[:50]}")
                    print(f"      featured_media: {current_featured} → {new_featured}")
                    if not self.dry_run:
                        self._update_featured_media(post_type, post_id, new_featured)
                    total_updated += 1

        if self.dry_run:
            print(f"\n[DRY-RUN] Would update {total_updated} item(s) (images).")
        else:
            print(f"\n  Updated {total_updated} item(s) (images).")

    def _get_attachment_url(self, attachment_id: str) -> str:
        """Fetch and cache the source URL for a WP media attachment."""
        return self._get_attachment_info(attachment_id)[0]

    def _get_attachment_info(self, attachment_id: str) -> tuple[str, int, int]:
        """Fetch and cache (source_url, width, height) for a WP media attachment."""
        if not hasattr(self, "_attachment_info_cache"):
            self._attachment_info_cache: dict[str, tuple[str, int, int]] = {}
        # Legacy URL-only cache migration
        if not hasattr(self, "_attachment_url_cache"):
            self._attachment_url_cache: dict[str, str] = {}
        if attachment_id in self._attachment_info_cache:
            return self._attachment_info_cache[attachment_id]
        url = f"{self.wp_base_url}/wp-json/wp/v2/media/{attachment_id}"
        req = urlrequest.Request(url, headers={"Authorization": self._auth_header})
        try:
            with urlrequest.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            src = data.get("source_url", "")
            details = data.get("media_details", {})
            w = int(details.get("width", 0))
            h = int(details.get("height", 0))
            result = (src, w, h)
            self._attachment_info_cache[attachment_id] = result
            self._attachment_url_cache[attachment_id] = src  # keep legacy cache warm
            return result
        except Exception as exc:
            logger.warning("Could not fetch info for attachment %s: %s", attachment_id, exc)
            empty: tuple[str, int, int] = ("", 0, 0)
            self._attachment_info_cache[attachment_id] = empty
            self._attachment_url_cache[attachment_id] = ""
            return empty

    def _update_featured_media(self, post_type: str, post_id: int, media_id: int) -> None:
        """Update the featured_media field of a post/page via REST API."""
        url = f"{self.wp_base_url}/wp-json/wp/v2/{post_type}/{post_id}"
        payload = json.dumps({"featured_media": media_id}, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            url, data=payload,
            headers={"Authorization": self._auth_header,
                     "Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                json.loads(resp.read())
                logger.info("Updated featured_media %s:%d → %d", post_type, post_id, media_id)
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.error("Failed to update featured_media %s:%d — %s %s",
                         post_type, post_id, exc.code, body[:200])

    def _fetch_all_posts(self, post_type: str) -> list[dict]:
        """Fetch all items of a given WP post type with raw content (context=edit)."""
        results: list[dict] = []
        page = 1
        per_page = 100

        while True:
            url = (
                f"{self.wp_base_url}/wp-json/wp/v2/{post_type}"
                f"?context=edit&per_page={per_page}&page={page}&status=any"
            )
            req = urlrequest.Request(url, headers={"Authorization": self._auth_header})
            try:
                with urlrequest.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read())
                if not data:
                    break
                results.extend(data)
                if len(data) < per_page:
                    break
                page += 1
            except urlerror.HTTPError as exc:
                if exc.code == 400:  # WP returns 400 when page is out of range
                    break
                logger.warning("Failed to fetch %s page %d: %s", post_type, page, exc)
                break
            except Exception as exc:
                logger.warning("Error fetching %s page %d: %s", post_type, page, exc)
                break

        return results

    def _update_post_content(self, post_type: str, post_id: int, content: str) -> None:
        """Update raw content of a post/page/block via WP REST API (POST)."""
        url = f"{self.wp_base_url}/wp-json/wp/v2/{post_type}/{post_id}"
        payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=payload,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                json.loads(resp.read())
                logger.info("Updated %s:%d", post_type, post_id)
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.error(
                "Failed to update %s:%d — %s %s", post_type, post_id, exc.code, body[:200]
            )

    def _bridge_token(self) -> str:
        """Return WP_THEME_OPTIONS_TOKEN or raise if unset."""
        token = os.environ.get("WP_THEME_OPTIONS_TOKEN", "")
        if not token:
            raise RuntimeError(
                "WP_THEME_OPTIONS_TOKEN not set — cannot communicate with wp-theme-options.php bridge. "
                "Set it in .env and ensure the bridge is deployed on the server."
            )
        return token

    def _read_flatsome_options(self) -> dict[str, Any]:
        """
        Read current Flatsome options via the PHP bridge endpoint
        (wp-theme-options.php?action=read).  Returns empty dict if bridge unavailable.
        Token sent as HTTP header X-Bridge-Token (not in URL).
        """
        try:
            token = self._bridge_token()
        except RuntimeError as exc:
            logger.warning("%s — snapshot will be empty stub.", exc)
            return {}

        url = f"{self.wp_base_url}/wp-theme-options.php?action=read"
        try:
            req = urlrequest.Request(
                url,
                headers={
                    "Authorization": self._auth_header,
                    "X-Bridge-Token": token,
                },
            )
            with urlrequest.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                if data.get("ok"):
                    return data.get("options", {})
                logger.warning("wp-theme-options.php returned ok=false: %s", data)
                return {}
        except Exception as exc:
            logger.warning(
                "Could not read Flatsome options via bridge (%s). "
                "Snapshot will be empty stub. Deploy wp-theme-options.php to enable.",
                exc,
            )
            return {}

    def _write_flatsome_options(self, options: dict[str, Any]) -> None:
        """
        Write Flatsome options via the PHP bridge (action=write).

        The bridge ALWAYS auto-snapshots before writing on the server side.
        Token sent as HTTP header X-Bridge-Token.
        Payload: {"keys": {flatsome_key: value, ...}}
        """
        token = self._bridge_token()  # raises if unset

        url = f"{self.wp_base_url}/wp-theme-options.php?action=write"
        payload = json.dumps({"keys": options}, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=payload,
            headers={
                "Authorization": self._auth_header,
                "Content-Type": "application/json; charset=utf-8",
                "X-Bridge-Token": token,
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
                if not data.get("ok"):
                    raise RuntimeError(f"wp-theme-options.php write failed: {data}")
                logger.info(
                    "Flatsome options written. Keys: %s | Server snapshot: %s",
                    data.get("keys_written"),
                    data.get("snapshot_before"),
                )
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Failed to write Flatsome options: {exc.code} {body[:400]}") from exc


# ---------------------------------------------------------------------------
# Skin file parser
# ---------------------------------------------------------------------------

def _parse_skin_file(path: Path) -> dict[str, Any]:
    """
    Parse a skin .md file into a flat dict.

    Supported line formats:
      key: "value"       → string (quotes stripped)
      key: value         → string (bare)
      key: [1, 2, 3]     → stored as raw string (not used for colour mapping)
      # comment lines    → ignored
      blank lines        → ignored

    Special block (indented sub-keys):
      color_replacements:
        "#old_hex": "new_value"   → stored as dict under 'color_replacements' key
    """
    tokens: dict[str, Any] = {}
    css_lines: list[str] = []
    in_css_block = False
    current_block_key: str | None = None   # e.g. "color_replacements" or "image_replacements"
    block_data: dict[str, str] = {}

    # Keys that contain indented "old": "new" sub-dicts
    _REPLACEMENT_BLOCK_KEYS = {"color_replacements", "image_replacements"}

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        # Fenced custom_css block
        if stripped.startswith("```"):
            in_css_block = not in_css_block
            current_block_key = None
            continue

        if in_css_block:
            css_lines.append(line)
            continue

        if not stripped or stripped.startswith("#"):
            continue

        # Detect a replacements block start (e.g. "color_replacements:" or "image_replacements: {}")
        block_match = re.match(r'^(\w+_replacements)\s*:\s*(?:\{\})?\s*$', stripped)
        if block_match:
            if current_block_key:
                tokens[current_block_key] = dict(block_data)
            current_block_key = block_match.group(1)
            block_data = {}
            continue

        # Parse indented entries inside a replacements block
        if current_block_key:
            if line.startswith((" ", "\t")):
                m = re.match(r'^"([^"]+)"\s*:\s*"([^"]*)"', stripped)
                if m:
                    block_data[m.group(1)] = m.group(2)
                continue
            else:
                # Indentation ended — save block and fall through
                tokens[current_block_key] = dict(block_data)
                current_block_key = None
                block_data = {}

        # Standard  key: "value"  or  key: value
        m = re.match(r'^(\w+)\s*:\s*(.+)$', stripped)
        if not m:
            continue

        key = m.group(1)
        raw_value = m.group(2).strip()
        if (raw_value.startswith('"') and raw_value.endswith('"')) or \
           (raw_value.startswith("'") and raw_value.endswith("'")):
            raw_value = raw_value[1:-1]

        tokens[key] = raw_value

    # Flush any open replacements block at EOF
    if current_block_key is not None:
        tokens[current_block_key] = dict(block_data)

    if css_lines:
        tokens["custom_css"] = "\n".join(css_lines)

    return tokens
