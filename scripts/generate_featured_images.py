#!/usr/bin/env python3
"""
Generate featured images via Jimeng (Volcengine T2I) and upload to WordPress.

── Mode 1: Skin background images (newcastlehub and other sites) ────────────
  python scripts/generate_featured_images.py --site newcastlehub --skin newcastlehub-mothers-day --dry-run
  python scripts/generate_featured_images.py --site newcastlehub --skin newcastlehub-mothers-day
  python scripts/generate_featured_images.py --site newcastlehub --skin newcastlehub-mothers-day --upload --live
  python scripts/generate_featured_images.py --site newcastlehub --skin newcastlehub-mothers-day --slot hero --upload --live

  Reads:   sites/<site_id>/image_slots.json     — slot dimensions & business context
           skin file image_prompt_<slot_id>      — seasonal brief
  Uses Claude to build contextual Jimeng prompts from site purpose + seasonal brief.
  Images match the site's actual business — never generic unrelated stock photos.

── Mode 2: Blog post featured images (sweetsworld, legacy) ─────────────────
  python scripts/generate_featured_images.py --dry-run
  python scripts/generate_featured_images.py
  python scripts/generate_featured_images.py --ids 71761,71060
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import requests

# Import Jimeng signing from sweetsworld-volcengine-agent
_VOLC_AGENT_SRC = Path(__file__).parent.parent.parent.parent / "agents" / "sweetsworld-volcengine-agent" / "src_py"
sys.path.insert(0, str(_VOLC_AGENT_SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jimeng import volc_sign_v4_headers, get_volc_ak, get_volc_sk  # noqa: E402
from wp_ai_ops.skin_manager import _parse_skin_file  # noqa: E402

# ---------------------------------------------------------------------------
# Paths (skin mode)
# ---------------------------------------------------------------------------

_REPO_ROOT  = Path(__file__).resolve().parent.parent.parent.parent
_SITES_DIR  = _REPO_ROOT / "agents" / "sweetsworld-seo-agent" / "sites"
_SKIN_DIR   = _REPO_ROOT / "agents" / "sweetsworld-seo-agent" / "design-system" / "skins"

# ---------------------------------------------------------------------------
# Config (sweetsworld legacy mode)
# ---------------------------------------------------------------------------

SITE_API = "https://sweetsworld.com.au/wp-json/wp/v2"
VOLC_BASE = "https://visual.volcengineapi.com"
VOLC_REGION = "cn-north-1"
JIMENG_REQ_KEY = "jimeng_t2i_v40"   # 即梦AI图片生成4.0，仅支持 1024x1024

# SEO/content pages that need images — system pages excluded
SEO_PAGE_IDS = [
    71756, 71757, 71758, 71759, 71760,  # seasonal sub-pages (force-regenerate with proper images)
    71060,   # store-locator
    25972,   # returns-refunds
    69773,   # best-sour-lollies-australia
    69768,   # wholesale-candy-australia
    63138,   # takis chips guide
    22503,   # british-lollies
    22499,   # new-arrivals
    22225,   # contact
    15119,   # sweet-stories
    12626,   # imported-sweets-shop
    507,     # on-sale
    221,     # shipping-information
    2,       # about-us
]

POST_IDS = [
    71761,   # nerds-candy-australia
]

# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

def _load_env() -> dict:
    result: dict = {}
    for p in [
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent.parent.parent / "agents" / "tg_agent" / ".env",
    ]:
        if p.exists():
            for line in p.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k and k not in result:
                        result[k] = v.strip()
    return result


def _get(env: dict, *keys: str) -> str:
    for k in keys:
        v = os.environ.get(k) or env.get(k, "")
        if v:
            return v.strip()
    return ""

def _volc_sign(ak: str, sk: str, method: str, url: str,
               query: dict, body: bytes) -> dict:
    """Wrapper around jimeng.py's battle-tested signing function."""
    return volc_sign_v4_headers(
        ak=ak, sk=sk, service="cv", region=VOLC_REGION,
        method=method, url=url, query=query,
        headers={"Content-Type": "application/json"}, body=body,
    )

# ---------------------------------------------------------------------------
# Jimeng T2I
# ---------------------------------------------------------------------------

