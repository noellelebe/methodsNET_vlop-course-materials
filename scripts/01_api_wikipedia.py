"""Run a reproducible Wikipedia/MediaWiki API collection workflow.

This script is the automatable version of the Day 1 API example. It is meant to
be run from the command line, including from a scheduler such as cron.

Example:
    python scripts/runnable_workflows/01_api_wikipedia.py \
      --query "digital services act" \
      --pages 1 \
      --page-size 10 \
      --extract-chars 500 \
      --outdir data/runs \
      --run-label dsa_demo
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# Reuse the course helper functions for writing outputs instead of redefining
# JSON/JSONL/CSV writing in every script.
from common import (
    DEFAULT_USER_AGENT,
    file_sha256,
    write_csv,
    write_json,
    write_jsonl,
)


# This is the API endpoint used in the Day 1 notebook. The script never scrapes
# Wikipedia HTML; it asks the MediaWiki API for structured JSON.
API_URL = "https://en.wikipedia.org/w/api.php"


def utc_stamp() -> str:
    """Return a compact UTC timestamp for run-folder names."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utc_now() -> str:
    """Return an ISO UTC timestamp for reports."""
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    """Create a filesystem-friendly label from a human label or query."""
    # Run labels often contain spaces or punctuation. Folder names are easier to
    # handle if we keep only letters/numbers and replace other characters.
    cleaned = "".join(char if char.isalnum() else "_" for char in value.lower())
    return "_".join(part for part in cleaned.split("_") if part)[:80] or "run"


def setup_logger(log_path: Path) -> logging.Logger:
    """Create a logger that writes to the run log and to the terminal."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # A named logger is easier to reset and control than Python's root logger.
    logger = logging.getLogger("wikipedia_api_workflow")
    logger.setLevel(logging.INFO)
    # Clear handlers so rerunning the script in an interactive environment does
    # not duplicate every log line.
    logger.handlers.clear()

    # The formatter controls what one line in logs/run.log looks like.
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # FileHandler writes the permanent log file inside the run folder.
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # StreamHandler also prints messages to the terminal during manual runs.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def run_command(command: list[str]) -> str | None:
    """Run a diagnostic command such as git status without crashing the workflow."""
    try:
        # capture_output=True keeps the command output available as text instead
        # of printing it directly. check=True raises an error for failed commands.
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        # Version diagnostics are useful, but they should not crash the whole
        # collection if Git is unavailable or the folder is not a Git repository.
        return None


def command_line() -> str:
    """Record the exact command used to start this run."""
    # sys.executable records the Python interpreter path. sys.argv records the
    # script path and flags. Quoting keeps spaces safe in the saved command.
    return " ".join(shlex.quote(part) for part in [sys.executable, *sys.argv])


def request_json(
    params: dict[str, Any],
    delay_seconds: float,
    logger: logging.Logger,
) -> tuple[requests.Response, dict[str, Any]]:
    """Request one MediaWiki API URL and parse the JSON response."""
    # Pause between requests so a scheduled workflow does not make rapid-fire
    # calls to a public API.
    time.sleep(max(delay_seconds, 0))

    # This is the same requests.get(...) pattern used in the Day 1 API notebook.
    # params become the query string in the final API URL.
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = requests.get(
        API_URL,
        params=params,
        headers=headers,
        timeout=30,
    )
    logger.info("Requested %s -> HTTP %s", response.url, response.status_code)
    # Turn HTTP errors such as 403, 404, 429, or 500 into visible failures.
    response.raise_for_status()
    # The MediaWiki API returns JSON, so we parse the response body into Python
    # dictionaries/lists before returning it.
    return response, response.json()


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    """Split a list into batches."""
    # range(0, len(items), size) gives start positions such as 0, 10, 20.
    # items[start:start + size] then slices one batch.
    return [items[start : start + size] for start in range(0, len(items), size)]


def collect_search(
    query: str,
    pages: int,
    page_size: int,
    delay_seconds: float,
    logger: logging.Logger,
    initial_continuation: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect search-result rows and raw search API responses."""
    # rows is the flattened, table-shaped output for analysis.
    rows: list[dict[str, Any]] = []
    # raw_pages preserves the original API responses for inspection/provenance.
    raw_pages: list[dict[str, Any]] = []
    # MediaWiki pagination uses a continuation object returned by the API. If a
    # previous scheduled run saved one, start from there instead of result 1.
    continuation: dict[str, Any] = dict(initial_continuation or {})

    for page_number in range(1, pages + 1):
        # These parameters are the actual API request design. Changing query,
        # page_size, or continuation changes what can enter the dataset.
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": page_size,
            "format": "json",
            "formatversion": 2,
            **continuation,
        }

        request_continuation = dict(continuation)
        response, payload = request_json(
            params=params,
            delay_seconds=delay_seconds,
            logger=logger,
        )

        # Use .get(..., {}) so a changed/missing API field does not crash this
        # line. Monitoring below checks whether the output still looks plausible.
        search_items = payload.get("query", {}).get("search", [])
        raw_pages.append(
            {
                # Store request metadata alongside the full payload. This is the
                # raw evidence that lets you revisit parsing decisions later.
                "request_type": "search",
                "page_number": page_number,
                "request_continuation": request_continuation,
                "request_url": response.url,
                "status_code": response.status_code,
                "result_count": len(search_items),
                "payload": payload,
            }
        )

        # sroffset tells us where this batch starts in the full search-result
        # sequence. It makes ranks continue across scheduled runs.
        page_start_offset = int(params.get("sroffset", 0))
        for item_index, item in enumerate(search_items, start=1):
            # This is the lossy transformation from nested API JSON into a row.
            # Keep only the fields that are useful for the teaching table.
            rows.append(
                {
                    "query": query,
                    "search_rank": page_start_offset + item_index,
                    "page_number": page_number,
                    "sroffset_used": page_start_offset,
                    "pageid": item.get("pageid"),
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "timestamp": item.get("timestamp"),
                    "wordcount": item.get("wordcount"),
                }
            )

        logger.info("Search page %s returned %s rows", page_number, len(search_items))

        # If there is no continuation object, the API has no next batch for this
        # query. That becomes the stopping rule before max pages is reached.
        continuation = payload.get("continue", {})
        raw_pages[-1]["next_continuation"] = continuation
        if not continuation:
            logger.info("No continuation token returned; stopping search pagination")
            break

    return rows, raw_pages


