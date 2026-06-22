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
        page = await browser.new_page()

        # networkidle waits until network activity has settled. Dynamic pages are
        # often incomplete immediately after navigation, so waiting strategy is a
        # key methodological choice.
        await page.goto(url, wait_until="networkidle")

        # Infinite scroll is not magic: we scroll, wait, and later verify whether
        # the number of extracted items changed. The default limits are small
        # because this is a classroom demonstration, not bulk collection.
        for _ in range(scrolls):
            await page.mouse.wheel(0, 1800)
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

    rows = [
        {"source_url": url, "link_text": item["link_text"], "href": urljoin(url, item["href"])}
        for item in links
    ]
    return html, rows, screenshot


def main() -> None:
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
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]
    outdir = Path(args.outdir)

    html, links, screenshot = asyncio.run(collect(args.url, args.scrolls, args.wait_ms))

    # Saving rendered HTML and screenshot together lets students compare "what
    # the browser saw" with "what the parser extracted."
    html_path = outdir / "raw" / f"browser_{safe_name}.html"
    image_path = outdir / "raw" / f"browser_{safe_name}.png"
    links_path = outdir / "processed" / f"browser_{safe_name}_links.csv"
    report_path = outdir / "reports" / f"browser_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
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