_SLUG_PROMPT_MAP: dict[str, str] = {
    # Seasonal sub-pages
    "christmas-sweets": (
        "Christmas candy and festive sweets display — candy canes, chocolate Santa, Christmas lolly gift boxes "
        "in red green and gold, Australian Christmas summer theme, colourful flat lay on white background, "
        "no text, no watermark, photorealistic"
    ),
    "easter-sweets": (
        "Easter chocolate and sweets assortment — Darrell Lea rocky road Easter eggs, Cadbury Mini Eggs, "
        "pastel-coloured Easter lollies and chocolate bunnies, soft pastel background, "
        "Australian Easter candy flat lay, no text, no watermark, photorealistic"
    ),
    "halloween-sweets": (
        "Halloween candy and lollies assortment — Lolliland Halloween platter, gummy eyeballs, "
        "skull-shaped lollies, orange black and purple colour scheme, spooky fun atmosphere, "
        "flat lay on dark background, no text, no watermark, photorealistic"
    ),
    "valentines-day-sweets": (
        "Valentine's Day chocolate and sweets gift — heart-shaped chocolate box, red and pink lollies, "
        "rose petals, romantic candy gift display, soft pink background, "
        "no text, no watermark, photorealistic"
    ),
    "mothers-day-sweets": (
        "Mother's Day chocolate gift box — premium chocolates and sweets elegantly arranged, "
        "pink flowers and ribbon, luxury confectionery gift, soft pink and gold tones, "
        "no text, no watermark, photorealistic"
    ),
    # Blog posts
    "nerds-candy-australia": (
        "Nerds Clusters candy and Nerds Rope spilling onto white surface, "
        "small crunchy rainbow-coloured sugar clusters in neon pink, blue, purple and yellow, "
        "close-up product flat lay, bright studio lighting, Australian candy store style, "
        "no text, no watermark, photorealistic"
    ),
    # SEO pages
    "store-locator": (
        "Australian candy shop interior in Newcastle NSW, "
        "wooden shelves lined with colourful glass lolly jars filled with rainbow sweets, "
        "warm inviting shop lighting, cheerful retail atmosphere, no people, no text, no watermark, photorealistic"
    ),
    "returns-refunds": (
        "Candy gift box open on white surface showing colourful Australian lollies inside, "
        "clean minimal product photography, soft studio lighting, trust and quality theme, "
        "no text, no watermark, photorealistic"
    ),
    "best-sour-lollies-australia": (
        "Australian sour lolly assortment — Warheads, sour gummy worms, sour straps, "
        "sour watermelon slices — bright neon green yellow orange, extreme sour candy, "
        "flat lay on white background, bold vivid colours, no text, no watermark, photorealistic"
    ),
    "wholesale-candy-australia": (
        "Wholesale bulk candy display — large transparent bags of mixed lollies, "
        "stacked candy jars and bulk confectionery in commercial quantities, "
        "bright product photography, white background, no text, no watermark, photorealistic"
    ),
    "takis-chips-the-ultimate-guide-to-these-bold-and-spicy-tortilla-chips": (
        "Takis Fuego rolled tortilla chips bursting from the red and black bag, "
        "bold spicy Mexican snack, chips scattered dramatically on dark background, "
        "red chilli powder dusting, intense product photography, no text overlay, no watermark, photorealistic"
    ),
    "british-lollies": (
        "Classic British sweets assortment — Jelly Babies, Wine Gums, Fruit Pastilles, "
        "Sherbet Lemons, Murray Mints, Percy Pigs — colourful flat lay on white background, "
        "UK confectionery, cheerful and nostalgic, no text, no watermark, photorealistic"
    ),
    "new-arrivals": (
        "Fresh new imported candy and sweets just arrived — American and British confectionery — "
        "colourful products displayed as if just unboxed, bright studio lighting, "
        "white background, excitement and discovery theme, no text, no watermark, photorealistic"
    ),
    "contact": (
        "Welcoming Australian candy shop service counter, "
        "colourful lolly jars and sweet displays behind the counter, "
        "bright cheerful atmosphere, no people, no text, no watermark, photorealistic"
    ),
    "sweet-stories": (
        "Flat lay of colourful Australian lollies and chocolates arranged with open notebook, "
        "lifestyle candy blog photography, pastel pink background, "
        "storytelling and candy culture theme, no text, no watermark, photorealistic"
    ),
    "imported-sweets-shop": (
        "International imported candy from America, UK and Japan — Hershey's, Cadbury, Pocky, "
        "Reese's, Haribo — arranged together in colourful flat lay on white background, "
        "global sweets collection, no text, no watermark, photorealistic"
    ),
    "on-sale": (
        "Colourful Australian candy bags and lolly packs on sale display, "
        "bright orange and yellow sale theme, assorted discounted sweets, "
        "cheerful product photography, white background, no text, no watermark, photorealistic"
    ),
    "shipping-information": (
        "Australian candy gift box being packed for delivery — colourful lollies visible inside open box, "
        "kraft paper, bubble wrap, flat-rate shipping theme, clean white surface, "
        "no text, no watermark, photorealistic"
    ),
    "newcastle-candy-store-about-us": (
        "SweetsWorld candy store in Newcastle NSW Australia — "
        "bright colourful shop interior with rainbow lolly jars and chocolate displays, "
        "friendly Australian confectionery store atmosphere, no people, no text, no watermark, photorealistic"
    ),
}


