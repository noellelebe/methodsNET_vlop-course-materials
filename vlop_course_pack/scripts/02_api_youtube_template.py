"""YouTube Data API search template.

Requires an API key:
    export YOUTUBE_API_KEY="..."
    python scripts/02_api_youtube_template.py --query "digital services act"

This script is intentionally conservative. It demonstrates authentication,
pagination, and provenance without encouraging large-scale collection.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import polite_get, provenance, require_env, write_csv, write_json, write_jsonl


SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def collect(query: str, max_pages: int, page_size: int, api_key: str) -> tuple[list[dict], list[dict]]:
    rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []
    page_token: str | None = None

    for page_number in range(1, max_pages + 1):
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(page_size, 50),
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        response = polite_get(SEARCH_URL, params=params, delay_seconds=1.5)
        payload = response.json()
        raw_pages.append(
            {
                "page_number": page_number,
                "status_code": response.status_code,
                "payload": payload,
            }
        )

        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")
            rows.append(
                {
                    "query": query,
                    "page_number": page_number,
                    "video_id": video_id,
                    "title": snippet.get("title"),
                    "channel_id": snippet.get("channelId"),
                    "channel_title": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "description": snippet.get("description"),
                }
            )

        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return rows, raw_pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    api_key = require_env("YOUTUBE_API_KEY")
    stem = args.query.lower().replace(" ", "_")[:60]
    outdir = Path(args.outdir)
    rows, raw_pages = collect(args.query, args.pages, args.page_size, api_key)

    raw_path = outdir / "raw" / f"youtube_{stem}.jsonl"
    csv_path = outdir / "processed" / f"youtube_{stem}.csv"
    report_path = outdir / "reports" / f"youtube_{stem}_provenance.json"

    write_jsonl(raw_path, raw_pages)
    write_csv(csv_path, rows)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "api_key": "stored in YOUTUBE_API_KEY"},
            outputs=[raw_path, csv_path],
            notes=[
                "Do not commit API keys.",
                "Check YouTube API terms, quota use, and redistribution limits.",
            ],
        ),
    )

    print(f"Collected {len(rows)} rows.")
    print(f"Processed: {csv_path}")


if __name__ == "__main__":
    main()
