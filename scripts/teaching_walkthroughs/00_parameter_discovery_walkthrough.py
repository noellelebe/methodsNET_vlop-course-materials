"""Teaching walkthrough: discovering parameters before collecting data.

This file should be taught before the API, scraping, DSA, and AI walkthroughs.
The aim is to show students how to find out what options exist before they start
collecting data.

Teaching goals:
1. Learn where parameters, fields, filters, selectors, and flags are documented.
2. Distinguish official parameters from guessed or undocumented ones.
3. Record parameter choices as part of research design.
4. Avoid treating default settings as neutral.
"""

# %% 1. Why parameter discovery matters

# Every collection approach has "knobs":
# - API parameters such as query terms, date windows, page size, and pagination.
# - Scraping selectors such as .post, article, a[href], or data-testid values.
# - Browser automation options such as wait conditions, scroll limits, and clicks.
# - DSA data fields such as category, platform_name, content_type, and dates.
# - Command-line flags such as --start, --end, --input, and --outdir.
# - Python function arguments such as timeout=30 or index=False.
#
# These knobs are methodological choices. They decide what can enter the
# dataset, what is excluded, how much data is collected, and how reproducible the
# workflow will be.

parameter_questions = [
    "Where is this parameter documented?",
    "What values are allowed?",
    "What is the default if we do not set it?",
    "Does changing it change the population of records?",
    "Does it affect ethics, legality, privacy, or server load?",
    "Will we record this choice in provenance?",
]

for question in parameter_questions:
    print("-", question)


# %% 2. API parameters: start from official documentation

# APIs usually have documented endpoints and parameters. For MediaWiki, the API
# has a built-in help system. The URL below asks the API to describe the search
# module rather than to return search results.

import requests


API_HELP_URL = "https://en.wikipedia.org/w/api.php"

help_params = {
    # action=help asks MediaWiki for API help text.
    "action": "help",
    # modules=query+search asks specifically for documentation about the search
    # module used later in 01_api_collection_walkthrough.py.
    "modules": "query+search",
}

help_response = requests.get(API_HELP_URL, params=help_params, timeout=30)
help_response.raise_for_status()

# The help response is text/html rather than JSON. We print a short excerpt so
# students can see that APIs sometimes expose their own documentation.
print(help_response.url)
print(help_response.text[:1500])

# Teaching note:
# For many APIs, parameter discovery starts in human-readable docs, OpenAPI
# schemas, client-library help pages, or examples. Do not infer parameters from
# an AI model or a random blog post without checking official documentation.


# %% 3. API parameters: document the options we choose

# A small parameter inventory makes the research design explicit. It is not code
# required by the API; it is documentation for humans.

api_parameter_inventory = [
    {
        "parameter": "action",
        "example_value": "query",
        "meaning": "which API operation to run",
        "why_we_set_it": "we want to read/query wiki data",
    },
    {
        "parameter": "list",
        "example_value": "search",
        "meaning": "which query module to use",
        "why_we_set_it": "we want search-result records",
    },
    {
        "parameter": "srsearch",
        "example_value": "digital services act",
        "meaning": "the search string",
        "why_we_set_it": "defines the substantive population of candidate pages",
    },
    {
        "parameter": "srlimit",
        "example_value": 5,
        "meaning": "number of results requested per page",
        "why_we_set_it": "small value for inspectable teaching output",
    },
    {
        "parameter": "format",
        "example_value": "json",
        "meaning": "response format",
        "why_we_set_it": "Python can parse JSON with response.json()",
    },
]

for row in api_parameter_inventory:
    print(row)


# %% 4. Scraping parameters: selectors are parameters too

# Scraping rarely has a formal parameter list. Instead, the key choices are often
# selectors. A selector tells the parser which parts of the HTML become records
# or fields.
#
# These examples are from https://quotes.toscrape.com/:

selector_inventory = [
    {
        "selector": ".quote",
        "meaning": "every element with class='quote'",
        "role": "one repeated record container",
        "risk": "breaks if the site renames the CSS class",
    },
    {
        "selector": ".text",
        "meaning": "element with class='text' inside each quote block",
        "role": "quote text field",
        "risk": "captures only visible excerpt, not hidden metadata",
    },
    {
        "selector": ".author",
        "meaning": "element with class='author' inside each quote block",
        "role": "author field",
        "risk": "can become sensitive on real platforms with user accounts",
    },
    {
        "selector": "a[href]",
        "meaning": "all link elements with an href attribute",
        "role": "link extraction",
        "risk": "collects navigation links as well as content links",
    },
]

