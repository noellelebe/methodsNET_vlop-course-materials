"""Teaching walkthrough: BeautifulSoup extraction patterns.

This file is a companion to book/handouts/beautifulsoup_extraction_patterns.md.
It uses a small artificial HTML document so students can focus on selectors,
nested tags, missing fields, attributes, siblings, tables, images, and metadata
without depending on a live website.
"""

# %% 1. Imports and a small HTML document

from io import StringIO
from pprint import pprint
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup


PAGE_URL = "https://example.org/search?q=dsa"

html = """
<!doctype html>
<html>
  <head>
    <title>Platform research examples</title>
    <meta property="og:title" content="Platform research search results">
    <meta name="description" content="Example page for static scraping practice.">
  </head>
  <body>
    <main id="content">
      <h1>Search results for platform governance</h1>

      <article class="result card featured" data-id="A17" data-source="registry">
        <h2><a href="/items/a17">Digital Services Act explainer</a></h2>
        <p class="summary">A short introduction to platform accountability.</p>
        <div class="related">
          <p>Related item that is nested inside the card.</p>
        </div>
        <span class="date">2026-06-24</span>
        <ul class="tags">
          <li>EU</li>
          <li>platform governance</li>
          <li>regulation</li>
        </ul>
        <a class="download" href="/files/dsa-explainer.pdf">Download PDF</a>
      </article>

      <article class="result card" data-id="B22" data-source="archive">
        <h2><a href="/items/b22">Transparency report collection</a></h2>
        <p class="summary">Reports from several large online platforms.</p>
        <span class="date">2026-06-25</span>
        <ul class="tags">
          <li>transparency</li>
          <li>reports</li>
        </ul>
      </article>

      <article class="result card" data-id="C03">
        <h2>Result without link</h2>
        <p class="summary">This record has no title link and no date.</p>
      </article>

      <section class="result">
        <div class="card note">This is a nested card inside a result.</div>
      </section>

      <dl class="metadata">
        <dt>Published</dt>
        <dd>2026-06-24</dd>
        <dt>Author</dt>
        <dd>Noelle</dd>
        <dt>Topic</dt>
        <dd>Platform governance</dd>
      </dl>

      <table class="results-table">
        <thead>
          <tr><th>Name</th><th>Status</th><th>Count</th></tr>
        </thead>
        <tbody>
          <tr><td>API records</td><td>complete</td><td>120</td></tr>
          <tr><td>Scraped pages</td><td>partial</td><td>15</td></tr>
        </tbody>
      </table>

      <figure>
        <img src="/images/dsa-chart.png" alt="Chart of DSA reports">
        <figcaption>Example chart.</figcaption>
      </figure>
    </main>
  </body>
</html>
"""

soup = BeautifulSoup(html, "html.parser")


# %% 2. First inspection: what kind of document did we parse?

print("Page title:", soup.title.get_text(strip=True))
print("H1:", soup.select_one("h1").get_text(" ", strip=True))
print("Number of links:", len(soup.select("a[href]")))
print("Number of result cards:", len(soup.select("article.result.card")))


# %% 3. select() vs select_one()

# select() always returns a list, even if there is only one match.
all_cards = soup.select("article.result.card")
print(type(all_cards))
print("Cards:", len(all_cards))

# select_one() returns the first match, or None if there is no match.
first_card = soup.select_one("article.result.card")
print(type(first_card))
print(first_card.get("data-id"))


# %% 4. Multiple classes: .result.card vs .result .card

# .result.card means: one element that has both classes at the same time.
same_element = soup.select(".result.card")
print(".result.card count:", len(same_element))
print([tag.name + ":" + " ".join(tag.get("class", [])) for tag in same_element])

# .result .card means: an element with class card somewhere inside an element
# with class result. The space is important.
nested_element = soup.select(".result .card")
print(".result .card count:", len(nested_element))
print([tag.name + ":" + " ".join(tag.get("class", [])) for tag in nested_element])

# .result, .card means: elements matching .result OR .card.
either_element = soup.select(".result, .card")
print(".result, .card count:", len(either_element))


# %% 5. Extract one repeated card safely

card = soup.select_one("article.result.card")

title_link = card.select_one("h2 a")
summary = card.select_one(".summary")
date = card.select_one(".date")
tag_items = card.select(".tags li")

one_row = {
    "record_id": card.get("data-id"),
    "source": card.get("data-source"),
    "title": title_link.get_text(" ", strip=True) if title_link else None,
    "href": title_link.get("href") if title_link else None,
    "summary": summary.get_text(" ", strip=True) if summary else None,
    "date": date.get_text(" ", strip=True) if date else None,
    "tags": [tag.get_text(" ", strip=True) for tag in tag_items],
}

