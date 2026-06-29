"""Collect public repository metadata from the GitHub REST API.

Example:
    python scripts/runnable_workflows/02_api_github.py --query "digital services act" --pages 1

Authentication:
    This script can run without a token for small classroom demos that use only
    public data. GitHub's unauthenticated rate limit is much lower, so for more
    repeated testing set a token before running:

        export GITHUB_TOKEN="paste-your-token-here"

    The token is read from the environment and is never written into output
    files.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from common import polite_get, provenance, write_csv, write_json, write_jsonl


SEARCH_REPOSITORIES_URL = "https://api.github.com/search/repositories"
API_BASE_URL = "https://api.github.com"


def github_headers(token: str | None = None) -> dict[str, str]:
    """Return GitHub REST API headers.

    GitHub asks REST API clients to send an Accept header. The Authorization
    header is optional for public data, but useful because authenticated requests
    have a higher rate limit. We never hard-code the token in the script.
    """

    headers = {
        # Accept asks for GitHub's REST API JSON format.
        "Accept": "application/vnd.github+json",
        # This pins the documented API version so response behavior is less
        # likely to change silently over time.
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        # The token comes from the environment, not from a file or command-line
        # argument, so it is less likely to be accidentally committed.
        headers["Authorization"] = f"Bearer {token}"
    return headers


def collect_repository_search(
    query: str,
    pages: int,
    page_size: int,
    *,
    sort: str | None = None,
    order: str = "desc",
    token: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Collect public repository search results from GitHub.

    This is the GitHub equivalent of the Wikipedia search step:
    - the endpoint is resource-specific: /search/repositories;
    - q is the search query;
    - per_page is the page size;
    - page is the page number.
    """

    rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []

    for page_number in range(1, pages + 1):
        # GitHub's search API uses a classic REST-ish pagination pattern:
        # page=1, page=2, etc. This contrasts with MediaWiki's continuation
        # object and is useful for teaching that pagination differs by API.
        params: dict[str, Any] = {
            "q": query,
            "per_page": page_size,
            "page": page_number,
            "order": order,
        }
        if sort:
            params["sort"] = sort

        response = polite_get(
            SEARCH_REPOSITORIES_URL,
            params=params,
            headers=github_headers(token),
        )
        # Parse the JSON response into Python dictionaries/lists so we can access
        # keys such as "items" and "total_count".
        payload = response.json()

        # Rate-limit headers are methodologically useful: they show how much
        # request budget remains and when it resets. This is especially visible
        # when comparing unauthenticated and authenticated requests.
        rate_limit = {
            "limit": response.headers.get("x-ratelimit-limit"),
            "remaining": response.headers.get("x-ratelimit-remaining"),
            "used": response.headers.get("x-ratelimit-used"),
            "reset": response.headers.get("x-ratelimit-reset"),
            "resource": response.headers.get("x-ratelimit-resource"),
        }

        # Save the entire raw search payload plus request metadata. The CSV below
        # keeps only selected fields, so the raw file is the audit trail.
        raw_pages.append(
            {
                "request_type": "repository_search",
                "page_number": page_number,
                "request_url": response.url,
                "status_code": response.status_code,
                "rate_limit": rate_limit,
                "payload": payload,
            }
        )

        for item in payload.get("items", []):
            # GitHub nests owner information inside each repository item.
            # item.get("owner") may be None, so "or {}" gives us a safe empty dict.
            owner = item.get("owner") or {}

            # This flattening step is a research-design choice. GitHub returns
            # many more fields than we keep here; raw JSONL preserves the rest.
            rows.append(
                {
                    "query": query,
                    "search_rank": len(rows) + 1,
                    "page_number": page_number,
                    "repository_id": item.get("id"),
                    "node_id": item.get("node_id"),
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "owner_login": owner.get("login"),
                    "owner_type": owner.get("type"),
                    "html_url": item.get("html_url"),
                    "api_url": item.get("url"),
                    "description": item.get("description"),
                    "language": item.get("language"),
                    "stargazers_count": item.get("stargazers_count"),
                    "forks_count": item.get("forks_count"),
                    "open_issues_count": item.get("open_issues_count"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "pushed_at": item.get("pushed_at"),
                    "archived": item.get("archived"),
                    "disabled": item.get("disabled"),
                    "private": item.get("private"),
                    # license can be null, so we use "or {}" before asking for key.
                    "license_key": (item.get("license") or {}).get("key"),
                    # Topics are a list in JSON. For this simple CSV we join them
                    # into one cell; raw JSON preserves the original list.
                    "topics": "|".join(item.get("topics") or []),
                }
            )

        # If GitHub returns fewer items than requested, there is no next full
        # page for this query under the current settings.
        if len(payload.get("items", [])) < page_size:
            break

    return rows, raw_pages


def collect_repository_details(
    search_rows: list[dict],
    *,
    token: str | None = None,
    max_repositories: int = 10,
) -> tuple[list[dict], list[dict]]:
    """Collect one detail endpoint per repository.

    The search response is already rich, but this second step shows the common
    API pattern:

        search results -> stable identifier / URL -> detail request

    For GitHub, the detail endpoint is the repository API URL returned in each
    search result. We keep the default small because it is a teaching workflow.
    """

    detail_rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []

    # The search table can contain duplicate repositories if settings change, so
    # we deduplicate detail URLs before requesting them.
    seen_api_urls = set()
    api_urls = []
    for row in search_rows:
        api_url = row.get("api_url")
        if api_url and api_url not in seen_api_urls:
            api_urls.append(api_url)
            seen_api_urls.add(api_url)

    for detail_number, api_url in enumerate(api_urls[:max_repositories], start=1):
        # api_url is supplied by GitHub in the search response. Following it is
        # safer than constructing the detail URL by hand.
        response = polite_get(api_url, headers=github_headers(token))
        # The detail endpoint returns one repository object as JSON.
        payload = response.json()

        # Keep the full detail response for provenance and later inspection.
        raw_pages.append(
            {
                "request_type": "repository_detail",
                "detail_number": detail_number,
                "request_url": response.url,
                "status_code": response.status_code,
                "payload": payload,
            }
        )

        # Keep a small teaching subset of detail fields in the processed table.
        detail_rows.append(
            {
                "repository_id": payload.get("id"),
                "full_name": payload.get("full_name"),
                "default_branch": payload.get("default_branch"),
                "network_count": payload.get("network_count"),
                "subscribers_count": payload.get("subscribers_count"),
                "watchers_count": payload.get("watchers_count"),
                "size": payload.get("size"),
                "has_issues": payload.get("has_issues"),
                "has_projects": payload.get("has_projects"),
                "has_wiki": payload.get("has_wiki"),
                "has_pages": payload.get("has_pages"),
                "visibility": payload.get("visibility"),
            }
        )

    return detail_rows, raw_pages


def merge_search_and_details(
    search_rows: list[dict],
    detail_rows: list[dict],
) -> list[dict]:
    """Add repository-detail fields to each search-result row."""

    # Build repository_id -> detail row so each search row can be enriched quickly.
    details_by_id = {row.get("repository_id"): row for row in detail_rows}
    merged_rows = []
    for search_row in search_rows:
        # Some repositories may not have detail rows if --details is smaller than
        # the number of search results. In that case, keep the search row.
        detail_row = details_by_id.get(search_row.get("repository_id"), {})
        # Combine search fields and detail fields into one output row.
        merged_rows.append({**search_row, **detail_row})
    return merged_rows


def main() -> None:
    # Command-line arguments make collection decisions explicit and repeatable.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument(
        "--sort",
        choices=["stars", "forks", "help-wanted-issues", "updated"],
        default=None,
        help="Optional GitHub repository search sort field.",
    )
    parser.add_argument("--order", choices=["asc", "desc"], default="desc")
    parser.add_argument(
        "--details",
        type=int,
        default=5,
        help="Number of repositories for which to request the detail endpoint; use 0 to skip.",
    )
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    # Read authentication from the environment. This avoids putting tokens into
    # scripts, shell history, output files, or Git.
    token = os.getenv("GITHUB_TOKEN")
    # stem becomes a short query-based filename component.
    stem = args.query.lower().replace(" ", "_")[:60]
    outdir = Path(args.outdir)

    # First API step: collect repository search results.
    search_rows, raw_search_pages = collect_repository_search(
        args.query,
        args.pages,
        args.page_size,
        sort=args.sort,
        order=args.order,
        token=token,
    )

    if args.details > 0:
        # Optional second API step: request repository-detail endpoints for the
        # first N unique repositories.
        detail_rows, raw_detail_pages = collect_repository_details(
            search_rows,
            token=token,
            max_repositories=args.details,
        )
    else:
        # An empty details table keeps the merge code simple when details are off.
        detail_rows, raw_detail_pages = [], []

    # Merge the two API steps into one processed table.
    rows = merge_search_and_details(search_rows, detail_rows)

    # Use the same raw/processed/reports convention as the other workflows.
    raw_path = outdir / "raw" / f"github_repositories_{stem}.jsonl"
    csv_path = outdir / "processed" / f"github_repositories_{stem}.csv"
    report_path = outdir / "reports" / f"github_repositories_{stem}_provenance.json"

    write_jsonl(raw_path, [*raw_search_pages, *raw_detail_pages])
    write_csv(csv_path, rows)
    write_json(
        report_path,
        provenance(
            script=__file__,
            # Record whether authentication was used without recording the token.
            parameters={**vars(args), "authenticated": bool(token)},
            outputs=[raw_path, csv_path],
            notes=[
                "GitHub REST API example for public repository metadata.",
                "The script can run without GITHUB_TOKEN for small public-data demos, but unauthenticated rate limits are lower.",
                "Raw JSONL preserves search and optional repository-detail payloads.",
                "Processed CSV flattens selected repository fields and is therefore a lossy transformation.",
                "Authentication token, if used, is read from the environment and is not written to output files.",
            ],
        ),
    )

    auth_note = "authenticated" if token else "unauthenticated"
    print(f"Collected {len(search_rows)} repository search rows ({auth_note}).")
    print(f"Retrieved detail endpoint for {len(detail_rows)} repositories.")
    print(f"Raw: {raw_path}")
    print(f"Processed: {csv_path}")
    print(f"Provenance: {report_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Small unauthenticated run from the repository root:
#
#     python scripts/runnable_workflows/02_api_github.py \
#       --query "digital services act" \
#       --pages 1 \
#       --page-size 5 \
#       --details 2 \
#       --outdir /tmp/methodsnet_github_test
#
# Optional authenticated run:
#
#     export GITHUB_TOKEN="paste-your-token-here"
#     python scripts/runnable_workflows/02_api_github.py \
#       --query "platform governance" \
#       --pages 2 \
#       --page-size 10 \
#       --sort stars \
#       --details 5 \
#       --outdir data
#
# What each part means:
#
# - export GITHUB_TOKEN="..."
#   Stores a GitHub token in the terminal environment. The script reads it but
#   does not write it to output files. This is optional for small public demos.
#
# - --query
#   The repository search query sent to GitHub.
#
# - --pages
#   The number of search-result pages to request.
#
# - --page-size
#   The number of repositories requested per page.
#
# - --sort stars
#   Optional sorting rule. GitHub also supports other documented sort values.
#
# - --details
#   How many repository-detail endpoints to request after the search step.
#
# - --outdir
#   The output folder for raw JSONL, processed CSV, and provenance.
