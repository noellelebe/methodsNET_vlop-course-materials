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

# These parameters are sent after the ? in the API URL. Together they define
# both the API task and the small population of records we can receive back.
params = {
    # action="query" tells MediaWiki that we want to ask for existing wiki data.
    # Other MediaWiki actions can edit pages, parse wikitext, or log in; this
    # walkthrough only reads data.
    "action": "query",
    # list="search" says that the query action should return search results.
    # Without this, the API would not know which query module to run.
    "list": "search",
    # srsearch is the actual search string. Changing this to "platform
    # governance" or "misinformation" changes the records that can enter the
    # dataset, just as changing a search term in a database search would.
    "srsearch": "digital services act",
    # srlimit is the number of search results requested on this page of results.
    # We use 5 so students can inspect the response by eye. Larger values collect
    # more rows per request but make debugging harder.
    "srlimit": 5,
    # format="json" asks for machine-readable JSON rather than XML or another
    # response format. JSON is what response.json() expects below.
    "format": "json",
    # formatversion=2 makes the JSON structure a bit simpler and more modern:
    # lists are returned as lists, and some older compatibility wrappers are
    # removed. This is a reproducibility choice because it changes response shape.
    "formatversion": 2,
}

headers = {
    # A User-Agent identifies the script. Many APIs ask researchers to identify
    # automated requests instead of appearing as a generic Python client.
    "User-Agent": "methodsNET-VLOP-course/1.0 teaching walkthrough",
}

# requests.get() sends an HTTP GET request to API_URL with params encoded into
# the query string and headers attached to the request metadata. timeout=30 means
# Python should stop waiting after 30 seconds instead of hanging indefinitely.
response = requests.get(API_URL, params=params, headers=headers, timeout=30)

# response.url shows the final URL after requests has encoded the params
# dictionary. This is useful for teaching because students can see exactly what
# was sent to the API.
print(response.url)
# status_code is the HTTP response status. 200 means the request succeeded; 404,
# 429, or 500-series codes would require different handling.
print(response.status_code)


# %% 3. Inspect the JSON response before flattening it

payload = response.json()

# response.json() turns the JSON text into Python dictionaries and lists. pprint
# makes that nested structure easier to inspect than a single long print line.
pprint(payload)

# Discussion prompt:
# What fields are metadata about the API response, and what fields describe
# actual search results?


# %% 4. Flatten one page into rows

rows = []

# payload["query"]["search"] is the list of search-result records returned by
# MediaWiki. Each item is one search result, not one full Wikipedia article.
for item in payload["query"]["search"]:
    # This is where we decide which source fields become columns. That decision
    # should be documented because it is a lossy transformation.
    row = {
        # pageid is MediaWiki's stable numeric page identifier. It is better for
        # joins than the title because titles can be renamed.
        "pageid": item.get("pageid"),
        # title is the human-readable page title returned by the search result.
        "title": item.get("title"),
        # timestamp is when the page was last edited according to this search
        # result record, not when our script collected the data.
        "timestamp": item.get("timestamp"),
        # wordcount is a rough size measure for the page. It can be useful for
        # filtering, but it is not a measure of importance.
        "wordcount": item.get("wordcount"),
        # snippet is a short HTML-marked search excerpt showing why the result
        # matched. It is not the full article text and should not be treated as
        # article content.
        "snippet": item.get("snippet"),
    }
    rows.append(row)

# pandas.DataFrame converts a list of row dictionaries into a table. Each
# dictionary key becomes a column, and each dictionary becomes a row.
df = pd.DataFrame(rows)
print(df)


# %% 5. Follow the continuation token for a second page

# Many APIs do not use page=2. They use a continuation token or cursor returned
# by the previous response. If we ignore this, we silently collect only the first
# page of a larger result set.
continuation = payload.get("continue", {})
print("Continuation object:")
pprint(continuation)

# {**params, **continuation} creates a new dictionary containing the original
# query parameters plus the continuation fields returned by the API. If both
# dictionaries contained the same key, the continuation value would win.
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
    # continuation starts empty for the first request. After each response, it is
    # replaced with the API's "continue" object if another page exists.
    continuation = {}

    for page_number in range(1, max_pages + 1):
        # request_params is rebuilt inside the loop because the continuation
        # token changes from page to page.
        request_params = {
            "action": "query",
            "list": "search",
            # Here srsearch comes from the function argument, so the function can
            # be reused for different queries without editing the function body.
            "srsearch": query,
            # page_size controls the number of results requested per API call.
            "srlimit": page_size,
            "format": "json",
            "formatversion": 2,
            # On the first loop this contributes nothing. On later loops it adds
            # continuation keys such as sroffset and continue.
            **continuation,
        }

        r = requests.get(API_URL, params=request_params, headers=headers, timeout=30)
        # raise_for_status() turns HTTP error statuses into Python exceptions.
        # That is better than silently saving an error page as if it were data.
        r.raise_for_status()
        page_payload = r.json()

        # raw_pages stores evidence about each request. The request_url matters
        # because it records the exact parameters and continuation token used.
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
                    # query and page_number are not from the API item itself; we
                    # add them so each processed row keeps collection context.
                    "query": query,
                    "page_number": page_number,
                    "pageid": item.get("pageid"),
                    "title": item.get("title"),
                    "timestamp": item.get("timestamp"),
                    "wordcount": item.get("wordcount"),
                    "snippet": item.get("snippet"),
                }
            )

        # If the response has no continue object, the API has no next page for
        # this query, so the loop stops even if max_pages was larger.
        continuation = page_payload.get("continue", {})
        if not continuation:
            break

    return rows, raw_pages


rows, raw_pages = collect_wikipedia_search("digital services act", max_pages=2)
df = pd.DataFrame(rows)
print(df[["page_number", "title", "wordcount"]])


# %% 7. Save raw, processed, and provenance files

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
# The conditional path above keeps the example usable whether students run it
# from the repository root or from inside scripts/teaching_walkthroughs.
raw_dir = outdir / "raw"
processed_dir = outdir / "processed"
reports_dir = outdir / "reports"

# parents=True creates missing parent folders such as data/ and data/raw/.
# exist_ok=True means it is not an error if the folders already exist.
raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

# File names describe both the source and the processing stage. This helps avoid
# confusing raw evidence with cleaned analysis tables.
raw_path = raw_dir / "walkthrough_wikipedia_raw.json"
processed_path = processed_dir / "walkthrough_wikipedia_processed.csv"
provenance_path = reports_dir / "walkthrough_wikipedia_provenance.json"

# For compactness in a teaching walkthrough, we use pandas JSON writing. In a
# large project, JSONL is often better because each line can be streamed.
pd.Series(raw_pages).to_json(raw_path, orient="values", indent=2)
df.to_csv(processed_path, index=False)

provenance = {
    # source and endpoint identify the access route.
    "source": "MediaWiki API",
    "endpoint": API_URL,
    # query and max_pages capture the main collection parameters.
    "query": "digital services act",
    "max_pages": 2,
    # These paths point from the provenance note back to the actual outputs.
    "raw_output": str(raw_path),
    "processed_output": str(processed_path),
    # A method_note records an interpretation warning, not a technical setting.
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
