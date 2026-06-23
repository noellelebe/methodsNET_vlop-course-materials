# Day 1: APIs and Platform Data Access

## What This Day Is About

The first day introduces the central idea of the course: platform data are not
simply "out there" waiting to be collected. They become available through access
routes. An API, a scraped web page, a DSA transparency database, and a platform
research portal all reveal different parts of a platform and hide others.

Today focuses on APIs because they are a good first access route for teaching.
They are structured, inspectable, and usually easier to reproduce than manual
copying or browser-based scraping. At the same time, APIs are not neutral. They
are designed by platform owners or data providers. Their parameters, rate
limits, field choices, authentication systems, and pagination rules shape what
researchers can know.

The aim is not only to learn how to "call an API." The aim is to learn how to
turn an API call into a documented research method.

## 1. Platform Data Access Regimes

Platform researchers rarely access "the platform itself." They access traces
created by specific technical and institutional arrangements. A useful first
distinction is between several access regimes.

Open or semi-open APIs provide structured responses to documented requests. A
researcher sends an endpoint, parameters, headers, and sometimes credentials.
The server returns data, often as JSON. Examples include MediaWiki, YouTube Data
API, Reddit API, or platform-specific research APIs.

Web scraping extracts data from web pages. Scraping is useful when relevant
information is visible in public interfaces but unavailable through an API.
However, scraping is more fragile and raises legal and ethical questions that
must be handled explicitly.

Platform research tools are controlled access systems provided by platforms,
such as Meta Content Library or TikTok Research API. They may be more official
than scraping, but they still impose eligibility rules, query restrictions,
missing fields, and platform-defined scopes.

DSA mechanisms create legal routes for researchers to request or access data
from designated Very Large Online Platforms and Very Large Online Search
Engines. These mechanisms are important, but they are procedural and scoped.
They require careful request drafting, proportionality, data-security planning,
and a clear link to systemic risks.

Transparency databases and ad repositories provide regulator- or
platform-produced datasets. They are valuable because they create public data
infrastructures, but they must still be audited. A statement of reasons in the
DSA Transparency Database is not the same thing as all moderation activity.

The practical lesson is that access route is part of method. A dataset is never
just "Twitter data," "TikTok data," or "Wikipedia data." It is data collected
through a particular interface, under particular rules, at a particular time.

## 2. What an API Is

An Application Programming Interface, or API, is a structured way for software
to communicate with another system. For data collection, an API request usually
has several parts.

The word "interface" is important. An API is not the database, not the platform,
and not the full internal system. It is a controlled surface through which one
software system makes certain actions available to another. A platform may store
far more information internally than its API exposes. The API defines which
operations are allowed, which parameters can be used, which fields can be
returned, how many results can be requested, and who is authorized to ask.

This means that an API is both technical infrastructure and a methodological
filter. If a platform API does not expose deleted content, private moderation
metadata, impression counts, or recommender-system features, then an API-based
study cannot directly analyze those things. The absence of a field in an API
response does not mean the platform does not have that information. It means the
information is not available through that interface.

### 2.1 API vs. REST API

API is the broad category. A REST API is one common kind of API.

An API can be any structured interface for software interaction. The `pandas`
function `read_csv()` is part of a library API: Python code calls a function
provided by the pandas package. An operating system has APIs for file access,
networking, windows, and permissions. A database driver has an API for sending
queries. These are APIs, but they are not necessarily web APIs.

A REST API is a web-based API style built around standard web concepts:

- URLs identify resources or operations.
- HTTP methods such as `GET`, `POST`, `PUT`, and `DELETE` describe the type of
  action.
- Parameters specify filters, query terms, formats, limits, or continuation
  tokens.
- Headers provide request metadata such as user agent, authentication, content
  type, or rate-limit handling.
- Responses usually return structured data such as JSON.
- Each request is usually stateless, meaning the request should contain the
  information needed for the server to interpret it.

Many platform data APIs are REST or REST-like APIs. They may not follow every
REST principle perfectly, but they usually use HTTP requests, URLs, parameters,
headers, and JSON responses. For this course, when we say "API collection," we
mostly mean REST-style web API collection.

### 2.2 Client, Server, Database

It helps to visualize an API workflow as three layers.

The client is the program making the request. In this course, the client is
usually your Python script. It builds a URL, attaches parameters and headers,
and sends a request.

The API server receives the request. It checks whether the request is valid,
whether the client is allowed to make it, how many requests have already been
made, what parameters were supplied, and which internal service or database
query should be used. The API server is the gatekeeper.

The database or internal platform system stores records. The client usually does
not query this database directly. The API server queries it, transforms the
result, removes or adds fields, applies limits, and returns a response.

This is why a simple diagram of "client -> REST API -> database" is useful but
also incomplete. It correctly shows that the client does not directly access the
database. But it can make the API look like a transparent pipe. It is not. The
API is an active translator and filter.

### 2.3 HTTP Methods

REST-style APIs often use HTTP methods. The most important method for this
course is `GET`.

`GET` requests retrieve data. A researcher using a public API to search for
Wikipedia pages, retrieve video metadata, or list public records is usually
making `GET` requests. GET requests are normally not supposed to change the
server's data.

`POST` requests send data to a server. They may create a record, submit a job,
send a search body, or request a more complex operation. Some APIs use POST even
for data retrieval when the query is complex or includes a long JSON body.

`PUT` requests usually replace or update a resource. `PATCH` may partially
update a resource. `DELETE` removes a resource. These methods are important in
software engineering, but they are usually not what students should use for
platform data collection unless they are working with their own systems.

