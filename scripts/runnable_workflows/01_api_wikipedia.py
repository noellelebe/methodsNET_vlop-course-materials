"""Collect search results from the Wikipedia/MediaWiki API.

Example:
    python scripts/01_api_wikipedia.py --query "digital services act" --pages 3
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import polite_get, provenance, write_csv, write_json, write_jsonl


API_URL = "https://en.wikipedia.org/w/api.php"


def collect_search(query: str, pages: int, page_size: int) -> tuple[list[dict], list[dict]]:
    # We keep two outputs on purpose:
    # 1. rows: a flattened table that students can inspect in a spreadsheet.
    # 2. raw_pages: the original API responses plus request metadata.
    #
    # This separation is central to reproducible API research. The processed table
    # is convenient for analysis, but the raw response lets us later check whether
    # a cleaning step dropped records, misunderstood a field, or hid an API error.
    rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []

    # MediaWiki uses a continuation object for pagination. Some APIs call this a
    # cursor, next token, offset, or page token. The important teaching point is
    # that "get more results" is almost never automatic: the researcher must
    # explicitly follow the API's pagination mechanism.
    continuation: dict[str, Any] = {}

    for page_number in range(1, pages + 1):
        # Query parameters are the research design in miniature. Changing
        # srsearch, srlimit, or filters changes the population of retrievable
        # records, so we save the request URL below as part of provenance.
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": page_size,
            "format": "json",
            "formatversion": 2,
            **continuation,
        }

        # polite_get adds a user agent, waits briefly, and raises an error for
        # failed HTTP statuses. In real projects, you would also log rate-limit
        # headers and retry behavior.
        response = polite_get(API_URL, params=params)
        payload = response.json()

        # Store the full payload, not only the fields we currently care about.
        # Future analysis may need a field we did not include in the flat CSV.
        raw_pages.append(
            {
                "page_number": page_number,
                "request_url": response.url,
                "status_code": response.status_code,
                "payload": payload,
            }
        )

        for item in payload.get("query", {}).get("search", []):
            # This is the lossy transformation from nested JSON to tabular data.
            # We use .get() so the script records missing fields as blanks rather
            # than crashing. Missingness is later something to audit, not ignore.
            rows.append(
                {
                    "query": query,
                    "page_number": page_number,
                    "pageid": item.get("pageid"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "timestamp": item.get("timestamp"),
                    "wordcount": item.get("wordcount"),
                }
            )

        # If the API returns no continuation token, we have reached the last page
        # of available results for this query.
        continuation = payload.get("continue", {})
        if not continuation:
            break

    return rows, raw_pages


def main() -> None:
    # argparse makes the script reproducible from the terminal. The command used
    # to run the script becomes part of the method: query, pages, page size, and
    # output directory are all explicit rather than hidden inside the code.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    stem = args.query.lower().replace(" ", "_")[:60]
    outdir = Path(args.outdir)
    rows, raw_pages = collect_search(args.query, args.pages, args.page_size)

    # A simple but durable directory convention:
    # raw/ contains source-shaped data,
    # processed/ contains analysis-shaped data,
    # reports/ contains provenance and audit information.
    raw_path = outdir / "raw" / f"wikipedia_{stem}.jsonl"
    csv_path = outdir / "processed" / f"wikipedia_{stem}.csv"
    report_path = outdir / "reports" / f"wikipedia_{stem}_provenance.json"

    write_jsonl(raw_path, raw_pages)
    write_csv(csv_path, rows)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters=vars(args),
            outputs=[raw_path, csv_path],
            notes=[
                "Raw JSONL preserves request URLs and full API payloads.",
                "Processed CSV flattens search results for classroom analysis.",
                "Use the provenance file to reconstruct how the dataset was made.",
            ],
        ),
    )

    print(f"Collected {len(rows)} rows.")
    print(f"Raw: {raw_path}")
    print(f"Processed: {csv_path}")
    print(f"Provenance: {report_path}")


if __name__ == "__main__":
    main()
