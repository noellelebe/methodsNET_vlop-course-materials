"""Static web scraper for permitted classroom pages.

Example:
    python scripts/runnable_workflows/03_static_scraper.py --url https://quotes.toscrape.com/
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common import polite_get, provenance, robots_allowed, write_json


FIELDNAMES = {
    "headings": ["source_url", "level", "text"],
    "links": ["source_url", "link_text", "href_raw", "href_absolute", "link_type"],
    "quotes": [
        "source_url",
        "quote_number",
        "quote",
        "author",
        "author_href",
        "tags",
        "tag_count",
    ],
    "tags": ["source_url", "quote_number", "quote", "tag", "tag_href"],
    "pagination": ["source_url", "link_text", "href_raw", "href_absolute"],
    "images": ["source_url", "src_raw", "src_absolute", "alt"],
}


def write_table(path: str | Path, rows: list[dict], fieldnames: list[str]) -> Path:
    """Write a CSV with stable headers, even when rows is empty."""
    # Convert strings to Path objects so the rest of the function can use Path
    # methods such as .parent and .open().
    path = Path(path)
    # Create the output folder if it does not yet exist.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        # DictWriter writes dictionaries as CSV rows using the fixed field order.
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write headers even for empty tables so students can see the intended
        # data structure.
        writer.writeheader()
        # Write all extracted rows.
        writer.writerows(rows)
    return path


def classify_link(href: str) -> str:
    """Classify common classroom-page link roles from their URL path."""
    # startswith() is a simple rule-based classifier for known URL patterns.
    if href.startswith("/author/"):
        return "author_profile"
    if href.startswith("/tag/"):
        return "tag_page"
    if href.startswith("/page/"):
        return "pagination"
    if href.startswith("#"):
        return "same_page_anchor"
    return "other"


def parse_page(url: str, html: str) -> dict[str, object]:
    # BeautifulSoup parses the HTML text into a searchable tree. This works well
    # for static pages where the content is already present in the HTML response.
    # It will not see content that is added later by JavaScript in the browser.
    soup = BeautifulSoup(html, "html.parser")

    # select_one returns the first matching element or None. Here we look for a
    # metadata tag such as <meta name="description" content="...">.
    meta_description = soup.select_one("meta[name='description']")

    # The summary is intentionally modest. In a first scraping exercise, students
    # should learn to inspect page structure before extracting large datasets.
    summary = {
        "url": url,
        "title": soup.title.get_text(" ", strip=True) if soup.title else None,
        "description": meta_description.get("content") if meta_description else None,
        "h1": " | ".join(h.get_text(" ", strip=True) for h in soup.select("h1")),
        "h2_count": len(soup.select("h2")),
        "link_count": len(soup.select("a[href]")),
        "image_count": len(soup.select("img[src]")),
        "quote_block_count": len(soup.select(".quote")),
    }

    headings = []
    for level in ["h1", "h2", "h3"]:
        # Loop over heading levels so one piece of code can extract h1, h2, h3.
        for heading in soup.select(level):
            # get_text(" ", strip=True) extracts visible text, joins internal
            # whitespace with spaces, and trims leading/trailing whitespace.
            headings.append(
                {
                    "source_url": url,
                    "level": level,
                    "text": heading.get_text(" ", strip=True),
                }
            )

    links = []
    for a in soup.select("a[href]"):
        # CSS selector a[href] means: every <a> element that has an href
        # attribute. urljoin converts relative links such as /about into full
        # URLs, which makes the output easier to audit later.
        text = a.get_text(" ", strip=True)
        # Square brackets access a required attribute. This is safe here because
        # the selector a[href] only selected links with an href attribute.
        href_raw = a["href"]
        # urljoin handles both absolute URLs and relative paths.
        href = urljoin(url, href_raw)
        links.append(
            {
                "source_url": url,
                "link_text": text,
                "href_raw": href_raw,
                "href_absolute": href,
                "link_type": classify_link(href_raw),
            }
        )

    quote_rows = []
    tag_rows = []
    for quote_number, quote_block in enumerate(soup.select(".quote"), start=1):
        # The quotes.toscrape.com classroom page uses .quote as one repeated
        # record container. If another site does not use this structure, these
        # tables will simply be empty and students should adapt the selectors.
        text = quote_block.select_one(".text")
        author = quote_block.select_one(".author")
        author_link = quote_block.select_one("span a[href]")
        tag_links = quote_block.select(".tags a.tag")

        tags = [tag.get_text(" ", strip=True) for tag in tag_links]
        quote_text = text.get_text(" ", strip=True) if text else None

        # One quote row keeps the main record in one table.
        quote_rows.append(
            {
                "source_url": url,
                "quote_number": quote_number,
                "quote": quote_text,
                "author": author.get_text(" ", strip=True) if author else None,
                # If the author link is missing, store None instead of crashing.
                "author_href": urljoin(url, author_link.get("href")) if author_link else None,
                "tags": "|".join(tags),
                "tag_count": len(tags),
            }
        )

        for tag_link in tag_links:
            # A second tags table uses one row per quote-tag pair. This is better
            # for counting/filtering tags than storing all tags in one cell.
            tag_rows.append(
                {
                    "source_url": url,
                    "quote_number": quote_number,
                    "quote": quote_text,
                    "tag": tag_link.get_text(" ", strip=True),
                    "tag_href": urljoin(url, tag_link.get("href")),
                }
            )

    pagination = []
    for a in soup.select("li.next a[href], .pager a[href]"):
        # The comma in a CSS selector means OR: match either selector pattern.
        pagination.append(
            {
                "source_url": url,
                "link_text": a.get_text(" ", strip=True),
                "href_raw": a.get("href"),
                "href_absolute": urljoin(url, a.get("href")),
            }
        )

    images = []
    for image in soup.select("img[src]"):
        # Image URLs often appear as relative paths, so we again store both the
        # raw attribute and the absolute URL.
        images.append(
            {
                "source_url": url,
                "src_raw": image.get("src"),
                "src_absolute": urljoin(url, image.get("src")),
                "alt": image.get("alt"),
            }
        )

    return {
        "summary": summary,
        "headings": headings,
        "links": links,
        "quotes": quote_rows,
        "tags": tag_rows,
        "pagination": pagination,
        "images": images,
    }


def main() -> None:
    # Command-line arguments let the same scraper run against different allowed
    # pages without editing the Python file.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--outdir", default="data")
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Do not block collection if robots.txt disallows the URL.",
    )
    args = parser.parse_args()

    # robots.txt is not the whole legal/ethical story, but it is a useful first
    # check. If this blocks the classroom example, choose another page rather
    # than teaching students to treat access controls as puzzles to defeat.
    allowed = robots_allowed(args.url)
    if allowed is False and not args.ignore_robots:
        raise SystemExit(
            "robots.txt check disallows this URL. Use a different classroom page."
        )

    # We fetch once, then parse locally. Separating collection from parsing makes
    # scraper development safer: students can refine selectors without repeatedly
    # hitting the website.
    response = polite_get(args.url, delay_seconds=1.5)
    # For static pages, response.text is the HTML source we will parse.
    html = response.text
    # parse_page turns the raw HTML into several structured tables.
    parsed_page = parse_page(args.url, html)
    # The summary dictionary is used both for JSON output and status printing.
    summary = parsed_page["summary"]

    outdir = Path(args.outdir)
    # Build a filesystem-safe filename stem from the URL.
    safe_name = args.url.replace("https://", "").replace("http://", "")
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]

    # Save the raw HTML snapshot. When a scraper breaks later, this snapshot lets
    # us determine whether the site changed or our parser was wrong.
    html_path = outdir / "raw" / f"scrape_{safe_name}.html"
    summary_path = outdir / "processed" / f"scrape_{safe_name}_summary.json"
    headings_path = outdir / "processed" / f"scrape_{safe_name}_headings.csv"
    links_path = outdir / "processed" / f"scrape_{safe_name}_links.csv"
    quotes_path = outdir / "processed" / f"scrape_{safe_name}_quotes.csv"
    tags_path = outdir / "processed" / f"scrape_{safe_name}_tags.csv"
    pagination_path = outdir / "processed" / f"scrape_{safe_name}_pagination.csv"
    images_path = outdir / "processed" / f"scrape_{safe_name}_images.csv"
    report_path = outdir / "reports" / f"scrape_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    # Use the server-provided encoding if available, otherwise default to UTF-8.
    html_path.write_text(html, encoding=response.encoding or "utf-8")
    # The following writes separate output tables so each extraction type can be
    # inspected independently.
    write_json(summary_path, summary)
    write_table(headings_path, parsed_page["headings"], FIELDNAMES["headings"])
    write_table(links_path, parsed_page["links"], FIELDNAMES["links"])
    write_table(quotes_path, parsed_page["quotes"], FIELDNAMES["quotes"])
    write_table(tags_path, parsed_page["tags"], FIELDNAMES["tags"])
    write_table(pagination_path, parsed_page["pagination"], FIELDNAMES["pagination"])
    write_table(images_path, parsed_page["images"], FIELDNAMES["images"])
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "robots_allowed": allowed},
            outputs=[
                html_path,
                summary_path,
                headings_path,
                links_path,
                quotes_path,
                tags_path,
                pagination_path,
                images_path,
            ],
            notes=[
                "This script is for static pages and simple classroom parsing.",
                "Adapt selectors deliberately; do not collect more than needed.",
                "Raw HTML was saved so parsing decisions can be revisited.",
                "Quote-specific outputs are populated for quotes.toscrape.com and empty otherwise.",
            ],
        ),
    )

    print(f"Title: {summary['title']}")
    print(f"Links extracted: {len(parsed_page['links'])}")
    print(f"Quote rows extracted: {len(parsed_page['quotes'])}")
    print(f"HTML: {html_path}")
    print(f"Links: {links_path}")
    print(f"Quotes: {quotes_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Run a Wikipedia static-HTML comparison from the repository root:
#
#     python scripts/runnable_workflows/03_static_scraper.py \
#       --url https://en.wikipedia.org/wiki/Digital_Services_Act \
#       --outdir data
#
# Run the clean repeated-record practice page:
#
#     python scripts/runnable_workflows/03_static_scraper.py \
#       --url https://quotes.toscrape.com/ \
#       --outdir data
#
# Optional controlled classroom override:
#
#     python scripts/runnable_workflows/03_static_scraper.py \
#       --url https://quotes.toscrape.com/ \
#       --outdir data \
#       --ignore-robots
#
# What each part means:
#
# - --url
#   The web page to fetch and parse. For Wikipedia, the generic heading/link/image
#   outputs are useful. For quotes.toscrape.com, quote-specific outputs are also
#   populated.
#
# - --outdir
#   The folder where raw HTML, processed CSV files, and provenance are saved.
#
# - --ignore-robots
#   Overrides the robots.txt block in a controlled teaching demo. Do not use
#   this casually; robots.txt is one access signal that should be taken seriously.
