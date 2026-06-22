"""Generate prompt templates and review checklists for AI-assisted collection.

This script does not call an AI API. Students can copy the prompts into the
approved tool for the course, then verify outputs before running any code.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import write_json


PROMPTS = {
    "api_query": """You are helping design a platform API collection workflow.
Research question: {research_question}
Platform/API: {platform}
Known endpoint/docs: {docs}

Return:
1. necessary fields only;
2. query parameters;
3. pagination plan;
4. rate-limit and error-handling plan;
5. provenance fields to save;
6. assumptions that must be verified in the official documentation.
Do not invent endpoints or permissions.""",
    "scraper_debug": """You are helping debug a research scraper.
URL type: {platform}
Observed problem: {problem}
HTML excerpt or selector summary: {html_excerpt}

Return:
1. likely cause;
2. safer selectors to test;
3. validation checks;
4. ethical/legal checks before running at scale;
5. what raw evidence to save for reproducibility.
Do not suggest bypassing access controls or anti-bot systems.""",
    "codebook": """Create a codebook draft for this platform dataset.
Research question: {research_question}
Access route: {access_route}
Columns: {columns}

Return a table with:
column name, definition, source field, transformations, missingness meaning,
privacy sensitivity, and analysis cautions.""",
    "audit_plan": """Create a data-quality audit plan.
Dataset source: {access_route}
Research question: {research_question}
Known risks: {known_risks}

Return checks for completeness, duplicates, missing metadata, time gaps,
platform-specific scope restrictions, rate-limit artifacts, and reproducibility.""",
}


CHECKLIST = [
    "Did the AI invent endpoints, fields, legal permissions, or platform policies?",
    "Did a human verify all API and legal claims against primary documentation?",
    "Was sensitive or personal data pasted into an external AI system?",
    "Does generated code include network calls, file deletion, or credential handling?",
    "Are selectors and parsing assumptions validated on multiple pages?",
    "Are model/tool name, date, and prompt purpose documented?",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-question", default="[insert research question]")
    parser.add_argument("--platform", default="[insert platform/API]")
    parser.add_argument("--docs", default="[insert official documentation URL]")
    parser.add_argument("--problem", default="[insert observed problem]")
    parser.add_argument("--html-excerpt", default="[insert small non-sensitive excerpt]")
    parser.add_argument("--access-route", default="[API / scraping / DSA / research tool]")
    parser.add_argument("--columns", default="[insert column list]")
    parser.add_argument("--known-risks", default="[insert known risks]")
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()

    values = vars(args)
    rendered = {name: template.format(**values) for name, template in PROMPTS.items()}
    output = {"prompts": rendered, "review_checklist": CHECKLIST}

    out_path = Path(args.outdir) / "reports" / "ai_augmented_collection_prompts.json"
    write_json(out_path, output)

    for name, prompt in rendered.items():
        print(f"\n--- {name} ---\n{prompt}\n")
    print("--- review checklist ---")
    for item in CHECKLIST:
        print(f"- {item}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
