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
        # post_id is the join key: it is the identifier we use to compare whether
        # the same content appears in both access routes.
        #
        # url is the public-facing location of the content in this toy example.
        # author and engagement are metadata that the public interface contains.
        # created_at supports time-window checks.
        {"post_id": "a1", "url": "https://example.test/a1", "author": "u01", "created_at": "2026-01-01", "engagement": 10},
        {"post_id": "a2", "url": "https://example.test/a2", "author": "u02", "created_at": "2026-01-01", "engagement": 5},
        {"post_id": "a3", "url": "https://example.test/a3", "author": "u03", "created_at": "2026-01-02", "engagement": 22},
        {"post_id": "a4", "url": "https://example.test/a4", "author": "u04", "created_at": "2026-01-02", "engagement": 1},
    ]
)

observed = pd.DataFrame(
    [
        # The observed dataset represents an API or platform research tool
        # export. It contains some matching post_id values, but author and
        # engagement are missing. This simulates metadata stripping.
        {"post_id": "a1", "url": "https://example.test/a1", "author": None, "created_at": "2026-01-01", "engagement": None},
        {"post_id": "a2", "url": "https://example.test/a2", "author": None, "created_at": "2026-01-01", "engagement": None},
        # a2 appears twice on purpose. Duplicate records can happen because of
        # pagination bugs, overlapping queries, reposts, or merge mistakes.
        {"post_id": "a2", "url": "https://example.test/a2", "author": None, "created_at": "2026-01-01", "engagement": None},
        # x9 appears only in observed. This could be an API-only record, a public
        # benchmark miss, a deleted page, or a matching error.
        {"post_id": "x9", "url": "https://example.test/x9", "author": None, "created_at": "2026-01-03", "engagement": None},
    ]
)

print("Reference:")
print(reference)
print("\nObserved:")
print(observed)


# %% 3. Compare IDs

id_col = "post_id"
# set(...) keeps only unique IDs. We use sets because overlap questions are
# about membership: is this ID present in both sources?
ref_ids = set(reference[id_col])
obs_ids = set(observed[id_col])

# & is set intersection: IDs found in both sources.
common = ref_ids & obs_ids
# - is set difference: IDs in reference that are absent from observed.
missing_from_observed = ref_ids - obs_ids
# These IDs appear in observed but not in the reference benchmark.
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
# isna() returns True for missing cells. mean() treats True as 1 and False as 0,
# so observed.isna().mean() is the proportion missing in each column. 1 - that
# value is the proportion present, which we call completeness.
completeness = 1 - observed.isna().mean()

print("Observed missing counts:")
print(missing_counts)

print("\nObserved completeness:")
print(completeness)

# The observed dataset contains some IDs, but author and engagement are stripped.
# That may be fine for one research question and fatal for another.


# %% 6. Write an audit report

report = {
    # Row counts are basic diagnostics, but they are not enough on their own
    # because two files can have the same number of rows but different IDs.
    "reference_rows": len(reference),
    "observed_rows": len(observed),
    # Unique ID counts remove duplicates before comparing coverage.
    "reference_unique_ids": len(ref_ids),
    "observed_unique_ids": len(obs_ids),
    # common_ids is a count, while the next two fields preserve the actual ID
    # values that need interpretation.
    "common_ids": len(common),
    "missing_from_observed": sorted(missing_from_observed),
    "extra_in_observed": sorted(extra_in_observed),
    # duplicated().sum() counts repeated IDs after their first occurrence.
    "observed_duplicate_ids": int(observed[id_col].duplicated().sum()),
    # astype(int) converts pandas integer-like objects into plain JSON-friendly
    # integers before saving.
    "observed_missing_by_column": missing_counts.astype(int).to_dict(),
    "observed_completeness": completeness.to_dict(),
    # interpretation is written by the researcher. It translates diagnostics
    # into methodological implications.
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
# pd.Series(report).to_json() is a compact way to write this small dictionary as
# JSON. For larger nested reports, json.dump() would give more control.
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