def _build_image_prompt(title: str, slug: str) -> str:
    """Return a Jimeng T2I prompt matched to this page's slug."""
    if slug in _SLUG_PROMPT_MAP:
        return _SLUG_PROMPT_MAP[slug]
    # Fallback — should not be reached if all slugs are mapped above
    clean_title = title.replace("&#038;", "&").replace("&#8211;", "-").strip()
    raise ValueError(
        f"No prompt defined for slug '{slug}' (title: {clean_title!r}). "
        "Add an entry to _SLUG_PROMPT_MAP before running."
    )


def generate_image(prompt: str, ak: str, sk: str) -> bytes:
    """Call Jimeng T2I API, poll until done, return image bytes."""
    # CVProcess is synchronous — no polling needed
    payload = {
        "req_key": JIMENG_REQ_KEY,
        "prompt": prompt,
        "width": 1600,
        "height": 900,
    }
    body = json.dumps(payload, ensure_ascii=False).encode()
    params = {"Action": "CVProcess", "Version": "2022-08-31"}
    headers = _volc_sign(ak, sk, "POST", f"{VOLC_BASE}/", params, body)

    r = requests.post(f"{VOLC_BASE}/", params=params,
                      headers=headers, data=body, timeout=120)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 10000 and data.get("status") != 10000:
        raise RuntimeError(f"Jimeng error: {data.get('message', str(data)[:200])}")

    data_obj = data.get("data") or {}
    b64_list = data_obj.get("binary_data_base64") or []
    if b64_list:
        return base64.b64decode(b64_list[0])

    img_url = (data_obj.get("image_urls") or [None])[0]
    if img_url:
        img_r = requests.get(img_url, timeout=60)
        img_r.raise_for_status()
        return img_r.content

    raise RuntimeError(f"No image data in response: {str(data)[:320]}")

# ---------------------------------------------------------------------------
# WordPress helpers
# ---------------------------------------------------------------------------

def _wp_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}"}


def wp_get_resource(resource_type: str, resource_id: int,
                    username: str, password: str) -> dict:
    url = f"{SITE_API}/{resource_type}/{resource_id}"
    req = urllib.request.Request(url, headers=_wp_headers(username, password))
    return json.loads(urllib.request.urlopen(req).read())


def wp_upload_image(image_bytes: bytes, filename: str,
                    username: str, password: str) -> int:
    url = f"{SITE_API}/media"
    headers = {
        **_wp_headers(username, password),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/png",
    }
    req = urllib.request.Request(url, data=image_bytes, headers=headers, method="POST")
    result = json.loads(urllib.request.urlopen(req).read())
    return result["id"]