pprint(one_row)


# %% 6. Extract all repeated cards into rows

rows = []

for card in soup.select("article.result.card"):
    title_link = card.select_one("h2 a")
    summary = card.select_one(".summary")
    date = card.select_one(".date")
    tag_items = card.select(".tags li")

    tags = [tag.get_text(" ", strip=True) for tag in tag_items]

    row = {
        "record_id": card.get("data-id"),
        "source": card.get("data-source"),
        "title": title_link.get_text(" ", strip=True) if title_link else None,
        "href_raw": title_link.get("href") if title_link else None,
        "href_absolute": urljoin(PAGE_URL, title_link.get("href")) if title_link else None,
        "summary": summary.get_text(" ", strip=True) if summary else None,
        "date": date.get_text(" ", strip=True) if date else None,
        # Lists are good inside Python. If saving to CSV, a pipe-separated string
        # is often easier for students to inspect.
        "tags": "|".join(tags),
        "tag_count": len(tags),
    }

    rows.append(row)

cards_df = pd.DataFrame(rows)
print(cards_df)


# %% 7. Attribute selectors

# All links with an href attribute.
print("All hrefs:")
for link in soup.select("a[href]"):
    print("-", link.get("href"))

# Links ending in .pdf.
pdf_links = soup.select("a[href$='.pdf']")
print("PDF links:", [link.get("href") for link in pdf_links])

# Elements with a data-source attribute.
data_source_records = soup.select("[data-source]")
print("Records with data-source:", [tag.get("data-id") for tag in data_source_records])

# Elements where data-source is exactly archive.
archive_records = soup.select("[data-source='archive']")
print("Archive records:", [tag.get("data-id") for tag in archive_records])


# %% 8. Direct children vs any descendant

# article p means any paragraph anywhere inside an article.
all_article_paragraphs = soup.select("article p")
print("article p:", [p.get_text(" ", strip=True) for p in all_article_paragraphs])

# article > p means paragraph tags that are direct children of article.
direct_article_paragraphs = soup.select("article > p")
print("article > p:", [p.get_text(" ", strip=True) for p in direct_article_paragraphs])


# %% 9. Parents and siblings for label-value structures

# In a definition list, the value often sits in the next sibling after a label.
published_label = soup.find("dt", string="Published")

published = None
if published_label:
    published_value = published_label.find_next_sibling("dd")
    if published_value:
        published = published_value.get_text(strip=True)

print("Published:", published)

# Extract all dt/dd pairs into a dictionary.
metadata = {}
for label in soup.select("dl.metadata dt"):
    value = label.find_next_sibling("dd")
    metadata[label.get_text(strip=True)] = value.get_text(strip=True) if value else None

pprint(metadata)


# %% 10. Tables

table_rows = []

for tr in soup.select("table.results-table tbody tr"):
    cells = [td.get_text(" ", strip=True) for td in tr.select("td")]

    table_rows.append(
        {
            "name": cells[0] if len(cells) > 0 else None,
            "status": cells[1] if len(cells) > 1 else None,
            "count": cells[2] if len(cells) > 2 else None,
        }
    )

table_df = pd.DataFrame(table_rows)
print(table_df)

# pandas can also read simple HTML tables directly.
tables = pd.read_html(StringIO(html))
print(tables[0])


# %% 11. Images and metadata

image_rows = []

for img in soup.select("img[src]"):
    image_rows.append(
        {
            "src_raw": img.get("src"),
            "src_absolute": urljoin(PAGE_URL, img.get("src")),
            "alt": img.get("alt"),
        }
    )

print(pd.DataFrame(image_rows))

og_title = soup.select_one("meta[property='og:title']")
description = soup.select_one("meta[name='description']")

head_metadata = {
    "og_title": og_title.get("content") if og_title else None,
    "description": description.get("content") if description else None,
}

pprint(head_metadata)


# %% 12. Debugging selectors

selector = ".result.card"
matches = soup.select(selector)

print("Selector:", selector)
print("Number of matches:", len(matches))

if matches:
    print("First match:")
    print(matches[0].prettify())


# %% 13. Teaching prompts

questions = [
    "What is the difference between .result.card and .result .card?",
    "Why do we loop over record containers before extracting fields?",
    "Which examples return a list, and which return one tag?",
    "Where did the script handle missing fields explicitly?",
    "When would you save tags as a list, as a string, or as a separate table?",
    "Which selectors would be fragile if the website changed its CSS classes?",
]

for question in questions:
    print("-", question)
