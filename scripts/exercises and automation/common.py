"""Shared helpers for the VLOP course scripts."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, TYPE_CHECKING
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

if TYPE_CHECKING:
    import requests


DEFAULT_USER_AGENT = (
    "methodsNET-VLOP-course/1.0 "
    "(educational research script; contact instructor before reuse)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: str | Path, data: Any) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provenance(
    *,
    script: str,
    parameters: dict[str, Any],
    outputs: list[str | Path],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    output_info = []
    for output in outputs:
        p = Path(output)
        if p.exists() and p.is_file():
            output_info.append(
                {
                    "path": str(p),
                    "bytes": p.stat().st_size,
                    "sha256": file_sha256(p),
                }
            )
        else:
            output_info.append({"path": str(p), "exists": p.exists()})
    return {
        "created_at_utc": utc_now(),
        "script": script,
        "parameters": parameters,
        "outputs": output_info,
        "notes": notes or [],
    }


def polite_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    delay_seconds: float = 1.0,
) -> requests.Response:
    import requests

    merged_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        merged_headers.update(headers)
    time.sleep(max(delay_seconds, 0))
    response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
    response.raise_for_status()
    return response


def robots_allowed(url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool | None:
    """Return True/False if robots.txt can be checked, None if unavailable."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        return None


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value
