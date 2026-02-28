from __future__ import annotations

import base64
import mimetypes
import json
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlencode

from .exceptions import WPClientError


RESOURCE_PATHS = {
    "post": "posts",
    "page": "pages",
    "category": "categories",
    "tag": "tags",
    "media": "media",
    "ux-blocks": "ux-blocks",
    "menu-items": "menu-items",
    "template-parts": "template-parts",
}


def _resource_path(resource_type: str) -> str:
    return RESOURCE_PATHS.get(resource_type, resource_type)


class WPClient:
    def __init__(self, wp_api_base: str, username: str, app_password: str, timeout: int = 20) -> None:
        self.base = wp_api_base.rstrip("/")
        self.timeout = timeout
        token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")
        self.auth_header = f"Basic {token}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_payload: dict | None = None,
        raw_body: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.base}/{path.lstrip('/')}"
        if params:
            q = urlencode(params)
            url = f"{url}?{q}"

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                headers = {
                    "Authorization": self.auth_header,
                    "Accept": "application/json",
                }
                if json_payload is not None:
                    headers["Content-Type"] = "application/json; charset=utf-8"
                if extra_headers:
                    headers.update(extra_headers)
                body: bytes | None = None
                if json_payload is not None:
                    body = json.dumps(json_payload, ensure_ascii=False).encode("utf-8")
                elif raw_body is not None:
                    body = raw_body

                req = urlrequest.Request(url=url, data=body, headers=headers, method=method.upper())
                with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                    status = int(getattr(resp, "status", 0) or 0)
                    body_bytes = resp.read() or b""
                body_text = body_bytes.decode("utf-8", errors="replace")

                if status >= 400 or status == 0:
                    raise WPClientError(f"{method} {url} failed: {status} {body_text[:500]}")
                if not body_text:
                    return None
                return json.loads(body_text)
            except urlerror.HTTPError as exc:
                err_body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
                last_error = WPClientError(f"{method} {url} failed: {exc.code} {err_body[:500]}")
                if attempt < 2:
                    time.sleep(1.2**attempt)
                    continue
                raise last_error from exc
            except urlerror.URLError as exc:
                last_error = WPClientError(f"{method} {url} failed: {exc.reason}")
                if attempt < 2:
                    time.sleep(1.2**attempt)
                    continue
                raise last_error from exc
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1.2**attempt)
                    continue
                raise WPClientError(f"{method} {url} failed: {exc}") from exc

        raise WPClientError(f"{method} {url} failed: {last_error}")

    def list_resources(self, resource_type: str, *, params: dict | None = None) -> list[dict]:
        resource = _resource_path(resource_type)
        q = dict(params or {})
        q.setdefault("context", "edit")
        try:
            rows = self._request("GET", resource, params=q)
        except WPClientError as exc:
            # Some sites block context=edit via REST although authenticated requests are valid.
            # Fallback to view context so target resolution can still proceed.
            if "rest_forbidden_context" in str(exc) and q.get("context") == "edit":
                q["context"] = "view"
                rows = self._request("GET", resource, params=q)
            else:
                raise
        return rows if isinstance(rows, list) else []

    def get_resource(self, resource_type: str, resource_id: int, *, params: dict | None = None) -> dict:
        resource = _resource_path(resource_type)
        q = dict(params or {})
        q.setdefault("context", "edit")
        try:
            row = self._request("GET", f"{resource}/{resource_id}", params=q)
        except WPClientError as exc:
            if "rest_forbidden_context" in str(exc) and q.get("context") == "edit":
                # Preferred fallback: POST with empty payload often returns content.raw/meta on locked sites.
                try:
                    row = self._request("POST", f"{resource}/{resource_id}", json_payload={})
                except WPClientError:
                    # Secondary fallback: at least get public payload so read-only/metadata tasks can continue.
                    q["context"] = "view"
                    row = self._request("GET", f"{resource}/{resource_id}", params=q)
            else:
                raise
        return row if isinstance(row, dict) else {}

    def update_resource(self, resource_type: str, resource_id: int, payload: dict) -> dict:
        resource = _resource_path(resource_type)
        row = self._request("POST", f"{resource}/{resource_id}", json_payload=payload)
        return row if isinstance(row, dict) else {}

    def create_resource(self, resource_type: str, payload: dict) -> dict:
        resource = _resource_path(resource_type)
        row = self._request("POST", resource, json_payload=payload)
        return row if isinstance(row, dict) else {}

    def get_settings(self) -> dict:
        row = self._request("GET", "settings", params={"context": "edit"})
        return row if isinstance(row, dict) else {}

    def update_settings(self, payload: dict) -> dict:
        row = self._request("POST", "settings", json_payload=payload)
        return row if isinstance(row, dict) else {}

    def upload_media(self, file_path: str, *, title: str | None = None, alt_text: str | None = None) -> dict:
        fp = Path(file_path)
        if not fp.exists() or not fp.is_file():
            raise WPClientError(f"Media file not found: {file_path}")
        binary = fp.read_bytes()
        content_type = mimetypes.guess_type(fp.name)[0] or "application/octet-stream"
        media = self._request(
            "POST",
            RESOURCE_PATHS["media"],
            raw_body=binary,
            extra_headers={
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{fp.name}"',
            },
        )
        if not isinstance(media, dict):
            raise WPClientError("Media upload failed: empty response")

        media_id = media.get("id")
        if media_id and (title or alt_text):
            patch: dict[str, str] = {}
            if title:
                patch["title"] = title
            if alt_text:
                patch["alt_text"] = alt_text
            media = self.update_resource("media", int(media_id), patch)
        return media
