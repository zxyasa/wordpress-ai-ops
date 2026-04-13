#!/usr/bin/env python3
"""
Universal snapshot utility for WordPress content operations.

Usage (as a library):
    from wp_snapshot import Snapshotter
    snap = Snapshotter("bulk_topic_links")
    snap.save(pid, title, content)          # before writing
    snap.restore(pid, username, password)   # rollback one post
    snap.restore_all(username, password)    # rollback all

Usage (as CLI):
    python scripts/wp_snapshot.py list [script_name]
    python scripts/wp_snapshot.py restore --script bulk_topic_links --post-id 71043
    python scripts/wp_snapshot.py restore-all --script bulk_topic_links
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path

SITE_BASE = "https://sweetsworld.com.au"
SNAPSHOTS_ROOT = Path(__file__).parent.parent / "snapshots"


class Snapshotter:
    def __init__(self, script_name: str):
        self.script_name = script_name
        self.snap_dir = SNAPSHOTS_ROOT / script_name
        self.snap_dir.mkdir(parents=True, exist_ok=True)

    def save(self, resource_type: str, rid: int, title: str, content: str) -> Path:
        """
        Save a snapshot before modifying a resource.
        resource_type: "post", "page", "product", "category"
        """
        snap = {
            "script": self.script_name,
            "resource_type": resource_type,
            "id": rid,
            "title": title,
            "content": content,
            "saved_at": datetime.utcnow().isoformat(),
        }
        path = self.snap_dir / f"{resource_type}_{rid}.json"
        path.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
        return path

    def list_snapshots(self) -> list[dict]:
        return [json.loads(p.read_text()) for p in sorted(self.snap_dir.glob("*.json"))]

    def restore_one(self, resource_type: str, rid: int, username: str, password: str) -> bool:
        path = self.snap_dir / f"{resource_type}_{rid}.json"
        if not path.exists():
            print(f"  No snapshot: {path.name}")
            return False
        snap = json.loads(path.read_text())
        return _write_to_wp(resource_type, rid, snap["content"], username, password)

    def restore_all(self, username: str, password: str) -> None:
        snaps = self.list_snapshots()
        if not snaps:
            print(f"No snapshots for '{self.script_name}'")
            return
        for snap in snaps:
            ok = _write_to_wp(snap["resource_type"], snap["id"], snap["content"], username, password)
            status = "✅" if ok else "❌"
            print(f"  {status} {snap['resource_type']} {snap['id']}: {snap['title'][:50]}")
            time.sleep(0.3)


def _auth_headers(username: str, password: str) -> dict:
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def _write_to_wp(resource_type: str, rid: int, content: str, username: str, password: str) -> bool:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    type_map = {
        "post": "posts",
        "page": "pages",
        "product": "products",  # WC — needs different auth
    }
    if resource_type == "category":
        url = f"{SITE_BASE}/wp-json/wc/v3/products/categories/{rid}"
        body = json.dumps({"description": content}).encode()
    else:
        endpoint = type_map.get(resource_type, "posts")
        url = f"{SITE_BASE}/wp-json/wp/v2/{endpoint}/{rid}?context=edit"
        body = json.dumps({"content": content}).encode()

    headers = _auth_headers(username, password)
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            return "id" in result
    except HTTPError as e:
        print(f"    HTTP {e.code}: {e.read()[:200]}")
        return False
    except Exception as e:
        print(f"    Error: {e}")
        return False


def _load_env() -> dict:
    env_file = Path(__file__).parent.parent / ".env"
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="WordPress snapshot manager")
    sub = parser.add_subparsers(dest="cmd")

    # list
    p_list = sub.add_parser("list", help="List snapshots")
    p_list.add_argument("script", nargs="?", help="Script name (omit to list all)")

    # restore
    p_restore = sub.add_parser("restore", help="Restore one post from snapshot")
    p_restore.add_argument("--script", required=True)
    p_restore.add_argument("--post-id", type=int, required=True)
    p_restore.add_argument("--type", default="post", choices=["post", "page", "product", "category"])

    # restore-all
    p_all = sub.add_parser("restore-all", help="Restore all snapshots for a script")
    p_all.add_argument("--script", required=True)

    args = parser.parse_args()

    if args.cmd == "list":
        if args.script:
            snap = Snapshotter(args.script)
            snaps = snap.list_snapshots()
            print(f"{len(snaps)} snapshots for '{args.script}':")
            for s in snaps:
                print(f"  {s['resource_type']} {s['id']}: {s['title'][:55]} (saved {s['saved_at'][:16]})")
        else:
            if not SNAPSHOTS_ROOT.exists():
                print("No snapshots yet.")
                return
            for d in sorted(SNAPSHOTS_ROOT.iterdir()):
                if d.is_dir():
                    count = len(list(d.glob("*.json")))
                    print(f"  {d.name}: {count} snapshots")

    elif args.cmd == "restore":
        env = _load_env()
        snap = Snapshotter(args.script)
        ok = snap.restore_one(args.type, args.post_id, env.get("SWEETSWORLD_USERNAME", ""), env.get("SWEETSWORLD_APP_PASSWORD", ""))
        print("restored ✅" if ok else "FAILED ❌")

    elif args.cmd == "restore-all":
        env = _load_env()
        snap = Snapshotter(args.script)
        snap.restore_all(env.get("SWEETSWORLD_USERNAME", ""), env.get("SWEETSWORLD_APP_PASSWORD", ""))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
