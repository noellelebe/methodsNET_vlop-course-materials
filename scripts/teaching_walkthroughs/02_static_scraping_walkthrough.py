"""Teaching walkthrough: static HTML scraping.

Suggested classroom page:
    https://quotes.toscrape.com/

Teaching goals:
1. Distinguish fetching HTML from parsing HTML.
2. Teach CSS selectors as methodological choices.
3. Save raw HTML before extracting a table.
4. Discuss robots.txt, terms, personal data, and proportionality.
"""

# %% 1. Imports and a classroom URL

from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL = "https://quotes.toscrape.com/"
# USER_AGENT is sent in the HTTP request headers. It names this script instead
# of making the request look like a completely anonymous Python process.
USER_AGENT = "methodsNET-VLOP-course/1.0 static scraping walkthrough"


# %% 2. Check robots.txt as a first access signal

parsed = urlparse(URL)
# urlparse() splits a URL into components such as scheme ("https") and network
# location ("quotes.toscrape.com"). We use those parts to construct robots.txt.
robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

rp = RobotFileParser()
# set_url() tells RobotFileParser where the site's robots.txt file lives.
rp.set_url(robots_url)
# read() downloads and parses robots.txt. In larger projects, handle failures
# explicitly because some sites block or omit robots.txt.
rp.read()

# can_fetch() asks whether the given user agent is allowed to fetch URL under
# the robots.txt rules. This is a first access signal, not a full permission.
allowed = rp.can_fetch(USER_AGENT, URL)
print("robots.txt URL:", robots_url)
print("Can fetch classroom URL?", allowed)

# Discussion prompt:
# Why is robots.txt not the same as full legal or ethical permission?


# %% 3. Fetch the page once

# requests.get() retrieves the raw HTML returned by the server. The header adds
# our user agent; timeout=30 prevents the script from waiting forever.
response = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
# raise_for_status() makes HTTP errors visible. Without it, a 404 or 500 page
# might be parsed and saved as if it were the target content.
response.raise_for_status()

# response.text is the server response decoded as text. For static pages, this
# usually contains the content we want. For dynamic pages, it may only contain an
# empty app shell.
html = response.text
print("HTTP status:", response.status_code)
print("Characters of HTML:", len(html))
print(html[:500])


# %% 4. Save raw HTML before parsing

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
raw_dir = outdir / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

raw_html_path = raw_dir / "walkthrough_quotes_raw.html"
# Saving raw HTML before parsing lets students re-run extraction code without
# repeatedly contacting the site. It also creates evidence of exactly what the
# scraper saw at collection time.
raw_html_path.write_text(html, encoding=response.encoding or "utf-8")

print("Saved raw HTML:", raw_html_path)


# %% 5. Parse HTML and inspect the page structure

soup = BeautifulSoup(html, "html.parser")

# soup.title finds the <title> element in the HTML document. This is a quick
# sanity check that we fetched the expected page.
print("Page title:", soup.title.get_text(strip=True))
# a[href] is a CSS selector meaning "all <a> tags that have an href attribute."
# It counts links, not necessarily unique destinations.
print("Number of links:", len(soup.select("a[href]")))
# .quote is a CSS class selector. It means elements with class="quote". On this
# practice site, each quote block is wrapped in one such element.
print("Number of quote blocks:", len(soup.select(".quote")))

# In class: open the page in a browser, inspect one quote, and connect the DOM
# structure to the .quote, .text, .author, and .tags selectors below.


# %% 6. Extract repeated quote records

rows = []

for quote_block in soup.select(".quote"):
    # quote_block is one repeated record container. Everything selected inside
    # it belongs to that one quote, so we avoid mixing authors and texts from
    # different records.
    #
    # .text selects the element containing the quote text. The dot means "class",
    # not visible text.
    text = quote_block.select_one(".text")
    # .author selects the author name inside the same quote block.
    author = quote_block.select_one(".author")
    # .tags a.tag means: first look inside an element with class="tags", then
    # select <a> elements with class="tag". This returns all tags for the quote.
    tag_links = quote_block.select(".tags a.tag")

    rows.append(
        {
            # get_text(" ", strip=True) extracts visible text, joins internal
            # whitespace with spaces, and removes leading/trailing whitespace.
            # If text is missing, we store None so the missingness is visible.
            "quote": text.get_text(" ", strip=True) if text else None,
            "author": author.get_text(" ", strip=True) if author else None,
            # Multiple tags are collapsed into one pipe-separated string so they
            # fit in a simple CSV cell. A richer design could use one row per tag.
            "tags": "|".join(tag.get_text(" ", strip=True) for tag in tag_links),
            # tag_count is derived by our script, not collected directly from
            # the page. Derived fields should be easy to recompute.
            "tag_count": len(tag_links),
        }
    )

# The DataFrame is a structured table: each quote becomes one row, and each
# extracted or derived field becomes one column.
df = pd.DataFrame(rows)
print(df.head())


# %% 7. Extract links and resolve relative URLs

links = []

for link in soup.select("a[href]"):
    links.append(
        {
            # link_text is the clickable text between <a> and </a>.
            "link_text": link.get_text(" ", strip=True),
            # href_raw is exactly what appeared in the HTML, which may be a
            # relative path such as /page/2/.
            "href_raw": link["href"],
            # urljoin combines the page URL with a relative href to produce a
            # full absolute URL.
            "href_absolute": urljoin(URL, link["href"]),
        }
    )

links_df = pd.DataFrame(links)
print(links_df.head(10))


# %% 8. Save processed outputs

processed_dir = outdir / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

quotes_path = processed_dir / "walkthrough_quotes.csv"
links_path = processed_dir / "walkthrough_quotes_links.csv"

# index=False prevents pandas from writing its row number index as an extra CSV
# column. For teaching data, that extra column usually creates confusion.
df.to_csv(quotes_path, index=False)
links_df.to_csv(links_path, index=False)

print("Saved processed quote table:", quotes_path)
print("Saved link table:", links_path)


# %% 9. Selector robustness discussion

questions = [
    "Which selectors depend on visible content and which depend on HTML classes?",
    "What would break if the site renamed class='quote' to class='quotation'?",
    "Why did we save raw HTML before extracting rows?",
    "What would change if this page included user profiles or personal data?",
    "How would you limit the collection to what is necessary for a research question?",
]

for question in questions:
    print("-", question)
