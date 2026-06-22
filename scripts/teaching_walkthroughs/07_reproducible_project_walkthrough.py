"""Teaching walkthrough: putting a small collection project together.

This is a capstone-style walkthrough. It builds a minimal project structure,
stores configuration separately from code, writes outputs in raw/processed/report
folders, and creates a manifest.

Teaching goals:
1. Make parameters explicit.
2. Avoid mixing raw and processed data.
3. Write a manifest that describes how the dataset was made.
4. Treat limitations as part of the output.
"""

# %% 1. Imports

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# %% 2. Configuration

# In a larger project this would live in a YAML file. The teaching point is that
# query terms, page limits, and output folders should be visible and reviewable.
config = {
    "project_name": "walkthrough_reproducible_api_project",
    "endpoint": "https://en.wikipedia.org/w/api.php",
    "query": "platform governance",
    "pages": 1,
    "page_size": 10,
    "outdir": "../data" if Path.cwd().name == "teaching_walkthroughs" else "data",
}

print(config)


# %% 3. Prepare folders

outdir = Path(config["outdir"])
raw_dir = outdir / "raw"
processed_dir = outdir / "processed"
reports_dir = outdir / "reports"

for folder in [raw_dir, processed_dir, reports_dir]:
    folder.mkdir(parents=True, exist_ok=True)


# %% 4. Collect one page from the API

params = {
    "action": "query",
    "list": "search",
    "srsearch": config["query"],
    "srlimit": config["page_size"],
    "format": "json",
    "formatversion": 2,
}

headers = {"User-Agent": "methodsNET-VLOP-course/1.0 reproducible project walkthrough"}

response = requests.get(config["endpoint"], params=params, headers=headers, timeout=30)
response.raise_for_status()
payload = response.json()

print("Request URL:", response.url)
print("Status:", response.status_code)


# %% 5. Save raw response

raw_path = raw_dir / "walkthrough_project_raw_response.json"
pd.Series(
    {
        "request_url": response.url,
        "status_code": response.status_code,
        "payload": payload,
    }
).to_json(raw_path, indent=2)

print("Saved raw response:", raw_path)


# %% 6. Process into an analysis table

rows = []
for item in payload.get("query", {}).get("search", []):
    rows.append(
        {
            "query": config["query"],
            "pageid": item.get("pageid"),
            "title": item.get("title"),
            "timestamp": item.get("timestamp"),
            "wordcount": item.get("wordcount"),
        }
    )

df = pd.DataFrame(rows)

processed_path = processed_dir / "walkthrough_project_processed.csv"
df.to_csv(processed_path, index=False)

print(df)
print("Saved processed table:", processed_path)


# %% 7. Write a manifest

manifest = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "project_name": config["project_name"],
    "access_route": "MediaWiki API",
    "parameters": config,
    "raw_output": str(raw_path),
    "processed_output": str(processed_path),
    "row_count": len(df),
    "limitations": [
        "Search results are API-ranked and query-dependent.",
        "This is not a measure of all platform-governance content on Wikipedia.",
        "Only one small page of results was collected for teaching purposes.",
    ],
}

manifest_path = reports_dir / "walkthrough_project_manifest.json"
pd.Series(manifest).to_json(manifest_path, indent=2)

print("Saved manifest:", manifest_path)


# %% 8. Teaching prompts

questions = [
    "Which parts of the workflow are parameters rather than code?",
    "What would another researcher need to reproduce this collection?",
    "What is the difference between raw and processed output here?",
    "Which limitations belong in the manifest?",
    "How would this structure change for scraping or DSA transparency data?",
]

for question in questions:
    print("-", question)
