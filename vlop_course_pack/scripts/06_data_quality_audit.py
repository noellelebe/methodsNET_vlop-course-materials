"""Audit completeness and overlap between two platform-data CSV files.

Example:
    python scripts/06_data_quality_audit.py --reference public.csv --observed api.csv --id-col url
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from common import provenance, write_json


def audit(reference: pd.DataFrame, observed: pd.DataFrame, id_col: str) -> dict:
    # The "reference" file is not assumed to be perfect truth. It is simply the
    # benchmark we are comparing against: for example, a public-interface sample
    # compared with a platform research API export.
    if id_col not in reference.columns:
        raise ValueError(f"{id_col!r} is not in reference columns")
    if id_col not in observed.columns:
        raise ValueError(f"{id_col!r} is not in observed columns")

    # We compare unique IDs, not row counts alone. Row counts can look similar
    # while the actual items are different, duplicated, or missing.
    ref_ids = set(reference[id_col].dropna().astype(str))
    obs_ids = set(observed[id_col].dropna().astype(str))
    common = ref_ids & obs_ids

    return {
        "reference_rows": int(len(reference)),
        "observed_rows": int(len(observed)),
        "reference_unique_ids": len(ref_ids),
        "observed_unique_ids": len(obs_ids),
        "common_ids": len(common),
        "missing_from_observed": len(ref_ids - obs_ids),
        "extra_in_observed": len(obs_ids - ref_ids),
        "reference_duplicate_ids": int(reference[id_col].duplicated().sum()),
        "observed_duplicate_ids": int(observed[id_col].duplicated().sum()),
        # Missing fields can be just as important as missing rows. For platform
        # data, stripped metadata may make some research questions impossible even
        # when the content ID itself is present.
        "observed_missing_by_column": observed.isna().sum().astype(int).to_dict(),
        "reference_missing_by_column": reference.isna().sum().astype(int).to_dict(),
        "observed_field_completeness": {
            col: float(1 - observed[col].isna().mean()) for col in observed.columns
        },
    }


def main() -> None:
    # The script is deliberately generic: students can compare any two CSV files
    # as long as both contain the same identifier column.
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--observed", required=True)
    parser.add_argument("--id-col", required=True)
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    reference = pd.read_csv(args.reference)
    observed = pd.read_csv(args.observed)

    # The report is JSON so it can be read by humans, versioned in a project, or
    # consumed by later scripts in a reproducible workflow.
    report = audit(reference, observed, args.id_col)

    out_path = Path(args.outdir) / "reports" / "data_quality_audit.json"
    write_json(out_path, report)
    write_json(
        Path(args.outdir) / "reports" / "data_quality_audit_provenance.json",
        provenance(
            script=__file__,
            parameters=vars(args),
            outputs=[out_path],
            notes=[
                "Reference does not mean truth; it means benchmark for this audit.",
                "Interpret missingness substantively, not just technically.",
            ],
        ),
    )

    print(f"Common IDs: {report['common_ids']}")
    print(f"Missing from observed: {report['missing_from_observed']}")
    print(f"Extra in observed: {report['extra_in_observed']}")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
