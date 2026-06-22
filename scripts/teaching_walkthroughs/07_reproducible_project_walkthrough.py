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
    # project_name becomes part of the manifest. It gives this run a human-
    # readable label that is more informative than "script output."
    "project_name": "walkthrough_reproducible_api_project",
    # endpoint is the API URL. Keeping it in config makes it visible and easier
    # to change if the workflow is adapted to another API.
    "endpoint": "https://en.wikipedia.org/w/api.php",
    # query is the substantive search term. Changing it changes the population
    # of records that can enter the dataset.
    "query": "platform governance",
    # pages is the maximum number of result pages to collect. This walkthrough
    # uses one page so the output remains small enough to inspect by hand.
    "pages": 1,
    # page_size is the number of results requested per API request.
    "page_size": 10,
    # outdir chooses where outputs go. The conditional keeps paths working when
    # the file is run from the repository root or from this script folder.
    "outdir": "../data" if Path.cwd().name == "teaching_walkthroughs" else "data",
}

print(config)


# %% 3. Prepare folders

outdir = Path(config["outdir"])
# These three folders encode the workflow stages:
# raw = source-shaped evidence, processed = analysis-shaped tables, reports =
# documentation such as manifests and audits.
raw_dir = outdir / "raw"
processed_dir = outdir / "processed"
reports_dir = outdir / "reports"

for folder in [raw_dir, processed_dir, reports_dir]:
    # mkdir creates the folder if needed. parents=True also creates data/ if it
    # does not exist yet; exist_ok=True avoids errors on repeated runs.
    folder.mkdir(parents=True, exist_ok=True)


# %% 4. Collect one page from the API

params = {
    # action=query tells MediaWiki to read/query wiki data.
    "action": "query",
    # list=search selects the search module within the query action.
    "list": "search",
    # srsearch takes the substantive query from config rather than hard-coding it
    # inside the request.
    "srsearch": config["query"],
    # srlimit takes the page size from config, making collection scope explicit.
    "srlimit": config["page_size"],
    # JSON is the response format consumed by response.json().
    "format": "json",
    # Version 2 gives a cleaner JSON shape for modern clients.
    "formatversion": 2,
}

# The User-Agent names the script in the HTTP request. This is a small but
# important habit for responsible automated collection.
headers = {"User-Agent": "methodsNET-VLOP-course/1.0 reproducible project walkthrough"}

response = requests.get(config["endpoint"], params=params, headers=headers, timeout=30)
# If the API returns an error status, stop here rather than saving an error
# response as raw data.
response.raise_for_status()
# payload is the parsed JSON response: nested Python dicts and lists.
payload = response.json()

print("Request URL:", response.url)
print("Status:", response.status_code)


# %% 5. Save raw response

raw_path = raw_dir / "walkthrough_project_raw_response.json"
pd.Series(
    {
        # request_url records the final URL with encoded query parameters.
        "request_url": response.url,
        # status_code records whether the HTTP request succeeded.
        "status_code": response.status_code,
        # payload preserves the full parsed API response, not just selected
        # columns. This lets us revisit extraction decisions later.
        "payload": payload,
    }
).to_json(raw_path, indent=2)

print("Saved raw response:", raw_path)


# %% 6. Process into an analysis table

rows = []
# The search results live under query -> search in the MediaWiki response. The
# .get() pattern avoids crashing if the API response has a different shape, but
# in a production workflow we would also log that anomaly.
for item in payload.get("query", {}).get("search", []):
    rows.append(
        {
            # query is added by us so each row preserves the search term that
            # produced it.
            "query": config["query"],
            # pageid is MediaWiki's numeric page identifier.
            "pageid": item.get("pageid"),
            # title is the page title shown to users.
            "title": item.get("title"),
            # timestamp is the page's last-edit timestamp in this API result.
            "timestamp": item.get("timestamp"),
            # wordcount is a rough page-size indicator.
            "wordcount": item.get("wordcount"),
        }
    )

df = pd.DataFrame(rows)

processed_path = processed_dir / "walkthrough_project_processed.csv"
# index=False prevents pandas from adding a synthetic row-number column.
df.to_csv(processed_path, index=False)

print(df)
print("Saved processed table:", processed_path)


# %% 7. Write a manifest

manifest = {
    # UTC timestamps avoid ambiguity across time zones and daylight-saving rules.
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "project_name": config["project_name"],
    # access_route names how the data was obtained. This is a methodological
    # field, not just a technical detail.
    "access_route": "MediaWiki API",
    # parameters records the config dictionary so a reader can see the query,
    # endpoint, page limit, page size, and output directory used in this run.
    "parameters": config,
    "raw_output": str(raw_path),
    "processed_output": str(processed_path),
    # row_count is a quick check that helps detect empty or unexpectedly large
    # outputs.
    "row_count": len(df),
    # limitations are part of the research output. They prevent the dataset from
    # being interpreted as more complete than it is.
    "limitations": [
        "Search results are API-ranked and query-dependent.",
        "This is not a measure of all platform-governance content on Wikipedia.",
        "Only one small page of results was collected for teaching purposes.",
    ],
}

manifest_path = reports_dir / "walkthrough_project_manifest.json"
# The manifest is saved separately from the data so it can be read before
# analysis and attached to assignments or project submissions.
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
