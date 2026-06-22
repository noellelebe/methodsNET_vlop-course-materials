"""Teaching walkthrough: API collection with pagination and provenance.

Use this file in a live coding session. It is written as a cell-style script:
many editors let you run one # %% section at a time.

Teaching goals:
1. Show that an API request is a research design choice.
2. Show how pagination works.
3. Separate raw API responses from processed tables.
4. Write a small provenance record.
"""

# %% 1. Imports and the API endpoint

from pathlib import Path
from pprint import pprint

import pandas as pd
import requests


# MediaWiki is a good teaching API because it is public, documented, and does
# not require authentication for basic queries. That lets us focus on method
# before credentials.
API_URL = "https://en.wikipedia.org/w/api.php"


# %% 2. Build one API request by hand

# These parameters say what population of records we are asking the API to
# search. The query is not just a technical detail: it determines what can enter
# the dataset.
params = {
    "action": "query",
    "list": "search",
    "srsearch": "digital services act",
    "srlimit": 5,
    "format": "json",
    "formatversion": 2,
}

headers = {
    "User-Agent": "methodsNET-VLOP-course/1.0 teaching walkthrough",
}

response = requests.get(API_URL, params=params, headers=headers, timeout=30)

# In class: print this URL and ask students what each parameter means.
print(response.url)
print(response.status_code)


# %% 3. Inspect the JSON response before flattening it

payload = response.json()

# pprint makes nested JSON easier to read than print().
pprint(payload)

# Discussion prompt:
# What fields are metadata about the API response, and what fields describe
# actual search results?


# %% 4. Flatten one page into rows

rows = []

for item in payload["query"]["search"]:
    # This is where we decide which source fields become columns. That decision
    # should be documented because it is a lossy transformation.
    row = {
        "pageid": item.get("pageid"),
        "title": item.get("title"),
        "timestamp": item.get("timestamp"),
        "wordcount": item.get("wordcount"),
        "snippet": item.get("snippet"),
    }
    rows.append(row)

df = pd.DataFrame(rows)
print(df)


# %% 5. Follow the continuation token for a second page

# Many APIs do not use page=2. They use a continuation token or cursor returned
# by the previous response. If we ignore this, we silently collect only the first
# page of a larger result set.
continuation = payload.get("continue", {})
print("Continuation object:")
pprint(continuation)

params_page_2 = {**params, **continuation}
response_2 = requests.get(API_URL, params=params_page_2, headers=headers, timeout=30)
payload_2 = response_2.json()

print(response_2.url)
print("Number of results on page 2:", len(payload_2["query"]["search"]))


# %% 6. Collect several pages in a reusable function

def collect_wikipedia_search(query: str, max_pages: int = 3, page_size: int = 10):
    """Return both processed rows and raw response pages.

    The two-output design is deliberate:
    - rows are convenient for analysis;
    - raw_pages are evidence of what the API returned.
    """

    rows = []
    raw_pages = []
    continuation = {}

    for page_number in range(1, max_pages + 1):
        request_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": page_size,
            "format": "json",
            "formatversion": 2,
            **continuation,
        }

        r = requests.get(API_URL, params=request_params, headers=headers, timeout=30)
        r.raise_for_status()
        page_payload = r.json()

        raw_pages.append(
            {
                "page_number": page_number,
                "request_url": r.url,
                "status_code": r.status_code,
                "payload": page_payload,
            }
        )

        for item in page_payload.get("query", {}).get("search", []):
            rows.append(
                {
                    "query": query,
                    "page_number": page_number,
                    "pageid": item.get("pageid"),
                    "title": item.get("title"),
                    "timestamp": item.get("timestamp"),
                    "wordcount": item.get("wordcount"),
                    "snippet": item.get("snippet"),
                }
            )

        continuation = page_payload.get("continue", {})
        if not continuation:
            break

    return rows, raw_pages


rows, raw_pages = collect_wikipedia_search("digital services act", max_pages=2)
df = pd.DataFrame(rows)
print(df[["page_number", "title", "wordcount"]])


# %% 7. Save raw, processed, and provenance files

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
raw_dir = outdir / "raw"
processed_dir = outdir / "processed"
reports_dir = outdir / "reports"

raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

raw_path = raw_dir / "walkthrough_wikipedia_raw.json"
processed_path = processed_dir / "walkthrough_wikipedia_processed.csv"
provenance_path = reports_dir / "walkthrough_wikipedia_provenance.json"

# For compactness in a teaching walkthrough, we use pandas JSON writing. In a
# large project, JSONL is often better because each line can be streamed.
pd.Series(raw_pages).to_json(raw_path, orient="values", indent=2)
df.to_csv(processed_path, index=False)

provenance = {
    "source": "MediaWiki API",
    "endpoint": API_URL,
    "query": "digital services act",
    "max_pages": 2,
    "raw_output": str(raw_path),
    "processed_output": str(processed_path),
    "method_note": "Search API results are not a complete measure of platform attention or relevance.",
}

pd.Series(provenance).to_json(provenance_path, indent=2)

print("Saved:")
print(raw_path)
print(processed_path)
print(provenance_path)


# %% 8. Teaching prompts

questions = [
    "What exactly is the population of records this API query can return?",
    "What would change if we altered the query string or page size?",
    "Which fields did we drop when flattening JSON into a table?",
    "How would rate limits or authentication change this workflow?",
    "What could this dataset not tell us about Wikipedia or the DSA?",
]

for question in questions:
    print("-", question)
