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
    script_path = Path(__file__).with_name("01_api_wikipedia.py")
    spec = importlib.util.spec_from_file_location("api_wikipedia", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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
        return DEFAULT_CONFIG
    import yaml

    with Path(path).open("r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}
    return {**DEFAULT_CONFIG, **user_config}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="YAML config file.")
    args = parser.parse_args()
    config = load_config(args.config)

    if config["collector"] != "wikipedia_search":
        raise SystemExit("Only collector=wikipedia_search is implemented in this demo.")

    collect_search = load_wikipedia_collector()
    rows, raw_pages = collect_search(
        query=config["query"],
        pages=int(config["pages"]),
        page_size=int(config["page_size"]),
    )

    from common import write_csv, write_jsonl

    outdir = Path(config["outdir"])
    stem = config["query"].lower().replace(" ", "_")[:60]
    raw_path = outdir / "raw" / f"workflow_wikipedia_{stem}.jsonl"
    csv_path = outdir / "processed" / f"workflow_wikipedia_{stem}.csv"
    manifest_path = outdir / "reports" / f"workflow_wikipedia_{stem}_manifest.json"

    write_jsonl(raw_path, raw_pages)
    write_csv(csv_path, rows)
    write_json(
        manifest_path,
        provenance(
            script=__file__,
            parameters={"config_file": args.config, "config": config},
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
