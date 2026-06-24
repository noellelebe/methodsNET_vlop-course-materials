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

import os
from pathlib import Path
from pprint import pprint

import pandas as pd
import requests
from bs4 import BeautifulSoup


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
    # srlimit is the number of search results requested per API response, not the
    # total number of results in the whole dataset. We use 5 only because this is
    # a classroom inspection run: the response is small enough to read by eye.
    # In a real project, page size should be chosen based on API limits,
    # reliability, server load, and the research question.
    "srlimit": 50,
    # format="json" asks for machine-readable JSON rather than XML or another
    # response format. JSON is what response.json() expects below.
    "format": "json",
    # formatversion=2 makes the JSON structure a bit simpler and more modern:
    # lists are returned as lists, and some older compatibility wrappers are
    # removed. This is a reproducibility choice because it changes response shape.
    "formatversion": 2,
}

# srlimit/page_size = how many results per batch
# sroffset = next starting point, provided by Wikipedia
# pages = how many batches we choose to collect

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

print(response.headers.get("content-type"))

# If content-type is application/json, use .json(). If content-type is text/html
# or text/plain when you expected JSON, inspect response.text before continuing:
# the server may be returning an error page, an authentication warning, or a
# rate-limit message rather than data.

payload = response.json()

# response.json() turns the JSON text into Python dictionaries and lists. pprint
# makes that nested structure easier to inspect than a single long print line.
pprint(payload)

# Discussion prompt:
# What fields are metadata about the API response, and what fields describe
# actual search results?

for item in payload["query"]["search"]:
    # pprint(item)
    pprint(item.keys())

for item in payload["query"]["search"]:
    print(list(item))

print(set().union(*(item.keys() for item in payload["query"]["search"])))

# %% 4. Flatten one page of JSON search results into rows

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

pprint(rows)


# pandas.DataFrame converts a list of row dictionaries into a table. Each
# dictionary key becomes a column, and each dictionary becomes a row.
df = pd.DataFrame(rows)
print(df)

for a in df.snippet:
    print(a, '\n')

# %% 5. Follow the continuation token for a second page

# Many APIs do not use page=2. They use a continuation token or cursor returned
# by the previous response. If we ignore this, we silently collect only the first
# page of a larger result set.
continuation = payload.get("continue", {})
print("Continuation object:", continuation)


# {**params, **continuation} creates a new dictionary containing the original
# query parameters plus the continuation fields returned by the API. If both
# dictionaries contained the same key, the continuation value would win.

# Important: srlimit=5 still applies. The continuation fields do not increase
# the page size; they tell MediaWiki to return the next slice of 5 results.
params_page_2 = {**params, **continuation}
response_2 = requests.get(API_URL, params=params_page_2, headers=headers, timeout=30)
payload_2 = response_2.json()

continuation_2 = payload_2.get("continue", {})
print("Continuation object:", continuation_2)
print(response_2.url) # API request URL, NOT real wikipedia url


# Printing only len(payload_2["query"]["search"]) is not very informative here:
# if there are at least 5 more matches, it will be 5 because we set srlimit=5.
# The more useful teaching check is whether page 2 contains different records.
page_1_ids = [item["pageid"] for item in payload["query"]["search"]]
page_2_ids = [item["pageid"] for item in payload_2["query"]["search"]]

print("Page 1 IDs:", page_1_ids)
print("Page 2 IDs:", page_2_ids)
print("Overlap between page 1 and page 2:", set(page_1_ids) & set(page_2_ids))

print("\n Page 1 titles:")
for item in payload["query"]["search"]:
    print("-", item["title"])
    print("-", item["pageid"])

print("\nPage 2 titles:")
for item in payload_2["query"]["search"]:
    print("-", item["title"])
    print("-", item["pageid"])

# GET ARTICLE URLS:
page_url = []

for item in payload_2["query"]["search"]:
    page_url.append(f"https://en.wikipedia.org/?curid={item['pageid']}")


page_url = f"https://en.wikipedia.org/?curid={item['pageid']}"

# %% 6. Scale the same idea for a real collection

