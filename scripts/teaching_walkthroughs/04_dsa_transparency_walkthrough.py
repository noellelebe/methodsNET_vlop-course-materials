"""Teaching walkthrough: thinking with DSA transparency data.

This file does not download the full DSA Transparency Database. The full data is
large and should be handled deliberately. Instead, it teaches the logic of
working with statements of reasons using a tiny synthetic extract.

Teaching goals:
1. Understand what a statement of reasons is.
2. Practice grouping and comparing moderation records.
3. Discuss why transparency data is not the same as all moderation.
4. Prepare students for using official dsa-tdb tooling on small windows.
"""

# %% 1. Imports

from pathlib import Path

import pandas as pd


# %% 2. A tiny synthetic extract

# These rows mimic some common fields in transparency data. They are not real
# platform records. Synthetic data lets students learn the structure without
# downloading gigabytes or handling sensitive content.
records = [
    {
        "platform_name": "ExamplePlatform",
        "content_date": "2026-01-01",
        "category": "STATEMENT_CATEGORY_NEGATIVE_EFFECTS_ON_CIVIC_DISCOURSE_OR_ELECTIONS",
        "decision_visibility": "DECISION_VISIBILITY_CONTENT_REMOVED",
        "content_type": "CONTENT_TYPE_TEXT",
        "automated_detection": "Yes",
        "automated_decision": "AUTOMATED_DECISION_PARTIALLY",
    },
    {
        "platform_name": "ExamplePlatform",
        "content_date": "2026-01-01",
        "category": "STATEMENT_CATEGORY_ILLEGAL_OR_HARMFUL_SPEECH",
        "decision_visibility": "DECISION_VISIBILITY_CONTENT_LABELLED",
        "content_type": "CONTENT_TYPE_VIDEO",
        "automated_detection": "No",
        "automated_decision": "AUTOMATED_DECISION_NO",
    },
    {
        "platform_name": "AnotherPlatform",
        "content_date": "2026-01-02",
        "category": "STATEMENT_CATEGORY_CONSUMER_INFORMATION",
        "decision_visibility": "DECISION_VISIBILITY_CONTENT_DISABLED",
        "content_type": "CONTENT_TYPE_PRODUCT",
        "automated_detection": "Yes",
        "automated_decision": "AUTOMATED_DECISION_FULLY",
    },
]

df = pd.DataFrame(records)
print(df)


# %% 3. Basic counts

print("Rows by platform:")
print(df["platform_name"].value_counts())

print("\nRows by category:")
print(df["category"].value_counts())

print("\nAutomation fields:")
print(pd.crosstab(df["automated_detection"], df["automated_decision"]))


# %% 4. What the data can and cannot mean

# A count of statements is not automatically a count of all harmful content.
# It is a count of statements submitted to the transparency database. It can be
# shaped by platform reporting practices, moderation volume, enforcement style,
# legal interpretation, and schema choices.

method_notes = [
    "A statement of reasons records a moderation decision explanation, not the full moderation pipeline.",
    "Categories may not be comparable across platforms without checking reporting behavior.",
    "Automated_detection and automated_decision are related but not identical concepts.",
    "Missing or vague fields can limit downstream inference.",
]

for note in method_notes:
    print("-", note)


# %% 5. Save the synthetic extract and method notes

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
processed_dir = outdir / "processed"
reports_dir = outdir / "reports"
processed_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

csv_path = processed_dir / "walkthrough_synthetic_dsa_tdb.csv"
notes_path = reports_dir / "walkthrough_synthetic_dsa_tdb_notes.txt"

df.to_csv(csv_path, index=False)
notes_path.write_text("\n".join(method_notes), encoding="utf-8")

print("Saved synthetic extract:", csv_path)
print("Saved notes:", notes_path)


# %% 6. Official tooling command templates

print("Official dsa-tdb tooling should be used deliberately on small windows first.")
print()
print("Install:")
print(
    "pip install dsa-tdb "
    "--index-url https://code.europa.eu/api/v4/projects/943/packages/pypi/simple"
)
print()
print("Example small aggregate download:")
print("dsa-tdb-cli download-aggs -o data/dsa_tdb_aggs -i 2025-01-01 -f 2025-01-03")
print()
print("Example small daily parquet download:")
print("dsa-tdb-cli download-pqts -o data/dsa_tdb_daily -i 2025-01-01 -f 2025-01-03 -d")


# %% 7. Teaching prompts

questions = [
    "What is the unit of analysis in this dataset?",
    "Why is this not the same as all content moderation activity?",
    "Which fields would you need for a study of election-related moderation?",
    "What platform differences would make cross-platform comparison hard?",
    "What should go into a provenance note for a DSA Transparency Database extract?",
]

for question in questions:
    print("-", question)
