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
from pprint import pprint
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL = "https://quotes.toscrape.com/"
# USER_AGENT is sent in the HTTP request headers. It names this script instead
# of making the request look like a completely anonymous Python process.
# It can be chosen by the researcher, but it should be meaningful rather than
# pretending to be a normal browser or someone else.

USER_AGENT = "methodsNET-VLOP-course/1.0_static_scraping_walkthrough"


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
pprint(html[:500])


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

# prettify() makes the nested HTML easier to read. Do not print the whole page
# every time in a large project; it is useful here because this is a small
# classroom page.
print(soup.prettify()[:1500])

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


# %% 6. Inspect one repeated record before looping

# A good scraping workflow starts with one record. If we cannot correctly parse
# one quote block, looping over all quote blocks will only repeat the mistake.
first_quote = soup.select_one(".quote")

print(first_quote.prettify())

# These selectors are searched inside first_quote, not across the whole page.
# That keeps the quote text, author, tags, and author link from the same record
# together.
print("Quote text element:", first_quote.select_one(".text"))
print("Author element:", first_quote.select_one(".author"))
print("Tag link elements:", first_quote.select(".tags a.tag"))
print("Author profile link:", first_quote.select_one("span a[href]"))


# %% 7. Extract repeated quote records


rows = []

for quote_block in soup.select(".quote"):
    # quote_block is one repeated record container. Everything selected inside it
    # belongs to that one quote, so we avoid mixing authors and texts from
    # different records.
    text = quote_block.select_one(".text")
    author = quote_block.select_one(".author")
    tag_links = quote_block.select(".tags a.tag")
    author_link = quote_block.select_one("span a[href]")

    quote_text = text.get_text(" ", strip=True) if text else None
    author_name = author.get_text(" ", strip=True) if author else None
    tags = "|".join(tag.get_text(" ", strip=True) for tag in tag_links)
    tag_count = len(tag_links)
    author_href = author_link.get("href") if author_link else None

    row = dict(
        quote=quote_text,
        author=author_name,
        author_href_raw=author_href,
        author_href_absolute=urljoin(URL, author_href) if author_href else None,
        tags=tags,
        tag_count=tag_count,
    )

    rows.append(row)

# The DataFrame is a structured table: each quote becomes one row, and each
# extracted or derived field becomes one column.
df = pd.DataFrame(rows)
print(df.head())


# %% 8. Extract links and resolve relative URLs

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


# %% 9. Classify links by page role

# A scraping task often needs to distinguish content links from navigation.
# On this page, author links, tag links, and pagination links have different
# meanings even though they are all <a href="..."> elements.
classified_links = []

for link in soup.select("a[href]"):
    href_raw = link.get("href")
    href_absolute = urljoin(URL, href_raw)

    if href_raw.startswith("/author/"):
        link_type = "author_profile"
    elif href_raw.startswith("/tag/"):
        link_type = "tag_page"
    elif href_raw.startswith("/page/"):
        link_type = "pagination"
    else:
        link_type = "other"

    classified_links.append(
        {
            "link_text": link.get_text(" ", strip=True),
            "href_raw": href_raw,
            "href_absolute": href_absolute,
            "link_type": link_type,
        }
    )

classified_links_df = pd.DataFrame(classified_links)
print(classified_links_df)


# %% 10. Extract tags as a separate table

# Earlier we stored tags as one pipe-separated string in the quote table. That is
# convenient for a quick CSV, but sometimes tags should become their own table:
# one row per quote-tag combination.
tag_rows = []

for quote_number, quote_block in enumerate(soup.select(".quote"), start=1):
    text = quote_block.select_one(".text")
    quote_text = text.get_text(" ", strip=True) if text else None

    for tag_link in quote_block.select(".tags a.tag"):
        tag_rows.append(
            {
                "quote_number": quote_number,
                "quote": quote_text,
                "tag": tag_link.get_text(" ", strip=True),
                "tag_href": urljoin(URL, tag_link.get("href")),
            }
        )

tags_df = pd.DataFrame(tag_rows)
print(tags_df.head(15))


# %% 11. Extract pagination links

# Pagination links define how a scraper could move from this page to the next
# page. We inspect them separately because following pagination changes the
# collection scope.
pagination_links = []

for link in soup.select("li.next a[href], .pager a[href]"):
    pagination_links.append(
        {
            "link_text": link.get_text(" ", strip=True),
            "href_raw": link.get("href"),
            "href_absolute": urljoin(URL, link.get("href")),
        }
    )

pagination_df = pd.DataFrame(pagination_links)
print(pagination_df)


# %% 12. Extract page-level metadata, headings, and images

# Not all useful data are repeated records. Sometimes we also want page-level
# context: title, headings, metadata, or images.
meta_description = soup.select_one("meta[name='description']")

page_metadata = {
    "url": URL,
    "title": soup.title.get_text(" ", strip=True) if soup.title else None,
    "description": meta_description.get("content") if meta_description else None,
    "h1_text": " | ".join(h.get_text(" ", strip=True) for h in soup.select("h1")),
    "quote_count": len(soup.select(".quote")),
    "link_count": len(soup.select("a[href]")),
}

pprint(page_metadata)

image_rows = []

for image in soup.select("img[src]"):
    image_rows.append(
        {
            "src_raw": image.get("src"),
            "src_absolute": urljoin(URL, image.get("src")),
            "alt": image.get("alt"),
        }
    )

images_df = pd.DataFrame(image_rows)
print(images_df)


# %% 13. Save processed outputs

processed_dir = outdir / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

quotes_path = processed_dir / "walkthrough_quotes.csv"
links_path = processed_dir / "walkthrough_quotes_links.csv"
classified_links_path = processed_dir / "walkthrough_quotes_classified_links.csv"
tags_path = processed_dir / "walkthrough_quotes_tags.csv"
pagination_path = processed_dir / "walkthrough_quotes_pagination.csv"
metadata_path = processed_dir / "walkthrough_quotes_page_metadata.json"
images_path = processed_dir / "walkthrough_quotes_images.csv"

# index=False prevents pandas from writing its row number index as an extra CSV
# column. For teaching data, that extra column usually creates confusion.
df.to_csv(quotes_path, index=False)
links_df.to_csv(links_path, index=False)
classified_links_df.to_csv(classified_links_path, index=False)
tags_df.to_csv(tags_path, index=False)
pagination_df.to_csv(pagination_path, index=False)
pd.Series(page_metadata).to_json(metadata_path, indent=2)
images_df.to_csv(images_path, index=False)

print("Saved processed quote table:", quotes_path)
print("Saved link table:", links_path)
print("Saved classified link table:", classified_links_path)
print("Saved tag table:", tags_path)
print("Saved pagination table:", pagination_path)
print("Saved page metadata:", metadata_path)
print("Saved image table:", images_path)


# %% 14. Selector robustness discussion

questions = [
    "Which selectors depend on visible content and which depend on HTML classes?",
    "What would break if the site renamed class='quote' to class='quotation'?",
    "Why did we extract tags both as one CSV cell and as a separate table?",
    "Which links are content links, and which are navigation links?",
    "How would following the pagination link change the dataset?",
    "Why did we save raw HTML before extracting rows?",
    "What would change if this page included user profiles or personal data?",
    "How would you limit the collection to what is necessary for a research question?",
]

for question in questions:
    print("-", question)
