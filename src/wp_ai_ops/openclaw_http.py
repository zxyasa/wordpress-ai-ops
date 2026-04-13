from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class OpenClawConfig:
    base_url: str
    api_key: str | None = None


def load_openclaw_config() -> OpenClawConfig:
    base_url = os.getenv("OPENCLAW_BASE_URL", "").strip()
    if not base_url:
        raise ValueError("Missing OPENCLAW_BASE_URL")
    api_key = os.getenv("OPENCLAW_API_KEY")
    if api_key:
        api_key = api_key.strip()
    return OpenClawConfig(base_url=base_url.rstrip("/"), api_key=api_key)


def _curl_json(method: str, url: str, *, api_key: str | None, payload: dict | None = None, timeout_s: int = 30) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            out = resp.read().decode("utf-8").strip()
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(body or f"OpenClaw request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenClaw request failed: {exc.reason}") from exc

    if not out:
        return {}
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from OpenClaw: {out[:400]}") from exc

    if not isinstance(data, dict):
        return {"data": data}
    return data


def submit_job(job: dict, *, base_url: str, api_key: str | None) -> dict:
    # Expected contract (default): POST /jobs -> {id|job_id,...}
    return _curl_json("POST", f"{base_url}/jobs", api_key=api_key, payload=job)


def get_job(job_id: str, *, base_url: str, api_key: str | None) -> dict:
    return _curl_json("GET", f"{base_url}/jobs/{job_id}", api_key=api_key)


def dispatch_job_file(job_path: Path, *, state_dir: Path, timeout_s: int = 30) -> dict:
    cfg = load_openclaw_config()
    job = json.loads(job_path.read_text(encoding="utf-8"))
    resp = submit_job(job, base_url=cfg.base_url, api_key=cfg.api_key)

    remote_id = resp.get("job_id") or resp.get("id") or resp.get("data", {}).get("job_id") or resp.get("data", {}).get("id")
    summary = {
        "status": "submitted" if remote_id else "submitted_unknown_id",
        "job_file": str(job_path),
        "remote_job_id": remote_id,
        "response": resp,
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "openclaw_dispatch.jsonl").open("a", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False) + "\n")
    return summary


def poll_job_status(job_id: str, *, state_dir: Path, timeout_s: int = 30) -> dict:
    cfg = load_openclaw_config()
    resp = get_job(job_id, base_url=cfg.base_url, api_key=cfg.api_key)
    summary = {
        "status": "ok",
        "remote_job_id": job_id,
        "response": resp,
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "openclaw_poll.jsonl").open("a", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False) + "\n")
    return summary
