"""Plan or inspect DSA Transparency Database work.

The full DSA Transparency Database is very large. This script avoids accidental
multi-gigabyte downloads. It can either:

1. print official dsa-tdb CLI commands for a small date window; or
2. summarize an instructor-provided CSV/parquet extract.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import provenance, write_json


def summarize_file(path: Path) -> dict:
    # pandas is imported here so the script can still print template commands
    # even if pandas is not needed for a no-input run.
    import pandas as pd

    # Parquet is a common columnar format for large data extracts.
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        # CSV is simpler for small classroom examples.
        df = pd.read_csv(path)

    summary = {
        # Store the source file path so the summary can be traced back.
        "path": str(path),
        "rows": int(len(df)),
        "columns": list(df.columns),
        # isna().sum() counts missing values by column.
        "missing_by_column": df.isna().sum().astype(int).to_dict(),
    }
    for col in ["platform_name", "category", "automated_decision", "content_language"]:
        if col in df.columns:
            # value_counts(...).head(20) gives a quick overview of common values
            # without printing huge tables.
            summary[f"top_{col}"] = df[col].value_counts(dropna=False).head(20).to_dict()
    return summary


def main() -> None:
    # The input file is optional because this script can also act as a planning
    # helper for DSA TDB command-line collection.
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Optional CSV/parquet extract to summarize.")
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-01-03")
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    if args.input:
        # Convert the user-provided path string into a Path object.
        path = Path(args.input)
        # summarize_file returns a dictionary that can be saved as JSON.
        summary = summarize_file(path)
        out_path = Path(args.outdir) / "reports" / "dsa_tdb_extract_summary.json"
        write_json(out_path, summary)
        write_json(
            Path(args.outdir) / "reports" / "dsa_tdb_workflow_provenance.json",
            provenance(
                # The provenance records the script, arguments, and output path.
                script=__file__,
                parameters=vars(args),
                outputs=[out_path],
                notes=["Summarized an instructor-provided DSA TDB extract."],
            ),
        )
        print(f"Rows: {summary['rows']}")
        print(f"Report: {out_path}")
        # return stops here because the input-file workflow is complete.
        return

    # If no input is supplied, the script prints careful starter commands rather
    # than downloading a large database accidentally.
    print("No input extract supplied.")
    print("For official DSA Transparency Database dumps, use the dsa-tdb CLI.")
    print("Start with a very small date window and confirm disk requirements.")
    print()
    print("Install:")
    print(
        "pip install dsa-tdb "
        "--index-url https://code.europa.eu/api/v4/projects/943/packages/pypi/simple"
    )
    print()
    print("Example small-window aggregate command:")
    print(
        "dsa-tdb-cli download-aggs "
        f"-o data/dsa_tdb_aggs -i {args.start} -f {args.end}"
    )
    print()
    print("Example small-window daily parquet command:")
    print(
        "dsa-tdb-cli download-pqts "
        f"-o data/dsa_tdb_daily -i {args.start} -f {args.end} -d"
    )
    print()
    print("Method note:")
    print(
        "The database records statements of reasons submitted under the DSA; "
        "it should not be interpreted as complete moderation activity."
    )


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Template run without an input file:
#
#     python scripts/runnable_workflows/05_dsa_transparency_workflow.py \
#       --start 2025-01-01 \
#       --end 2025-01-03 \
#       --outdir data
#
# Run using a CSV/parquet extract:
#
#     python scripts/runnable_workflows/05_dsa_transparency_workflow.py \
#       --input examples/data/synthetic_dsa_tdb_extract.csv \
#       --start 2025-01-01 \
#       --end 2025-01-03 \
#       --outdir data
#
# What each part means:
#
# - --input
#   Optional path to a DSA Transparency Database extract or synthetic example.
#   If omitted, the script creates a template-style report.
#
# - --start and --end
#   The date range documented for the workflow.
#
# - --outdir
#   The folder where summaries, processed outputs, and provenance are saved.