def wp_set_featured_media(resource_type: str, resource_id: int,
                           media_id: int, username: str, password: str) -> None:
    url = f"{SITE_API}/{resource_type}/{resource_id}"
    payload = json.dumps({"featured_media": media_id}).encode()
    headers = {
        **_wp_headers(username, password),
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    urllib.request.urlopen(req)

# ---------------------------------------------------------------------------
# Skin image generation mode
# ---------------------------------------------------------------------------

def _load_site_env(site_id: str) -> None:
    env_file = _SITES_DIR / site_id / ".env"
    if not env_file.exists():
        print(f"ERROR: No .env for site '{site_id}'", file=sys.stderr)
        sys.exit(1)
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def _build_skin_prompt(site_desc: str, slot: dict, seasonal_brief: str) -> str:
    """
    Use Claude Haiku to craft a contextual Jimeng prompt from site context + seasonal brief.
    Images must be relevant to the site's actual business, not generic stock photos.
    Falls back to simple concatenation if ANTHROPIC_API_KEY is unset.
    """
    import urllib.request as _ureq
    import urllib.error as _uerr

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return f"{slot['default_prompt']}, {seasonal_brief}"

    system = (
        "You write image prompts for Jimeng (即梦) text-to-image AI. "
        "Given a website's business, a specific image slot's usage, and a seasonal theme brief, "
        "write ONE Jimeng prompt in English (~60 words) for a background photo. "
        "The image MUST reflect the site's actual business and purpose — never use generic or unrelated imagery. "
        "No UI, text, logos, or watermarks in the image. Output ONLY the prompt, nothing else."
    )
    user = (
        f"Business: {site_desc}\n\n"
        f"Image slot: {slot['usage']}\n"
        f"Dimensions: {slot['width']}x{slot['height']}px\n\n"
        f"Seasonal theme: {seasonal_brief}\n\n"
        "Write the Jimeng image prompt:"
    )
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 200,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"].strip()
    except Exception as exc:
        print(f"  [warn] Claude prompt failed ({exc}) — using fallback")
        return f"{slot['default_prompt']}, {seasonal_brief}"


def _upload_image_to_wp(image_path: Path, wp_base_url: str, auth_header: str,
                         title: str) -> int:
    """Upload JPEG to WP media library. Returns new attachment ID."""
    url = f"{wp_base_url}/wp-json/wp/v2/media"
    img_bytes = image_path.read_bytes()
    boundary = "----SkinUploadBoundary9b2e1a"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{image_path.name}\"\r\nContent-Type: image/jpeg\r\n\r\n".encode()
        + img_bytes + b"\r\n"
        + f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{title}\r\n".encode()
        + f"--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": auth_header,
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["id"]


def run_skin_image_mode(args: argparse.Namespace) -> None:
    """Generate skin background images for a site using Jimeng + site context."""
    _load_site_env(args.site)

    # Load site image slots
    slots_file = _SITES_DIR / args.site / "image_slots.json"
    if not slots_file.exists():
        print(f"ERROR: {slots_file} not found — create image_slots.json for this site first",
              file=sys.stderr)
        sys.exit(1)
    slots_cfg = json.loads(slots_file.read_text(encoding="utf-8"))
    site_desc = slots_cfg["site_description"]
    all_slots = {s["slot_id"]: s for s in slots_cfg["slots"]}

    # Load skin
    skin_path = _SKIN_DIR / f"{args.skin}.md"
    if not skin_path.exists():
        skin_path = _SITES_DIR / args.site / "skins" / f"{args.skin}.md"
    if not skin_path.exists():
        print(f"ERROR: Skin '{args.skin}' not found", file=sys.stderr)
        sys.exit(1)
    skin_tokens = _parse_skin_file(skin_path)

    # Volc credentials (from tg_agent .env via jimeng module)
    volc_ak = get_volc_ak()
    volc_sk = get_volc_sk()
    if not args.dry_run and (not volc_ak or not volc_sk):
        print("ERROR: VOLC_ACCESS_KEY_ID / VOLC_SECRET_ACCESS_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Output dir
    out_dir = Path(args.state_dir) / "generated-images" / args.skin
    out_dir.mkdir(parents=True, exist_ok=True)

    # Select slots
    target_slots = [s for s in all_slots.values()
                    if args.slot is None or s["slot_id"] == args.slot]
    if not target_slots:
        print(f"ERROR: slot '{args.slot}' not in image_slots.json", file=sys.stderr)
        sys.exit(1)

    print(f"\nSite: {args.site}  Skin: {args.skin}  Slots: {[s['slot_id'] for s in target_slots]}")
    if args.dry_run:
        print("[ DRY-RUN — no Jimeng API calls ]\n")

    generated: list[dict] = []

    for slot in target_slots:
        slot_id = slot["slot_id"]
        seasonal_brief = skin_tokens.get(f"image_prompt_{slot_id}", "")
        if not seasonal_brief:
            print(f"  [warn] No image_prompt_{slot_id} in skin — using slot default")
            seasonal_brief = slot["default_prompt"]

        print(f"\n── {slot_id} ({slot['width']}×{slot['height']}px) ──")
        print(f"  Seasonal brief : {seasonal_brief}")

        prompt = _build_skin_prompt(site_desc, slot, seasonal_brief)
        print(f"  Jimeng prompt  : {prompt}")

        out_path = out_dir / f"{slot_id}.jpg"

        if args.dry_run:
            print(f"  [DRY-RUN] Would save → {out_path}")
            generated.append({"slot_id": slot_id, "old_id": slot["wp_media_id"],
                               "path": str(out_path), "new_id": None})
            continue

        # Generate via Jimeng (synchronous CVProcess)
        print("  Calling Jimeng T2I...")
        payload = {
            "req_key": JIMENG_REQ_KEY,
            "prompt": prompt,
            "width": slot["width"],
            "height": slot["height"],
        }
        body = json.dumps(payload, ensure_ascii=False).encode()
        params = {"Action": "CVProcess", "Version": "2022-08-31"}
        headers = _volc_sign(volc_ak, volc_sk, "POST", f"{VOLC_BASE}/", params, body)
        r = requests.post(f"{VOLC_BASE}/", params=params, headers=headers, data=body, timeout=120)
        r.raise_for_status()
        data = r.json()

        if data.get("code") != 10000 and data.get("status") != 10000:
            raise RuntimeError(f"Jimeng error: {data.get('message', str(data)[:200])}")

        data_obj = data.get("data") or {}
        b64_list = data_obj.get("binary_data_base64") or []
        img_url_list = data_obj.get("image_urls") or []

        if b64_list:
            img_bytes = base64.b64decode(b64_list[0])
        elif img_url_list:
            img_bytes = requests.get(img_url_list[0], timeout=60).content
        else:
            raise RuntimeError(f"No image data in Jimeng response: {str(data)[:300]}")

        out_path.write_bytes(img_bytes)
        print(f"  Saved ({len(img_bytes)//1024}KB) → {out_path}")

        new_id = None
        if args.upload:
            if not args.live:
                print(f"  [--upload without --live] Would upload to WP. Add --live to write.")
            else:
                wp_base = os.environ.get("WP_BASE_URL", "").rstrip("/")
                wp_user = os.environ.get("WP_USERNAME", "")
                wp_pass = os.environ.get("WP_APP_PASSWORD", "")
                auth = "Basic " + base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
                new_id = _upload_image_to_wp(out_path, wp_base, auth,
                                              f"{args.skin}-{slot_id}")
                print(f"  Uploaded → WP media ID: {new_id}")

        generated.append({"slot_id": slot_id, "old_id": slot["wp_media_id"],
                           "path": str(out_path), "new_id": new_id})

    # Print image_replacements — forward (apply skin) + reverse (rollback via default skin)
    print("\n" + "=" * 60)
    has_ids = any(g["new_id"] for g in generated)
    if has_ids:
        print(f"  1. Paste into [{args.skin}.md] (applies seasonal images):")
        print("=" * 60)
        print("image_replacements:")
        for g in generated:
            if g["new_id"]:
                print(f'  "{g["old_id"]}": "{g["new_id"]}"  # {g["slot_id"]}')

        print(f"\n  2. Paste into [newcastlehub-default.md] (ROLLBACK — restores originals):")
        print("=" * 60)
        print("image_replacements:")
        for g in generated:
            if g["new_id"]:
                print(f'  "{g["new_id"]}": "{g["old_id"]}"  # {g["slot_id"]} rollback')
        print("\n  After pasting both, test rollback:")
        print(f"  python scripts/apply_skin.py --site {args.site} --skin newcastlehub-default --dry-run")
    else:
        print("  Images saved locally:")
        print("=" * 60)
        for g in generated:
            print(f"  [{g['slot_id']}] {g['path']}")
        if not args.dry_run:
            print("\n  Re-run with --upload --live to upload to WP and get IDs.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate featured images via Jimeng T2I")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts, no API calls")
    # Skin image mode
    parser.add_argument("--site", default=None, help="Site ID for skin image mode (e.g. newcastlehub)")
    parser.add_argument("--skin", default=None, help="Skin name (e.g. newcastlehub-mothers-day)")
    parser.add_argument("--slot", default=None, help="Only process this slot ID (default: all)")
    parser.add_argument("--upload", action="store_true", help="Upload generated images to WP")
    parser.add_argument("--live", action="store_true", help="Required with --upload to actually write")
    parser.add_argument("--state-dir", default=".wp-ai-ops-state")
    # Sweetsworld legacy mode
    parser.add_argument("--ids", help="Comma-separated page IDs to process (overrides defaults)")
    parser.add_argument("--type", choices=["pages", "posts", "all"], default="all")
    parser.add_argument("--force", action="store_true", help="Regenerate even if featured_media already set")
    args = parser.parse_args()

    # Route to skin image mode if --skin provided
    if args.skin:
        if not args.site:
            parser.error("--skin requires --site")
        run_skin_image_mode(args)
        return

    env = _load_env()
    wp_user = _get(env, "SWEETSWORLD_USERNAME")
    wp_pass = _get(env, "SWEETSWORLD_APP_PASSWORD")
    volc_ak = _get(env, "VOLC_ACCESS_KEY_ID", "VOLCENGINE_ACCESS_KEY_ID")
    volc_sk = _get(env, "VOLC_SECRET_ACCESS_KEY", "VOLCENGINE_SECRET_ACCESS_KEY")

    if not wp_user or not wp_pass:
        print("ERROR: SWEETSWORLD_USERNAME / SWEETSWORLD_APP_PASSWORD not set")
        sys.exit(1)
    # Prefer jimeng module's own env resolution (reads tg_agent/.env automatically)
    if not volc_ak:
        volc_ak = get_volc_ak()
    if not volc_sk:
        volc_sk = get_volc_sk()

    if not args.dry_run and (not volc_ak or not volc_sk):
        print("ERROR: VOLC_ACCESS_KEY_ID / VOLC_SECRET_ACCESS_KEY not set")
        sys.exit(1)

    # Build work list: [(resource_type, id), ...]
    if args.ids:
        ids = [int(i.strip()) for i in args.ids.split(",")]
        # Auto-detect resource type: try pages first, fall back to posts
        work = []
        for i in ids:
            try:
                wp_get_resource("pages", i, wp_user, wp_pass)
                work.append(("pages", i))
            except Exception:
                work.append(("posts", i))
    else:
        work = []
        if args.type in ("pages", "all"):
            work += [("pages", i) for i in SEO_PAGE_IDS]
        if args.type in ("posts", "all"):
            work += [("posts", i) for i in POST_IDS]

    print(f"Processing {len(work)} items (dry_run={args.dry_run})\n")

    ok = skip = fail = 0
    for resource_type, resource_id in work:
        try:
            item = wp_get_resource(resource_type, resource_id, wp_user, wp_pass)
        except Exception as e:
            print(f"  [{resource_id}] FETCH ERROR: {e}")
            fail += 1
            continue

        slug = item.get("slug", str(resource_id))
        title = (item.get("title") or {}).get("rendered") or slug
        existing_media = item.get("featured_media", 0)

        if existing_media and not args.force:
            print(f"  [{resource_id}] SKIP /{slug}/ — already has featured_media={existing_media}")
            skip += 1
            continue

        prompt = _build_image_prompt(title, slug)

        if args.dry_run:
            print(f"  [{resource_id}] WOULD GENERATE /{slug}/")
            print(f"    prompt: {prompt[:120]}...")
            continue

        print(f"  [{resource_id}] Generating image for /{slug}/ ...")
        try:
            img_bytes = generate_image(prompt, volc_ak, volc_sk)
            filename = f"{slug}-featured.png"
            media_id = wp_upload_image(img_bytes, filename, wp_user, wp_pass)
            wp_set_featured_media(resource_type, resource_id, media_id, wp_user, wp_pass)
            print(f"    OK — media_id={media_id} assigned ✅")
            ok += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            fail += 1

        time.sleep(1)

    print(f"\nDone. Generated: {ok}, Skipped: {skip}, Failed: {fail}")


if __name__ == "__main__":
    main()