# The 5 + 5 example above is intentionally tiny. It is for understanding the
# mechanics of pagination, not for producing a meaningful research dataset.
#
# A real collection would usually set:
# - a larger page_size, if the API allows it;
# - a deliberate max_pages value;
# - stopping rules tied to the research question;
# - logging for errors, rate limits, and empty pages.
#
# Example:
#   page_size = 50
#   max_pages = 20
#   maximum requested results = 50 * 20 = 1000
#
# That still does not mean "all relevant Wikipedia pages." It means "up to 1000
# API search results returned by this query under these API settings."
real_run_example = {
    "query": "digital services act",
    "page_size": 50,
    "max_pages": 20,
    "maximum_requested_results": 50 * 20,
}

pprint(real_run_example)


# %% 7. From a search result to one individual Wikipedia page

# Search results are useful discovery objects, but they are not the page itself.
# Each search result gives us identifiers that can be used to ask for the full
# page, a summary, metadata, or a browser URL.
first_result = rows[0]

# pageid is the safest bridge from the search result to a page-level request
# because it is a stable numeric identifier. Titles are more readable, but they
# can change when pages are renamed.
page_id = first_result["pageid"]
page_title = first_result["title"]

print("First search result:")
print("pageid:", page_id)
print("title:", page_title)

# The curid URL is a normal browser URL that opens the page identified by
# pageid. This is useful for inspection and citation, but for reproducible data
# collection we usually prefer an API request because its response structure is
# more predictable than a web page's HTML.
page_browser_url = f"https://en.wikipedia.org/?curid={page_id}"
print("Browser URL:", page_browser_url)


# %% 8. Retrieve page-level content through the API

# Here we ask MediaWiki for information about the individual page, not for more
# search results. The switch from list="search" to prop="info|extracts" changes
# the meaning of the request:
# - list="search" returns records matching a query;
# - prop="info|extracts" returns properties of page(s) we already identified.
page_params = {
    # action="query" is still the general MediaWiki read-data action.
    "action": "query",
    # prop requests page properties instead of a list of search results.
    # "info" gives metadata such as the canonical URL when paired with inprop.
    # "extracts" gives a plain-text or limited-HTML summary of the page content.
    # "prop": "info|extracts",
    "prop": "extlinks",
    # pageids tells the API exactly which page we want. Multiple page IDs can be
    # requested as a pipe-separated string such as "123|456|789".
    "pageids": page_id,
    # inprop="url" asks the info module to include fullurl in the response.
    # Without it, we would get metadata but not the canonical page URL.
    "inprop": "url",
    # exintro asks for the lead section only. This is usually enough for a
    # classroom example and avoids pretending that a summary is the full article.
    "exintro": 1,
    # explaintext asks for plain text rather than HTML. This makes the result
    # easier to read, but it removes links and formatting that may matter in some
    # research designs.
    "explaintext": 1,
    # exchars limits the extract length. It is a teaching/debugging limit, not a
    # substantive sampling rule.
    "exchars": 1200,
    "format": "json",
    "formatversion": 2,
}

page_response = requests.get(API_URL, params=page_params, headers=headers, timeout=30)
page_response.raise_for_status()
page_payload = page_response.json()

# With formatversion=2, pages are returned as a list. Because we requested one
# pageid, the first list element is our page-level record.
page_record = page_payload["query"]["pages"][0]

print("Page-level API URL:")
print(page_response.url)

print("\nPage-level fields:")
print(page_record.keys())

print("\nTitle from page-level API:")
print(page_record.get("title"))

print("\nCanonical page URL from page-level API:")
print(page_record.get("fullurl"))

print("\nLead extract from page-level API:")
print(page_record.get("extract"))

for key in page_record.keys():
    print(key)
    print(page_record.get(str(key)))

## Other content

# 1. External links

external_links_params = {
    # This is still a read-only query request to the same MediaWiki endpoint.
    "action": "query",
    # prop="extlinks" asks for external links used on the page. These are URLs
    # pointing away from Wikipedia, for example to EU institutions, news sites,
    # PDFs, reports, or other web pages cited in the article.
    "prop": "extlinks",
    # We use the same page_id as above, so the unit of analysis is still the
    # individual Wikipedia page selected from the search results.
    "pageids": page_id,
    # inprop belongs to prop="info", not prop="extlinks". Leaving it here does
    # not help this request; it is useful to show students that parameters are
    # module-specific and should be checked against the documentation.
    "inprop": "url",
    # ellimit controls how many external links MediaWiki returns. Without a
    # limit, APIs often return only a default number of records.
    "ellimit": "max",
    "format": "json",
    "formatversion": 2,
}

