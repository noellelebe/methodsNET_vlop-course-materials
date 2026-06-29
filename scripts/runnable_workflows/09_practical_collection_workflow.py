"""Create a reproducible run folder with logging, monitoring, and schedules.

This script is a teaching workflow for Day 5: practical collection operations.
It does not scrape a live site by default. Instead, it demonstrates the wrapper
that should surround real collectors:

1. create one folder per run;
2. save the config and command;
3. write a run log;
4. record git/package/Python versions;
5. write monitoring checks;
6. generate cron, launchd, and GitHub Actions examples.

For a real project, the collection step inside this wrapper could call one of
the earlier scripts, such as 01_api_wikipedia.py or 03b_methodsnet_course_scraper.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import provenance, write_csv, write_json


def utc_stamp() -> str:
    """Return a filename-safe UTC timestamp."""

    # datetime.now(timezone.utc) creates an unambiguous timestamp; strftime turns
    # it into a compact string that works in folder names.
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_name(text: str) -> str:
    """Make a short filesystem-safe name."""

    # Keep letters/numbers and replace other characters with underscores. This
    # prevents spaces or punctuation from creating awkward folder names.
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower())[:60].strip("_")


def run_command(command: list[str]) -> str | None:
    """Run a small diagnostic command and return stdout.

    Diagnostics such as git commit hashes should not crash the whole workflow.
    If the command fails, return None and let the manifest record that the value
    was unavailable.
    """

    try:
        # subprocess.run executes a command such as git rev-parse HEAD.
        result = subprocess.run(
            command,
            # check=True turns non-zero exit codes into Python exceptions.
            check=True,
            # capture_output=True stores stdout/stderr instead of printing them.
            capture_output=True,
            # text=True returns strings instead of bytes.
            text=True,
        )
        # strip() removes trailing newlines from command output.
        return result.stdout.strip()
    except Exception:
        # Diagnostics are useful but should not crash the whole collection run.
        return None


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    """Read a CSV into a list of dictionaries."""

    # newline="" is the recommended way to open CSV files in Python.
    with path.open("r", encoding="utf-8", newline="") as f:
        # DictReader returns one dictionary per row using the CSV headers as keys.
        return list(csv.DictReader(f))


def demo_rows() -> list[dict[str, Any]]:
    """Return small synthetic rows for a no-network classroom demo."""

    return [
        {
            "source": "demo",
            "record_id": "demo-001",
            "title": "First collected record",
            "url": "https://example.org/records/1",
            "status_code": "200",
        },
        {
            "source": "demo",
            "record_id": "demo-002",
            "title": "Second collected record",
            "url": "https://example.org/records/2",
            "status_code": "200",
        },
    ]


def setup_logger(log_path: Path) -> logging.Logger:
    """Create a logger that writes to file and terminal."""

    # Make sure the logs folder exists before creating the log file.
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Named loggers are easier to control than the root logger.
    logger = logging.getLogger("practical_collection_workflow")
    # INFO means we record normal progress messages as well as warnings/errors.
    logger.setLevel(logging.INFO)
    # Clear handlers so rerunning the script/notebook does not duplicate output.
    logger.handlers.clear()

    # Formatter controls what each log line looks like.
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    # FileHandler writes log messages into logs/run.log.
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # StreamHandler also prints log messages to the terminal.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def monitor_rows(
    rows: list[dict[str, Any]],
    *,
    min_rows: int,
    required_columns: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    """Return monitoring checks and whether the run passed.

    Monitoring is not analysis. It asks: did the collector produce output that
    looks plausible enough to inspect further?
    """

    # This set comprehension collects every column name appearing in any row.
    observed_columns = sorted({key for row in rows for key in row.keys()})
    # checks will become the monitoring report.
    checks = []

    checks.append(
        {
            # Check 1: did we get at least the expected number of rows?
            "check": "minimum_row_count",
            "passed": len(rows) >= min_rows,
            "observed": len(rows),
            "expected": f">= {min_rows}",
            "why_it_matters": "Empty or unexpectedly tiny outputs often indicate selector/API breakage.",
        }
    )

    for column in required_columns:
        checks.append(
            {
                # Check 2: does each required column exist?
                "check": f"required_column:{column}",
                "passed": column in observed_columns,
                "observed": ",".join(observed_columns),
                "expected": column,
                "why_it_matters": "Missing columns can mean that parsing assumptions changed.",
            }
        )

    if "status_code" in observed_columns:
        # Count how many times each HTTP status code occurred.
        status_counts: dict[str, int] = {}
        for row in rows:
            status = str(row.get("status_code", "missing"))
            # Increment the count for this status code.
            status_counts[status] = status_counts.get(status, 0) + 1
        checks.append(
            {
                # Check 3: successful HTTP responses usually begin with 2.
                "check": "status_code_distribution",
                "passed": all(status.startswith("2") for status in status_counts),
                "observed": json.dumps(status_counts, sort_keys=True),
                "expected": "mostly 2xx statuses",
                "why_it_matters": "403, 404, 429, and 5xx statuses can indicate access, URL, rate-limit, or server problems.",
            }
        )

    # The whole run passes only if every individual check passed.
    passed = all(bool(check["passed"]) for check in checks)
    return checks, passed


def write_schedule_examples(
    path: Path,
    *,
    repo_dir: Path,
    command: str,
    run_label: str,
) -> Path:
    """Write cron, launchd, and GitHub Actions examples."""

    # Make sure the reports folder exists before writing the markdown file.
    path.parent.mkdir(parents=True, exist_ok=True)
    # This long f-string inserts the current repo directory and collector command
    # into reusable scheduling templates.
    text = f"""# Scheduling Examples for {run_label}

