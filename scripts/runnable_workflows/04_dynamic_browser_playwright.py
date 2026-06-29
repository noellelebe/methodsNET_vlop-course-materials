"""Browser automation example with Playwright.

Install browsers first:
    playwright install chromium

Example:
    python scripts/04_dynamic_browser_playwright.py --url https://quotes.toscrape.com/js/
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from urllib.parse import urljoin

from common import provenance, robots_allowed, write_csv, write_json


async def collect(url: str, scrolls: int, wait_ms: int) -> tuple[str, list[dict], bytes]:
    # Playwright is imported inside the function so the rest of the script can be
    # inspected even before browser dependencies are installed.
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # headless=True means no visible browser window. For live teaching, set
        # this to False so students can watch the browser navigate and scroll.
        browser = await p.chromium.launch(headless=True)
        # new_page() creates one browser tab/page for this collection run.
        page = await browser.new_page()

        # networkidle waits until network activity has settled. Dynamic pages are
        # often incomplete immediately after navigation, so waiting strategy is a
        # key methodological choice.
        await page.goto(url, wait_until="networkidle")

        # Infinite scroll is not magic: we scroll, wait, and later verify whether
        # the number of extracted items changed. The default limits are small
        # because this is a classroom demonstration, not bulk collection.
        for _ in range(scrolls):
            # mouse.wheel scrolls the rendered page. This can trigger lazy
            # loading on pages that load more content as the user scrolls.
            await page.mouse.wheel(0, 1800)
            # wait_for_timeout gives the page time to load content after each
            # scroll. The time is in milliseconds.
            await page.wait_for_timeout(wait_ms)

        # page.content() returns the rendered DOM after JavaScript has run. This
        # may differ substantially from the static HTML returned by requests.
        html = await page.content()

        # eval_on_selector_all runs a small JavaScript function in the page. Here
        # we extract link text and resolved hrefs from the rendered document.
        links = await page.eval_on_selector_all(
            "a[href]",
            """els => els.map(a => ({
                link_text: a.innerText.trim(),
                href: a.href
            }))""",
        )

        # A screenshot is research documentation: it shows what the script saw at
        # collection time and helps catch cookie banners, broken loads, or layout
        # states that raw HTML alone may not make obvious.
        screenshot = await page.screenshot(full_page=True)
        await browser.close()

        # Turn the JavaScript-extracted link objects into CSV-ready rows.
        rows = [
            {
                # source_url records which page produced this link.
                "source_url": url,
                # link_text is text extracted by JavaScript from the rendered page.
                "link_text": item["link_text"],
                # urljoin makes sure relative links become absolute URLs.
                "href": urljoin(url, item["href"]),
            }
            for item in links
        ]
    return html, rows, screenshot


def main() -> None:
    # argparse reads the command-line options used for this run.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--scrolls", type=int, default=2)
    parser.add_argument("--wait-ms", type=int, default=1000)
    parser.add_argument("--outdir", default="data")
    parser.add_argument("--ignore-robots", action="store_true")
    args = parser.parse_args()

    # As with static scraping, robots.txt is a first-line check rather than a
    # complete ethics review. Dynamic automation can impose more server load than
    # static fetching, so conservative defaults matter.
    allowed = robots_allowed(args.url)
    if allowed is False and not args.ignore_robots:
        raise SystemExit(
            "robots.txt check disallows this URL. Use a different classroom page."
        )

    safe_name = args.url.replace("https://", "").replace("http://", "")
    # Keep only alphanumeric characters in filenames so URLs do not create
    # awkward path separators or punctuation-heavy names.
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]
    outdir = Path(args.outdir)

    # asyncio.run starts the asynchronous Playwright workflow from normal Python
    # code. The collect() function returns rendered HTML, link rows, screenshot.
    html, links, screenshot = asyncio.run(collect(args.url, args.scrolls, args.wait_ms))

    # Saving rendered HTML and screenshot together lets students compare "what
    # the browser saw" with "what the parser extracted."
    html_path = outdir / "raw" / f"browser_{safe_name}.html"
    image_path = outdir / "raw" / f"browser_{safe_name}.png"
    links_path = outdir / "processed" / f"browser_{safe_name}_links.csv"
    report_path = outdir / "reports" / f"browser_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    # write_text saves the rendered HTML snapshot.
    html_path.write_text(html, encoding="utf-8")
    # write_bytes saves the PNG screenshot bytes.
    image_path.write_bytes(screenshot)
    write_csv(links_path, links)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "robots_allowed": allowed},
            outputs=[html_path, image_path, links_path],
            notes=[
                "Browser automation captures rendered page state.",
                "Check site policies and do not use automation to bypass controls.",
                "Use the screenshot as a visual audit of the collection state.",
            ],
        ),
    )

    print(f"Rendered HTML: {html_path}")
    print(f"Screenshot: {image_path}")
    print(f"Links: {links_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Install the browser once if needed:
#
#     playwright install chromium
#
# Browser-automation comparison with the same Wikipedia page:
#
#     python scripts/runnable_workflows/04_dynamic_browser_playwright.py \
#       --url https://en.wikipedia.org/wiki/Digital_Services_Act \
#       --scrolls 0 \
#       --wait-ms 1000 \
#       --outdir data
#
# Main JavaScript-rendered classroom example:
#
#     python scripts/runnable_workflows/04_dynamic_browser_playwright.py \
#       --url https://quotes.toscrape.com/js/ \
#       --scrolls 2 \
#       --wait-ms 1000 \
#       --outdir data
#
# What each part means:
#
# - playwright install chromium
#   Downloads the Chromium browser used by Playwright.
#
# - --url
#   The page opened in the automated browser. Use Wikipedia for comparison with
#   API/static routes; use quotes.toscrape.com/js/ to demonstrate JS rendering.
#
# - --scrolls
#   How many times the script scrolls down to trigger dynamic loading.
#
# - --wait-ms
#   How long to wait after page load/scrolling, in milliseconds.
#
# - --outdir
#   The folder where rendered HTML, screenshots/metadata, and reports are saved.
#
# - --ignore-robots
#   Overrides the robots.txt check in a controlled demo. Do not use casually.