# This request returns page-level external-link metadata, not article text.
external_links_response = requests.get(API_URL, params=external_links_params, headers=headers, timeout=30)
external_links_response.raise_for_status()
external_links_payload = external_links_response.json()

# With formatversion=2, pages are a list of page dictionaries. Since we requested
# one pageid, the first element is the page record we need.
external_links_record = external_links_payload["query"]["pages"][0]
external_links_record.keys()

# extlinks is a list of dictionaries, usually one dictionary per external URL.
print(external_links_record.get("extlinks"))

# Use a default empty list so the code still works if a page has no external
# links or if the API response does not include the extlinks field.
external_links = external_links_record.get("extlinks", [])

external_link_rows = []

for link in external_links:
    # This is the "long" table format: one row per external URL. It is good when
    # you want to count, filter, or analyze links as separate observations.
    external_link_rows.append({
        "pageid": external_links_record.get("pageid"),
        "page_title": external_links_record.get("title"),
        "external_url": link.get("url"),
    })

external_links_df = pd.DataFrame(external_link_rows)

print(external_links_df)

# OR one entry with a list of links in the external_links column. This "wide"
# format is useful when one row should represent one Wikipedia page.

external_urls = [
    # Keep only actual URL strings. If a malformed link record has no "url" key,
    # the if condition below drops it instead of saving None.
    link.get("url")
    for link in external_links
    if link.get("url")
]

external_links_row = {
    # These fields identify which Wikipedia page the list belongs to.
    "pageid": external_links_record.get("pageid"),
    "page_title": external_links_record.get("title"),
    # This column contains a Python list. That is convenient in memory and in
    # JSON, but CSV will store it as a string representation of a list.
    "external_links": external_urls,
    # A count column is often useful for quick data-quality checks.
    "external_link_count": len(external_urls),
}

external_links_df = pd.DataFrame([external_links_row])

print(external_links_df)

# 2. Images
# 2.1. get image titles

image_params = {
    # This request asks which files/images are used on the article page.
    "action": "query",
    # prop="images" returns file titles such as "File:Example.jpg". It does not
    # yet return the direct image URL; that requires a second imageinfo request.
    "prop": "images",
    "pageids": page_id,
    # imlimit controls how many image/file records are returned, not image size.
    # "max" asks the API for as many as it allows in one response.
    "imlimit": "max",
    "format": "json",
    "formatversion": 2,
}

# First image request: pageid -> file titles.
image_response = requests.get(API_URL, params=image_params, headers=headers, timeout=30)
image_response.raise_for_status()
image_payload = image_response.json()

image_record = image_payload["query"]["pages"][0]
image_record.keys()

# If a page has no images, .get("images", []) returns an empty list so the next
# line produces an empty list instead of a TypeError.
images = image_record.get("images", [])
image_titles = [image["title"] for image in images]

# 2.2. get image info (i.e., url)

image_info_params = {
    # Second image request: file titles -> file URLs and file metadata.
    "action": "query",
    # prop="imageinfo" returns metadata about files, such as URL, dimensions, and
    # MIME type.
    "prop": "imageinfo",
    # MediaWiki expects multiple titles as one string separated by |.
    "titles": "|".join(image_titles),
    # iiprop selects which image metadata fields to return. Here we ask for:
    # - url: the direct file URL;
    # - size: file size and dimensions;
    # - mime: file type, such as image/jpeg or image/svg+xml.
    "iiprop": "url|size|mime",
    "format": "json",
    "formatversion": 2,
}

image_info_response = requests.get(API_URL, params=image_info_params, headers=headers, timeout=30)
image_info_response.raise_for_status()

image_info_payload = image_info_response.json()

image_rows = []

for file_page in image_info_payload["query"]["pages"]:
    # imageinfo is also a list because files can have multiple revisions. We take
    # the first item returned by the API for this simple teaching example.
    info = file_page.get("imageinfo", [{}])[0]
    # print(file_page["title"])
    # print(info.get("url"))
    # print(info.get("mime"))
    image_rows.append({
        # file_title is the MediaWiki file-page title.
        "file_title": file_page.get("title"),
        # image_url is the direct downloadable file URL.
        "image_url": info.get("url"),
        # MIME type tells us whether this is a JPEG, PNG, SVG, etc.
        "mime": info.get("mime"),
        # Width, height, and size are useful for filtering and auditing images.
        "width": info.get("width"),
        "height": info.get("height"),
        "size": info.get("size"),
    })