These examples are templates. Do not schedule a scraper until you know the site
allows the planned collection, the script has rate limits, and monitoring is in
place.

## 1. Cron on macOS/Linux

Cron runs commands at scheduled times. Edit your crontab with:

```bash
crontab -e
```

Example: run at 09:00 every Monday.

```cron
0 9 * * 1 cd {repo_dir} && {command} >> data/scheduled_cron.log 2>&1
```

Cron syntax:

```text
minute hour day-of-month month day-of-week command
```

Notes:

- Cron has a minimal environment. Use full paths if Python/conda is not found.
- Redirect stdout/stderr to a log file.
- Start with an infrequent schedule.
- Never use cron to hammer a website.

## 2. launchd on macOS

macOS often prefers launchd over cron. A LaunchAgent plist can run a script at
scheduled times. Save a file like this as:

```text
~/Library/LaunchAgents/org.methodsnet.collection.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.methodsnet.collection</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd {repo_dir} && {command}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{repo_dir}/data/launchd_stdout.log</string>
  <key>StandardErrorPath</key>
  <string>{repo_dir}/data/launchd_stderr.log</string>
</dict>
</plist>
```

Load it with:

```bash
launchctl load ~/Library/LaunchAgents/org.methodsnet.collection.plist
```

Unload it with:

```bash
launchctl unload ~/Library/LaunchAgents/org.methodsnet.collection.plist
```

## 3. GitHub Actions

GitHub Actions can schedule workflows in a repository. This is useful for public
or institutional projects, but it requires careful handling of secrets and
network load.

```yaml
name: Scheduled collection

on:
  schedule:
    - cron: "0 7 * * 1"
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: {command}
```

