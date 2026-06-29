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
    # rows will become the processed CSV: one flattened row per video result.
    rows: list[dict[str, Any]] = []
    # raw_pages preserves the source-shaped API responses for reproducibility.
    raw_pages: list[dict[str, Any]] = []
    # page_token starts as None because the first API request has no previous
    # page to continue from.
    page_token: str | None = None

    for page_number in range(1, max_pages + 1):
        # params are the query-string parameters sent to the YouTube Data API.
        params = {
            # part=snippet requests basic metadata such as title, channel, and
            # description. Other parts require different quota/account choices.
            "part": "snippet",
            # q is the substantive search string.
            "q": query,
            # type=video excludes channels/playlists from this teaching example.
            "type": "video",
            # YouTube caps maxResults at 50. min(...) keeps user input inside
            # the documented maximum.
            "maxResults": min(page_size, 50),
            # key authenticates the request. It comes from the environment, not
            # from hard-coded script text.
            "key": api_key,
        }
        if page_token:
            # pageToken asks YouTube for the next page of results.
            params["pageToken"] = page_token

        # polite_get sends the request with a small delay and raises visible
        # errors for failed HTTP status codes.
        response = polite_get(SEARCH_URL, params=params, delay_seconds=1.5)
        # .json() parses the JSON response into Python dictionaries/lists.
        payload = response.json()
        raw_pages.append(
            {
                # page_number is added by us so we know which request produced
                # each raw response.
                "page_number": page_number,
                "status_code": response.status_code,
                "payload": payload,
            }
        )

        for item in payload.get("items", []):
            # snippet is a nested dictionary containing the visible metadata.
            snippet = item.get("snippet", {})
            # videoId is nested under id. .get() avoids crashing if an item has
            # an unexpected shape.
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

        # nextPageToken is YouTube's pagination token. If it is absent, there is
        # no next page under this query.
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return rows, raw_pages


def main() -> None:
    # argparse turns command-line flags into the args object below.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    # require_env stops with a readable error if YOUTUBE_API_KEY is not set.
    api_key = require_env("YOUTUBE_API_KEY")
    # stem creates a short filename-safe label from the query.
    stem = args.query.lower().replace(" ", "_")[:60]
    outdir = Path(args.outdir)
    # collect() returns both processed rows and raw API payloads.
    rows, raw_pages = collect(args.query, args.pages, args.page_size, api_key)

    # Paths follow the course convention: raw, processed, reports.
    raw_path = outdir / "raw" / f"youtube_{stem}.jsonl"
    csv_path = outdir / "processed" / f"youtube_{stem}.csv"
    report_path = outdir / "reports" / f"youtube_{stem}_provenance.json"

    # JSONL is useful for raw pages because it stores one JSON object per line.
    write_jsonl(raw_path, raw_pages)
    # CSV is useful for the flattened result table.
    write_csv(csv_path, rows)
    write_json(
        report_path,
        provenance(
            # Store parameters, but never store the actual API key.
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


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# First set your API key in the terminal:
#
#     export YOUTUBE_API_KEY="paste-your-key-here"
#
# Then run from the repository root:
#
#     python scripts/runnable_workflows/02_api_youtube_template.py \
#       --query "digital services act" \
#       --pages 1 \
#       --page-size 10 \
#       --outdir data
#
# What each part means:
#
# - export YOUTUBE_API_KEY="..."
#   Stores the YouTube Data API key in the terminal environment. The key should
#   not be hard-coded into the script.
#
# - --query
#   The search string sent to the YouTube Data API.
#
# - --pages
#   The number of result pages/batches to request.
#
# - --page-size
#   The number of results requested per API call.
#
# - --outdir
#   The folder where raw JSON, processed CSV, and provenance files are saved.