image_df = pd.DataFrame(image_rows)

# Use the same data/processed convention as the rest of the course materials.
outdir = Path("data")
processed_dir = outdir / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

# Save image metadata separately from the actual image files. For many research
# projects, URLs and metadata are enough; downloading files is a further choice.
image_csv_path = processed_dir / "wikipedia_image_urls.csv"
image_df.to_csv(image_csv_path, index=False)

print("Saved image metadata to:", image_csv_path)

# Save the external-link table as its own CSV. The variable currently contains
# the wide one-row-per-page version created above.
external_links_path = processed_dir / "external_links.csv"
external_links_df.to_csv(external_links_path, index=False)

print("Saved external links to:", external_links_path)


# 2.3. Download the Actual Image Files

from urllib.parse import urlparse
import time

# Downloading image bytes is a different step from collecting image metadata.
# It creates larger files, may raise licensing questions, and should be done only
# if the research question actually needs image content.
image_dir = Path("data/raw/images")
image_dir.mkdir(parents=True, exist_ok=True)

for row in image_rows:
    image_url = row["image_url"]

    # Some file records may not have a direct URL. Skip those cleanly.
    if not image_url:
        continue

    # The filename is taken from the URL path, for example something.jpg.
    filename = Path(urlparse(image_url).path).name
    output_path = image_dir / filename

    # This request downloads the binary image content, not JSON.
    image_response = requests.get(image_url, headers=headers, timeout=30)
    image_response.raise_for_status()

    # write_bytes is used for binary files such as images. write_text would be
    # wrong here because image files are not plain text.
    output_path.write_bytes(image_response.content)

    print("Saved:", output_path)

    # Pause between file downloads so the script does not make rapid-fire
    # requests to Wikimedia file servers.
    time.sleep(1)

# %% 10. A second platform API example: YouTube Data API

# Wikipedia is unusually open. Many platform APIs require authentication, quota
# management, and project registration. YouTube still offers an official Data
# API, but students need an API key from a Google Cloud project to run this cell.
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube_params = {
    # part="snippet" tells YouTube which section of the search resource to
    # return. For search.list, snippet contains the title, description, channel,
    # and publication time shown in search-result metadata.
    "part": "snippet",
    # q is the search query. As with Wikipedia's srsearch, this is a research
    # design choice because it defines what can enter the dataset.
    "q": "digital services act",
    # type="video" excludes channel and playlist results. Without this, the
    # endpoint can return a mixed set of resource types.
    "type": "video",
    # maxResults is YouTube's page size. The documented maximum is 50; a small
    # value is better for classroom inspection.
    "maxResults": 5,
    # order controls ranking. "relevance" is the default; "date" would answer a
    # different question and produce a different dataset.
    "order": "relevance",
    # key authenticates the request. We add it only if an environment variable is
    # present so the script can be shared without exposing a private API key.
    "key": YOUTUBE_API_KEY,
}

