"""Teaching walkthrough: auditing platform research data.

This script uses synthetic public-interface and API-export datasets. It teaches
the logic of comparing what is visible in one access route with what appears in
another.

Teaching goals:
1. Show that row counts alone are insufficient.
2. Compare IDs across sources.
3. Audit missing metadata.
4. Discuss scope narrowing and metadata stripping.
"""

# %% 1. Imports

from pathlib import Path

import pandas as pd


# %% 2. Synthetic benchmark and observed data

# Imagine the reference data came from a small, ethically approved public
# interface observation. Imagine the observed data came from a platform research
# API. The values are synthetic.
reference = pd.DataFrame(
    [
        {"post_id": "a1", "url": "https://example.test/a1", "author": "u01", "created_at": "2026-01-01", "engagement": 10},
        {"post_id": "a2", "url": "https://example.test/a2", "author": "u02", "created_at": "2026-01-01", "engagement": 5},
        {"post_id": "a3", "url": "https://example.test/a3", "author": "u03", "created_at": "2026-01-02", "engagement": 22},
        {"post_id": "a4", "url": "https://example.test/a4", "author": "u04", "created_at": "2026-01-02", "engagement": 1},
    ]
)

observed = pd.DataFrame(
    [
        {"post_id": "a1", "url": "https://example.test/a1", "author": None, "created_at": "2026-01-01", "engagement": None},
        {"post_id": "a2", "url": "https://example.test/a2", "author": None, "created_at": "2026-01-01", "engagement": None},
        {"post_id": "a2", "url": "https://example.test/a2", "author": None, "created_at": "2026-01-01", "engagement": None},
        {"post_id": "x9", "url": "https://example.test/x9", "author": None, "created_at": "2026-01-03", "engagement": None},
    ]
)

print("Reference:")
print(reference)
print("\nObserved:")
print(observed)


# %% 3. Compare IDs

id_col = "post_id"
ref_ids = set(reference[id_col])
obs_ids = set(observed[id_col])

common = ref_ids & obs_ids
missing_from_observed = ref_ids - obs_ids
extra_in_observed = obs_ids - ref_ids

print("Common IDs:", common)
print("Missing from observed:", missing_from_observed)
print("Extra in observed:", extra_in_observed)


# %% 4. Check duplicates

print("Reference duplicate IDs:", reference[id_col].duplicated().sum())
print("Observed duplicate IDs:", observed[id_col].duplicated().sum())

# Discussion prompt:
# Why might duplicates appear in an API export? Pagination errors? Reposts?
# Query overlap? Platform-side bugs? Researcher-side merge mistakes?


# %% 5. Audit missing metadata

missing_counts = observed.isna().sum()
completeness = 1 - observed.isna().mean()

print("Observed missing counts:")
print(missing_counts)

print("\nObserved completeness:")
print(completeness)

# The observed dataset contains some IDs, but author and engagement are stripped.
# That may be fine for one research question and fatal for another.


# %% 6. Write an audit report

report = {
    "reference_rows": len(reference),
    "observed_rows": len(observed),
    "reference_unique_ids": len(ref_ids),
    "observed_unique_ids": len(obs_ids),
    "common_ids": len(common),
    "missing_from_observed": sorted(missing_from_observed),
    "extra_in_observed": sorted(extra_in_observed),
    "observed_duplicate_ids": int(observed[id_col].duplicated().sum()),
    "observed_missing_by_column": missing_counts.astype(int).to_dict(),
    "observed_completeness": completeness.to_dict(),
    "interpretation": [
        "The observed data is incomplete relative to the benchmark.",
        "Metadata stripping affects author and engagement fields.",
        "The duplicate ID a2 should be investigated before analysis.",
    ],
}

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
reports_dir = outdir / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

report_path = reports_dir / "walkthrough_data_quality_audit.json"
pd.Series(report).to_json(report_path, indent=2)

print("Saved audit report:", report_path)


# %% 7. Teaching prompts

questions = [
    "Would a large observed dataset solve these problems?",
    "Which research questions survive metadata stripping?",
    "When is the public-interface benchmark itself biased?",
    "How should missingness be reported in a paper?",
    "What would you ask the platform or data provider after seeing this audit?",
]

for question in questions:
    print("-", question)
