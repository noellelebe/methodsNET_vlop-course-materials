"""Static web scraper for permitted classroom pages.

Example:
    python scripts/03_static_scraper.py --url https://quotes.toscrape.com/
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common import polite_get, provenance, robots_allowed, write_csv, write_json


def parse_page(url: str, html: str) -> tuple[dict, list[dict]]:
    # BeautifulSoup parses the HTML text into a searchable tree. This works well
    # for static pages where the content is already present in the HTML response.
    # It will not see content that is added later by JavaScript in the browser.
    soup = BeautifulSoup(html, "html.parser")

    # The summary is intentionally modest. In a first scraping exercise, students
    # should learn to inspect page structure before extracting large datasets.
    summary = {
        "url": url,
        "title": soup.title.get_text(" ", strip=True) if soup.title else None,
        "h1": " | ".join(h.get_text(" ", strip=True) for h in soup.select("h1")),
        "h2_count": len(soup.select("h2")),
        "link_count": len(soup.select("a[href]")),
    }
    links = []
    for a in soup.select("a[href]"):
        # CSS selector a[href] means: every <a> element that has an href
        # attribute. urljoin converts relative links such as /about into full
        # URLs, which makes the output easier to audit later.
        text = a.get_text(" ", strip=True)
        href = urljoin(url, a["href"])
        links.append({"source_url": url, "link_text": text, "href": href})
    return summary, links


def main() -> None:
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
    html = response.text
    summary, links = parse_page(args.url, html)

    outdir = Path(args.outdir)
    safe_name = args.url.replace("https://", "").replace("http://", "")
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]

    # Save the raw HTML snapshot. When a scraper breaks later, this snapshot lets
    # us determine whether the site changed or our parser was wrong.
    html_path = outdir / "raw" / f"scrape_{safe_name}.html"
    summary_path = outdir / "processed" / f"scrape_{safe_name}_summary.json"
    links_path = outdir / "processed" / f"scrape_{safe_name}_links.csv"
    report_path = outdir / "reports" / f"scrape_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding=response.encoding or "utf-8")
    write_json(summary_path, summary)
    write_csv(links_path, links)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "robots_allowed": allowed},
            outputs=[html_path, summary_path, links_path],
            notes=[
                "This script is for static pages and simple classroom parsing.",
                "Adapt selectors deliberately; do not collect more than needed.",
                "Raw HTML was saved so parsing decisions can be revisited.",
            ],
        ),
    )

    print(f"Title: {summary['title']}")
    print(f"Links extracted: {len(links)}")
    print(f"HTML: {html_path}")
    print(f"Links: {links_path}")


if __name__ == "__main__":
    main()
