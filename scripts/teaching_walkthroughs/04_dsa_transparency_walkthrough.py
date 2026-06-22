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
        # platform_name identifies the reporting platform. In real DSA data, this
        # is crucial because reporting practices may differ across platforms.
        "platform_name": "ExamplePlatform",
        # content_date is the date associated with the content or moderation
        # record in this simplified example. Real extracts may contain several
        # date fields, so always check the schema before analysis.
        "content_date": "2026-01-01",
        # category is the platform's reported statement category. These long
        # uppercase values mirror controlled-vocabulary style fields: they are
        # designed for machines, not for easy reading.
        "category": "STATEMENT_CATEGORY_NEGATIVE_EFFECTS_ON_CIVIC_DISCOURSE_OR_ELECTIONS",
        # decision_visibility describes the visible moderation outcome, such as
        # removal, labelling, disabling, demotion, or another access restriction.
        "decision_visibility": "DECISION_VISIBILITY_CONTENT_REMOVED",
        # content_type distinguishes text, video, product listings, images, etc.
        # This matters because moderation patterns may differ by content format.
        "content_type": "CONTENT_TYPE_TEXT",
        # automated_detection asks whether automated systems helped detect the
        # content. Detection is about finding or flagging content.
        "automated_detection": "Yes",
        # automated_decision asks whether automated systems made or contributed
        # to the decision. Decision-making is not the same as detection.
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

# DataFrame turns the list of statement dictionaries into a table. Each
# dictionary is one synthetic statement of reasons.
df = pd.DataFrame(records)
print(df)


# %% 3. Basic counts

print("Rows by platform:")
# value_counts() counts how many rows appear for each platform_name. It does not
# prove that one platform moderates more overall; it only counts this extract.
print(df["platform_name"].value_counts())

print("\nRows by category:")
# Counting categories is a first descriptive step. Interpretation requires
# knowing whether categories are reported consistently across platforms.
print(df["category"].value_counts())

print("\nAutomation fields:")
# crosstab() creates a two-way table. Here it compares automated detection with
# automated decision-making to show that the two fields answer different
# questions.
print(pd.crosstab(df["automated_detection"], df["automated_decision"]))


# %% 4. What the data can and cannot mean

# A count of statements is not automatically a count of all harmful content.
# It is a count of statements submitted to the transparency database. It can be
# shaped by platform reporting practices, moderation volume, enforcement style,
# legal interpretation, and schema choices.

method_notes = [
    # Each note is written as a plain-language caution students could adapt into
    # a methods section or data appendix.
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
# processed/ contains analysis-shaped tables. reports/ contains notes, audits,
# manifests, or other documentation about how to interpret those tables.
processed_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

csv_path = processed_dir / "walkthrough_synthetic_dsa_tdb.csv"
notes_path = reports_dir / "walkthrough_synthetic_dsa_tdb_notes.txt"

# index=False avoids writing pandas row numbers as a fake data column.
df.to_csv(csv_path, index=False)
# The notes file is deliberately separate from the CSV: data and interpretation
# travel together, but they are not the same object.
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
# download-aggs retrieves aggregate files. Aggregates are smaller and safer for a
# first classroom run because they summarize counts rather than downloading many
# individual statement records.
print("dsa-tdb-cli download-aggs -o data/dsa_tdb_aggs -i 2025-01-01 -f 2025-01-03")
print()
print("Example small daily parquet download:")
# download-pqts retrieves daily parquet files. The -i and -f arguments define
# the start and end dates; -d asks for daily partitions. Parquet is efficient,
# but students should start with a tiny window because files can be large.
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
