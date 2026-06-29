"""Run a small configured collection and write a manifest.

Currently supports the Wikipedia API example. This script shows the workflow
pattern students can reuse for other access regimes.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from common import provenance, write_json


def load_wikipedia_collector():
    # __file__ is the path to this script. with_name(...) swaps this script's
    # filename for the Wikipedia workflow filename in the same folder.
    script_path = Path(__file__).with_name("01_api_wikipedia.py")
    # spec_from_file_location lets us load another Python file even though its
    # filename starts with a number and cannot be imported with normal syntax.
    spec = importlib.util.spec_from_file_location("api_wikipedia", script_path)
    if spec is None or spec.loader is None:
        # This makes a broken import path visible immediately.
        raise RuntimeError(f"Could not load {script_path}")
    # module_from_spec creates an empty module object that the loader can fill.
    module = importlib.util.module_from_spec(spec)
    # exec_module actually runs the imported file and makes its functions
    # available on the module object.
    spec.loader.exec_module(module)
    # collect_search is the reusable function from 01_api_wikipedia.py.
    return module.collect_search


DEFAULT_CONFIG = {
    "collector": "wikipedia_search",
    "query": "digital services act",
    "pages": 1,
    "page_size": 10,
    "outdir": "data",
}


def load_config(path: str | None) -> dict:
    if not path:
        # If no YAML file is supplied, use the small built-in classroom config.
        return DEFAULT_CONFIG
    # yaml is imported only when needed because this script can run with the
    # default config without reading a YAML file.
    import yaml

    # Open the YAML config as text.
    with Path(path).open("r", encoding="utf-8") as f:
        # safe_load parses YAML into Python dictionaries/lists without executing
        # arbitrary Python objects.
        user_config = yaml.safe_load(f) or {}
    # {**DEFAULT_CONFIG, **user_config} means: start with defaults, then let user
    # config values override matching default keys.
    return {**DEFAULT_CONFIG, **user_config}


def main() -> None:
    # argparse reads optional command-line flags such as --config.
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="YAML config file.")
    args = parser.parse_args()
    # Load either the supplied YAML config or DEFAULT_CONFIG.
    config = load_config(args.config)

    if config["collector"] != "wikipedia_search":
        # This demo only knows how to run the Wikipedia collector. A larger
        # project could dispatch to different collectors here.
        raise SystemExit("Only collector=wikipedia_search is implemented in this demo.")

    # Load the collection function from the Wikipedia workflow script.
    collect_search = load_wikipedia_collector()
    # Run the collector with values from the config file.
    rows, raw_pages = collect_search(
        query=config["query"],
        pages=int(config["pages"]),
        page_size=int(config["page_size"]),
    )

    # Import these here to keep the top of the script focused on config/loading.
    from common import write_csv, write_jsonl

    # Convert the configured output folder into a Path object.
    outdir = Path(config["outdir"])
    # Build a short filename stem from the query.
    stem = config["query"].lower().replace(" ", "_")[:60]
    # Raw output keeps source-shaped API responses.
    raw_path = outdir / "raw" / f"workflow_wikipedia_{stem}.jsonl"
    # Processed output keeps flattened rows.
    csv_path = outdir / "processed" / f"workflow_wikipedia_{stem}.csv"
    # Manifest records parameters and output metadata.
    manifest_path = outdir / "reports" / f"workflow_wikipedia_{stem}_manifest.json"

    # Save raw API pages as JSONL.
    write_jsonl(raw_path, raw_pages)
    # Save processed rows as CSV.
    write_csv(csv_path, rows)
    write_json(
        manifest_path,
        provenance(
            # __file__ records which script created the output.
            script=__file__,
            # Store both the config file path and merged config values.
            parameters={"config_file": args.config, "config": config},
            # provenance() will compute file sizes/checksums for these outputs.
            outputs=[raw_path, csv_path],
            notes=[
                "This manifest is the minimum pattern for reproducible collection.",
                "Extend it with git commit, package versions, and IRB/ethics notes.",
            ],
        ),
    )

    print(f"Rows: {len(rows)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Run with an example YAML config:
#
#     python scripts/runnable_workflows/08_reproducible_workflow.py \
#       --config examples/configs/wikipedia_workflow.yml
#
# Or run with the built-in default config:
#
#     python scripts/runnable_workflows/08_reproducible_workflow.py
#
# What each part means:
#
# - --config
#   Optional path to a YAML file containing workflow parameters such as query,
#   page size, number of pages, collector name, and output folder.
#
# If --config is omitted, the script uses DEFAULT_CONFIG inside this file. This
# is useful for a quick demo, but real projects should keep important parameters
# in a visible config file.