For platform research, the method matters ethically. A script that retrieves
public metadata is very different from a script that creates, modifies, or
deletes platform content. Students should know what method their code is using.

### 2.4 Anatomy of an API Request

The endpoint is the URL where the request is sent. In the MediaWiki example, the
endpoint is:

```text
https://en.wikipedia.org/w/api.php
```

Parameters specify what you are asking for. Parameters can define an operation,
a search term, a date range, a language, a page size, or a cursor for
pagination. In the MediaWiki search example, `action=query` says we want to read
data, `list=search` says we want search results, `srsearch=digital services act`
is the search query, and `srlimit=5` requests five results in one response.

Headers are metadata sent with the request. One important header is the
`User-Agent`, which identifies the client. For research scripts, the user agent
should be honest and informative. It should not pretend to be a normal browser
if it is not.

Authentication identifies the user or application. Some APIs are open for basic
queries. Others require API keys, OAuth, institutional credentials, or approved
researcher status. Authentication affects what data can be accessed and how the
request is governed.

The response is what the server sends back. APIs often return JSON, which Python
turns into dictionaries and lists. A response also has a status code. A `200`
usually means success. A `403` means forbidden. A `404` means not found. A `429`
usually means rate limited. A `500`-level response means a server-side problem.

### 2.5 API Responses Are Designed Objects

An API response is not raw reality. It is a designed object. It may contain:

- records that match the query;
- metadata about the query;
- pagination or continuation information;
- warnings or error messages;
- fields selected by the provider;
- fields omitted for privacy, safety, business, legal, or technical reasons.

The structure of a response should be studied before analysis. Which part of the
response contains actual records? Which part contains metadata? Which field is a
stable identifier? Which timestamp is being reported? Are snippets full text or
search excerpts? Are counts exact or approximate?

This is why the first API exercise asks students to inspect the JSON before
turning it into a DataFrame. Premature flattening hides the structure of the
response and makes it easier to misinterpret fields.

## 3. Parameter Discovery

Before collecting data, researchers should ask: what parameters are available?
This is not a trivial technical question. Parameters define the data-generating
process. If an API supports filtering by date, language, content type, account,
region, or moderation category, those choices shape the dataset.

Good sources for parameter discovery include official API documentation, built
in API help pages, OpenAPI schemas, command-line `--help` output, package
documentation, and examples from the data provider. Less reliable sources
include random blog posts, outdated Stack Overflow answers, or AI-generated
suggestions that have not been checked against official documentation.

For MediaWiki, the API itself can return help pages. The parameter-discovery
walkthrough shows how to ask for documentation about the search module. The
important principle is transferable: do not guess the parameters first and read
the documentation later. Start from the documented interface.

A simple parameter log should include the parameter name, where it was found,
allowed values, chosen value, default value if known, reason for the choice, and
the risk or limitation created by that choice.

## 4. JSON and Flattening

JSON is a nested data format. A response may contain metadata, continuation
tokens, search information, and a list of result objects. Researchers often need
to flatten that nested structure into a table. Flattening is useful, but it is
lossy.

For example, a MediaWiki search result may contain `pageid`, `title`,
`timestamp`, `wordcount`, and `snippet`. Selecting these fields creates a table,
but it also excludes other response information. The snippet is not full article
text. The timestamp is not the time of collection. The word count is not a
measure of relevance.

Students should learn to inspect the raw JSON before making a table. The raw
response shows what the API actually returned. The processed table shows what
the researcher chose to keep.

## 5. Pagination

Most APIs do not return all matching data in one response. They return one page
of results and some instruction for how to request the next page. This may be
called a cursor, continuation token, offset, page token, or next URL.

A common beginner mistake is to confuse page size with total dataset size. If
`srlimit=5`, the API returns up to five results in that one response. It does not
mean only five results exist. If the response contains a continuation object,
there are more results available under the same query.

The first collection should be tiny on purpose. Five results are enough to
inspect by eye. The pedagogical goal is to see how request parameters, response
structure, and continuation tokens work. A real research collection would use a
larger page size, a deliberate maximum number of pages, and documented stopping
rules.

The important teaching check is not simply whether page two returns five more
results. It usually will if `srlimit=5` and more matches exist. The useful check
is whether page two contains different records from page one. Comparing page IDs
and titles shows that the continuation token moves the researcher to the next
slice of results.

## 6. Raw, Processed, Reports

A reproducible collection workflow should separate output types.

Raw data are close to the source response. For an API, raw data may be full JSON
responses, request URLs, status codes, and timestamps. Raw data help audit later
processing decisions.

Processed data are analysis-shaped tables. They may be CSV files with selected
columns, cleaned text, parsed dates, or normalized identifiers.

Reports contain documentation: provenance files, audit summaries, codebooks,
logs, and notes about failures.

This structure prevents confusion. A polished CSV is easier to analyze, but the
raw response is often more important for checking whether the researcher
misunderstood the API.

## 7. Provenance

Provenance means documenting how the dataset came to exist. At minimum, an API
provenance note should record the endpoint, query parameters, date and time,
script name, output paths, page size, number of pages, status codes, and known
limitations.

Provenance is not administrative decoration. It is what lets another person
understand, reproduce, and critique the dataset. It is also what lets future you
remember what you actually did.

## End-of-Day Questions

- What access route produced the data?
- Which parameters defined the population of retrievable records?
- What did the API return that you did not keep in the processed table?
- What does page size control, and what does it not control?
- How would a real collection differ from the tiny classroom example?
- What claims would be inappropriate to make from API search results alone?
