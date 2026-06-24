"""Collect search results and article text from the Wikipedia/MediaWiki API.

Example:
    python scripts/runnable_workflows/01_api_wikipedia.py --query "digital services act" --pages 3
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import polite_get, provenance, write_csv, write_json, write_jsonl


API_URL = "https://en.wikipedia.org/w/api.php"


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list into same-sized chunks, keeping the final shorter chunk."""
    return [items[start : start + size] for start in range(0, len(items), size)]


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
                    "search_rank": len(rows) + 1,
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


def collect_article_extracts(
    search_rows: list[dict],
    *,
    extract_chars: int,
    batch_size: int = 1,
) -> tuple[list[dict], list[dict]]:
    """Retrieve page-level article text for search results via the API.

    This deliberately does not use BeautifulSoup or HTML scraping. Day 1 stays
    inside the API workflow: first discover pages with list=search, then retrieve
    text and page URLs with prop=info|extracts.
    """

    # pageid is the bridge between the search-result API response and the
    # article-content API response. We remove blanks and duplicates so the same
    # page is not requested multiple times.
    pageids = []
    seen_pageids = set()
    for row in search_rows:
        pageid = row.get("pageid")
        if pageid and pageid not in seen_pageids:
            pageids.append(pageid)
            seen_pageids.add(pageid)

    article_rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []

    for batch_number, pageid_batch in enumerate(chunked(pageids, batch_size), start=1):
        params = {
            "action": "query",
            # prop="info|extracts" asks for page-level metadata and text extracts.
            # This is a different API task from list="search": here we already
            # know which pages we want because the search step gave us pageids.
            "prop": "info|extracts",
            # pageids is written as a pipe-separated list because MediaWiki uses
            # that syntax. For whole-article extracts, this script uses one page
            # per request because the extracts module may otherwise return text
            # only for the first page in a batch.
            "pageids": "|".join(str(pageid) for pageid in pageid_batch),
            # inprop="url" adds fullurl, which is the human-facing article URL.
            "inprop": "url",
            # explaintext=1 returns plain text instead of HTML. This keeps the
            # workflow API-based and avoids teaching HTML parsing before Day 2.
            "explaintext": 1,
            # redirects=1 follows redirects so a search result that points through
            # a redirect can still return the target page content.
            "redirects": 1,
            "format": "json",
            "formatversion": 2,
        }

        # extract_chars is a methodological limit on how much article text to
        # store. A low value is useful for class demos; a real project should
        # justify this choice or set --extract-chars 0 to request full extracts.
        if extract_chars > 0:
            params["exchars"] = extract_chars

        response = polite_get(API_URL, params=params)
        payload = response.json()

        raw_pages.append(
            {
                "request_type": "article_extracts",
                "batch_number": batch_number,
                "pageids": pageid_batch,
                "request_url": response.url,
                "status_code": response.status_code,
                "payload": payload,
            }
        )

        for page in payload.get("query", {}).get("pages", []):
            article_rows.append(
                {
                    "pageid": page.get("pageid"),
                    "article_title": page.get("title"),
                    "article_url": page.get("fullurl"),
                    "article_extract": page.get("extract"),
                    "article_extract_chars_requested": extract_chars,
                }
            )

    return article_rows, raw_pages


def merge_search_and_articles(
    search_rows: list[dict],
    article_rows: list[dict],
) -> list[dict]:
    """Add article URL and article text fields to each search-result row."""

    # The page-level API response may come back in a different order from the
    # search results, so we merge by pageid rather than position.
    articles_by_pageid = {row.get("pageid"): row for row in article_rows}

    merged_rows = []
    for search_row in search_rows:
        article_row = articles_by_pageid.get(search_row.get("pageid"), {})
        merged_rows.append({**search_row, **article_row})

    return merged_rows


def main() -> None:
    # argparse makes the script reproducible from the terminal. The command used
    # to run the script becomes part of the method: query, pages, page size, and
    # output directory are all explicit rather than hidden inside the code.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument(
        "--extract-chars",
        type=int,
        default=2500,
        help="Maximum plain-text article characters to request per page; use 0 for full extracts.",
    )
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    stem = args.query.lower().replace(" ", "_")[:60]
    outdir = Path(args.outdir)
    search_rows, raw_search_pages = collect_search(args.query, args.pages, args.page_size)
    article_rows, raw_article_pages = collect_article_extracts(
        search_rows,
        extract_chars=args.extract_chars,
    )
    rows = merge_search_and_articles(search_rows, article_rows)

    # A simple but durable directory convention:
    # raw/ contains source-shaped data,
    # processed/ contains analysis-shaped data,
    # reports/ contains provenance and audit information.
    raw_path = outdir / "raw" / f"wikipedia_{stem}.jsonl"
    csv_path = outdir / "processed" / f"wikipedia_{stem}.csv"
    report_path = outdir / "reports" / f"wikipedia_{stem}_provenance.json"

    write_jsonl(
        raw_path,
        [
            *(
                {"request_type": "search", **raw_page}
                for raw_page in raw_search_pages
            ),
            *raw_article_pages,
        ],
    )
    write_csv(csv_path, rows)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters=vars(args),
            outputs=[raw_path, csv_path],
            notes=[
                "Raw JSONL preserves both search-result and article-extract API payloads.",
                "Processed CSV merges search-result metadata with article URLs and API text extracts.",
                "Article content is retrieved through the MediaWiki API, not through HTML scraping.",
                "Use the provenance file to reconstruct how the dataset was made.",
            ],
        ),
    )

    print(f"Collected {len(search_rows)} search-result rows.")
    print(f"Retrieved article extracts for {len(article_rows)} unique pages.")
    print(f"Raw: {raw_path}")
    print(f"Processed: {csv_path}")
    print(f"Provenance: {report_path}")


if __name__ == "__main__":
    main()