def collect_article_extracts(
    search_rows: list[dict[str, Any]],
    extract_chars: int,
    delay_seconds: float,
    logger: logging.Logger,
    batch_size: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect article URLs and text extracts for the search-result page IDs."""
    # pageid connects search results to page-level API requests. Remove blanks
    # and duplicates so each page is requested only once.
    pageids: list[Any] = []
    seen_pageids = set()

    for row in search_rows:
        pageid = row.get("pageid")
        if pageid and pageid not in seen_pageids:
            pageids.append(pageid)
            seen_pageids.add(pageid)

    article_rows: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []

    for batch_number, pageid_batch in enumerate(chunked(pageids, batch_size), start=1):
        # This second API call asks for page-level information for known page IDs.
        # It is still API collection, not website HTML scraping.
        params: dict[str, Any] = {
            "action": "query",
            "prop": "info|extracts",
            "pageids": "|".join(str(pageid) for pageid in pageid_batch),
            "inprop": "url",
            "explaintext": 1,
            "redirects": 1,
            "format": "json",
            "formatversion": 2,
        }
        # If extract_chars is 0, omit exchars and let the API return fuller text.
        if extract_chars > 0:
            params["exchars"] = extract_chars

        response, payload = request_json(
            params=params,
            delay_seconds=delay_seconds,
            logger=logger,
        )

        pages = payload.get("query", {}).get("pages", [])
        raw_pages.append(
            {
                # Again, save request metadata plus the full raw payload.
                "request_type": "article_extracts",
                "batch_number": batch_number,
                "pageids": pageid_batch,
                "request_url": response.url,
                "status_code": response.status_code,
                "result_count": len(pages),
                "payload": payload,
            }
        )

        for page in pages:
            # Keep one article row per page so it can be merged back to the
            # search-result table by pageid.
            article_rows.append(
                {
                    "pageid": page.get("pageid"),
                    "article_title": page.get("title"),
                    "article_url": page.get("fullurl"),
                    "article_extract": page.get("extract"),
                    "article_extract_chars_requested": extract_chars,
                }
            )

        logger.info(
            "Article batch %s returned %s page records",
            batch_number,
            len(pages),
        )

    return article_rows, raw_pages


def merge_search_and_articles(
    search_rows: list[dict[str, Any]],
    article_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge search metadata with article URL/extract fields by pageid."""
    # The article API response may come back in a different order than the search
    # results. A lookup dictionary makes the merge independent of row order.
    articles_by_pageid = {row.get("pageid"): row for row in article_rows}
    return [
        # If no article record exists for a search result, keep the search row
        # and add no article fields.
        {**search_row, **articles_by_pageid.get(search_row.get("pageid"), {})}
        for search_row in search_rows
    ]


def make_check(
    name: str,
    passed: bool,
    observed: Any,
    expected: Any,
    severity: str = "error",
) -> dict[str, Any]:
    """Create one monitoring check result."""
    # Every monitoring check gets the same structure. That makes the JSON report
    # predictable and easy to scan.
    return {
        "check": name,
        "passed": bool(passed),
        "severity": severity,
        "observed": observed,
        "expected": expected,
    }


def run_monitoring_checks(
    rows: list[dict[str, Any]],
    raw_records: list[dict[str, Any]],
    raw_path: Path,
    processed_path: Path,
    required_columns: list[str],
    min_rows: int,
) -> dict[str, Any]:
    """Check whether this run produced plausible, inspectable outputs."""
    # Monitoring is not substantive validation. It asks whether the run looks
    # operationally plausible before anyone trusts the CSV.
    checks: list[dict[str, Any]] = []

    # Count HTTP statuses across all raw API requests. A scheduled workflow
    # should not silently accept 403, 429, or 500 responses.
    status_counts: dict[str, int] = {}
    for record in raw_records:
        status = str(record.get("status_code", "missing"))
        status_counts[status] = status_counts.get(status, 0) + 1

    checks.append(
        make_check(
            "http_statuses_all_200",
            set(status_counts) == {"200"},
            status_counts,
            {"200": len(raw_records)},
        )
    )

    # Empty output is one of the clearest signs that a collector broke or the
    # query/access route changed unexpectedly.
    checks.append(
        make_check(
            "minimum_row_count",
            len(rows) >= min_rows,
            len(rows),
            f">= {min_rows}",
        )
    )

    # Collect the columns that actually appeared in the processed rows.
    observed_columns = sorted({key for row in rows for key in row})
    # Required columns are structural expectations for downstream analysis.
    for column in required_columns:
        checks.append(
            make_check(
                f"required_column:{column}",
                column in observed_columns,
                observed_columns,
                column,
            )
        )

    # Columns can exist but still be unusable if important values are blank.
    for column in ["pageid", "title", "article_url"]:
        if column in observed_columns:
            missing_count = sum(1 for row in rows if not row.get(column))
            checks.append(
                make_check(
                    f"missing_values:{column}",
                    missing_count == 0,
                    missing_count,
                    0,
                )
            )

    # Duplicate page IDs can mean pagination or merging repeated records.
    pageids = [row.get("pageid") for row in rows if row.get("pageid")]
    duplicate_count = len(pageids) - len(set(pageids))
    checks.append(
        make_check(
            "duplicate_pageids",
            duplicate_count == 0,
            duplicate_count,
            0,
            severity="warning",
        )
    )

    # wordcount should be numeric and non-negative. Treat this as a warning
    # because it does not necessarily make the whole collection unusable.
    if "wordcount" in observed_columns:
        invalid_wordcounts = 0
        negative_wordcounts = 0
        for row in rows:
            try:
                value = int(row.get("wordcount"))
            except (TypeError, ValueError):
                invalid_wordcounts += 1
                continue
            if value < 0:
                negative_wordcounts += 1
        checks.append(
            make_check(
                "wordcount_numeric",
                invalid_wordcounts == 0,
                invalid_wordcounts,
                0,
                severity="warning",
            )
        )
        checks.append(
            make_check(
                "wordcount_non_negative",
                negative_wordcounts == 0,
                negative_wordcounts,
                0,
                severity="warning",
            )
        )

    # A run is not inspectable if the expected files were never written.
    for label, path in [
        ("raw_output_file", raw_path),
        ("processed_output_file", processed_path),
    ]:
        size = path.stat().st_size if path.exists() else 0
        checks.append(
            make_check(
                label,
                path.exists() and size > 0,
                {"exists": path.exists(), "bytes": size},
                "file exists and is not empty",
            )
        )

    # Error-level failures make the whole monitoring result fail. Warnings are
    # still reported, but they do not block the run by themselves.
    failed_checks = [check for check in checks if not check["passed"]]
    blocking_failures = [
        check for check in failed_checks if check["severity"] == "error"
    ]

    # Return one report object that can be written to JSON.
    return {
        "passed": len(blocking_failures) == 0,
        "checked_at_utc": utc_now(),
        "failed_check_count": len(failed_checks),
        "blocking_failure_count": len(blocking_failures),
        "summary": {
            "row_count": len(rows),
            "raw_record_count": len(raw_records),
            "columns": observed_columns,
            "status_counts": status_counts,
        },
        "checks": checks,
    }


def write_monitoring_summary(path: Path, report: dict[str, Any]) -> Path:
    """Write a short human-readable monitoring summary."""
    # The JSON report is complete, but a Markdown summary is quicker to read in
    # class or after a scheduled run.
    failed = [check for check in report["checks"] if not check["passed"]]
    failed_lines = [
        f"- {check['check']} ({check['severity']}): observed {check['observed']}; expected {check['expected']}"
        for check in failed
    ] or ["- None"]

    text = "\n".join(
        [
            f"# Monitoring Summary: {'PASS' if report['passed'] else 'FAIL'}",
            "",
            f"Checked at: {report['checked_at_utc']}",
            f"Rows: {report['summary']['row_count']}",
            f"Raw API records: {report['summary']['raw_record_count']}",
            f"Failed checks: {report['failed_check_count']}",
            "",
            "## Failed Checks",
            *failed_lines,
            "",
            "## Status Counts",
            json.dumps(report["summary"]["status_counts"], indent=2),
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_schedule_examples(
    path: Path,
    repo_dir: Path,
    command: str,
    log_path: Path,
) -> Path:
    """Write copyable cron examples into the run reports folder."""
    # Cron starts in a minimal environment, so the command explicitly changes
    # into the repository before running Python.
    cron_command = f"cd {shlex.quote(str(repo_dir))} && {command} >> {shlex.quote(str(log_path))} 2>&1"
    text = "\n".join(
        [
            "# Scheduling Examples",
            "",
            "The workflow script can be scheduled with `crontab -e` after you have",
            "checked that the access route, request volume, logging, and monitoring",
            "are appropriate for the project.",
            "",
            "Run every Monday at 09:00:",
            "",
            "```cron",
            f"0 9 * * 1 {cron_command}",
            "```",
            "",
            "Run every day at 07:30:",
            "",
            "```cron",
            f"30 7 * * * {cron_command}",
            "```",
            "",
            "Important: cron has a minimal environment. If `python` points to the",
            "wrong interpreter in cron, replace it with the full path printed in",
            "`reports/version_info.json` under `python_executable`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def output_info(path: Path) -> dict[str, Any]:
    """Return size and checksum for an output file."""
    # The manifest stores bytes and a checksum so future readers can tell which
    # exact file was produced by this run.
    if path.exists() and path.is_file():
        return {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
    return {"path": str(path), "exists": path.exists()}


def state_file_path(state_dir: Path, query: str, page_size: int) -> Path:
    """Return the continuation-state file for this query/page-size combination."""
    # Keep separate state files for different query/page-size settings. Otherwise
    # a run for one query could accidentally continue a different query.
    state_name = f"wikipedia_api_{safe_name(query)}_page_size_{page_size}.json"
    return state_dir / state_name


def load_continuation_state(path: Path) -> dict[str, Any]:
    """Load the saved MediaWiki continuation object, or return an empty one."""
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return state.get("next_continuation", {})


def save_continuation_state(
    path: Path,
    query: str,
    page_size: int,
    next_continuation: dict[str, Any],
) -> Path:
    """Save the MediaWiki continuation object for the next scheduled run."""
    return write_json(
        path,
        {
            "updated_at_utc": utc_now(),
            "query": query,
            "page_size": page_size,
            "next_continuation": next_continuation,
        },
    )


def parse_args() -> argparse.Namespace:
    # argparse defines the command-line interface. Values that may change from
    # run to run belong here instead of being edited inside the script.
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="digital services act")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument(
        "--extract-chars",
        type=int,
        default=500,
        help="Maximum article-extract characters per page; use 0 for full extracts.",
    )
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument("--run-label", default="wikipedia_api")
    parser.add_argument("--outdir", default="data/runs")
    parser.add_argument(
        "--state-dir",
        default="data/state",
        help="Folder for continuation state so scheduled runs can continue where the previous run stopped.",
    )
    parser.add_argument(
        "--reset-continuation",
        action="store_true",
        help="Ignore saved continuation and start from the first search results again.",
    )
    return parser.parse_args()


def main() -> None:
    # main() is the top-level workflow:
    # parse settings -> create run folder -> collect -> save -> monitor -> report.
    args = parse_args()
    repo_dir = Path.cwd()

    # Each execution gets its own run folder. This prevents old outputs from
    # being overwritten and makes scheduled runs easy to compare.
    run_id = f"{utc_stamp()}_{safe_name(args.run_label)}"
    run_dir = Path(args.outdir) / run_id

    # The run folder mirrors the workflow stages:
    # config = plan, raw = source-shaped evidence, processed = table,
    # logs = what happened, reports = monitoring/provenance/version records.
    config_dir = run_dir / "config"
    raw_dir = run_dir / "raw"
    processed_dir = run_dir / "processed"
    logs_dir = run_dir / "logs"
    reports_dir = run_dir / "reports"
    for folder in [config_dir, raw_dir, processed_dir, logs_dir, reports_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / "run.log"
    logger = setup_logger(log_path)
    logger.info("Starting Wikipedia API workflow")
    logger.info("Run directory: %s", run_dir)

    # Continuation state is the small piece that makes scheduled runs move
    # forward. Run 1 saves the next sroffset; run 2 starts from that sroffset.
    state_path = state_file_path(Path(args.state_dir), args.query, args.page_size)
    starting_continuation = (
        {}
        if args.reset_continuation
        else load_continuation_state(state_path)
    )
    logger.info("Continuation state file: %s", state_path)
    logger.info("Starting continuation: %s", starting_continuation or "{}")

    # The config snapshot records the intended settings for this run. It is the
    # "plan before the run" saved inside the run folder.
    config = {
        "run_id": run_id,
        "collector": "wikipedia_api",
        "collector_script": "scripts/runnable_workflows/01_api_wikipedia.py",
        "collector_command": command_line(),
        "endpoint": API_URL,
        "query": args.query,
        "pages": args.pages,
        "page_size": args.page_size,
        "extract_chars": args.extract_chars,
        "delay_seconds": args.delay_seconds,
        "min_rows": args.min_rows,
        "outdir": args.outdir,
        "state_dir": args.state_dir,
        "state_path": str(state_path),
        "reset_continuation": args.reset_continuation,
        "starting_continuation": starting_continuation,
        "run_dir": str(run_dir),
        "user_agent": DEFAULT_USER_AGENT,
        "access_policy": "Small MediaWiki API demo; identify with User-Agent and pause between requests.",
    }
    config_path = write_json(config_dir / "config_snapshot.json", config)
    logger.info("Saved config snapshot: %s", config_path)

    # Step 1: search the API for pages matching the query.
    search_rows, raw_search_pages = collect_search(
        query=args.query,
        pages=args.pages,
        page_size=args.page_size,
        delay_seconds=args.delay_seconds,
        logger=logger,
        initial_continuation=starting_continuation,
    )
    # The last search raw record contains the next continuation object returned
    # by MediaWiki. Save it outside this run folder for the next scheduled run.
    next_continuation = (
        raw_search_pages[-1].get("next_continuation", {})
        if raw_search_pages
        else {}
    )
    state_path = save_continuation_state(
        state_path,
        query=args.query,
        page_size=args.page_size,
        next_continuation=next_continuation,
    )
    logger.info("Saved next continuation for future runs: %s", next_continuation or "{}")
    logger.info("Saved continuation state: %s", state_path)

    # Step 2: use the search-result page IDs to request article URLs/extracts.
    article_rows, raw_article_pages = collect_article_extracts(
        search_rows=search_rows,
        extract_chars=args.extract_chars,
        delay_seconds=args.delay_seconds,
        logger=logger,
    )
    # Step 3: combine search metadata and article details into one table.
    rows = merge_search_and_articles(search_rows, article_rows)

    # Save raw API responses separately from the processed table. The CSV is
    # convenient, but the JSONL is the evidence for how the CSV was produced.
    raw_records = raw_search_pages + raw_article_pages
    # write_jsonl(), write_csv(), and write_json() come from common.py. Reusing
    # them keeps this workflow consistent with the earlier course scripts.
    raw_path = write_jsonl(raw_dir / "wikipedia_api_raw.jsonl", raw_records)
    processed_path = write_csv(processed_dir / "wikipedia_api_results.csv", rows)
    logger.info("Saved raw API records: %s", raw_path)
    logger.info("Saved processed CSV: %s", processed_path)
    logger.info("Processed row count: %s", len(rows))

    # Monitoring checks make failure visible. They do not prove the data are
    # substantively correct; they catch operational problems such as empty
    # output, missing columns, bad HTTP statuses, or missing files.
    monitoring_report = run_monitoring_checks(
        rows=rows,
        raw_records=raw_records,
        raw_path=raw_path,
        processed_path=processed_path,
        required_columns=[
            "query",
            "search_rank",
            "pageid",
            "title",
            "wordcount",
            "article_url",
            "article_extract",
        ],
        min_rows=args.min_rows,
    )
    monitoring_path = write_json(reports_dir / "monitoring_report.json", monitoring_report)
    monitoring_summary_path = write_monitoring_summary(
        reports_dir / "monitoring_summary.md",
        monitoring_report,
    )
    logger.info("Monitoring passed: %s", monitoring_report["passed"])
    logger.info("Saved monitoring report: %s", monitoring_path)
    logger.info("Saved monitoring summary: %s", monitoring_summary_path)

    # Version info records the code/environment context. This helps explain why
    # a run might differ later after code, packages, or Python versions change.
    version_info = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_commit": run_command(["git", "rev-parse", "HEAD"]),
        "git_status_short": run_command(["git", "status", "--short"]),
        "pip_freeze": run_command([sys.executable, "-m", "pip", "freeze"]),
    }
    version_path = write_json(reports_dir / "version_info.json", version_info)
    logger.info("Saved version info: %s", version_path)

    # Write cron examples into the run folder so the scheduling step is linked to
    # the exact command and environment used in this run.
    schedule_path = write_schedule_examples(
        reports_dir / "scheduling_examples.md",
        repo_dir=repo_dir,
        command=config["collector_command"],
        log_path=repo_dir / "data" / "wikipedia_api_cron.log",
    )
    logger.info("Saved schedule examples: %s", schedule_path)

    # The manifest is the run-level map. It points to the config, raw evidence,
    # processed table, logs, monitoring report, version info, and schedule notes.
    manifest = {
        "created_at_utc": utc_now(),
        "run_id": run_id,
        "collector": "wikipedia_api",
        "parameters": config,
        "outputs": [
            output_info(config_path),
            output_info(raw_path),
            output_info(processed_path),
            output_info(log_path),
            output_info(monitoring_path),
            output_info(monitoring_summary_path),
            output_info(version_path),
            output_info(schedule_path),
            output_info(state_path),
        ],
        "monitoring_passed": monitoring_report["passed"],
        "starting_continuation": starting_continuation,
        "next_continuation": next_continuation,
        "limitations": [
            "MediaWiki search results are API-ranked and query-dependent.",
            "This workflow collects a small teaching sample by default.",
            "Article extracts are requested through the MediaWiki API, not scraped from website HTML.",
            "Scheduling should only be used with an appropriate request frequency and monitoring routine.",
        ],
    }
    manifest_path = write_json(reports_dir / "manifest.json", manifest)
    logger.info("Saved manifest: %s", manifest_path)
    logger.info("Finished Wikipedia API workflow")

    # These print statements are for the person running the script manually.
    # Scheduled runs will also capture them in the cron log if output is redirected.
    print(f"Run folder: {run_dir}")
    print(f"Raw JSONL: {raw_path}")
    print(f"Processed CSV: {processed_path}")
    print(f"Log: {log_path}")
    print(f"Monitoring: {monitoring_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Monitoring passed: {monitoring_report['passed']}")


if __name__ == "__main__":
    main()
