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
USER_AGENT = "methodsNET-VLOP-course/1.0 static scraping walkthrough"


# %% 2. Check robots.txt as a first access signal

parsed = urlparse(URL)
robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

rp = RobotFileParser()
rp.set_url(robots_url)
rp.read()

allowed = rp.can_fetch(USER_AGENT, URL)
print("robots.txt URL:", robots_url)
print("Can fetch classroom URL?", allowed)

# Discussion prompt:
# Why is robots.txt not the same as full legal or ethical permission?


# %% 3. Fetch the page once

response = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
response.raise_for_status()

html = response.text
print("HTTP status:", response.status_code)
print("Characters of HTML:", len(html))
print(html[:500])


# %% 4. Save raw HTML before parsing

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
raw_dir = outdir / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

raw_html_path = raw_dir / "walkthrough_quotes_raw.html"
raw_html_path.write_text(html, encoding=response.encoding or "utf-8")

print("Saved raw HTML:", raw_html_path)


# %% 5. Parse HTML and inspect the page structure

soup = BeautifulSoup(html, "html.parser")

print("Page title:", soup.title.get_text(strip=True))
print("Number of links:", len(soup.select("a[href]")))
print("Number of quote blocks:", len(soup.select(".quote")))

# In class: open the page in a browser, inspect one quote, and connect the DOM
# structure to the .quote, .text, .author, and .tags selectors below.


# %% 6. Extract repeated quote records

rows = []

for quote_block in soup.select(".quote"):
    text = quote_block.select_one(".text")
    author = quote_block.select_one(".author")
    tag_links = quote_block.select(".tags a.tag")

    rows.append(
        {
            "quote": text.get_text(" ", strip=True) if text else None,
            "author": author.get_text(" ", strip=True) if author else None,
            "tags": "|".join(tag.get_text(" ", strip=True) for tag in tag_links),
            "tag_count": len(tag_links),
        }
    )

df = pd.DataFrame(rows)
print(df.head())


# %% 7. Extract links and resolve relative URLs

links = []

for link in soup.select("a[href]"):
    links.append(
        {
            "link_text": link.get_text(" ", strip=True),
            "href_raw": link["href"],
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
