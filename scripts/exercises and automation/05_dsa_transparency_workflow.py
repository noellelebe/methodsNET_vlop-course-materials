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
    import pandas as pd

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    summary = {
        "path": str(path),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "missing_by_column": df.isna().sum().astype(int).to_dict(),
    }
    for col in ["platform_name", "category", "automated_decision", "content_language"]:
        if col in df.columns:
            summary[f"top_{col}"] = df[col].value_counts(dropna=False).head(20).to_dict()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Optional CSV/parquet extract to summarize.")
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-01-03")
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    if args.input:
        path = Path(args.input)
        summary = summarize_file(path)
        out_path = Path(args.outdir) / "reports" / "dsa_tdb_extract_summary.json"
        write_json(out_path, summary)
        write_json(
            Path(args.outdir) / "reports" / "dsa_tdb_workflow_provenance.json",
            provenance(
                script=__file__,
                parameters=vars(args),
                outputs=[out_path],
                notes=["Summarized an instructor-provided DSA TDB extract."],
            ),
        )
        print(f"Rows: {summary['rows']}")
        print(f"Report: {out_path}")
        return

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