for row in selector_inventory:
    print(row)

# Teaching note:
# In real platform scraping, selector discovery should be documented with raw
# HTML snapshots, screenshots, and notes about why a selector is stable enough.


# %% 5. Browser automation parameters: what did the browser do?

# Browser automation adds parameters that are not visible in a static HTML
# parser. These should be documented because they shape the observed page state.

browser_parameter_inventory = [
    {
        "parameter": "headless",
        "example_value": True,
        "meaning": "whether the browser runs invisibly",
        "methodological_issue": "headless and visible browsers can sometimes behave differently",
    },
    {
        "parameter": "wait_until",
        "example_value": "networkidle",
        "meaning": "when Playwright considers page loading finished",
        "methodological_issue": "waiting too little can miss content; waiting too much can be slow",
    },
    {
        "parameter": "scrolls",
        "example_value": 2,
        "meaning": "how many times the script scrolls the page",
        "methodological_issue": "scroll limits define how much infinite-scroll content can appear",
    },
    {
        "parameter": "timeout",
        "example_value": 30,
        "meaning": "how long to wait before giving up",
        "methodological_issue": "timeouts can create systematic missingness on slow pages",
    },
]

for row in browser_parameter_inventory:
    print(row)


# %% 6. DSA and platform-tool parameters: schema first

# For DSA transparency data and platform research tools, students should look
# for schemas, data dictionaries, data catalogues, API docs, and request forms.
# The "parameters" may be fields, filters, date windows, access modalities, or
# eligibility criteria.

dsa_parameter_inventory = [
    {
        "field_or_filter": "platform_name",
        "meaning": "which platform submitted the record",
        "question_to_ask": "Are platform names standardized across files?",
    },
    {
        "field_or_filter": "content_date",
        "meaning": "date associated with content or moderation record",
        "question_to_ask": "Is this content creation, detection, decision, or reporting date?",
    },
    {
        "field_or_filter": "category",
        "meaning": "reported statement category",
        "question_to_ask": "Are categories comparable across platforms?",
    },
    {
        "field_or_filter": "automated_decision",
        "meaning": "whether automation made or contributed to the decision",
        "question_to_ask": "How does the platform define partial vs full automation?",
    },
    {
        "field_or_filter": "date window",
        "meaning": "start and end dates for download or request",
        "question_to_ask": "Does the date window align with the research question?",
    },
]

for row in dsa_parameter_inventory:
    print(row)


# %% 7. Command-line scripts: use --help

# Command-line scripts should expose their own parameters. The runnable scripts
# in this repository use argparse, so students can ask each script what arguments
# it accepts by running it with --help in the terminal.

help_commands = [
    'python "scripts/runnable_workflows/01_api_wikipedia.py" --help',
    'python "scripts/runnable_workflows/03_static_scraper.py" --help',
    'python "scripts/runnable_workflows/05_dsa_transparency_workflow.py" --help',
    'python "scripts/runnable_workflows/06_data_quality_audit.py" --help',
]

for command in help_commands:
    print(command)

# Teaching note:
# --help is one of the easiest ways to show students that scripts have declared
# parameters. It also reinforces that parameters should not be hidden inside code
# if students are expected to reproduce or adapt a workflow.


# %% 8. Python functions: inspect signatures and help

# Python itself can show the arguments accepted by functions. This is useful for
# packages such as pandas, requests, BeautifulSoup, and Playwright.

import inspect
import pandas as pd


# inspect.signature() prints the function's argument names and default values.
# Here, it shows that DataFrame.to_csv has many options beyond just the file path.
print(inspect.signature(pd.DataFrame.to_csv))

# help() opens fuller documentation. In an interactive session, students can run:
# help(pd.DataFrame.to_csv)


# %% 9. Parameter log template

# This template can be copied into project notes, a README, or a provenance file.

parameter_log_template = [
    {
        "name": "[parameter or field name]",
        "where_found": "[official docs / schema / --help / page inspection]",
        "allowed_values": "[values or type]",
        "chosen_value": "[value used]",
        "default_if_unset": "[default or unknown]",
        "why_this_choice": "[methodological reason]",
        "risk_or_limitation": "[what this choice excludes or distorts]",
    }
]

print(parameter_log_template)