if YOUTUBE_API_KEY:
    youtube_response = requests.get(
        YOUTUBE_SEARCH_URL,
        params=youtube_params,
        timeout=30,
    )
    youtube_response.raise_for_status()
    youtube_payload = youtube_response.json()

    print("YouTube request URL:")
    print(youtube_response.url)

    youtube_rows = []
    for item in youtube_payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})

        youtube_rows.append(
            {
                # video_id is the platform identifier needed to retrieve more
                # video-level metadata later with videos.list.
                "video_id": video_id,
                # The watch URL is useful for inspection, citation, and manual
                # validation, but it is not the same as an API data record.
                "watch_url": f"https://www.youtube.com/watch?v={video_id}",
                "title": snippet.get("title"),
                "channel_id": snippet.get("channelId"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description"),
            }
        )

    youtube_df = pd.DataFrame(youtube_rows)
    print(youtube_df[["video_id", "title", "channel_title", "published_at"]])

    # YouTube pagination uses nextPageToken, not MediaWiki's "continue" object.
    # The concept is the same: the API tells us which token to send next.
    print("Next page token:", youtube_payload.get("nextPageToken"))

    # Search results are not full video records. To move from search-result
    # metadata to individual video-level metadata, we pass the video IDs into a
    # second endpoint: videos.list.
    video_ids = [row["video_id"] for row in youtube_rows if row["video_id"]]

    video_params = {
        # part selects which blocks of video-level metadata to return.
        # snippet repeats descriptive metadata, statistics adds engagement counts,
        # and contentDetails adds duration and other media-level information.
        "part": "snippet,statistics,contentDetails",
        # id accepts a comma-separated list of video IDs. This is the bridge from
        # the search endpoint to the video endpoint.
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    video_response = requests.get(
        YOUTUBE_VIDEOS_URL,
        params=video_params,
        timeout=30,
    )
    video_response.raise_for_status()
    video_payload = video_response.json()

    video_rows = []
    for item in video_payload.get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        video_rows.append(
            {
                "video_id": item.get("id"),
                "title": snippet.get("title"),
                "channel_id": snippet.get("channelId"),
                "published_at": snippet.get("publishedAt"),
                # viewCount, likeCount, and commentCount are returned as strings.
                # Convert them later if you need numeric analysis.
                "view_count": statistics.get("viewCount"),
                "like_count": statistics.get("likeCount"),
                "comment_count": statistics.get("commentCount"),
                # duration is an ISO 8601 duration string such as PT3M12S, not a
                # number of seconds. Parsing it is a separate cleaning step.
                "duration": content_details.get("duration"),
            }
        )

    video_df = pd.DataFrame(video_rows)
    print("\nVideo-level metadata:")
    print(video_df)
else:
    print("Skipping YouTube request because YOUTUBE_API_KEY is not set.")
    print("In Terminal, set it before opening/running Python, for example:")
    print("export YOUTUBE_API_KEY='paste-your-key-here'")


# %% 11. A small OpenAI API example for later AI-assisted workflows

# People often say "the ChatGPT API", but technically this is the OpenAI API.
# ChatGPT is the consumer/product interface; API scripts call endpoints such as
# /v1/responses and receive structured JSON back.
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# The OpenAI docs currently point learners toward the Responses API for general
# model responses. We keep the model in an environment variable so the course can
# update it without editing the script if model availability changes.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

openai_body = {
    # model selects which model should answer. This affects cost, latency,
    # accuracy, and sometimes available features.
    "model": OPENAI_MODEL,
    # input is the user-facing task. In later course sessions this might be a
    # prompt asking the model to classify text, draft API queries, or summarize
    # collection logs.
    "input": (
        "In one sentence, explain why API search results should not be treated "
        "as a complete sample of all relevant online content."
    ),
}

if OPENAI_API_KEY:
    openai_headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    openai_response = requests.post(
        OPENAI_RESPONSES_URL,
        headers=openai_headers,
        json=openai_body,
        timeout=60,
    )
    openai_response.raise_for_status()
    openai_payload = openai_response.json()

    print("OpenAI response id:", openai_payload.get("id"))
    print("OpenAI response status:", openai_payload.get("status"))

    # The full response object contains metadata, output items, token usage, and
    # model information. Inspecting the full JSON is useful before deciding what
    # to save in a research workflow.
    pprint(openai_payload)

    # The model's visible answer is nested inside output items. This small loop is
    # deliberately defensive because response objects can contain tool calls or
    # other output item types in addition to plain text.
    text_parts = []
    for output_item in openai_payload.get("output", []):
        for content_item in output_item.get("content", []):
            if content_item.get("type") == "output_text":
                text_parts.append(content_item.get("text", ""))

    print("\nModel text:")
    print("\n".join(text_parts) if text_parts else "No plain text output found.")
else:
    print("Skipping OpenAI request because OPENAI_API_KEY is not set.")
    print("In Terminal, set it before opening/running Python, for example:")
    print("export OPENAI_API_KEY='paste-your-key-here'")
    print("Optional: export OPENAI_MODEL='gpt-5.5'")


# %% 12. Collect several pages in a reusable function

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


# %% 13. Save raw, processed, and provenance files

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


# %% 14. Teaching prompts

questions = [
    "What exactly is the population of records this API query can return?",
    "What would change if we altered the query string or page size?",
    "Which fields did we drop when flattening JSON into a table?",
    "When should we retrieve page-level data through an API, and when might scraping be necessary?",
    "How does YouTube's pageToken pagination compare to MediaWiki's continuation object?",
    "What extra risks appear when an API requires credentials or sends data to an AI model?",
    "How would rate limits or authentication change this workflow?",
    "What could this dataset not tell us about Wikipedia or the DSA?",
]

for question in questions:
    print("-", question)