Important: scheduled collection should be small, documented, monitored, and
compliant with the relevant API/site rules.
"""
    # Write the schedule templates as a plain-text markdown file.
    path.write_text(text, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    # argparse defines the command-line interface for this workflow wrapper.
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-label", default="demo_collection")
    parser.add_argument("--outdir", default="data/runs")
    parser.add_argument(
        "--input-csv",
        default=None,
        help="Optional existing CSV to monitor instead of using demo rows.",
    )
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument(
        "--required-columns",
        default="record_id,title,url",
        help="Comma-separated columns expected in the processed output.",
    )
    parser.add_argument(
        "--collector-command",
        default="python scripts/runnable_workflows/09_practical_collection_workflow.py --run-label demo_collection",
        help="Command to include in schedule templates.",
    )
    return parser.parse_args()


def main() -> None:
    # Parse command-line flags into args.
    args = parse_args()

    # run_id combines timestamp and human label, creating one unique folder name.
    run_id = f"{utc_stamp()}_{safe_name(args.run_label)}"
    # run_dir is the top-level folder for this execution.
    run_dir = Path(args.outdir) / run_id
    # These subfolders separate evidence, tables, logs, reports, and config.
    raw_dir = run_dir / "raw"
    processed_dir = run_dir / "processed"
    logs_dir = run_dir / "logs"
    reports_dir = run_dir / "reports"
    config_dir = run_dir / "config"
    for folder in [raw_dir, processed_dir, logs_dir, reports_dir, config_dir]:
        # Create every folder before writing outputs.
        folder.mkdir(parents=True, exist_ok=True)

    # Configure logging as early as possible so later steps are recorded.
    log_path = logs_dir / "run.log"
    logger = setup_logger(log_path)
    logger.info("Starting practical collection workflow")
    logger.info("Run directory: %s", run_dir)

    # config is a snapshot of the important run settings.
    config = {
        "run_id": run_id,
        "run_label": args.run_label,
        "input_csv": args.input_csv,
        "min_rows": args.min_rows,
        "required_columns": [
            # Split the comma-separated column list into clean column names.
            column.strip()
            for column in args.required_columns.split(",")
            if column.strip()
        ],
        "collector_command": args.collector_command,
    }
    # Save the config snapshot inside the run folder.
    config_path = write_json(config_dir / "config_snapshot.json", config)
    logger.info("Saved config snapshot: %s", config_path)

    if args.input_csv:
        # If a CSV is supplied, this workflow monitors that existing output.
        input_path = Path(args.input_csv)
        logger.info("Reading existing processed CSV: %s", input_path)
        rows = read_csv_rows(input_path)
        # Keep a small raw/reference note so the run folder records where the
        # monitored input came from.
        raw_note_path = write_json(
            raw_dir / "input_reference.json",
            {"input_csv": str(input_path), "note": "This run monitored an existing CSV."},
        )
    else:
        # If no input is supplied, use synthetic rows so the demo works offline.
        logger.info("No input CSV supplied; using synthetic demo rows.")
        rows = demo_rows()
        raw_note_path = write_json(
            raw_dir / "demo_raw_records.json",
            {"records": rows, "note": "Synthetic rows for no-network teaching demo."},
        )

    # Save the rows being monitored as the processed output for this run.
    processed_path = write_csv(processed_dir / "records.csv", rows)
    logger.info("Saved processed records: %s", processed_path)

    # Run the operational monitoring checks.
    checks, passed = monitor_rows(
        rows,
        min_rows=args.min_rows,
        required_columns=config["required_columns"],
    )
    # Save the monitoring report as JSON.
    monitoring_path = write_json(
        reports_dir / "monitoring_report.json",
        {
            "passed": passed,
            "checks": checks,
            "interpretation": (
                "Passed basic operational checks."
                if passed
                else "One or more checks failed; inspect logs/raw data before using output."
            ),
        },
    )
    logger.info("Monitoring passed: %s", passed)

    # version_info records the computational context of the run.
    version_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "git_commit": run_command(["git", "rev-parse", "HEAD"]),
        "git_status_short": run_command(["git", "status", "--short"]),
        "pip_freeze": run_command([sys.executable, "-m", "pip", "freeze"]),
    }
    # Save version info separately so it can be inspected without opening the
    # larger manifest.
    version_path = write_json(reports_dir / "version_info.json", version_info)
    logger.info("Saved version info: %s", version_path)

    # Write scheduling templates adapted to the current collector command.
    schedule_path = write_schedule_examples(
        reports_dir / "scheduling_examples.md",
        repo_dir=Path.cwd(),
        command=args.collector_command,
        run_label=args.run_label,
    )
    logger.info("Saved schedule examples: %s", schedule_path)

    # The manifest is the run-level provenance file.
    manifest_path = write_json(
        reports_dir / "manifest.json",
        provenance(
            script=__file__,
            parameters=vars(args),
            outputs=[
                config_path,
                raw_note_path,
                processed_path,
                log_path,
                monitoring_path,
                version_path,
                schedule_path,
            ],
            notes=[
                "This run folder demonstrates practical collection operations.",
                "Scheduling examples are templates and should be adapted cautiously.",
                "Monitoring checks are operational checks, not substantive validation.",
                "Version info records Python, platform, git commit, git status, and package versions.",
            ],
        ),
    )
    logger.info("Saved manifest: %s", manifest_path)
    logger.info("Finished practical collection workflow")

    print(f"Run folder: {run_dir}")
    print(f"Monitoring passed: {passed}")
    print(f"Log: {log_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Schedule examples: {schedule_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# No-network classroom demo:
#
#     python scripts/runnable_workflows/09_practical_collection_workflow.py \
#       --run-label demo_collection \
#       --outdir /tmp/methodsnet_practical_runs
#
# Monitor an existing processed CSV:
#
#     python scripts/runnable_workflows/09_practical_collection_workflow.py \
#       --run-label methodsnet_course_monitor \
#       --input-csv data/processed/methodsnet_course_links.csv \
#       --required-columns course_url,course_code,title_guess,status_guess \
#       --min-rows 5 \
#       --collector-command "python scripts/runnable_workflows/03b_methodsnet_course_scraper.py --details 3 --outdir data" \
#       --outdir data/runs
#
# What each part means:
#
# - --run-label
#   A human-readable label included in the run-folder name.
#
# - --input-csv
#   Optional processed CSV to monitor. If omitted, the script uses synthetic demo
#   rows so the workflow works without network access.
#
# - --required-columns
#   Comma-separated columns that must exist in the monitored output.
#
# - --min-rows
#   Minimum acceptable row count. Smaller outputs trigger a failed monitoring
#   check.
#
# - --collector-command
#   The real collection command documented in scheduling templates.
#
# - --outdir
#   The parent folder where timestamped run folders are created.
