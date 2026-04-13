#!/usr/bin/env python3
"""
Restore a post from its bulk_topic_links snapshot.

Usage:
  python scripts/restore_from_snapshot.py --post-id 71043
  python scripts/restore_from_snapshot.py --all        # restore all snapshots
  python scripts/restore_from_snapshot.py --list       # list available snapshots
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

SITE_BASE = "https://sweetsworld.com.au"
SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "bulk_topic_links"


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def restore_post(pid: int, content: str, username: str, password: str) -> bool:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    url = f"{SITE_BASE}/wp-json/wp/v2/posts/{pid}?context=edit"
    headers = _auth_headers(username, password)
    body = json.dumps({"content": content}).encode()
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            return "id" in result
    except HTTPError as e:
        print(f"  HTTP {e.code}: {e.read()[:200]}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-id", type=int, help="Restore specific post ID")
    parser.add_argument("--all", action="store_true", help="Restore all snapshots")
    parser.add_argument("--list", action="store_true", help="List available snapshots")
    args = parser.parse_args()

    if not SNAPSHOTS_DIR.exists():
        print("No snapshots directory found.")
        sys.exit(0)

    snapshots = sorted(SNAPSHOTS_DIR.glob("*.json"))

    if args.list:
        print(f"{len(snapshots)} snapshots available:")
        for s in snapshots:
            data = json.loads(s.read_text())
            print(f"  {data['id']}: {data['title'][:60]}")
        return

    env_file = Path(__file__).parent.parent / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()

    username = env.get("SWEETSWORLD_USERNAME", "")
    password = env.get("SWEETSWORLD_APP_PASSWORD", "")

    if args.post_id:
        snap_file = SNAPSHOTS_DIR / f"post_{args.post_id}.json"
        if not snap_file.exists():
            print(f"No snapshot found for post {args.post_id}")
            sys.exit(1)
        data = json.loads(snap_file.read_text())
        ok = restore_post(args.post_id, data["content"], username, password)
        print(f"{args.post_id} ({data['title'][:50]}): {'restored ✅' if ok else 'FAILED ❌'}")

    elif args.all:
        for s in snapshots:
            data = json.loads(s.read_text())
            pid = data["id"]
            ok = restore_post(pid, data["content"], username, password)
            print(f"{pid} ({data['title'][:50]}): {'restored ✅' if ok else 'FAILED ❌'}")
            time.sleep(0.5)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
